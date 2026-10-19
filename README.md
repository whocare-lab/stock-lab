# stock-lab 股票分析站

iPhone 零安裝方案：GitHub Actions 跑 **yfinance + quantstats**，自動產出含 **EPS、本益比、ROE、年化報酬率（CAGR）、夏普比率、最大回撤** 的儀表板，發佈到 GitHub Pages。

## 報告網址

https://whocare-lab.github.io/stock-lab/

## 首次設定（iPhone 上約 2 分鐘，只做一次）

### 步驟 1：建立工作流程檔

> 因 GitHub 安全限制，workflow 檔只能由本人建立。請在 iPhone 上操作：

1. 開啟本倉庫首頁 → 點 **Add file → Create new file**
2. 檔名輸入：`.github/workflows/daily.yml`
3. 貼上以下完整內容：

```yaml
name: 股票分析報告

on:
  workflow_dispatch:            # 手動觸發：Actions 頁面按 Run workflow
  schedule:
    - cron: "30 6 * * 1-5"      # 平日 06:30 UTC＝台灣時間 14:30（台股收盤後）

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip
      - name: 安裝套件
        run: pip install -r requirements.txt
      - name: 執行分析並產生網站
        run: python analysis.py
      - uses: actions/configure-pages@v5
      - uses: actions/upload-pages-artifact@v3
        with:
          path: site

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4
```

4. 點 **Commit changes** 存檔

### 步驟 2：開啟 Pages

1. 倉庫 → **Settings** → 左側 **Pages**
2. **Build and deployment → Source** 選 **「GitHub Actions」**

### 步驟 3：第一次執行

1. 倉庫 → **Actions** → 左側「股票分析報告」→ 右側 **Run workflow** → 綠色按鈕確認
2. 等 2～3 分鐘轉綠勾，打開報告網址即可看到儀表板

## 日常使用（iPhone）

- **手動跑一次**：Actions → 「股票分析報告」→ **Run workflow**
- **自動排程**：平日台灣時間 14:30（台股收盤後）自動更新

## 修改分析標的

編輯 `analysis.py` 最上方的 `TICKERS` 字典即可（台股代號記得加 `.TW`，例如 `"2317.TW"`）。

## 檔案結構

| 檔案 | 用途 |
|---|---|
| `analysis.py` | 抓資料、算指標、產生 HTML |
| `requirements.txt` | Python 套件清單（含 akshare 備用） |
| `.github/workflows/daily.yml` | Actions 工作流程（步驟 1 建立） |
| `site/`（執行時產生） | 儀表板首頁＋個股 quantstats 完整報告 |

## 注意事項

- 資料來源為 Yahoo Finance，免費但偶爾限流；某檔股票更新失敗時會在卡片上顯示錯誤，不影響其他標的，下次執行會自動補上
- akshare 已列入套件；台股資料目前以 yfinance 為主，akshare 留作 A 股／總經資料擴充用
- 本專案僅供研究參考，不構成投資建議
