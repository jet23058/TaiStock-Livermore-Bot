import os
import requests
import json
import yfinance as yf
import pandas as pd
import twstock
from datetime import datetime
from tabulate import tabulate
from colorama import Fore, Style, init
from dotenv import load_dotenv

# 載入 .env (本地開發用，GitHub Action 會直接讀取 Secrets)
load_dotenv()

# 初始化
init(autoreset=True)

# ================= 設定區 =================
# 從環境變數讀取設定，預設為 False
TEST_MODE = os.getenv("TEST_MODE", "False").lower() == "true"
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
LOOKBACK_DAYS = 60 

METAL_DICT = {
    'GC=F': '黃金期貨', 'SI=F': '白銀期貨', 'PL=F': '白金期貨',
    'HG=F': '銅期貨',   'PA=F': '鈀金期貨', 'CL=F': '原油期貨'
}
# ==========================================

def get_all_tw_targets():
    targets = []
    for code in METAL_DICT.keys():
        targets.append(code)
    
    # 如果是測試模式，不需要跑 twstock 掃描，直接手動加入幾檔測試
    if TEST_MODE:
        print(f"{Fore.YELLOW}[測試模式] 僅掃描少量權值股...{Style.RESET_ALL}")
        return targets + ['2330.TW', '2317.TW', '2603.TW']

    print(f"正在整理台股清單...")
    for code, info in twstock.codes.items():
        if info.type == "股票":
            if info.market == "上市": suffix = ".TW"
            elif info.market == "上櫃": suffix = ".TWO"
            else: continue
            targets.append(f"{code}{suffix}")
            
    return targets

def check_livermore_criteria(ticker):
    try:
        df = yf.download(ticker, period="6mo", progress=False)
        
        if len(df) < LOOKBACK_DAYS + 2:
            return None
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
            
        df['MA5'] = df['Close'].rolling(window=5).mean()
        df['MA10'] = df['Close'].rolling(window=10).mean()
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA60'] = df['Close'].rolling(window=60).mean()
        
        today = df.iloc[-1]
        yesterday = df.iloc[-2]
        
        current_price = float(today['Close'])
        open_price = float(today['Open'])
        y_close = float(yesterday['Close'])
        y_open = float(yesterday['Open'])
        
        past_data = df['High'].iloc[-(LOOKBACK_DAYS+1):-1]
        prev_high = float(past_data.max())
        
        # --- 新增邏輯：計算目前連續幾根紅K ---
        consecutive_red_count = 0
        # 從最後一天往回數 (倒序)
        for i in range(len(df)-1, -1, -1):
            c = df['Close'].iloc[i]
            o = df['Open'].iloc[i]
            if c > o:
                consecutive_red_count += 1
            else:
                # 一旦遇到不是紅K (綠K或十字線)，就停止計數
                break
        # ----------------------------------

        # 條件檢查
        is_breakout = current_price > prev_high
        is_above_all_ma = (
            current_price > today['MA5'] and 
            current_price > today['MA10'] and 
            current_price > today['MA20'] and 
            current_price > today['MA60']
        )
        # 這裡其實可以用 consecutive_red_count >= 2 取代，但保留原邏輯也無妨
        is_two_red_k = consecutive_red_count >= 2
        
        if is_breakout and is_above_all_ma and is_two_red_k:
            entry_price = current_price
            tech_stop = float(today['Low'])
            money_stop = entry_price * 0.90
            stop_loss = max(tech_stop, money_stop)
            
            if ticker in METAL_DICT:
                name = METAL_DICT[ticker]
                sector = "國際商品"
                display_ticker = ticker
            else:
                stock_code = ticker.split('.')[0]
                if stock_code in twstock.codes:
                    info_data = twstock.codes[stock_code]
                    name = info_data.name
                    sector = info_data.group
                else:
                    try: name = yf.Ticker(ticker).info.get('longName', ticker)
                    except: name = ticker
                    sector = "其他/ETF"
                display_ticker = stock_code

            if len(name) > 8: name = name[:8] + ".."

            return [
                display_ticker,
                name,
                sector,
                round(current_price, 2),
                round(prev_high, 2),
                consecutive_red_count, # 新增這個欄位 (索引 5)
                round(stop_loss, 2)    # 停損變成索引 6
            ]
    except Exception:
        pass
    return None

def send_to_slack(table_str, match_count):
    if not SLACK_WEBHOOK_URL:
        print(f"{Fore.RED}未設定 SLACK_WEBHOOK_URL，跳過發送。{Style.RESET_ALL}")
        return

    # 使用 Slack Block Kit 設計漂亮版面
    scan_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "🚀 台股強勢突破訊號 (Livermore Breakout)",
                "emoji": True
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*📅 掃描時間:*\n{scan_time}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*🎯 符合檔數:*\n{match_count} 檔"
                }
            ]
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*🔎 篩選策略:*\n• 所有均線之上 (多頭排列)\n• 連續兩日紅 K\n• 收盤價突破近 {LOOKBACK_DAYS} 日新高"
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                # 使用代碼區塊 ``` 包裹表格，確保手機/電腦版對齊
                "text": f"```{table_str}```"
            }
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "⚠️ *Disclaimer*: 本程式僅供程式交易研究與學術用途，不代表任何投資建議。市場有風險，投資需謹慎。"
                }
            ]
        }
    ]

    payload = {"blocks": blocks}

    try:
        response = requests.post(
            SLACK_WEBHOOK_URL, 
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'}
        )
        if response.status_code == 200:
            print(f"{Fore.GREEN}Slack 通知發送成功！{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}Slack 發送失敗: {response.status_code}, {response.text}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Slack 發送錯誤: {e}{Style.RESET_ALL}")

def main():
    print(f"\n{Fore.CYAN}=== 強勢突破掃描 ==={Style.RESET_ALL}")
    target_list = get_all_tw_targets()
    
    results = []
    # 修改表頭，加入 "連紅"
    headers = ["代號", "名稱", "產業", "現價", f"{LOOKBACK_DAYS}日高", "連紅", "停損"]
    
    total = len(target_list)
    for i, ticker in enumerate(target_list):
        if i % 10 == 0:
            print(f"\r進度: {i}/{total}...", end="", flush=True)
        data = check_livermore_criteria(ticker)
        if data:
            results.append(data)

    print(f"\n{Fore.CYAN}掃描完成{Style.RESET_ALL}")
    
    if results:
        # 根據 "連紅天數" 排序 (越多天越強，或者你想照產業排也可以)
        # 這裡維持照產業排序
        results.sort(key=lambda x: x[2])
        
        table_str = tabulate(results, headers=headers, tablefmt="simple", numalign="right", stralign="center")
        print(table_str)
        
        # Slack 訊息也要記得傳入新的 table_str
        send_to_slack(table_str, len(results))
    else:
        print("今日無符合條件之標的。")

if __name__ == "__main__":
    main()