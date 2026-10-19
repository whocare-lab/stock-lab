"""
股票分析主程式：yfinance 抓基本面＋quantstats 算績效，產出 HTML 儀表板到 site/
由 GitHub Actions 執行；本機跑法：pip install -r requirements.txt && python analysis.py
"""
import datetime
import traceback
from pathlib import Path

import pandas as pd
import quantstats as qs
import yfinance as yf

# ---- 要分析的標的（隨時可改，台股代號加 .TW）----
TICKERS = {
    "2330.TW": "台積電",
    "0050.TW": "元大台灣50",
    "TSM": "台積電 ADR",
    "NVDA": "輝達 NVIDIA",
}

SITE = Path("site")
(SITE / "reports").mkdir(parents=True, exist_ok=True)


def safe(fn, default=None):
    try:
        v = fn()
        return default if v is None else v
    except Exception:
        return default


def fmt_pct(x, digits=1):
    return "—" if x is None else f"{x:.{digits}%}"


def fmt_num(x, digits=2):
    return "—" if x is None else f"{x:.{digits}f}"


rows = []
for ticker, name in TICKERS.items():
    print(f"=== 分析 {ticker} {name} ===", flush=True)
    try:
        t = yf.Ticker(ticker)
        info = safe(lambda: t.info, {}) or {}

        hist = yf.download(ticker, period="5y", auto_adjust=True, progress=False)
        if hist is None or hist.empty:
            raise RuntimeError("抓不到股價資料")
        close = hist["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
        close = close.dropna()
        rets = close.pct_change().dropna()

        price = float(close.iloc[-1])
        cagr = float(qs.stats.cagr(rets))
        sharpe = float(qs.stats.sharpe(rets))
        mdd = float(qs.stats.max_drawdown(rets))
        year = datetime.date.today().year
        ytd_rets = rets.loc[f"{year}-01-01":]
        ytd = float((1 + ytd_rets).prod() - 1) if len(ytd_rets) else None

        eps = info.get("trailingEps")
        pe = info.get("trailingPE")
        roe = info.get("returnOnEquity")
        dy = info.get("dividendYield")
        currency = info.get("currency", "")

        # 個股完整績效報告（quantstats 產出）
        report_file = f"reports/{ticker.replace('.', '_')}.html"
        qs.reports.html(
            rets,
            output=str(SITE / report_file),
            title=f"{name} ({ticker}) 五年績效報告",
        )

        rows.append({
            "ticker": ticker, "name": name, "price": price, "currency": currency,
            "eps": eps, "pe": pe, "roe": roe, "dy": dy,
            "cagr": cagr, "sharpe": sharpe, "mdd": mdd, "ytd": ytd,
            "report": report_file, "error": None,
        })
    except Exception as e:  # 單一標的失敗不影響其他
        traceback.print_exc()
        rows.append({"ticker": ticker, "name": name, "error": str(e)[:150]})

# ---- 產生首頁儀表板 ----
def pos_neg(x):
    if x is None:
        return ""
    return "pos" if x >= 0 else "neg"


cards = []
for r in rows:
    if r.get("error"):
        cards.append(f"""
      <div class="card">
        <div class="head"><span class="name">{r['name']}</span><span class="tk">{r['ticker']}</span></div>
        <p class="err">本次更新失敗：{r['error']}</p>
      </div>""")
        continue
    cards.append(f"""
      <div class="card">
        <div class="head"><span class="name">{r['name']}</span><span class="tk">{r['ticker']}</span></div>
        <div class="price">{fmt_num(r['price'])} <small>{r['currency']}</small></div>
        <table>
          <tr><td>EPS（每股盈餘）</td><td>{fmt_num(r['eps'])}</td></tr>
          <tr><td>本益比 P/E</td><td>{fmt_num(r['pe'], 1)}</td></tr>
          <tr><td>ROE</td><td>{fmt_pct(r['roe'])}</td></tr>
          <tr><td>殖利率</td><td>{fmt_pct(r['dy'])}</td></tr>
          <tr><td>年化報酬率 CAGR（5年）</td><td class="{pos_neg(r['cagr'])}">{fmt_pct(r['cagr'])}</td></tr>
          <tr><td>今年以來 YTD</td><td class="{pos_neg(r['ytd'])}">{fmt_pct(r['ytd'])}</td></tr>
          <tr><td>夏普比率</td><td>{fmt_num(r['sharpe'])}</td></tr>
          <tr><td>最大回撤（5年）</td><td class="neg">{fmt_pct(r['mdd'])}</td></tr>
        </table>
        <a class="btn" href="{r['report']}">📊 完整績效報告</a>
      </div>""")

now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%d %H:%M")
html = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>stock-lab 股票儀表板</title>
<style>
  body {{ margin:0; background:#0f1420; color:#e8ecf3; font-family:-apple-system,"PingFang TC","Noto Sans TC",sans-serif; }}
  .wrap {{ max-width:880px; margin:0 auto; padding:20px 14px 40px; }}
  h1 {{ font-size:22px; margin:8px 0 2px; }}
  .ts {{ color:#8b93a5; font-size:13px; margin-bottom:18px; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(280px,1fr)); gap:14px; }}
  .card {{ background:#1a2233; border:1px solid #2a3550; border-radius:14px; padding:16px; }}
  .head {{ display:flex; justify-content:space-between; align-items:baseline; }}
  .name {{ font-size:17px; font-weight:700; }}
  .tk {{ color:#8b93a5; font-size:13px; }}
  .price {{ font-size:26px; font-weight:800; margin:8px 0 10px; }}
  .price small {{ font-size:13px; color:#8b93a5; font-weight:400; }}
  table {{ width:100%; border-collapse:collapse; font-size:14px; }}
  td {{ padding:6px 0; border-top:1px solid #26304a; }}
  td:last-child {{ text-align:right; font-weight:600; }}
  .pos {{ color:#34d399; }} .neg {{ color:#f87171; }} .err {{ color:#fbbf24; font-size:13px; }}
  .btn {{ display:block; text-align:center; margin-top:12px; padding:10px; border-radius:10px;
         background:#2f6fed; color:#fff; text-decoration:none; font-weight:600; }}
  .foot {{ color:#5b6376; font-size:12px; margin-top:24px; line-height:1.7; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>📈 stock-lab 股票儀表板</h1>
  <div class="ts">更新時間：{now}（台灣時間）｜資料來源：Yahoo Finance</div>
  <div class="grid">{''.join(cards)}
  </div>
  <p class="foot">EPS、本益比、ROE、殖利率為最近四季（trailing）資料；CAGR、夏普、最大回撤以近五年調整後收盤價計算。本頁僅供研究參考，不構成投資建議。</p>
</div>
</body>
</html>"""

(SITE / "index.html").write_text(html, encoding="utf-8")
print("完成！site/index.html 已產生")
