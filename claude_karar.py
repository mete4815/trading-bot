import requests
import config

def karar_al(fiyat, rsi, ema, fear_greed, haber, funding, bakiye):
    prompt = f"""Sen bir kripto trading uzmanısın. Aşağıdaki piyasa verilerini analiz et ve karar ver.

GÜNCEL VERİLER:
- BTC/USDT Fiyatı: ${fiyat}
- RSI (14): {rsi:.2f}
- EMA (20): {ema:.2f}
- Fear & Greed Index: {fear_greed}
- Haber Sentiment: {haber}
- Funding Rate Durumu: {funding}
- Mevcut Bakiye: ${bakiye}

KURALLAR:
- Sadece 3 seçenekten birini seç: AL, SAT veya BEKLE
- Kısa ve net bir gerekçe yaz (maksimum 2 cümle)
- Yüksek riskli durumlarda mutlaka BEKLE de

YANIT FORMATI (sadece bu formatta yanıtla):
KARAR: [AL/SAT/BEKLE]
GEREKÇE: [kısa açıklama]
GÜVENİLİRLİK: [DÜŞÜK/ORTA/YÜKSEK]"""

    headers = {
        "x-api-key": config.CLAUDE_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    veri = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 150,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    try:
        yanit = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=veri,
            timeout=15
        )
        yanit_json = yanit.json()
        metin = yanit_json['content'][0]['text']

        print(f"\n🤖 Claude Analizi:\n{metin}")

        if "KARAR: AL" in metin:
            return "AL", metin
        elif "KARAR: SAT" in metin:
            return "SAT", metin
        else:
            return "BEKLE", metin

    except Exception as e:
        print(f"Claude API hatası: {e}")
        return "BEKLE", "API hatası, güvenli tarafta kal"
