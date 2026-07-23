name: daily-pipeline

on:
  schedule:
    # 18:10 台北時間（UTC+8）＝ 10:10 UTC，平日執行（分點日報約 16:30 後才齊）
    - cron: '10 10 * * 1-5'
  workflow_dispatch: {}

permissions:
  contents: write

jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install deps
        run: pip install requests beautifulsoup4 ddddocr onnxruntime

      - name: Fetch daily OHLCV + 當沖
        run: python scripts/fetch_daily.py

      - name: Fetch 分點日報（候選池）
        run: python scripts/fetch_bsr.py
        continue-on-error: true   # 分點源不穩時不擋整條管線

      - name: Scan 主升浪 + 隔日沖警示
        run: python scripts/scan.py

      - name: Commit data
        run: |
          git config user.name "twscan-bot"
          git config user.email "bot@users.noreply.github.com"
          git add docs/data
          git diff --cached --quiet || git commit -m "data: $(date +'%Y-%m-%d')"
          git push
