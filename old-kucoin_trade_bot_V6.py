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
import uuid
import hashlib
import hmac
import base64
import time
import sys
import requests



with open("user_data.txt", "r") as file:
    data = file.read().split("\n")
    API_KEY = data[0].split("=")[1].strip()
    API_SECRET = data[1].split("=")[1].strip()
    API_PASSPHRASE = data[2].split("=")[1].strip()

BASE_URL = "https://api.kucoin.com"
CONTENT_TYPE_JSON = "application/json"
client = User(API_KEY, API_SECRET, API_PASSPHRASE)
NO_DATA_RECEIVED_MSG = "No data received."

conn = sqlite3.connect('kucoin_data.db')
cursor = conn.cursor()
app = QtWidgets.QApplication(sys.argv)
MainWindow = QtWidgets.QMainWindow()
ui = Ui_MainWindow_bot()
ui.setupUi(MainWindow)
MainWindow.show()

cursor.execute("CREATE TABLE IF NOT EXISTS anlik_trade \
    (id INTEGER PRIMARY KEY AUTOINCREMENT, hacim FLoat,bakiye Text, token TEXT UNIQUE, ortalama_maliyet FLOAT, artis_limiti FLOAT, dusus_limiti FLOAT, stoploss BOOLEAN,stoploss_limiti FLOAT)")

# cursor.execute("CREATE TABLE IF NOT EXISTS islem_gecmisi \
#     (id INTEGER PRIMARY KEY AUTOINCREMENT, token TEXT, islem_tipi TEXT, miktar FLOAT, fiyat FLOAT, tarih TEXT)")

ui.tableWidget.setColumnWidth(0, 120)
ui.tableWidget.setColumnWidth(1, 140)
ui.tableWidget.setColumnWidth(2, 140)
ui.tableWidget.setColumnWidth(3, 140)
ui.tableWidget.setColumnWidth(4, 140)
ui.tableWidget.setColumnWidth(5, 110)
ui.tableWidget.setColumnWidth(6, 110)
ui.tableWidget.setColumnWidth(7, 40)
ui.tableWidget.setColumnWidth(8, 110)
ui.tableWidget.setColumnWidth(9, 50)

class CustomDoubleSpinBox(QDoubleSpinBox):
    def __init__(self):
        super().__init__()
        self.setRange(0, 9999999)

    def wheelEvent(self, event):
        # Fare tekerleği olaylarını engelle
        event.ignore()

class CustomSpinBox(QSpinBox):
    def __init__(self):
        super().__init__()
        self.setRange(0, 9999999)

    def wheelEvent(self, event):
        # Fare tekerleği olaylarını engelle
        event.ignore()

class CustomComboBox(QComboBox):
    def wheelEvent(self, event):
        event.ignore()

class CustomQDateEdit(QDateEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDate(QDate.currentDate())
        self.setStyleSheet("color: rgb(5, 5, 5);")
    def wheelEvent(self, event):
        event.ignore()

class PriceUpdateThread(QtCore.QThread):
    # Yeni fiyat bilgisi alındığında bir sinyal yayıyoruz
    new_price_signal = QtCore.pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.client = Market(url='https://api.kucoin.com')
        self.running = True

    def run(self):
        while self.running:
            try:
                # Tablodaki tüm veriler için güncel fiyatları alıyoruz
                currencies = []
                row_count = ui.tableWidget.rowCount()
                
                
                for row in range(row_count):
                    try:
                        currency = ui.tableWidget.item(row, 2).text()
                        if currency:
                            currencies.append(currency)
                    except AttributeError:
                        pass
                
                # Fiyatları toplu olarak almak için API çağrısı yapıyoruz
                if currencies:
                    print(f"Updating prices for {currencies}")
                    prices = self.get_all_tickers()
                    self.new_price_signal.emit(prices)
            except Exception as e:
                print(f"Fiyat güncellemesi sırasında hata oluştu: {e}")
            # Her 5 saniyede bir fiyat güncellemesi yapılacak
            self.sleep(10)

    def get_all_tickers(self):
        url = "https://api.kucoin.com/api/v1/market/allTickers"
        try:
            response = requests.get(url)
            response.raise_for_status()  # Hata durumunda istisna fırlatır
            data = response.json()
            
            # Gelen verileri kontrol edelim
            if data:
                tickers = data["data"]['ticker']
                return {ticker.get('symbol'): ticker.get('last') for ticker in tickers}
                # for ticker in tickers:
                    # print(f"Symbol: {ticker.get('symbol')}")
                    # print(f"Best Ask: {ticker.get('bestAsk')} ({ticker.get('bestAskSize')})")
                    # print(f"Best Bid: {ticker.get('bestBid')} ({ticker.get('bestBidSize')})")
                    # print(f"Change Rate: {ticker.get('changeRate')}")
                    # print(f"Change Price: {ticker.get('changePrice')}")
                    # print(f"High: {ticker.get('high')}")
                    # print(f"Low: {ticker.get('low')}")
                    # print(f"Volume: {ticker.get('vol')} ({ticker.get('volValue')})")
                    # print(f"Last Price: {ticker.get('last')}")
                    # print(f"Average Price: {ticker.get('averagePrice')}")
                    # print(f"Taker Fee Rate: {ticker.get('takerFeeRate')}")
                    # print(f"Maker Fee Rate: {ticker.get('makerFeeRate')}")
                    # print(f"Taker Coefficient: {ticker.get('takerCoefficient')}")
                    # print(f"Maker Coefficient: {ticker.get('makerCoefficient')}")
            else:
                print(NO_DATA_RECEIVED_MSG)
                print(NO_DATA_RECEIVED_MSG)

        except requests.exceptions.RequestException as e:
            
            print(f"An error occurred: {e}")

    def get_balance_for_token(self,token):
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

    def stop(self):
        self.running = False


def cancel_order(order_id):
    timestamp = str(int(time.time() * 1000))

    # İmza oluşturma (HMAC SHA256)
    endpoint = f"/api/v1/stop-order/{order_id}"  # Emir iptal etme
    str_to_sign = f"{timestamp}DELETE{endpoint}"
    signature = base64.b64encode(hmac.new(API_SECRET.encode('utf-8'), str_to_sign.encode('utf-8'), hashlib.sha256).digest())

    headers = {
        "KC-API-KEY": API_KEY,
        "KC-API-SIGN": signature,
        "KC-API-TIMESTAMP": timestamp,
        "KC-API-PASSPHRASE": API_PASSPHRASE,
        "Content-Type": "application/json"
    }

    response = requests.delete(BASE_URL + endpoint, headers=headers)

    if response.status_code == 200:
        print("Emir iptal edildi.")
        return True
    else:
        print(f"Emir iptal edilemedi: {response.text}")
        return False

def check_existing_order(symbol, side, stop_price, limit_price, size):
    # Zaman damgası oluşturun
    timestamp = str(int(time.time() * 1000))

    # İmza oluşturma (HMAC SHA256) - Mevcut emirleri sorgulamak için
    endpoint = "/api/v1/stop-order?status=active"  # Aktif stop emirlerini sorgula
    str_to_sign = f"{timestamp}GET{endpoint}"
    signature = base64.b64encode(hmac.new(API_SECRET.encode('utf-8'), str_to_sign.encode('utf-8'), hashlib.sha256).digest())

    # API imzalanmış başlıkları ayarla
    headers = {
        "KC-API-KEY": API_KEY,
        "KC-API-SIGN": signature,
        "KC-API-TIMESTAMP": timestamp,
        "KC-API-PASSPHRASE": API_PASSPHRASE,
        "Content-Type": CONTENT_TYPE_JSON
    }

    # HTTP isteği gönder
    response = requests.get(BASE_URL + endpoint, headers=headers)

    if response.status_code == 200:
        orders = response.json()
        for order in orders['data'].get('items', []):
            print(order)
            if (order['symbol'] == symbol and
                order['side'] == side and
                float(order['stopPrice']) == stop_price and
                float(order['price']) == limit_price and
                float(order['size']) == size):
                print(order['stopPrice'], stop_price)
                print(order['price'], limit_price)
                return 0, None  # Aynı emir mevcut
            elif (order['symbol'] == symbol and
                  order['side'] == side and
                  float(order['price'] or 0) != limit_price):
                return 1, order['id']  # Mevcut emri iptal et  
    else:
        print(f"Error fetching orders: {response.text}")
    
    return -1, None  # Aynı emir yok

def place_order(symbol, side, order_type="limit", price=None, size=None, funds=None):
    url = f"{BASE_URL}/api/v1/orders"

    client_oid = str(uuid.uuid4())  # Benzersiz bir clientOid oluşturuyoruz
    timestamp = str(int(time.time() * 1000))

    headers = {
        "KC-API-KEY": API_KEY,
        "KC-API-TIMESTAMP": timestamp,
        "KC-API-PASSPHRASE": API_PASSPHRASE,
        "Content-Type": "application/json",
    } # "KC-API-KEY-VERSION": "2",

    # Hangi tür emrin gönderileceğine göre parametreleri ayarlıyoruz
    data = {
        "clientOid": client_oid,
        "side": side,
        "symbol": symbol,
        "type": order_type,
    }

    if order_type == "limit" and price is not None and size is not None:
        data["price"] = price
        data["size"] = size
    elif order_type == "market":
        if size is not None:
            data["size"] = size
        elif funds is not None:
            data["funds"] = funds
        else:
            raise ValueError("Market emri için 'size' veya 'funds' belirtmelisiniz.")
    else:
        raise ValueError("Limit emri için 'price' ve 'size' parametreleri belirtilmelidir.")

    # JSON string'ini oluşturup imzalama işlemini gerçekleştiriyoruz
    json_data = str(data).replace("'", '"')
    str_to_sign = f"{timestamp}POST/api/v1/orders{json_data}"
    signature = base64.b64encode(
        hmac.new(API_SECRET.encode(), str_to_sign.encode(), hashlib.sha256).digest()
    )

    headers.update({
        "KC-API-SIGN": signature.decode()
    })

    response = requests.post(url, headers=headers, json=data)
    return response.json()


def get_balance_for_token(token):
    try:
        # Belirli bir token için bakiyeyi alıyoruz
        accounts = client.get_account_list()
        
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

def truncate_float(value, decimal_places=6):
    # Verilen değeri belirtilen ondalık basamağa göre kesiyoruz
    factor = 10 ** decimal_places
    return int(value * factor) / factor

def create_stop_limit_order(symbol, side, stop_price, limit_price, size, stop='loss', type='limit'):
    # Zaman damgası oluşturun
    timestamp = str(int(time.time() * 1000))

    # Benzersiz clientOid oluşturun
    client_oid = str(uuid.uuid4())

    # İstek gövdesi (JSON)
    data = {
        "clientOid": client_oid,
        "side": side,               # 'buy' ya da 'sell'
        "symbol": symbol,           # Örneğin 'BTC-USDT'
        "type": type,               # 'limit' olmalı
        "stop": stop,               # 'loss' ya da 'entry' olabilir
        "stopPrice": str(stop_price),# Stop fiyatı (emir tetiklenme noktası)
        "price": str(limit_price),  # Limit fiyatı (emrin gerçekleşmesi için minimum fiyat)
        "size": str(size)           # İşlem miktarı
    }

    # JSON verisini string'e çevir ve boşluk bırakma
    data_str = str(data).replace("'", '"').replace(" ", "")

    # İmza oluşturma (HMAC SHA256)
    endpoint = "/api/v1/stop-order"
    str_to_sign = f"{timestamp}POST{endpoint}{data_str}"
    signature = base64.b64encode(hmac.new(API_SECRET.encode('utf-8'), str_to_sign.encode('utf-8'), hashlib.sha256).digest())

    # API imzalanmış başlıkları ayarla
    headers = {
        "KC-API-KEY": API_KEY,
        "KC-API-SIGN": signature,
        "KC-API-TIMESTAMP": timestamp,
        "KC-API-PASSPHRASE": API_PASSPHRASE,
        "Content-Type": "application/json"
    }

    # HTTP isteği gönder
    response = requests.post(BASE_URL + endpoint, headers=headers, data=data_str)

    # Yanıtı kontrol edin
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": response.status_code, "message": response.text}

def tablo_doldur():
    ui.tableWidget.clearContents()
    ui.tableWidget.setRowCount(0)
    column_count = ui.tableWidget.columnCount()
    cursor.execute("SELECT * FROM anlik_trade")
    data = cursor.fetchall()
    for i in range(len(data)):
        ui.tableWidget.insertRow(i)
        ui.tableWidget.setItem(i, 0, QTableWidgetItem(str(data[i][1])))
        ui.tableWidget.setItem(i, 1, QTableWidgetItem(str(data[i][2])))
        ui.tableWidget.item(i, 1).setFlags(QtCore.Qt.ItemIsEnabled)
        ui.tableWidget.setItem(i, 2, QTableWidgetItem(str(data[i][3])))
        
        ui.tableWidget.setItem(i, 4, QTableWidgetItem(str(data[i][4])))
        ui.tableWidget.setItem(i, 5, QTableWidgetItem(str(data[i][5])))
        ui.tableWidget.setItem(i, 6, QTableWidgetItem(str(data[i][6])))
        
        check_box = QCheckBox()
        check_box.setChecked(bool(data[i][7]))
        ui.tableWidget.setCellWidget(i, 7, check_box)
        
        ui.tableWidget.setItem(i, 8, QTableWidgetItem(str(data[i][8])))
        
        push_buton_guncelle = QPushButton("Guncelle")
        push_buton_guncelle.setStyleSheet("background-color: rgb(0, 255, 0);")
        push_buton_guncelle.setCursor(QCursor(Qt.PointingHandCursor))
        push_buton_guncelle.clicked.connect(lambda: buton_yonlendirme("guncelle"))
        ui.tableWidget.setCellWidget(i, column_count-1, push_buton_guncelle)
                
def get_all_tickers():
    url = "https://api.kucoin.com/api/v1/market/allTickers"
    """{"time": 1602832092060,
  "ticker": [{
      "symbol": "BTC-USDT", // symbol
      "symbolName": "BTC-USDT", // Name of trading pairs, it would change after renaming
      "buy": "11328.9", // bestAsk
      "sell": "11329", // bestBid
	  "bestBidSize": "0.1", 
	  "bestAskSize": "1",
      "changeRate": "-0.0055", // 24h change rate
      "changePrice": "-63.6", // 24h change price
      "high": "11610", // 24h highest price
      "low": "11200", // 24h lowest price
      "vol": "2282.70993217", // 24h volume，the aggregated trading volume in BTC
      "volValue": "25984946.157790431", // 24h total, the trading volume in quote currency of last 24 hours
      "last": "11328.9", // last price
      "averagePrice": "11360.66065903", // 24h average transaction price yesterday
      "takerFeeRate": "0.001", // Basic Taker Fee
      "makerFeeRate": "0.001", // Basic Maker Fee
      "takerCoefficient": "1", // Taker Fee Coefficient
      "makerCoefficient": "1" // Maker Fee Coefficient}]}"""

    try:
        response = requests.get(url)
        response.raise_for_status()  # Hata durumunda istisna fırlatır
        data = response.json()
        
        # Gelen verileri kontrol edelim
        if data:

            tickers = data["data"]['ticker']
            for ticker in tickers:
                print(f"Symbol: {ticker.get('symbol')}")
                print(f"Best Ask: {ticker.get('bestAsk')} ({ticker.get('bestAskSize')})")
                print(f"Best Bid: {ticker.get('bestBid')} ({ticker.get('bestBidSize')})")
                print(f"Change Rate: {ticker.get('changeRate')}")
                print(f"Change Price: {ticker.get('changePrice')}")
                print(f"High: {ticker.get('high')}")
                print(f"Low: {ticker.get('low')}")
                print(f"Volume: {ticker.get('vol')} ({ticker.get('volValue')})")
                print(f"Last Price: {ticker.get('last')}")
                print(f"Average Price: {ticker.get('averagePrice')}")
                print(f"Taker Fee Rate: {ticker.get('takerFeeRate')}")
                print(f"Maker Fee Rate: {ticker.get('makerFeeRate')}")
                print(f"Taker Coefficient: {ticker.get('takerCoefficient')}")
                print(f"Maker Coefficient: {ticker.get('makerCoefficient')}")
        else:
            print("No data received.")

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        
def get_ticker(symbol):
    url = f"https://api.kucoin.com/api/v1/market/orderbook/level1?symbol={symbol}"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Hata durumunda istisna fırlatır
        data = response.json()
        
        # Gelen verileri kontrol edelim
        if data:
            data = data['data']
            return {symbol: data.get('price')}
        else:
            print(NO_DATA_RECEIVED_MSG)
            return {symbol: 0}
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

def parse_float_from_cell(cell_value, default=0):
    try:
        return float(cell_value) if cell_value else default
    except ValueError:
        return default

def get_volume_from_row(row):
    try:
        volume = ui.tableWidget.item(row, 0).text().split("/")
        return float(volume[0]), float(volume[1])
    except (ValueError, AttributeError, IndexError):
        return 0, 0

def get_balance_from_row(row):
    try:
        balance = ui.tableWidget.item(row, 1).text().split("/")
        return float(balance[0]), float(balance[1])
    except (ValueError, AttributeError, IndexError):
        return 0, 0

def get_currency_from_row(row):
    """Satırdaki para birimini döner."""
    try:
        return ui.tableWidget.cellWidget(row, 2).currentText()
    except AttributeError:
        return ui.tableWidget.item(row, 2).text()

def get_price_from_row(row, column):
    price = parse_float_from_cell(ui.tableWidget.item(row, column).text() if ui.tableWidget.item(row, column) else None)
    if price == 0:
        uyari_dondur("Fiyat bilgisi alınamadı!", 6000)
        return None
    return price

def handle_order_error(message, duration=6000):
    uyari_dondur(message, duration)

def handle_limit_exceeded(currency, change_rate, artis_limiti, dusus_limiti, row):
    """Fiyat artış veya düşüş limitini kontrol eder ve ilgili fonksiyonu tetikler."""
    if change_rate > artis_limiti:
        artis_tetiklendi(currency, row)
    elif change_rate  < dusus_limiti* -1 and change_rate < 0:
        dusus_tetiklendi(currency, row)

def handle_kaydet(row):
    onay = QMessageBox.question(MainWindow, "Onay", "Değişiklikleri kaydetmek istediğinizden emin misiniz?\n Program direkt çalışmaya başlayacak!!", QMessageBox.Yes | QMessageBox.No)
    if onay == QMessageBox.Yes:
        satir_kaydet(row=row)

def handle_fiyat_getir(row):
    try:
        currency = ui.tableWidget.cellWidget(row, 2).currentText()
    except AttributeError:
        currency = ui.tableWidget.item(row, 2).text()
    price = get_ticker(currency).get(currency)
    tabloya_ekle(price, row=row)

def handle_bakiye_guncelle():
    for i in range(ui.tableWidget.rowCount()):
        try:
            currency = ui.tableWidget.cellWidget(i, 2).currentText()
        except AttributeError:
            currency = ui.tableWidget.item(i, 2).text()
        token_1 = currency.split("-")[0]
        token_2 = currency.split("-")[1]

        bakiye_1 = get_balance_for_token(token_1)
        bakiye_2 = get_balance_for_token(token_2)
        bakiye = f"{bakiye_1}/{bakiye_2}"
        
        ui.tableWidget.setItem(i, 1, QTableWidgetItem(str(bakiye)))
        cursor.execute("UPDATE anlik_trade SET bakiye = ? WHERE token = ?", (bakiye, currency))
        conn.commit()
    uyari_dondur("Bakiyeler güncellendi", 2000)

def round_price_to_increment(price, price_increment):
    """
    Fiyatı belirtilen price_increment adımına göre yuvarlar.
    
    Args:
        price (float): Güncellenmek istenen fiyat.
        price_increment (float): Fiyatın artırılabileceği minimum adım.
        
    Returns:
        float: Yuvarlanmış fiyat.
    """
    return round(price / price_increment) * price_increment

def create_stop_loss_order(currency, row, balance, cost):
    cursor.execute("SELECT priceIncrement FROM trade_data WHERE symbol = ?", (currency,))
    price_increment = cursor.fetchone()[0]
    round_cost = round_price_to_increment(cost, price_increment)
    stoploss = ui.tableWidget.cellWidget(row, 7).isChecked() if ui.tableWidget.cellWidget(row, 7) else False
    if stoploss:
        stop_limit = parse_float_from_cell(ui.tableWidget.item(row, 8).text())
        if stop_limit == 0:
            handle_order_error(f"{currency} düşüş işlemi limiti belirlenmedi!")
            return
        
        price = get_price_from_row(row, 3)
        if price is None:
            return

        stop_price = price - (price * stop_limit / 100)
        round_stop_price = round_price_to_increment(stop_price, price_increment)
        order_response = create_stop_limit_order(
            symbol=currency,
            side="sell",
            stop_price=round_stop_price,
            limit_price=round_cost,
            size=balance,
            stop='loss'
        )
        print(order_response)
    else:
        order_response = place_order(currency, "sell", order_type="market", size=balance)
        print(order_response)

def artis_tetiklendi(currency, row):
    handle_bakiye_guncelle()
    bakiye, _ = get_balance_from_row(row)
    maliyet = parse_float_from_cell(ui.tableWidget.item(row, 4).text() if ui.tableWidget.item(row, 4) else None, -1)

    if maliyet == -1:
        handle_order_error(f"{currency} artış işlemi maliyetten kaynaklı yapılamadı!")
        return

    if bakiye == 0:
        # handle_order_error(f"{currency} artış işlemi bakiyeden kaynaklı yapılamadı!")
        print(f"{currency} artış işlemi bakiyeden kaynaklı yapılamadı!")
    else:
        price = get_price_from_row(row, 3)
        stop_limit = parse_float_from_cell(ui.tableWidget.item(row, 8).text())
        stop_price = price - (price * stop_limit / 100)
        kontrol,order_id = check_existing_order(currency, "sell", stop_price, maliyet, bakiye)
        print(kontrol)            
        if kontrol == 0:
            print(f"{currency} zaten satış emri verilmiş!")
            # handle_order_error(f"{currency} zaten satış emri verilmiş!")
            return 
        elif kontrol == 1:
            cancel_order(order_id=order_id)
            create_stop_loss_order(currency, row, bakiye, maliyet)
            # print("Stop Emri Fiyatı Güncellendi")
            # maliyet =truncate_float(maliyet)
            # ui.tableWidget.setItem(row, 8, QTableWidgetItem(str(maliyet)))
            return
        elif kontrol == -1:
            create_stop_loss_order(currency, row, bakiye, maliyet)

def dusus_tetiklendi(currency, row):
    handle_bakiye_guncelle()
    print(f"{currency} fiyatı düşüş limitini aştı")
    token_1, token_2 = get_balance_from_row(row)
    islem_hacmi,birim_hacim = get_volume_from_row(row)

    if islem_hacmi == 0:
        # handle_order_error(f"{currency} düşüş işlemi bakiyeden kaynaklı yapılamadı!")
        return
    if birim_hacim == 0:
        # handle_order_error(f"{currency} düşüş işlemi hacimden kaynaklı yapılamadı!")
        return
    
    islem_hacmi = min(islem_hacmi, token_2)
    price = get_price_from_row(row, 3)

    volume =token_1 * price
    islem_hacmi = islem_hacmi - volume
    if islem_hacmi < 0:
        print(f"{currency} işlem hacmi zaten kullanılmış")
        return
    
    cursor.execute("SELECT priceIncrement FROM trade_data WHERE symbol = ?", (currency,))
    price_increment = cursor.fetchone()[0]
    
    round_islem_hacmi = round_price_to_increment(islem_hacmi, price_increment=price_increment)
    round_birim_hacim = round_price_to_increment(birim_hacim, price_increment=price_increment)
    
    funds = min(round_islem_hacmi, birim_hacim)
    order_response = place_order(currency, "buy", order_type="market", funds=funds)
    maliyet_guncelle(row)
    print(order_response)

def parse_limits_from_row(row):
    """Row'dan maliyet, artış ve düşüş limitlerini döner."""
    maliyet = parse_float_from_cell(ui.tableWidget.item(row, 4).text() if ui.tableWidget.item(row, 4) else None, -1)
    artis_limiti = parse_float_from_cell(ui.tableWidget.item(row, 5).text(), 0)
    dusus_limiti = parse_float_from_cell(ui.tableWidget.item(row, 6).text(), 0)

    return maliyet, artis_limiti, dusus_limiti

def parse_balance(balance_text):
    """Bakiyeyi parçalayıp token_1 ve token_2 bakiyelerini döner."""
    try:
        token_1_bakiye = float(balance_text.split("/")[0])
        token_2_bakiye = float(balance_text.split("/")[1])
    except (ValueError, IndexError):
        token_1_bakiye, token_2_bakiye = 0, 0
    return token_1_bakiye, token_2_bakiye

def parse_old_maliyet(row):
    """Satırdaki eski maliyeti döner."""
    eski_maliyet = ui.tableWidget.item(row, 4).text() if ui.tableWidget.item(row, 4) else 0
    try:
        return float(eski_maliyet)
    except ValueError:
        return 0


def calculate_change_rate(current_price, maliyet):
    """Fiyat değişim oranını hesaplar."""
    if maliyet > 0:
        return (current_price - maliyet) / maliyet * 100
    return 0


def fiyat_kontrol(currency, data, row):
    """Güncel fiyat bilgisine göre artış veya düşüş işlemi tetiklenir."""
    price = parse_float_from_cell(data)
    maliyet, artis_limiti, dusus_limiti = parse_limits_from_row(row)

    if maliyet == -1:
        handle_order_error("Lütfen maliyet alanına geçerli bir sayı girin.")
        return

    print(f"Price: {price}, Maliyet: {maliyet}, Artış Limiti: {artis_limiti}, Düşüş Limiti: {dusus_limiti}")

    change_rate = calculate_change_rate(price, maliyet)
    print(f"{currency} fiyatı {change_rate:.2f}% oranında değişti")

    handle_limit_exceeded(currency, change_rate, artis_limiti, dusus_limiti, row)

def find_currency_in_row(row):
    """Belirtilen satırdaki para birimini döner."""
    try:
        return ui.tableWidget.item(row, 2).text()
    except AttributeError:
        return None

def update_price_in_row(row, price):
    """Belirtilen satırdaki fiyat hücresini günceller."""
    
    ui.tableWidget.setItem(row, 3, QTableWidgetItem(str(price)))
    print(f"Satır {row} için fiyat güncellendi: {price}")

def update_existing_currency_price(data, row_count):
    """Var olan para birimi için tabloyu günceller."""
    for row in range(row_count):
        currency = find_currency_in_row(row)
        if currency and currency in data:
            price = data[currency]
            update_price_in_row(row, price)
            fiyat_kontrol(currency, price, row)

def stoploss_guncelle(row):
    stoploss_fiyati = ui.tableWidget.item(row, 8).text()
    try:
        stoploss_fiyati = float(stoploss_fiyati)
    except ValueError:
        handle_order_error("Lütfen geçerli bir sayı girin.")
        return

def tabloya_ekle(data, row=None):
    """Tabloya yeni veri ekler veya var olan veriyi günceller."""
    row_count = ui.tableWidget.rowCount()

    if row is not None:
        update_price_in_row(row, data)
        return

    update_existing_currency_price(data, row_count)
        
def yeni_satir_ekle():
    row = ui.tableWidget.rowCount()
    column = ui.tableWidget.columnCount()
    ui.tableWidget.insertRow(row)
    combo_box=CustomComboBox()
    
    ui.tableWidget.setItem(row, 1, QTableWidgetItem("0/0"))
    ui.tableWidget.item(row, 1).setFlags(QtCore.Qt.ItemIsEnabled)

    cursor.execute("SELECT symbol FROM trade_data")
    data = cursor.fetchall()
    data = [i for i, in data]
    data.sort()
    combo_box.addItems(data)
    combo_box.setCurrentText("BTC-USDT")
    ui.tableWidget.setCellWidget(row, 2, combo_box)
    # ui.tableWidget.setItem(row, 1, QTableWidgetItem(price))
    
    
    check_box = QCheckBox()
    check_box.setChecked(True)
    ui.tableWidget.setCellWidget(row, column-3, check_box)
    
    
    push_buton_kaydet = QPushButton("Kaydet")
    push_buton_kaydet.setStyleSheet("background-color: rgb(0, 255, 0);")
    push_buton_kaydet.setCursor(QCursor(Qt.PointingHandCursor))
    push_buton_kaydet.clicked.connect(lambda: buton_yonlendirme("kaydet"))
    ui.tableWidget.setCellWidget(row, column-1, push_buton_kaydet)
    
    ui.statusBar.showMessage("Yeni satır eklendi", 2000)
       
def satir_kaydet(row):
    buton_yonlendirme("bakiye_guncelle",button=False)
    hacim = ui.tableWidget.item(row, 0).text()          if ui.tableWidget.item(row, 0) else "0"
    bakiye = ui.tableWidget.item(row, 1).text()          if ui.tableWidget.item(row, 1) else "0-0"
    try:
        currency = ui.tableWidget.cellWidget(row, 2).currentText()
    except AttributeError:
        currency = ui.tableWidget.item(row, 2).text()
    price = ui.tableWidget.item(row, 3).text()          if ui.tableWidget.item(row, 3) else "0"
    ortalama_maliyet = ui.tableWidget.item(row, 4).text()       if ui.tableWidget.item(row, 4) else "0"

    artis_limiti = ui.tableWidget.item(row, 5).text()    if ui.tableWidget.item(row, 5) else "0"
    dusus_limiti = ui.tableWidget.item(row, 6).text()   if ui.tableWidget.item(row, 6) else "0"
    stoploss_limiti = ui.tableWidget.item(row, 8).text()   if ui.tableWidget.item(row, 8) else "0"
    try:
        stoploss = ui.tableWidget.cellWidget(row,7).isChecked()  if ui.tableWidget.cellWidget(row,7) else False
    except AttributeError:
        stoploss = False
        
    try:
        hacim1 = hacim.split("/")[0]
        hacim1 = float(hacim1)
        hacim2 = hacim.split("/")[1]
        hacim2 = float(hacim2)
        price = float(price)
        ortalama_maliyet = float(ortalama_maliyet)
        artis_limiti = float(artis_limiti)
        dusus_limiti = float(dusus_limiti)
        stoploss_limiti = float(stoploss_limiti)
    except:
        print(hacim,price,ortalama_maliyet,artis_limiti,dusus_limiti)
        print("Hata")
        QMessageBox.warning(MainWindow, "Hata", "Lütfen  alanlara geçerli bir sayı girin.")
        return
            
    cursor.execute("SELECT * FROM anlik_trade WHERE token=?",(currency,))
    data = cursor.fetchall()
    if len(data)>0:
        cursor.execute("UPDATE anlik_trade SET hacim=?, bakiye=?, ortalama_maliyet=?, artis_limiti=?, dusus_limiti=?,stoploss=?,stoploss_limiti=? WHERE token=?",
        (hacim,bakiye,ortalama_maliyet,artis_limiti,dusus_limiti,stoploss,stoploss_limiti,currency))
        conn.commit()
        print("güncellendi")
        tablo_doldur()
    else:
        cursor.execute("INSERT INTO anlik_trade \
        (hacim,bakiye,token,ortalama_maliyet,artis_limiti,dusus_limiti,stoploss,stoploss_limiti) VALUES (?,?,?,?,?,?,?,?)",
        (hacim,bakiye,currency,ortalama_maliyet,artis_limiti,dusus_limiti,stoploss,stoploss_limiti))
        conn.commit()
        print("kaydedildi")
        tablo_doldur()

def satir_sil(row):
    try:
        try:
            currency = ui.tableWidget.cellWidget(row, 2).currentText()
        except Exception:
            currency = ui.tableWidget.item(row, 2).text()
            cursor.execute("DELETE FROM anlik_trade Where token = ?",(currency,))
            conn.commit()
        ui.tableWidget.removeRow(row)
        ui.statusBar.showMessage("Satır silindi", 2000)
    except Exception:
        uyari_dondur("Satır silinirken hata oluştu",5000)

def buton_yonlendirme(task=None, button=True):
    row = get_row(button)
    if task == "kaydet":
        handle_kaydet(row)
    elif task == "sil":
        satir_sil(row=row)
    elif task == "guncelle":
        satir_kaydet(row=row)
    elif task == "fiyat_getir":
        handle_fiyat_getir(row)
    elif task == "bakiye_guncelle":
        handle_bakiye_guncelle()
    elif task == "maliyet_guncelle":
        maliyet_guncelle(row)

def get_row(button):
    if button:
        sender = MainWindow.sender()
        return ui.tableWidget.indexAt(sender.pos()).row()
    else:
        return ui.tableWidget.currentRow()



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

def get_fills(symbol, api_key, api_secret, api_passphrase):
    endpoint = f'/api/v1/fills?symbol={symbol}&tradeType=TRADE'
    url = BASE_URL + endpoint
    headers = create_headers(api_key, api_secret, api_passphrase, endpoint, 'GET')

    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        # Yanıtın tamamını yazdırarak hatayı incele
        return response.json().get('data', [])
    else:
        print(f"Error fetching data: {response.status_code}, {response.text}")
        return []
    
def ortalama_hesapla(islemler, guncel_bakiye):
    toplam_maliyet = 0
    toplam_miktar = 0
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
            print(toplam_miktar,guncel_bakiye)
            break

    if toplam_miktar == 0:
        return 0  # Eğer hiç alım yapılmadıysa maliyet 0
    else:
        # Mevcut bakiyeye göre ortalama maliyeti döndür
        return toplam_maliyet / guncel_bakiye  # Ortalama maliyet

def maliyet_guncelle(row):
    handle_bakiye_guncelle()
    currency = get_currency_from_row(row)
    bakiye, _ = get_balance_from_row(row)
    islemler = get_fills(currency, API_KEY, API_SECRET, API_PASSPHRASE)
    ortalama_maliyet = ortalama_hesapla(islemler, bakiye)
    print(f"Ortalama maliyet: {ortalama_maliyet}")
    ui.tableWidget.setItem(row, 4, QTableWidgetItem(str(ortalama_maliyet)))
    cursor.execute("UPDATE anlik_trade SET ortalama_maliyet = ? WHERE token = ?", (ortalama_maliyet, currency))
    conn.commit()

def context_menu_event(event):
        context_menu = QMenu(MainWindow)
        add_row_action = context_menu.addAction("Yeni Satır Ekle")
        add_row_action.triggered.connect(lambda: yeni_satir_ekle())
        
        fiyat_getir_action = context_menu.addAction("Fiyat Getir")
        fiyat_getir_action.triggered.connect(lambda: buton_yonlendirme("fiyat_getir",button=False))
        
        delete_row_action = context_menu.addAction("Satırı Sil")
        delete_row_action.triggered.connect(lambda: buton_yonlendirme("sil",button=False))
        
        bakiye_guncelle_action = context_menu.addAction("Bakiyeyi Güncelle")
        bakiye_guncelle_action.triggered.connect(lambda: buton_yonlendirme("bakiye_guncelle",button=False))
        
        maliyet_guncelle_action = context_menu.addAction("Maliyeti Güncelle")
        maliyet_guncelle_action.triggered.connect(lambda: buton_yonlendirme("maliyet_guncelle",button=False))
        
        context_menu.exec_(QCursor.pos())

def uyari_dondur(text,time):
    ui.statusBar.showMessage(text,time)

def close_event(event):
    price_thread.stop()
    price_thread.wait()
    event.accept()


tablo_doldur()
yeni_satir_ekle()
price_thread = PriceUpdateThread()
price_thread.new_price_signal.connect(tabloya_ekle)
price_thread.start()

# ui.pushButton_baslat.clicked.connect(lambda: baslat())    
ui.tableWidget.setContextMenuPolicy(Qt.CustomContextMenu)
ui.tableWidget.customContextMenuRequested.connect(context_menu_event)
MainWindow.closeEvent = close_event

sys.exit(app.exec_())