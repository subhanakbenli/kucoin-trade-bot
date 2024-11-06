import hmac
import hashlib
import base64
import time
import requests
from PyQt5 import QtWidgets
from PyQt5.QtCore import QDate,Qt
from PyQt5.QtGui import QColor,QCursor
from PyQt5.QtWidgets import QComboBox,QPushButton,QMessageBox,QMenu,QTableWidgetItem,QTextEdit,QSpinBox,QDoubleSpinBox,QDateEdit,QCheckBox
from ui_design.arayuz_ui import Ui_MainWindow_bot
from ui_design.islem_gecmisi_ui import Ui_MainWindow_islemGecmisi
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QTableWidgetItem
from kucoin.client import User
from kucoin.client import Market  # Kucoin API paketini kullanıyorsanız
import sqlite3
import requests
import uuid
import hashlib
import hmac
import base64
import time
import sys

# KuCoin API bilgilerini girin
API_KEY ="66f8fa2d51fd880001dc3084"
API_SECRET ="60710427-1d7c-4571-866c-b0d6b98e43c2"
API_PASSPHRASE ="Et6yHBCiYW2zcJ7"

BASE_URL = 'https://api.kucoin.com'
client = User(API_KEY, API_SECRET, API_PASSPHRASE)

def create_headers(api_key, api_secret, api_passphrase, endpoint, method):
    now = int(time.time() * 1000)
    str_to_sign = str(now) + method + endpoint
    signature = base64.b64encode(hmac.new(api_secret.encode('utf-8'), str_to_sign.encode('utf-8'), hashlib.sha256).digest()).decode('utf-8')
    passphrase = base64.b64encode(hmac.new(api_secret.encode('utf-8'), api_passphrase.encode('utf-8'), hashlib.sha256).digest()).decode('utf-8')

    return {
        'KC-API-KEY': api_key,
        'KC-API-SIGN': signature,
        'KC-API-TIMESTAMP': str(now),
        'KC-API-PASSPHRASE': passphrase,
        'KC-API-KEY-VERSION': '2',
        'Content-Type': 'application/json',
    }


def get_balance_for_token(token):
    try:
        
        # Belirli bir token için bakiyeyi alıyoruz
        accounts = client.get_account_list()
        print(accounts)
        # Eğer accounts listesi boşsa, hesapta bakiye yoktur
        if not accounts:
            return 0.0

        # Belirli tokenin bakiyesini kontrol ediyoruz
        for account in accounts:
            if account['currency'] == token:
                return float(account['balance'])
        return 0.0
    except Exception as e:
        print(f"Bir hata oluştu: {e}")
        return 0.0


def get_fills(symbol, api_key, api_secret, api_passphrase):
    endpoint = f'/api/v1/fills?symbol={symbol}&tradeType=TRADE'
    url = BASE_URL + endpoint
    headers = create_headers(api_key, api_secret, api_passphrase, endpoint, 'GET')

    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        # Yanıtın tamamını yazdırarak hatayı incele
        print("Response JSON:", response.json())
        return response.json().get('data', [])
    else:
        print(f"Error fetching data: {response.status_code}, {response.text}")
        return []
    
def ortalama_maliyet_hesapla(islemler, guncel_bakiye):
    toplam_maliyet = 0
    toplam_miktar = 0
    print(islemler)
    for islem in islemler["items"]:
        print(islem)
        if islem['side'] == 'buy':
            miktar = float(islem['size'])  # Alınan miktar (örneğin BTC)
            fiyat = float(islem['price'])  # Alım fiyatı
            toplam_maliyet += miktar * fiyat
            toplam_miktar += miktar

        # Eğer tüm işlemlerden gelen miktar güncel bakiyeden fazla ise,
        # sadece güncel bakiyeyi karşılayacak kadar olan işlemleri dikkate al.
        if toplam_miktar >= guncel_bakiye:
            break

    if toplam_miktar == 0:
        return 0  # Eğer hiç alım yapılmadıysa maliyet 0
    else:
        # Mevcut bakiyeye göre ortalama maliyeti döndür
        return toplam_maliyet / guncel_bakiye  # Ortalama maliyet

# Kullanmak için örnek:
symbol = 'BTC-USDT'  # İstediğin koin çiftini buraya gir
guncel_bakiye = get_balance_for_token('BTC')  # Mevcut token bakiyen (örneğin 0.5 BTC)

fills = get_fills(symbol, API_KEY, API_SECRET, API_PASSPHRASE)
ortalama_maliyet = ortalama_maliyet_hesapla(fills, guncel_bakiye)
print(f"{symbol} için ortalama maliyet: {ortalama_maliyet} USDT")