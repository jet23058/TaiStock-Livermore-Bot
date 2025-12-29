# TaiStock Livermore Bot 📈

[English](#english) | [中文](#chinese)

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active-success)

## Chinese

### 專案簡介
這是一個自動化的台股強勢股掃描機器人。它基於傑西·利弗莫爾 (Jesse Livermore) 的關鍵點突破邏輯，每日自動掃描台灣股市與國際貴金屬期貨，尋找同時符合多項強勢技術指標的標的，並透過 Slack 發送通知。

### 核心策略
系統篩選條件如下（需同時符合）：
1.  **均線多頭排列**：收盤價 > 5日、10日、20日、60日均線。
2.  **動能強勢**：連續兩日收紅 K 線（收盤 > 開盤）。
3.  **關鍵點突破**：**今日收盤價突破過去 60 日（一季）的最高價**。

### 功能特色
* **全市場掃描**：支援台股上市櫃股票及主要貴金屬期貨。
* **自動化運行**：整合 GitHub Actions，每日台股收盤後（20:30）自動執行。
* **即時通知**：透過 Slack Webhook 發送排版精美的報表。
* **風險控管**：自動計算技術面停損點與資金控管停損點。

### 安裝與使用

1.  **安裝依賴套件**
    ```bash
    pip install -r requirements.txt
    ```

2.  **設定環境變數 (.env)**
    請複製 `.env.example` 為 `.env` 並填入：
    ```properties
    SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
    TEST_MODE=True  # True: 僅測試少量股票; False: 掃描全市場
    ```

3.  **執行掃描**
    ```bash
    python main.py
    ```

4.  **執行測試**
    ```bash
    python -m pytest
    ```

### 免責聲明 (Disclaimer)
本軟體僅供程式交易研究、學術分析與教育用途。本專案所產出之任何數據、圖表、訊號或文字，均不代表任何投資建議或買賣邀約。使用者應自行評估市場風險，開發者不對使用本軟體所產生的任何投資損益負責。

---

## English

### Project Overview
**TaiStock Livermore Bot** is an automated scanner for the Taiwan Stock Exchange (TWSE/TPEx). Based on Jesse Livermore's breakout theory, it automatically scans for stocks showing strong momentum patterns and sends daily reports via Slack.

### Strategy Logic
The bot filters stocks based on the following strict criteria:
1.  **Bullish Trend**: Price is above MA5, MA10, MA20, and MA60.
2.  **Momentum**: Two consecutive Red K-lines (Close > Open).
3.  **Breakout**: **Current close price exceeds the highest high of the last 60 days.**

### Features
* **Full Market Scan**: Covers all listed TW stocks and major precious metals.
* **CI/CD Automation**: Runs daily at 20:30 via GitHub Actions.
* **Slack Integration**: Delivers beautifully formatted block-kit alerts.
* **Risk Management**: Automatically calculates stop-loss levels based on technical lows or risk percentage.

### Installation

1.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configuration**
    Create a `.env` file based on your needs:
    ```properties
    SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
    TEST_MODE=True  # Set to False for full market scan
    ```

3.  **Run Script**
    ```bash
    python main.py
    ```

4.  **Run Tests**
    ```bash
    python -m pytest
    ```

### Disclaimer
This software is for educational and research purposes only. Nothing contained in this project constitutes investment advice or a solicitation to buy or sell any securities. The developers are not responsible for any financial losses arising from the use of this software. Investment involves risk; please trade responsibly.