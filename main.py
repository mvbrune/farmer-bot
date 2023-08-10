import os

from scripts.interface.main_window import MainWindow
from scripts.binance_gateway import BinanceFutures

if __name__ == "__main__":
    interface = MainWindow()
    interface.run()

