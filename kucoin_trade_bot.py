from PyQt5 import QtWidgets
from PyQt5.QtCore import QDate,Qt
from PyQt5.QtGui import QColor,QCursor
from PyQt5.QtWidgets import QComboBox,QPushButton,QMessageBox,QMenu,QTableWidgetItem,QTextEdit,QSpinBox,QDoubleSpinBox,QDateEdit
import sys
from ui_design.arayuz_ui import *
from kucoin.client import Market





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
    
class DatabaseManager:
    def __init__(self, db_name):
        self.db_name = db_name
        self.connection = con
        self.cursor = cursor

    def create_table(self, table_name, columns):
        columns_with_types = ", ".join([f"{col} {dtype}" for col, dtype in columns.items()])
        create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_with_types})"
        self.cursor.execute(create_table_query)
        self.connection.commit()

    def insert_row(self, table_name, data):
        columns = ", ".join(data.keys())
        placeholders = ", ".join(['?' for _ in data])
        insert_query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        self.cursor.execute(insert_query, tuple(data.values()))
        self.connection.commit()

    def delete_row(self, table_name, condition):
        condition_str = " AND ".join([f"{col} = ?" for col in condition])
        delete_query = f"DELETE FROM {table_name} WHERE {condition_str}"
        self.cursor.execute(delete_query, tuple(condition.values()))
        self.connection.commit()

    def get_rows(self, table_name,
             condition=None,
             cols="*",
             group_by=None,
             order_by=None):
        if condition:
            condition_str = " AND ".join([f"{col} = ?" for col in condition])
            select_query = f"SELECT {cols} FROM {table_name} WHERE {condition_str}"
            if group_by:
                select_query += f" GROUP BY {group_by}"
            if order_by:
                select_query += f" ORDER BY {order_by}"
            self.cursor.execute(select_query, tuple(condition.values()))
        else:
            select_query = f"SELECT {cols} FROM {table_name}"
            if group_by:
                select_query += f" GROUP BY {group_by}"
            if order_by:
                select_query += f" ORDER BY {order_by}"
            self.cursor.execute(select_query)
        rows = self.cursor.fetchall()
        return rows

    def update_row(self, table_name, data, condition):
        update_str = ", ".join([f"{col} = ?" for col in data])
        condition_str = " AND ".join([f"{col} = ?" for col in condition])
        update_query = f"UPDATE {table_name} SET {update_str} WHERE {condition_str}"
        self.cursor.execute(update_query, tuple(data.values()) + tuple(condition.values()))
        self.connection.commit()

def tabloya_ekle(ui,data):
    data={'BTC': '65721.0714499199714513'}
    row=ui.tableWidget.rowCount()
    ui.tableWidget.insertRow(row)
    currency = list(data.keys())[0]
    price = data[currency]
    ui.tableWidget.setItem(row,0,QTableWidgetItem(currency))
    ui.tableWidget.setItem(row,1,QTableWidgetItem(price))
    
import sys
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QTableWidgetItem
from kucoin.client import Market  # Kucoin API paketini kullanıyorsanız

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
                # KuCoin API'sinden USD bazında BTC fiyatı alınıyor
                price = self.client.get_fiat_price(base='USD', currencies='BTC')
                self.new_price_signal.emit(price)
            except Exception as e:
                print(f"Fiyat güncellemesi sırasında hata oluştu: {e}")
            # Her 5 saniyede bir fiyat güncellemesi yapılacak
            self.sleep(5)

    def stop(self):
        self.running = False

# Fiyatları tabloya ekleyen/güncelleyen fonksiyon
def tabloya_ekle(ui, data):
    currency = list(data.keys())[0]
    price = data[currency]
    
    # Tabloda mevcut satır var mı diye kontrol ediyoruz
    row_count = ui.tableWidget.rowCount()
    for row in range(row_count):
        if ui.tableWidget.item(row, 0).text() == currency:
            # Eğer aynı currency zaten varsa sadece fiyatı güncelle
            ui.tableWidget.setItem(row, 1, QTableWidgetItem(price))
            print(f"{currency} fiyatı güncellendi")
            return
    
    # Eğer tabloya ekli değilse yeni satır ekle
    row = ui.tableWidget.rowCount()
    ui.tableWidget.insertRow(row)
    ui.tableWidget.setItem(row, 0, QTableWidgetItem(currency))
    ui.tableWidget.setItem(row, 1, QTableWidgetItem(price))

app = QtWidgets.QApplication(sys.argv)
MainWindow = QtWidgets.QMainWindow()
ui = Ui_MainWindow_bot()
ui.setupUi(MainWindow)
MainWindow.show()

# Fiyat güncelleme işlemini ayrı bir iş parçacığında yapıyoruz
price_thread = PriceUpdateThread()
price_thread.new_price_signal.connect(lambda price: tabloya_ekle(ui, price))
price_thread.start()

# Uygulama kapatıldığında iş parçacığını durduruyoruz
def closeEvent(event):
    price_thread.stop()
    price_thread.wait()
    event.accept()

MainWindow.closeEvent = closeEvent

sys.exit(app.exec_())