📌 KOL 平台數據分析 🚀
使用 爬蟲技術 爬取 KOL 平台數據，並透過 Flask API 與 Swagger UI 呈現數據分析，幫助企業快速找到合適的網紅合作對象。


📌 功能介紹
✅ 爬取 KOL 平台數據（TikTok、YouTube、Instagram Reels）
✅ API 介面提供數據查詢（基於 Flask + Swagger UI）
✅ 數據分析與可視化（粉絲增長率、互動率、關鍵字分析）
✅ 企業可依條件篩選合適 KOL

📌 技術架構
後端：Flask、Swagger UI、RESTful API
爬蟲：Scrapy、Requests、BeautifulSoup
數據處理：Pandas、NumPy
可視化：Matplotlib、Seaborn
📌 安裝與執行
1️⃣ 環境準備
請先確保你的環境安裝了 Python（>=3.8）。

bash
複製
編輯
git clone https://github.com/你的帳號/KOL-Analysis.git
cd KOL-Analysis
pip install -r requirements.txt
2️⃣ 啟動 Flask 伺服器
bash
複製
編輯
python app.py
伺服器預設運行在 http://127.0.0.1:5000，你可以透過 Swagger UI 瀏覽 API 文件：
👉 http://127.0.0.1:5000/docs

📌 API 介面
方法	路由	描述
GET	/kol/list	獲取所有 KOL 資料
GET	/kol/{id}	根據 ID 獲取特定 KOL
POST	/kol/search	根據條件篩選 KOL
範例請參考 swagger.json 配置。

