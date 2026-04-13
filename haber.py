import requests

def haber_skoru_al():
    try:
        url = "https://min-api.cryptocompare.com/data/v2/news/?lang=EN&categories=BTC&sortOrder=latest"
        yanit = requests.get(url, timeout=10)
        veri = yanit.json()

        # Farklı yapıları dene
        haberler = []
        if isinstance(veri.get('Data'), list):
            haberler = veri['Data'][:10]
        elif isinstance(veri.get('Data'), dict):
            for key in veri['Data']:
                haberler += veri['Data'][key]
            haberler = haberler[:10]

        if not haberler:
            # Yedek API
            url2 = "https://api.coingecko.com/api/v3/news"
            yanit2 = requests.get(url2, timeout=10)
            veri2 = yanit2.json()
            haberler = veri2.get('data', [])[:10]

        pozitif_kelimeler = ['bull', 'surge', 'rally', 'gain', 'rise',
                             'growth', 'buy', 'support', 'breakout', 'adoption']
        negatif_kelimeler = ['bear', 'crash', 'drop', 'fall', 'sell',
                             'fear', 'hack', 'ban', 'lawsuit', 'warning']

        pozitif = 0
        negatif = 0

        for haber in haberler:
            baslik = str(haber.get('title', '') or haber.get('name', '')).lower()
            for k in pozitif_kelimeler:
                if k in baslik:
                    pozitif += 1
            for k in negatif_kelimeler:
                if k in baslik:
                    negatif += 1

        print(f"Haber analizi: +{pozitif} pozitif / -{negatif} negatif ({len(haberler)} haber)")

        if pozitif > negatif + 1:
            return "POZITIF"
        elif negatif > pozitif + 1:
            return "NEGATIF"
        else:
            return "NOTR"

    except Exception as e:
        print(f"Haber hatası: {e}")
        return "NOTR"
