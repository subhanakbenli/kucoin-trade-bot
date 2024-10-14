import requests
import uuid
import hashlib
import hmac
import base64
import time

# KuCoin API için gerekli olan bilgileri yerleştiriyoruz
API_KEY = "your_api_key"
API_SECRET = "your_api_secret"
API_PASSPHRASE = "your_api_passphrase"
BASE_URL = "https://api.kucoin.com"

def place_order(symbol, side, order_type="limit", price=None, size=None, funds=None):
    url = f"{BASE_URL}/api/v1/orders"

    client_oid = str(uuid.uuid4())  # Benzersiz bir clientOid oluşturuyoruz
    timestamp = str(int(time.time() * 1000))

    headers = {
        "KC-API-KEY": API_KEY,
        "KC-API-TIMESTAMP": timestamp,
        "KC-API-PASSPHRASE": API_PASSPHRASE,
        "KC-API-KEY-VERSION": "2",
        "Content-Type": "application/json",
    }

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

# Örnek kullanım
# Limit emri örneği
order_response = place_order("BTC-USDT", "buy", order_type="limit", price="30000", size="0.01")
print(order_response)

# Market emri örneği
order_response = place_order("BTC-USDT", "sell", order_type="market", size="0.01")
print(order_response)
