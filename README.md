# ☕ 晤光咖啡 點餐系統

完整的咖啡店點餐系統,**可直接部署到 GitHub Pages**。

兩種架構並存:
- **🌐 純前端版**(根目錄)— 用 localStorage 當資料庫,可上 GitHub Pages
- **🐍 Flask 後端版**(`backend/`)— 真正的 SQLite 資料庫,適合本機 / 雲端伺服器執行

---

## 📁 專案結構

```
.
├── index.html          # 自動跳轉到 customer.html
├── customer.html       # 顧客點餐機(純前端)
├── admin.html          # 後台管理頁(純前端)
├── data.js             # localStorage 資料層(共用)
├── .nojekyll           # 告訴 GitHub Pages 不要用 Jekyll 處理
├── .gitignore
├── README.md
└── backend/            # 進階版:Flask + SQLite 後端(可選)
    ├── app.py
    ├── database.py
    └── requirements.txt
```

---

## 🌐 部署到 GitHub Pages(5 步驟)

### 1️⃣ 建立 GitHub repo
登入 [github.com](https://github.com),點 **+ → New repository**,輸入 repo 名稱(例如 `coffee-pos`),設為 **Public**,**不要**勾「Add README」,按 Create。

### 2️⃣ 把專案推上去

打開終端機,在這個資料夾執行:

```bash
cd "/Users/yi-an/Desktop/23)咖啡店點餐機"
git init
git add .
git commit -m "Initial: 咖啡店點餐機"
git branch -M main
git remote add origin https://github.com/<你的帳號>/coffee-pos.git
git push -u origin main
```

### 3️⃣ 開啟 GitHub Pages
去 repo → **Settings** → 左側 **Pages** → **Source** 選 **Deploy from a branch** → Branch 選 `main` / `/ (root)` → **Save**。

### 4️⃣ 等 1~2 分鐘,網址出現
位置在同一頁,長這樣:

```
https://<你的帳號>.github.io/coffee-pos/
```

開啟就會跳到顧客點餐機;後台是 `https://<你的帳號>.github.io/coffee-pos/admin.html`。

### 5️⃣ 之後改了東西
```bash
git add .
git commit -m "更新菜單樣式"
git push
```
推上去後 1 分鐘左右網站就會自動更新。

---

## ⚠️ GitHub Pages 版的限制(很重要!)

因為 GitHub Pages 不能跑後端,所以這個版本是 **純前端 + localStorage**:

| 限制 | 說明 |
|------|------|
| ❌ **資料只在本機** | 每台電腦 / 手機 / 瀏覽器看到的資料是 **獨立的**。同學在家打開 ≠ 你的訂單,因為他的瀏覽器是空的 |
| ❌ **清除瀏覽資料 = 全沒** | 隱私模式、清快取、換瀏覽器都會讓資料消失 |
| ❌ **沒有真實「後台」** | 顧客下的單只存在他自己手機,你的後台看不到 |
| ✅ **適合單機展示** | 教學示範、店家自己用一台 iPad 展示沒問題 |

如果要解決這些限制,你需要的是 **真實後端**:
- 走 `backend/` 的 Flask 版本(本機可用,可上 Render / PythonAnywhere)
- 或改用 Firebase / Supabase 等雲端資料庫

**已內建**對應功能在 後台 → 💾 資料維護 分頁:
- 📤 匯出資料 — 下載 JSON 備份
- 📥 匯入資料 — 從備份還原
- 🗑️ 重置 — 清除訂單或回到預設菜單

---

## 🚀 本機測試(不上線)

直接 **雙擊 `customer.html`** 用瀏覽器打開即可。

或起一個簡易 web server(避免 file:// 路徑問題):

```bash
cd "/Users/yi-an/Desktop/23)咖啡店點餐機"
python3 -m http.server 8000
```

然後開:
- 顧客 → http://localhost:8000/customer.html
- 後台 → http://localhost:8000/admin.html

---

## 🐍 想用真正的後端?切到 backend/ 版本

```bash
cd backend
pip3 install -r requirements.txt
python3 app.py
```

開 http://localhost:5001/(顧客)、http://localhost:5001/admin(後台)。

兩版的菜單、UI、功能完全一樣,差別只在資料儲存:
- 純前端版 → 瀏覽器 localStorage
- Flask 版 → SQLite 檔案 `backend/coffee.db`

---

## 🎯 功能總覽

### 顧客端
- 分類瀏覽菜單(咖啡 / 茶飲 / 特調 / 點心)
- 客製化:溫度、尺寸(大杯+$15)、甜度、數量
- 即時購物車(加減數量、移除)
- 結帳找零(快捷金額按鈕)
- 訂單收據與列印

### 後台
- **儀表板**:今日 / 累計營業額、訂單數、待處理數、熱銷排行、過去 7 日營收
- **訂單管理**:狀態流轉(待處理 → 製作中 → 可取餐 → 已完成),日期 / 狀態過濾
- **菜單管理**:新增 / 編輯 / 刪除品項、一鍵切換上下架
- **資料維護**:匯出 / 匯入 JSON、清除訂單、完全重置

---

## 📚 課堂教學重點

1. **資料持久化的層次**:純前端 localStorage → 後端資料庫 → 雲端 BaaS
2. **前後端分離**:`data.js` 提供與 Flask API 完全對應的介面,前端可在兩者之間無痛切換
3. **資料快照原則**:`order_items` 保存品名與單價,改菜單不會影響歷史訂單
4. **狀態機**:訂單狀態 pending → preparing → ready → completed
5. **部署**:Git → GitHub → GitHub Pages 完整流程
