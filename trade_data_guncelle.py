from kucoin.client import Market


import sqlite3
import time
# Veritabanı bağlantısı oluştur

input("Bot uygulamasını Kapatın.. Başlatmak için enter tuşuna basınız...")
conn = sqlite3.connect('kucoin_data.db')
cursor = conn.cursor()

# Tabloyu oluştur (eğer yoksa)
cursor.execute('''
CREATE TABLE IF NOT EXISTS trade_data (
    symbol  TEXT UNIQUE,
    name TEXT,
    baseCurrency TEXT,
    quoteCurrency TEXT,
    feeCurrency TEXT,
    market TEXT,
    baseMinSize REAL,
    quoteMinSize REAL,
    baseMaxSize REAL,
    quoteMaxSize REAL,
    baseIncrement REAL,
    quoteIncrement REAL,
    priceIncrement REAL,
    priceLimitRate REAL,
    minFunds REAL,
    isMarginEnabled BOOLEAN,
    enableTrading BOOLEAN,
    st BOOLEAN
)
''')
client = Market(url='https://api.kucoin.com')

# Veriler (örnek veri)
data_list = client.get_symbol_list()

# Verileri veritabanına ekle
for data in data_list:
    print(data)
    try:
        MIN_FUND =float(data['minFunds'])
    except:
        MIN_FUND = None
    cursor.execute("Select * from trade_data where symbol = ?", (data['symbol'],))
    if cursor.fetchone():
        continue
    cursor.execute('''
    INSERT INTO trade_data (symbol, name, baseCurrency, quoteCurrency, feeCurrency, market, baseMinSize, quoteMinSize, 
    baseMaxSize, quoteMaxSize, baseIncrement, quoteIncrement, priceIncrement, priceLimitRate, minFunds, isMarginEnabled, 
    enableTrading, st) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['symbol'], data['name'], data['baseCurrency'], data['quoteCurrency'], data['feeCurrency'],
        data['market'], float(data['baseMinSize']), float(data['quoteMinSize']), float(data['baseMaxSize']), 
        float(data['quoteMaxSize']), float(data['baseIncrement']), float(data['quoteIncrement']),
        float(data['priceIncrement']), float(data['priceLimitRate']), MIN_FUND,
        data['isMarginEnabled'], data['enableTrading'], data['st']
    ))
print('Veriler eklendi')
time.sleep(6)



# Değişiklikleri kaydet ve bağlantıyı kapat
conn.commit()
conn.close()

