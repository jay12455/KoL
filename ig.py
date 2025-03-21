from playwright.sync_api import sync_playwright
import time
import json
import re
from datetime import datetime
import random
from tqdm import tqdm

USERNAMES = ["huangjiji51", "73_tricking"]
MAX_REELS = 2

def get_random_user_agent():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ]
    return random.choice(user_agents)

def convert_views(views_text):
    views_text = views_text.replace(',', '')
    match = re.search(r'(\d+(\.\d+)?)萬', views_text)
    if match:
        return int(float(match.group(1)) * 10000)
    elif views_text.isdigit():
        return int(views_text)
    return 0

def add_random_delay():
    time.sleep(random.uniform(2, 4))

def extract_likes_comments(text):
    """ 從 meta 標籤提取 likes 和 comments 數字，支持 K 格式和逗號分隔 """
    # 修改正則表達式以支持帶逗號的數字
    match = re.search(r'(\d+(?:,\d+)?(?:\.\d+)?[Kk]?)\s*likes,\s*(\d+(?:,\d+)?)\s*comments', text, re.IGNORECASE)
    if match:
        # 處理讚數（移除逗號並處理 K）
        likes_str = match.group(1).replace(',', '')  # 移除逗號
        if 'K' in likes_str.upper():
            likes = int(float(likes_str.replace('K', '').replace('k', '')) * 1000)
        else:
            likes = int(likes_str)

        # 處理留言數（移除逗號）
        comments_str = match.group(2).replace(',', '')
        comments = int(comments_str)

        return likes, comments
    return 0, 0  # 如果找不到則回傳 0

def get_reels_likes_comments(page, reels_url):
    """
    從特定 Reels URL 提取讚數和留言數
    
    Args:
        page: Playwright 頁面物件
        reels_url: Reels 的完整 URL
    
    Returns:
        dict: 包含讚數和留言數的字典
    """
    if reels_url == "N/A":
        return {
            "likes": 0,
            "comments": 0,
            "url": reels_url
        }

    try:
        page.goto(reels_url)
        page.wait_for_load_state("networkidle", timeout=20000)
        add_random_delay()  # 添加隨機延遲

        # 嘗試從 meta 標籤提取（優先使用 og:description）
        meta_element = page.query_selector('meta[property="og:description"]') or \
                       page.query_selector('meta[name="description"]')
        
        meta_content = meta_element.get_attribute("content") if meta_element else ""
        
        likes, comments = extract_likes_comments(meta_content)

        # 如果 meta 標籤無法提取，則嘗試網頁上的元素
        if likes == 0 and comments == 0:
            # 嘗試從頁面元素提取讚數
            likes_selector = 'a[href$="/liked_by/"] span span'
            likes_element = page.query_selector(likes_selector)
            if likes_element:
                likes_text = likes_element.inner_text().replace('個讚', '').replace(',', '')
                likes = int(likes_text) if likes_text.isdigit() else 0

            # 嘗試從頁面元素提取留言數
            comments_selector = 'div[role="button"] span'
            comments_elements = page.query_selector_all(comments_selector)
            for elem in comments_elements:
                comments_text = elem.inner_text()
                if '則留言' in comments_text:
                    comments_text = comments_text.replace('則留言', '').replace(',', '')
                    try:
                        comments = int(comments_text)
                        break
                    except ValueError:
                        pass

        return {
            "likes": likes,
            "comments": comments,
            "url": reels_url
        }
    
    except Exception as e:
        print(f"Error extracting data from {reels_url}: {e}")
        return {
            "likes": 0,
            "comments": 0,
            "url": reels_url
        }

def get_instagram_data(username):
    with sync_playwright() as p:
        browser_params = {
            "headless": True,
            "args": [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-infobars',
                '--window-position=0,0',
                '--ignore-certificate-errors',
                '--ignore-certificate-errors-spki-list',
                '--user-agent=' + get_random_user_agent(),
            ]
        }
        
        browser = p.chromium.launch(**browser_params)
        context = browser.new_context(
            storage_state="ig_login_state.json",
            viewport={'width': 1920, 'height': 1080},
            user_agent=get_random_user_agent(),
            java_script_enabled=True,
            locale='zh-TW',
            timezone_id='Asia/Taipei',
            permissions=['geolocation'],
            geolocation={'latitude': 25.105497, 'longitude': 121.597366},
            color_scheme='light',
            device_scale_factor=1,
            is_mobile=False,
            has_touch=False,
        )
        
        context.set_extra_http_headers({
            'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Connection': 'keep-alive',
            'Accept-Encoding': 'gzip, deflate, br',
        })

        page = context.new_page()

        profile_url = f"https://www.instagram.com/{username}/"
        page.goto(profile_url)
        page.wait_for_selector("header", timeout=10000)
        add_random_delay()
        
        try:
            user_name = page.inner_text('header section h2')
            posts = page.inner_text('header section ul li:nth-child(1) span')
            followers = page.inner_text('header section ul li:nth-child(2) span')
            
            reels_url = f"https://www.instagram.com/{username}/reels/"
            page.goto(reels_url)
            page.wait_for_selector("main", timeout=10000)
            add_random_delay()

            reels_data = []
            seen_urls = set()

            last_height = page.evaluate("document.body.scrollHeight")
            with tqdm(total=MAX_REELS, desc=f"Scraping reels for {username}") as pbar:
                while len(reels_data) < MAX_REELS:
                    reels_container = page.query_selector("main")
                    if reels_container:
                        svg_icons = reels_container.query_selector_all("svg[aria-label='觀看次數圖示']")
                        if svg_icons:
                            for svg in svg_icons:
                                if len(reels_data) >= MAX_REELS:
                                    break
                                try:
                                    reel_link_element = svg.evaluate_handle("(el) => el.closest('a')")
                                    reel_link = reel_link_element.get_attribute("href") if reel_link_element else None
                                    reel_url = f"https://www.instagram.com{reel_link}" if reel_link else "N/A"

                                    if reel_url in seen_urls:
                                        continue
                                    seen_urls.add(reel_url)

                                    view_container = svg.evaluate_handle("(el) => el.closest('div').parentElement")
                                    spans = view_container.query_selector_all("span")

                                    for span in spans:
                                        views_text = span.inner_text().strip()
                                        views = convert_views(views_text)
                                        
                                        if views > 0:
                                            reel_data = {
                                                "reel_index": len(reels_data) + 1, 
                                                "views": views, 
                                                "link": reel_url
                                            }
                                            reels_data.append(reel_data)
                                            pbar.update(1)
                                            break

                                except Exception:
                                    pass

                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    add_random_delay()
                    new_height = page.evaluate("document.body.scrollHeight")
                    if new_height == last_height:
                        break
                    last_height = new_height

        except Exception as e:
            print(f"Error scraping {username}: {e}")

        browser.close()

        return {
            "username": username,
            "user_name": user_name,
            "posts_count": posts,
            "followers_count": followers,
            "reels_data": reels_data
        }

def main():
    all_data = []
    for user in USERNAMES:
        all_data.append(get_instagram_data(user))

    with sync_playwright() as p:
        browser_params = {
            "headless": True,
            "args": [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-infobars',
                '--window-position=0,0',
                '--ignore-certificate-errors',
                '--ignore-certificate-errors-spki-list',
                '--user-agent=' + get_random_user_agent(),
            ]
        }
        
        browser = p.chromium.launch(**browser_params)
        context = browser.new_context(
            storage_state="ig_login_state.json",
            viewport={'width': 1920, 'height': 1080},
            user_agent=get_random_user_agent(),
            java_script_enabled=True,
            locale='zh-TW',
            timezone_id='Asia/Taipei',
            permissions=['geolocation'],
            geolocation={'latitude': 25.105497, 'longitude': 121.597366},
            color_scheme='light',
            device_scale_factor=1,
            is_mobile=False,
            has_touch=False,
        )
        
        context.set_extra_http_headers({
            'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Connection': 'keep-alive',
            'Accept-Encoding': 'gzip, deflate, br',
        })

        page = context.new_page()

        try:
            for user_data in tqdm(all_data, desc="Fetching detailed Reels data"):
                for reel in tqdm(user_data['reels_data'], desc=f"Processing reels for {user_data['username']}", leave=False):
                    if 'likes' in reel and 'comments' in reel:
                        continue

                    reel_details = get_reels_likes_comments(page, reel['link'])
                    reel.update({
                        'likes': reel_details['likes'],
                        'comments': reel_details['comments']
                    })

        except Exception as e:
            print(f"Error during detailed Reels data extraction: {e}")
        
        finally:
            browser.close()

    date_str = datetime.now().strftime("%Y%m%d")
    filename = f"ig_data_{date_str}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=4, ensure_ascii=False)

    print(f"JSON data saved as {filename}")

if __name__ == "__main__":
    main()