import json
import datetime
from googleapiclient.discovery import build

# ✅ 設定 API Key 和頻道 ID
API_KEY = "AIzaSyAVA7btRMalrJpBwjYS9Vw2moKjxwZPGg0"
CHANNELS = {
    "奇軒Tricking": "UCvw1LiGdyulhnGksJlGWB6g",
    "黃吉吉的無聊日子": "UC5DmwNPnlO4oqWgdFRee0YA"
}

youtube = build("youtube", "v3", developerKey=API_KEY)

# ✅ 取得頻道的基本資訊
def get_channel_stats(channel_id):
    request = youtube.channels().list(
        part="statistics",
        id=channel_id
    )
    response = request.execute()

    if "items" in response and len(response["items"]) > 0:
        stats = response["items"][0]["statistics"]
        return {
            "訂閱數": stats.get("subscriberCount", "N/A"),
            "總影片數": stats.get("videoCount", "N/A"),
            "總觀看數": stats.get("viewCount", "N/A")
        }
    else:
        return None

# ✅ 取得最新 N 部影片的 ID
def get_latest_video_ids(channel_id, max_results=20):
    video_ids = []
    request = youtube.search().list(
        part="id",
        channelId=channel_id,
        maxResults=max_results,
        order="date",
        type="video"
    )
    response = request.execute()

    for item in response["items"]:
        video_ids.append(item["id"]["videoId"])

    return video_ids

# ✅ 取得影片的觀看數、按讚數、留言數
def get_video_stats(video_ids):
    video_data = []
    request = youtube.videos().list(
        part="statistics",
        id=",".join(video_ids)
    )
    response = request.execute()

    for item in response["items"]:
        video_id = item["id"]
        stats = item["statistics"]
        video_data.append({
            "影片 ID": video_id,
            "觀看數": stats.get("viewCount", "N/A"),
            "按讚數": stats.get("likeCount", "N/A"),
            "留言數": stats.get("commentCount", "N/A")
        })

    return video_data

# 🚀 執行程序
all_channel_data = {}

for name, channel_id in CHANNELS.items():
    print(f"📢 正在處理 {name} 的頻道數據...")
    
    channel_stats = get_channel_stats(channel_id)
    video_ids = get_latest_video_ids(channel_id, max_results=20)
    video_stats = get_video_stats(video_ids)

    all_channel_data[name] = {
        "頻道資訊": channel_stats,
        "最新影片統計": video_stats
    }

# ✅ 將結果存成 JSON 檔案
current_date = datetime.datetime.now().strftime("%Y%m%d")
json_filename = f"youtube_data_{current_date}.json"
with open(json_filename, "w", encoding="utf-8") as json_file:
    json.dump(all_channel_data, json_file, ensure_ascii=False, indent=4)

print(f"✅ 所有頻道數據已存成 {json_filename}")
