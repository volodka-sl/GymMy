import os

class RobokassaConfig:
    MERCHANT_LOGIN = os.getenv("ROBOKASSA_MERCHANT_LOGIN")
    PASSWORD1       = os.getenv("ROBOKASSA_PASSWORD1")
    PASSWORD2       = os.getenv("ROBOKASSA_PASSWORD2")
    PAYMENT_URL     = "https://auth.robokassa.ru/Merchant/Index.aspx"
