import os
import sys
# Adiciona o diretório raiz do projeto ao caminho do sistema
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts')))
from datetime import datetime, timedelta
import pytest
import requests
from dotenv import load_dotenv

from binance_gateway import BinanceFutures

load_dotenv()

class TestBinanceGateway:
    @pytest.fixture(autouse=True)
    def init_trader(self):
        # instantiate object with API key and secret key
        self.api_key = os.getenv("BINANCE_TEST_API_KEY")
        self.secret_key = os.getenv("BINANCE_TEST_API_SECRET")
        self.end_time = datetime.now()
        self.start_time = self.end_time - timedelta(days=1) # 1 Day Interval
        self.symbol = "BTCUSDT" # symbol
        self.quantity = 0.001 # quantity trade
        self.trader = BinanceFutures(self.api_key, self.secret_key, is_test=True)
        
    def test_buy_market_order(self):
        """
        Test if buy_market_order returns the expected response for a given symbol and quantity.
        """
        # call the method with appropriate arguments
        symbol = self.symbol
        quantity = self.quantity
        origQty = self.quantity
        response = self.trader.buy_market_order(symbol, quantity)
        
        # verify the response
        assert response['symbol'] == symbol
        assert response['side'] == 'BUY'
        assert response['type'] == 'MARKET'
        assert response['origQty'] == str(origQty)
        assert response['status'] == 'NEW'

        # close position
        self.trader.close_all_postions(symbol, quantity, 'SELL')
    
    def test_sell_market_order(self):
        """
        Test if sell_market_order returns the expected response for a given symbol and quantity.
        """
        # call the method with appropriate arguments
        symbol = self.symbol
        quantity = self.quantity
        origQty = self.quantity
        response = self.trader.sell_market_order(symbol, quantity)
        
        # verify the response
        assert response['symbol'] == symbol
        assert response['side'] == 'SELL'
        assert response['type'] == 'MARKET'
        assert response['origQty'] == str(origQty)
        assert response['status'] == 'NEW'

    def test_close_all_postions(self):
        """
        Test if close_all_postions returns the expected response for a given symbol and quantity.
        """
        # call the method with appropriate arguments
        symbol = self.symbol
        quantity = self.quantity
        origQty = self.quantity
        side = 'BUY'
        response = self.trader.close_all_postions(symbol, quantity, side)

        # verify the response
        assert response['symbol'] == symbol
        assert response['side'] == side
        assert response['type'] == 'MARKET'
        assert response['origQty'] == str(origQty)
        assert response['status'] == 'NEW'

    def test_get_open_positions(self):
        """
        Test if get_open_positions returns the expected response for open position
        """
        positions = self.trader.get_open_positions(self.symbol)

        assert isinstance(positions, list)
        for position in positions:
            assert isinstance(position, dict)
            assert position.get('symbol') == self.symbol
        assert requests.codes.ok == 200

    def test_get_trade_history(self):
        """
        Test if get_trade_history returns the expected response for history prices
        """
        response = self.trader.get_trade_history(self.symbol, self.start_time, self.end_time)
        
        # verify the response
        for trade in response:
            assert trade['symbol'] == self.symbol

    def test_get_position_margin(self):
        """
        Test if get_position_margin returns the expected response for margin
        """
        response = self.trader.get_position_margin()

        # verify the response
        assert requests.codes.ok == 200

    def test_get_balance(self):
        """
        Test if get_balance returns the expected response for balance 
        """
        response = self.trader.get_balance()

        # verify the response
        assert requests.codes.ok == 200