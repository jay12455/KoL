import os
import sys
import json
import logging
from flask import Flask, jsonify, request, send_from_directory
from flask_swagger_ui import get_swaggerui_blueprint

# 設置日誌級別
logging.basicConfig(level=logging.DEBUG)

# 獲取路徑
current_file = os.path.abspath(__file__)
api_dir = os.path.dirname(current_file)
project_root = os.path.dirname(api_dir)

# 將專案根目錄添加到 Python 路徑
sys.path.insert(0, project_root)

try:
    from config.settings import PROCESSED_DATA_DIR, API_HOST, API_PORT
except ImportError:
    print("Python 路徑:")
    for path in sys.path:
        print(path)
    raise

# Swagger 配置
SWAGGER_URL = '/swagger'
API_URL = '/static/swagger.json'

def normalize_number(value):
    """統一化數字格式"""
    if isinstance(value, (int, float)):
        return str(value)
    if not value:
        return "0"
    
    value = str(value).replace(',', '')
    multipliers = {'K': 1000, 'M': 1000000, '萬': 10000}
    
    for suffix, multiplier in multipliers.items():
        if suffix in value:
            try:
                number = float(value.replace(suffix, ''))
                return str(int(number * multiplier))
            except ValueError:
                return "0"
    
    return value.replace(',', '')

def normalize_data(platform, raw_data):
    """統一化不同平台的數據格式"""
    def normalize_youtube_data(data):
        channel_data = {}
        for channel_name, info in data.items():
            channel_data[channel_name] = {
                "basic_info": {
                    "platform": "youtube",
                    "username": channel_name,
                    "followers_count": normalize_number(info["頻道資訊"]["訂閱數"]),
                    "posts_count": normalize_number(info["頻道資訊"]["總影片數"]),
                    "total_views": normalize_number(info["頻道資訊"]["總觀看數"])
                },
                "videos_data": [
                    {
                        "index": idx + 1,
                        "views": normalize_number(video["觀看數"]),
                        "likes": normalize_number(video["按讚數"]) if video["按讚數"] != "N/A" else "0",
                        "comments": normalize_number(video["留言數"])
                    }
                    for idx, video in enumerate(info["最新影片統計"])
                ]
            }
        return channel_data

    def normalize_instagram_data(data):
        return {
        item["username"]: {
            "basic_info": {
                "platform": "instagram",
                "username": item["username"],
                "followers_count": normalize_number(item["followers_count"].replace('位粉絲', '')),
                "posts_count": normalize_number(item["posts_count"].replace('貼文', ''))
            },
            "videos_data": [
                {
                    "index": reel["reel_index"],
                    "views": normalize_number(reel["views"]),
                    "likes": normalize_number(reel["likes"]),
                    "comments": normalize_number(reel["comments"]),
                    "link": reel["link"]
                }
                for reel in item["reels_data"]
            ]
        }
        for item in data
    }

    def normalize_tiktok_data(data):
        normalized_data = {}
        for username, info in data.items():
            normalized_data[username] = {
                "basic_info": {
                    "platform": "tiktok",
                    "username": username,
                    "followers_count": normalize_number(info["profile"]["followers"]),
                    "likes": normalize_number(info["profile"]["likes"])
                },
                "videos_data": [
                    {
                        "index": video["video_number"],
                        "views": normalize_number(video["views"]),
                        "likes": normalize_number(video["likes"]),
                        "comments": normalize_number(video["comments"]),
                        "shares": normalize_number(video["shares"])
                    }
                    for video in info["videos"]
                ]
            }
        return normalized_data

    processors = {
        'youtube': normalize_youtube_data,
        'instagram': normalize_instagram_data,
        'tiktok': normalize_tiktok_data
    }

    return processors[platform](raw_data)

def load_platform_data():
    """載入所有平台的數據"""
    data = {
        'youtube': {},
        'tiktok': {},
        'instagram': {}
    }
    
    file_paths = {
        'youtube': os.path.join(PROCESSED_DATA_DIR, 'youtube_data_20250220.json'),
        'tiktok': os.path.join(PROCESSED_DATA_DIR, 'tiktok_data_20250220.json'),
        'instagram': os.path.join(PROCESSED_DATA_DIR, 'ig_data_20250223.json')
    }
    
    for platform, file_path in file_paths.items():
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    raw_data = json.load(f)
                    data[platform] = normalize_data(platform, raw_data)
                    logging.info(f"成功載入並處理 {platform} 數據")
            else:
                logging.warning(f"找不到 {platform} 數據文件: {file_path}")
                
        except Exception as e:
            logging.error(f"載入 {platform} 數據時發生錯誤", exc_info=True)
            data[platform] = {}
    
    return data

def create_app():
    """創建並配置 Flask 應用"""
    app = Flask(__name__, static_folder='static')

    # 註冊 Swagger UI Blueprint
    swagger_ui = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={'app_name': "KOL 數據分析 API"}
    )
    app.register_blueprint(swagger_ui, url_prefix=SWAGGER_URL)

    # 全局變量存儲數據
    global PLATFORM_DATA
    PLATFORM_DATA = load_platform_data()

    @app.route('/')
    def index():
        """首頁路由"""
        return send_from_directory('static', 'index.html')

    @app.route('/api/platforms')
    def get_platforms():
        """獲取所有平台的創作者列表"""
        platforms = {}
        for platform in PLATFORM_DATA:
            if PLATFORM_DATA[platform]:
                platforms[platform] = list(PLATFORM_DATA[platform].keys())
            else:
                platforms[platform] = []
        return jsonify(platforms)

    @app.route('/api/stats')
    def get_stats():
        """獲取特定平台和創作者的統計數據"""
        platform = request.args.get('platform')
        creator = request.args.get('creator')
        
        logging.info(f"接收到請求 - 平台: {platform}, 創作者: {creator}")
        
        if not platform or not creator:
            return jsonify({"error": "需要提供平台和創作者參數"}), 400
        
        try:
            if platform not in PLATFORM_DATA:
                return jsonify({"error": f"不支持的平台: {platform}"}), 404
            
            platform_data = PLATFORM_DATA[platform]
            if not platform_data:
                return jsonify({"error": f"{platform} 平台沒有數據"}), 404
            
            if creator not in platform_data:
                return jsonify({"error": f"找不到創作者 {creator} 的數據"}), 404
            
            return jsonify(platform_data[creator])
            
        except Exception as e:
            logging.error("處理請求時發生錯誤", exc_info=True)
            return jsonify({"error": str(e)}), 500

    return app

def main():
    app = create_app()
    logging.info(f"啟動服務器: {API_HOST}:{API_PORT}")
    logging.info(f"Swagger UI 可訪問: http://{API_HOST}:{API_PORT}{SWAGGER_URL}")
    app.run(host=API_HOST, port=API_PORT, debug=True)

if __name__ == "__main__":
    main()