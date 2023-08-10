import requests

class CryptoConverter:
    def __init__(self):
        self.base_url = 'https://min-api.cryptocompare.com/data'

    def convert(self, from_currency, to_currency, amount):
        url = f'{self.base_url}/price?fsym={from_currency}&tsyms={to_currency}'
        response = requests.get(url)

        if response.status_code != 200:
            return None
        
        data = response.json()
        to_currency_price = data[to_currency]
        converted_amount = amount / to_currency_price

        return converted_amount
