import os 
import sys
import threading
import time
import queue
# Adiciona o diretório raiz do projeto ao caminho do sistema
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts')))

import tkinter as tk
from tkinter import ttk
import ttkthemes
from ttkthemes import ThemedTk

from scripts.interface.validate_form import FormValidator

from dotenv import load_dotenv

from scripts.trade_bot import BinanceTradingBot
from scripts.converter_currency import CryptoConverter

load_dotenv()

class MainWindow:
    def __init__(self, largura=890, altura=550, titulo="NexTrade"):
        #instance trade bot
        self.key = None
        self.secret = None
        self.test_mode = True
        self.quantity = None 
        self.symbol = None
        self.interval = None
        self.stop_gain = None
        self.stop_loss = None
        self.account_mode = None

        self.stop_bot = None

        self.pnl = '--/--'
        self.timer_bot = '--/--'
        self.timer_job = None
        
        # Cria a janela principal
        self.window =  ThemedTk(theme="yaru")
        self.msg_queue = queue.Queue()

        # Conversor 
        self.currency = CryptoConverter()

        # Define as propriedades da janela
        self.window.geometry(f"{largura}x{altura}")
        self.window.title(titulo)

        self.form_group = self.create_input_group()
        self.form_group.pack()

        button_group = self.btn_group()
        button_group.pack(side=tk.TOP, fill=tk.X)

        trade = self.info_trades()
        trade.pack()

        # Cria uma área de texto para exibir os retornos do websocket
        self.prompt = tk.Text(self.window, bg="black", fg="green")
        self.prompt.config(insertbackground="white")
        self.prompt.pack(fill=tk.BOTH, expand=True) 

    def update_timer_label(self, label):
        # Atualiza o texto da label com o valor atual do cronômetro
        label.config(text=f"Bot Activity: {self.timer_bot}")

        # Agenda a próxima atualização para daqui a 1 segundo
        self.timer_job = self.window.after(1000, lambda: self.update_timer_label(label))

    def stopwatch(self):
        seconds = 0
        while True:
            # Atualiza o valor do cronômetro
            minutes = seconds // 60
            seconds_remaining = seconds % 60
            self.timer_bot = f'{minutes:02d}:{seconds_remaining:02d}'

            # Aguarda 1 segundo
            time.sleep(1)
            seconds += 1

    def stop(self):
        if self.stop_bot is not None:
            self.stop_bot.stop()
            self.prompt.insert(tk.END, "Stopped bot...\n")

        return

    def start(self):
        api_key = self.key.get()
        api_secret = self.secret.get()
        quantity = self.quantity.get()
        symbol = self.symbol.get()
        interval = self.interval.get()
        stop_gain = self.stop_gain.get()
        stop_loss = self.stop_loss.get()
        account_mode = self.account_mode.get()

        # Valida Formulário
        validate_form = FormValidator(
            api_key=api_key,
            api_secret=api_secret,
            quantity=quantity,
            symbol=symbol,
            interval=interval,
            stop_gain=stop_gain,
            stop_loss=stop_loss,
            account_mode=account_mode
        )

        validation_errors = validate_form.validate()
        if validation_errors:
            self.prompt.delete("1.0", tk.END)
            self.prompt.insert(tk.END, "Validation errors:" + "\n\n")
            for i, (field, message) in enumerate(validation_errors.items(), start=1):
                self.prompt.insert(tk.END, f"{i}. {field}: {message}" + "\n")
            self.prompt.see(tk.END)
            return

        self.prompt.delete("1.0", tk.END)

        # Dividindo a variável "symbol" em duas partes
        base = symbol[:3] 
        quote = symbol[3:] 

        # Valor Convertido     
        converted_amount = self.currency.convert(base, quote, int(quantity))
        formated_amount = "{:.2f}".format(converted_amount)
        amount = float(formated_amount)

        # Stop Gain and Loss
        stop_gain_per_trade = float(stop_gain)
        stop_loss_per_trade = float(stop_loss)

        # Instancia Bot
        bot = BinanceTradingBot(
            api_key=api_key,
            api_secret=api_secret,
            symbol=symbol, 
            interval=interval, 
            volume=amount,
            stop_gain=stop_gain_per_trade,
            stop_loss=stop_loss_per_trade,
            is_test=True)

        self.stop_bot = bot

        # Thread 1
        self.bot_thread = threading.Thread(target=bot.run)
        self.bot_thread.start()

        # Thread 2
        self.prompt_thread = threading.Thread(target=lambda: self.update_prompt(bot))
        self.prompt_thread.start()

        # Thread timer
        self.timer_thread = threading.Thread(target=self.stopwatch)
        self.timer_thread.start()

    def update_prompt(self, bot):
        self.prompt.insert(tk.END, "Bot is running...\n")
        while True:
            message = bot.ws_message()  # get latest message from socket
            self.prompt.insert(tk.END, message + "\n")
            self.prompt.see(tk.END)
            time.sleep(0.1)


    def info_trades(self):
        info_trade = tk.Frame(self.window)
        info_trade.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        acumulate_pnl = tk.Label(info_trade, text=f"Acumulate PNL: {self.pnl}")
        acumulate_pnl.grid(row=0, column=2, padx=5, pady=5)

        timer_label = tk.Label(info_trade, text=f"Bot Activity: {self.timer_bot}")
        timer_label.grid(row=0, column=6, padx=5, pady=5)

        # Inicia a atualização contínua da label do cronômetro
        self.update_timer_label(label=timer_label)

        return info_trade

    def btn_group(self):
        # criar frame para os botões
        button_frame = tk.Frame(self.window)
        button_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        # Iniciar bot
        start_bot = tk.Button(button_frame, text="Run bot", command=self.start)
        start_bot.pack(side=tk.LEFT, padx=5)

        # Stop bot
        stop_bot = tk.Button(button_frame, text="Stop bot", command=self.stop)
        stop_bot.pack(side=tk.LEFT, padx=5)

        return button_frame
    
    def create_input_group(self):
        # Cria o frame que vai conter o grupo de inputs
        input_frame = tk.Frame(self.window)

        # Label Form
        label_settings = tk.Label(text='ACCOUNT AND TRADE SETTINGS', font="15")
        label_settings.pack(padx=10, pady=15)

        # Cria as labels e inputs
        api_key_label = tk.Label(input_frame, text="API Key: *")
        api_key_input = tk.Entry(input_frame)

        self.key = api_key_input

        api_secret_label = tk.Label(input_frame, text="API Secret: *")
        api_secret_input = tk.Entry(input_frame)

        self.secret = api_secret_input

        quantity_label = tk.Label(input_frame, text="Amount (USDT): *")
        quantity_input = tk.Entry(input_frame)

        self.quantity = quantity_input

        symbol_label = tk.Label(input_frame, text="Symbol: *")
        symbol_input = tk.Entry(input_frame)

        self.symbol = symbol_input

        interval_label = tk.Label(input_frame, text="Interval: *")
        interval_input = tk.Entry(input_frame)

        self.interval = interval_input

        stop_gain_label = tk.Label(input_frame, text="Stop Gain: *")
        stop_gain_input = tk.Entry(input_frame)

        self.stop_gain = stop_gain_input

        stop_loss_label = tk.Label(input_frame, text="Stop Loss: *")
        stop_loss_input = tk.Entry(input_frame)

        self.stop_loss = stop_loss_input

        # Cria os Radiobuttons
        account_mode_label = tk.Label(input_frame, text="Account Mode:")
        account_mode_frame = tk.Frame(input_frame)

        account_mode = tk.StringVar(value=True)
        testnet_radio = tk.Radiobutton(account_mode_frame, text="Testnet", variable=account_mode, value=True)
        mainnet_radio = tk.Radiobutton(account_mode_frame, text="Mainnet", variable=account_mode, value=False)

        # Adiciona as labels e inputs ao frame
        api_key_label.grid(row=0, column=0, padx=5, pady=5)
        api_key_input.grid(row=0, column=1, padx=5, pady=5)

        api_secret_label.grid(row=0, column=2, padx=5, pady=5)
        api_secret_input.grid(row=0, column=3, padx=5, pady=5)

        quantity_label.grid(row=0, column=4, padx=5, pady=5)
        quantity_input.grid(row=0, column=5, padx=5, pady=5)

        symbol_label.grid(row=1, column=0, padx=5, pady=5)
        symbol_input.grid(row=1, column=1, padx=5, pady=5)

        interval_label.grid(row=1, column=2, padx=5, pady=5)
        interval_input.grid(row=1, column=3, padx=5, pady=5)

        stop_gain_label.grid(row=1, column=4, padx=5, pady=5)
        stop_gain_input.grid(row=1, column=5, padx=5, pady=5)

        stop_loss_label.grid(row=2, column=0, padx=5, pady=5)
        stop_loss_input.grid(row=2, column=1, padx=5, pady=5)

        account_mode_label.grid(row=4, column=0, padx=(10, 0), pady=10, sticky=tk.W)
        account_mode_frame.grid(row=4, column=1, padx=(0, 10), pady=10, sticky=tk.W)
        testnet_radio.grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)
        mainnet_radio.grid(row=4, column=1, padx=5, pady=5, sticky=tk.W)

        self.account_mode = account_mode

        # Retorna o frame com os inputs
        return input_frame

    def run(self):
        # Inicia o loop principal 
        self.window.mainloop()
