import requests

TELEGRAM_TOKEN = "8778108932:AAEJPtzXhSgLITQGDlSg11ugwfkWaFXQq74"
CHAT_ID = "1023613940"

def bildirim_gonder(mesaj):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    veri = {
        "chat_id": CHAT_ID,
        "text": mesaj,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, data=veri)
    except Exception as e:
        print(f"Telegram hatası: {e}")
