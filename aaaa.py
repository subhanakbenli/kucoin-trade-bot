from PyQt5.QtWidgets import QComboBox

class CustomComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)

    def addItems(self, items):
        super().addItems(items)
        self.sortItems()  # Her öğe eklendiğinde sıralama yap

    def wheelEvent(self, event):
        event.ignore()

# Kullanım kısmı
data = [",","a","b","c","d","e","f","g","k","l","m","n","o","p","r","s","t","u","v","y","z","h","i","j"]
combo_box = CustomComboBox()  # CustomComboBox nesnesini oluşturun
combo_box.addItems(data)  # Verileri ekle