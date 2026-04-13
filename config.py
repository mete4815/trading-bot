import os

API_KEY = os.environ.get('API_KEY', '')
API_SECRET = os.environ.get('API_SECRET', '')
CLAUDE_API_KEY = os.environ.get('CLAUDE_API_KEY', '')
TESTNET = os.environ.get('TESTNET', 'True') == 'True'
SYMBOL = "BTC/USDT"
RISK_PERCENT = 2
STOP_LOSS_PERCENT = 3
TAKE_PROFIT_PERCENT = 6
CHECK_INTERVAL = 60
