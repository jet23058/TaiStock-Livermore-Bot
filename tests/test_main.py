import sys
import os
import pandas as pd
import pytest
from unittest.mock import MagicMock, patch

# 將上一層目錄加入路徑以便匯入 main.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import check_livermore_criteria, get_all_tw_targets

# 建立一個模擬的 DataFrame 資料產生器
def create_mock_df(prices, highs):
    data = {
        'Open': [p - 1 for p in prices], # 簡單設定開盤比收盤低 (紅K)
        'Close': prices,
        'High': highs,
        'Low': [p - 2 for p in prices],
        'Volume': [1000] * len(prices)
    }
    df = pd.DataFrame(data)
    # 建立均線所需長度
    return df

@patch('main.yf.download')
@patch('main.twstock.codes')
def test_check_livermore_criteria_match(mock_twstock, mock_download):
    """測試符合條件的情況"""
    
    # 1. 模擬 twstock 資料
    mock_twstock.__contains__.return_value = True
    mock_twstock.get.return_value = MagicMock(name='台積電', group='半導體')
    mock_twstock.__getitem__.return_value = MagicMock(name='台積電', group='半導體')

    # 2. 模擬 yfinance 數據
    # 創造 70 天數據
    # create_mock_df 的邏輯是 Open = Close - 1，所以這 70 天全是紅 K
    closes = [100.0] * 68 + [115.0, 120.0]
    highs = [110.0] * 68 + [116.0, 121.0]
    
    mock_df = create_mock_df(closes, highs)
    mock_download.return_value = mock_df

    # 3. 執行測試
    result = check_livermore_criteria('2330.TW')

    # 4. 驗證
    assert result is not None
    assert result[0] == '2330'   # 代碼
    assert result[3] == 120.0    # 現價
    assert result[4] == 116.0    # 前高
    
    # 新增驗證：連紅天數
    # 因為 create_mock_df 產生的每一天 Open 都比 Close 小 (Open = p-1)
    # 所以理論上這 70 天全部都是連紅
    assert result[5] == 70       # 連紅天數 (確認邏輯有跑對)
    
    assert result[6] < 120.0     # 停損 (原本是 result[5]，現在往後移一位)

@patch('main.yf.download')
def test_check_livermore_criteria_fail(mock_download):
    """測試不符合條件的情況 (例如跌破均線)"""
    
    # 創造價格一路下跌的數據
    closes = [100.0 - i for i in range(70)] 
    highs = [105.0 - i for i in range(70)]
    
    mock_df = create_mock_df(closes, highs)
    mock_download.return_value = mock_df

    result = check_livermore_criteria('2330.TW')
    
    assert result is None