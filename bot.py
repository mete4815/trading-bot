import time
import threading
import config
import exchange
import strategy
import trader
import logger
import telegram_bildirim
import piyasa_verisi
import claude_karar
import telegram_komut

def bot_calistir():
    mesaj = (
        "🤖 <b>AI Trading Bot Başlatıldı</b>\n"
        f"📊 Coin: {config.SYMBOL}\n"
        f"⚠️ Risk: %{config.RISK_PERCENT}\n"
        f"🛑 Stop-loss: %{config.STOP_LOSS_PERCENT}\n"
        f"🎯 Take-profit: %{config.TAKE_PROFIT_PERCENT}\n"
        f"🧠 Karar motoru: Claude AI\n\n"
        f"Komutlar: /bakiye /durum /gecmis /yardim"
    )
    telegram_bildirim.bildirim_gonder(mesaj)

    print("=" * 50)
    print("   AI Trading Bot Başlatıldı")
    print(f"   Coin: {config.SYMBOL}")
    print(f"   Karar motoru: Claude AI")
    print("=" * 50)

    ex = exchange.exchange_baglantisi_kur()
    acik_pozisyon = [None]

    dinleyici = threading.Thread(
        target=telegram_komut.komut_dinle,
        args=(ex, acik_pozisyon),
        daemon=True
    )
    dinleyici.start()

    while True:
        try:
            print(f"\n{'='*50}")
            print(f"Tarama Başladı")
            print(f"{'='*50}")

            fiyat = exchange.fiyat_al(ex)
            bakiye = exchange.bakiye_al(ex)

            df = strategy.mumlar_al(ex, config.SYMBOL)
            df['rsi'] = strategy.rsi_hesapla(df)
            df['ema'] = strategy.ema_hesapla(df)
            son = df.iloc[-1]
            rsi = son['rsi']
            ema = son['ema']

            print(f"RSI: {rsi:.2f} | EMA: {ema:.2f}")

            fg, fg_deger = piyasa_verisi.fear_greed_al()
            haber = piyasa_verisi.haber_skoru_al()
            funding = piyasa_verisi.funding_rate_al()

            if acik_pozisyon[0]:
                if fiyat <= acik_pozisyon[0]['stop']:
                    print(f"🛑 STOP-LOSS tetiklendi! ${fiyat}")
                    btc_bakiye = ex.fetch_balance()['BTC']['free']
                    if btc_bakiye > 0:
                        trader.sat(ex, btc_bakiye, fiyat)
                        logger.kaydet("SAT (stop-loss)", fiyat, btc_bakiye)
                        telegram_bildirim.bildirim_gonder(
                            f"🛑 <b>STOP-LOSS tetiklendi!</b>\n"
                            f"💰 Fiyat: ${fiyat}\n"
                            f"📉 Zarar durduruldu."
                        )
                    acik_pozisyon[0] = None

                elif fiyat >= acik_pozisyon[0]['hedef']:
                    print(f"🎯 TAKE-PROFIT tetiklendi! ${fiyat}")
                    btc_bakiye = ex.fetch_balance()['BTC']['free']
                    if btc_bakiye > 0:
                        trader.sat(ex, btc_bakiye, fiyat)
                        logger.kaydet("SAT (take-profit)", fiyat, btc_bakiye)
                        telegram_bildirim.bildirim_gonder(
                            f"🎯 <b>TAKE-PROFIT tetiklendi!</b>\n"
                            f"💰 Fiyat: ${fiyat}\n"
                            f"📈 Kâr alındı!"
                        )
                    acik_pozisyon[0] = None

                else:
                    kar = ((fiyat - acik_pozisyon[0]['giris']) / acik_pozisyon[0]['giris']) * 100
                    print(f"📊 Açık pozisyon: Giriş ${acik_pozisyon[0]['giris']} | Güncel %{round(kar,2)}")

            else:
                karar, aciklama = claude_karar.karar_al(
                    fiyat, rsi, ema, fg, haber, funding, bakiye
                )

                if karar == "AL":
                    sonuc = trader.al(ex, fiyat, bakiye)
                    if sonuc:
                        acik_pozisyon[0] = sonuc
                        logger.kaydet("AL", fiyat, sonuc['emir']['amount'],
                                      sonuc['stop'], sonuc['hedef'])
                        telegram_bildirim.bildirim_gonder(
                            f"🟢 <b>ALIŞ EMRİ — Claude AI</b>\n"
                            f"💰 Fiyat: ${fiyat}\n"
                            f"🛑 Stop: ${sonuc['stop']}\n"
                            f"🎯 Hedef: ${sonuc['hedef']}\n"
                            f"🧠 {aciklama}"
                        )

                elif karar == "SAT":
                    btc_bakiye = ex.fetch_balance()['BTC']['free']
                    if btc_bakiye > 0:
                        trader.sat(ex, btc_bakiye, fiyat)
                        logger.kaydet("SAT", fiyat, btc_bakiye)
                        telegram_bildirim.bildirim_gonder(
                            f"🔴 <b>SATIŞ EMRİ — Claude AI</b>\n"
                            f"💰 Fiyat: ${fiyat}\n"
                            f"🧠 {aciklama}"
                        )
                    else:
                        print("Satılacak BTC yok.")

            print(f"Sonraki tarama {config.CHECK_INTERVAL} saniye sonra...")
            time.sleep(config.CHECK_INTERVAL)

        except KeyboardInterrupt:
            print("\nBot durduruldu.")
            telegram_bildirim.bildirim_gonder("🔴 <b>AI Trading bot durduruldu.</b>")
            break
        except Exception as e:
            print(f"Hata: {e}")
            telegram_bildirim.bildirim_gonder(f"⚠️ <b>Bot hatası:</b>\n{e}")
            print("30 saniye sonra tekrar deneniyor...")
            time.sleep(30)

if __name__ == "__main__":
    bot_calistir()
