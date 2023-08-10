import os
import sys
# Adiciona o diretório raiz do projeto ao caminho do sistema
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts')))
import datetime
import websocket
from websocket import WebSocketApp
import numpy as np
import tulipy as ti
import requests
import json
import logging
import queue

from scripts.binance_gateway import BinanceFutures

class BinanceTradingBot:
    def __init__(self, api_key, api_secret, symbol, interval, volume, stop_gain,stop_loss, is_test=False):
        self.symbol = symbol
        self.interval = interval
        self.quantity = volume
        self.stop_gain = stop_gain
        self.stop_loss = stop_loss
        self.is_test = is_test
        self.is_running = False
        self.atr_period = 14 # Periodo do ATR
        self.atr_volatility = 40 # Limite Volatilidade
        self.rsi_period = 14 # Periodo do RSI
        self.rsi_oversold = 30 # Sobrevenda
        self.rsi_overbought = 70 # Sobrecompra
        self.gross_pnl = 0
        self.binance = BinanceFutures(api_key, api_secret, is_test=self.is_test)
        self.msg_queue = queue.Queue()
        self.logger = logging.getLogger(__name__)

        # configurando o logger
        LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')

        if not os.path.exists(LOG_DIR):
            os.mkdir(LOG_DIR)

        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)

        file_handler = logging.FileHandler(os.path.join(LOG_DIR, 'trade_bot.log'))
        file_handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        
        if self.is_test:
            self.base_url = 'https://testnet.binance.vision/api/v3'
            self.ticker_url = f'{self.base_url}/ticker/price?symbol={self.symbol}'
            self.socket_url = f'wss://testnet.binance.vision/ws/{self.symbol.lower()}@kline_{self.interval}'
        else:
            self.base_url = 'https://api.binance.com/api/v3'
            self.ticker_url = f'{self.base_url}/ticker/price?symbol={self.symbol}'
            self.socket_url = f'wss://stream.binance.com:9443/ws/{self.symbol.lower()}@kline_{self.interval}'

        self.last_price = self.get_last_price()
        self.ws = websocket.WebSocketApp(self.socket_url, on_message=self.on_message)

    def check_server_status(self):
        try:
            response = requests.get(self.ticker_url)
            if response.status_code == 200:
                return True
            else:
                self.logger.warning("Server is currently unavailable")
                return False
        except Exception as e:
            print(f"Error checking server status: {e}")
            self.logger.error(f'LAST PRICE: {str(e)}')
            exit()

    def get_last_price(self):
        try:
            response = requests.get(self.ticker_url)
            response.raise_for_status()  # check for HTTP errors
            ticker = response.json()
            if isinstance(ticker, dict) and 'price' in ticker:
                last_price = float(ticker['price'])
                return last_price
            else:
                raise ValueError('Invalid ticker response')
        except (requests.exceptions.RequestException, ValueError) as e:
            print(f"Error: {e}")
            self.logger.error(f'LAST PRICE: {str(e)}')
            raise SystemExit(1)

    def ws_message(self):
        return self.msg_queue.get()

    def on_message(self, ws, message):
        try:
            if not self.is_running:
                self.is_running = True

            json_message = json.loads(message)
            price = float(json_message['k']['c'])
            positions = self.binance.get_open_positions(self.symbol)

            if positions and len(positions) > 0:
                position = positions[0]
                margin = float(self.binance.get_position_margin())
                entry_price = float(position['entryPrice'])
                side = position['side']
                currentSide = position['currentSide']
                quantity = float(position['positionAmt'])
                pnl = quantity * (price - entry_price)
                roe = (pnl / margin * 100) if margin != 0 and pnl != 0 else 0
                market_msg = f"PNL: {pnl:.3f} USDT, ROE: {roe:.2f}%"
                self.msg_queue.put(market_msg)
                if (currentSide == 'BUY' and roe >= self.stop_gain) or (currentSide == 'SELL' and roe >= self.stop_gain): # Gain 
                    self.binance.close_all_postions(self.symbol, self.quantity, side)
                    self.msg_queue.put(f'closed with profit, {side.lower()} position for {self.symbol} at {price}')
                    self.gross_pnl += pnl
                if (currentSide == 'BUY' and roe <= (-1 * self.stop_loss)) or (currentSide == 'SELL' and roe <= (-1 * self.stop_loss)): # Loss
                    self.binance.close_all_postions(self.symbol, self.quantity, side)
                    self.msg_queue.put(f'closed with loss, {side.lower()} position for {self.symbol} at {price}')
                    self.gross_pnl += pnl

            prices = self.get_historical_prices(self.rsi_period)
            prices.append(price)
            prices = np.array(prices)

            if len(prices) < self.rsi_period:
                return

            rsi = ti.rsi(prices, self.rsi_period)

            # ATR calculation
            high_prices = np.array([float(json_message['k']['h'])])
            low_prices = np.array([float(json_message['k']['l'])])
            close_prices = np.array([float(json_message['k']['c'])])
            if len(prices) >= self.atr_period:
                high_prices = np.append(high_prices, prices[-self.atr_period:-1])
                low_prices = np.append(low_prices, prices[-self.atr_period:-1])
                close_prices = np.append(close_prices, prices[-self.atr_period:-1])
            atr = ti.atr(high_prices, low_prices, close_prices, self.atr_period)[-1]

            ws_indicator = f"RSI: {rsi[-1]:.2f}, Volatilidade: {atr:.2f}"
            self.msg_queue.put(ws_indicator)
            
            if rsi[-1] <= self.rsi_oversold and price > self.last_price:
                if len(positions) == 0:
                  # Enviar ordem de compra
                    response = self.binance.buy_market_order(self.symbol, self.quantity)

                    # Verificar se a ordem foi bem-sucedida
                    if "status" in response and response["status"] == "NEW":
                        # Adicionar mensagem na fila
                        self.msg_queue.put(f'executed buy order {self.symbol} at {price}')
                    else:
                        # Se a ordem não foi bem-sucedida, imprimir a mensagem de erro na tela
                       self.msg_queue.put(f'error executing buy order')
            elif rsi[-1] >= self.rsi_overbought and price < self.last_price:
                if len(positions) == 0:
                   # Enviar ordem de compra
                    response = self.binance.buy_market_order(self.symbol, self.quantity)
                    # Verificar se a ordem foi bem-sucedida
                    if "status" in response and response["status"] == "NEW":
                        # Adicionar mensagem na fila
                        self.msg_queue.put(f'executed sell order {self.symbol} at {price}')
                    else: 
                        self.msg_queue.put(f'error executing sell order')
            self.last_price = price
        except Exception as e:
            print(f"Error: {e}")
            self.logger.error(f'MESSAGE: {str(e)}')
            exit()


    def get_historical_prices(self, num_periods):
        try:
            # Obtém os preços históricos do intervalo especificado
            params = {'symbol': self.symbol, 'interval': self.interval, 'limit': num_periods + 1}
            response = requests.get(f'{self.base_url}/klines', params=params)
            klines = response.json()
            
            # Extrai os preços de fechamento dos klines
            prices = []
            for kline in klines:
                close = float(kline[4])
                prices.append(close)
                
            return prices[:-1]
        except Exception as e:
            print(f"Error: {e}")
            self.logger.error(f'HISTORICAL PRICES: {str(e)}')
            exit()
            
    def run(self):
        try:
            self.ws.run_forever()
        except Exception as e:
            self.logger.error(f'RUN: {str(e)}')
            self.msg_queue.put(f"Error: {str(e)}")

    def stop(self):
        try:
            self.ws.close()
        except Exception as e:
            self.msg_queue.put(f"Error: {str(e)}")