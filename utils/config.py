import os

class Config:
    ENV = os.getenv("ENV", "qa")

    URLS = {
        "qa": "https://test.flydubai.avileap.com/login",
        "stage": "",
        "prod": "https://flydubai.avileap.com/login"
    }

    BASE_URL = URLS.get(ENV)