from cerberus import Validator 
import json

class FormValidator:
    def __init__(self, api_key, api_secret, quantity, symbol, interval, stop_gain, stop_loss, account_mode):
        def validate_quantity(field, value, error):    
            if int(value) < 30:
                error(field, f"{field} must be at least 30 USDT.")

        self.document = {
            "api_key": api_key,
            "api_secret": api_secret,
            "quantity": quantity,
            "symbol": symbol,
            "interval": interval,
            "stop_gain": stop_gain,
            "stop_loss": stop_loss,
            "account_mode": account_mode,
        }

        self.validator = Validator({
            "api_key": {"required": True, "empty": False},
            "api_secret": {"required": True, "empty": False},
            "quantity": {"required": True, "empty": False, "check_with": validate_quantity},
            "symbol": {"required": True, "allowed": ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "LTCUSDT"],"empty": False},
            "interval": {"required": True, "allowed": ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1M"], "empty": False},
            "stop_gain": {"required": True, "empty": False},
            "stop_loss": {"required": True, "empty": False},
            "account_mode": {"required": True, "empty": False}
        })


    def validate(self):
        if not self.validator.validate(self.document):
            return self.validator.errors
        else:
            return None

    def to_json(self):
        validation_errors = self.validate()
        if validation_errors:
            raise ValueError(f"Invalid document: {validation_errors}")
        else:
            return json.dumps(self.document)
