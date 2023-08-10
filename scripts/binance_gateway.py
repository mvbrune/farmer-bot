import datetime
import requests
import logging
import hashlib
import hmac
import time
import os

class BinanceFutures:
    def __init__(self, api_key, secret_key,is_test=False):
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = "https://fapi.binance.com"
        self.is_test = is_test
        self.logger = logging.getLogger(__name__)

        if self.is_test:
            self.base_url = "https://testnet.binancefuture.com"

        # configurando o logger
        LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')

        if not os.path.exists(LOG_DIR):
            os.mkdir(LOG_DIR)

        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)

        file_handler = logging.FileHandler(os.path.join(LOG_DIR, 'binance.log'))
        file_handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)

    def signature(self, data):
        key = self.secret_key.encode('utf-8')
        signature = hmac.new(key, data.encode('utf-8'), hashlib.sha256).hexdigest()
        return signature

    def buy_market_order(self, symbol, quantity):
        try:
            endpoint = "/fapi/v1/order"
            timestamp = int(time.time() * 1000)
            data = f"symbol={symbol}&side=BUY&type=MARKET&quantity={quantity}&timestamp={timestamp}"
            signature = self.signature(data)
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "X-MBX-APIKEY": self.api_key
            }
            params = {
                "symbol": symbol,
                "side": "BUY",
                "type": "MARKET",
                "quantity": quantity,
                "timestamp": timestamp,
                "signature": signature
            }
            response = requests.post(f"{self.base_url}{endpoint}", headers=headers, params=params)
            return response.json()
        except Exception as e:
            print(f"Error: {e}")
            self.logger.error(f'BUY MARKET: {str(e)}')
            exit()


    def sell_market_order(self, symbol, quantity):
        try:
            endpoint = "/fapi/v1/order"
            timestamp = int(time.time() * 1000)
            data = f"symbol={symbol}&side=SELL&type=MARKET&quantity={quantity}&timestamp={timestamp}"
            signature = self.signature(data)
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "X-MBX-APIKEY": self.api_key
            }
            params = {
                "symbol": symbol,
                "side": "SELL",
                "type": "MARKET",
                "quantity": quantity,
                "timestamp": timestamp,
                "signature": signature
            }
            response = requests.post(f"{self.base_url}{endpoint}", headers=headers, params=params)
            return response.json()
        except Exception as e:
            print(f"Error: {e}")
            self.logger.error(f'SELL MARKET: {str(e)}')
            exit()


    def close_all_postions(self, symbol, quantity, side):
        try:
            endpoint = "/fapi/v1/order"
            timestamp = int(time.time() * 1000)
            data = f"symbol={symbol}&side={side}&type=MARKET&quantity={quantity}&timestamp={timestamp}"
            signature = self.signature(data)
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "X-MBX-APIKEY": self.api_key
            }
            params = {
                "symbol": symbol,
                "side": side,
                "type": "MARKET",
                "quantity": quantity,
                "timestamp": timestamp,
                "signature": signature
            }
            response = requests.post(f"{self.base_url}{endpoint}", headers=headers, params=params)
            return response.json()
        except Exception as e:
            print(f"Error: {e}")
            self.logger.error(f'CLOSE POSITIONS: {str(e)}')
            exit()

    def get_open_positions(self, symbol):
        try:
            endpoint = "/fapi/v2/positionRisk"
            url = f"{self.base_url}{endpoint}"
            timestamp = int(time.time() * 1000)
            signature = hmac.new(self.secret_key.encode('utf-8'), f'timestamp={timestamp}'.encode('utf-8'), hashlib.sha256).hexdigest()
            headers = {
                "Content-Type": "application/json",
                "X-MBX-APIKEY": self.api_key
            }
            params = {
                "timestamp": timestamp,
                'signature': signature
            }
            response = requests.get(url, headers=headers, params=params).json()
            
            if isinstance(response, list):
                positions = [p for p in response if p["symbol"] == symbol and float(p["positionAmt"]) != 0]
            else: 
                positions = []

            # verifica o lado correto para encerrar cada posição em aberto
            if len(positions) > 0:
                for position in positions:
                    if float(position["positionAmt"]) > 0:
                        position["side"] = "SELL"
                        position["currentSide"] = "BUY"
                    elif float(position["positionAmt"]) < 0:
                        position["side"] = "BUY"
                        position["currentSide"] = "SELL"
                    else:
                        position["side"] = None

                return positions
            else:
                return []
        except Exception as e:
            print(f"Error: {e}")
            self.logger.error(f'OPEN POSITIONS: {str(e)}')
            exit()


    def get_trade_history(self, symbol, start_time, end_time):
        try:
            endpoint = "/fapi/v1/userTrades"
            start_time = int(start_time.timestamp() * 1000)
            end_time = int(end_time.timestamp() * 1000)
            timestamp = int(time.time() * 1000)
            data = f"symbol={symbol}&startTime={start_time}&endTime={end_time}&timestamp={timestamp}"
            signature = self.signature(data)
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "X-MBX-APIKEY": self.api_key
            }
            params = {
                "symbol": symbol,
                "startTime": start_time,
                "endTime": end_time,
                "timestamp": timestamp,
                "signature": signature
            }
            response = requests.get(f"{self.base_url}{endpoint}", headers=headers, params=params)
            trades = response.json()

            return trades
        except Exception as e:
            print(f"Error: {e}")
            self.logger.error(f'TRADE HISTORY: {str(e)}')
            exit()

    def get_position_margin(self):
        try:
            endpoint = "/fapi/v2/account"
            url = f"{self.base_url}{endpoint}"
            timestamp = int(time.time() * 1000)
            signature = hmac.new(self.secret_key.encode('utf-8'), f'timestamp={timestamp}'.encode('utf-8'), hashlib.sha256).hexdigest()
            headers = {
                "Content-Type": "application/json",
                "X-MBX-APIKEY": self.api_key
            }
            params = {
                "timestamp": timestamp,
                "signature": signature
            }
            response = requests.get(url, headers=headers, params=params).json()
            total_initial_margin = response['totalInitialMargin']
            return total_initial_margin
        except Exception as e:
            print(f"Error: {e}")
            self.logger.error(f'POSTIONS MARGIN: {str(e)}')
            exit()

    def get_balance(self, symbol):
        try:
            endpoint = "/fapi/v2/balance"
            url = f"{self.base_url}{endpoint}"
            timestamp = int(time.time() * 1000)
            signature = hmac.new(self.secret_key.encode('utf-8'), f'timestamp={timestamp}'.encode('utf-8'), hashlib.sha256).hexdigest()
            headers = {
                "Content-Type": "application/json",
                "X-MBX-APIKEY": self.api_key
            }
            params = {
                "timestamp": timestamp,
                "symbol": symbol,
                "signature": signature
            }
            response = requests.get(url, headers=headers, params=params)
            return response.json()
        except Exception as e:
            print(f"Error: {e}")
            self.logger.error(f'BALANCE: {str(e)}')
            exit()
