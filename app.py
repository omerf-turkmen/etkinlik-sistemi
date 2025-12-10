import streamlit as st
import pandas as pd
import os
import time
import random
import smtplib
from email.message import EmailMessage

# --- 1. SAYFA AYARLARI ---
st.set_page_config(page_title="Üniversite Etkinlik Takip Sistemi", layout="wide", page_icon="🎓")

# --- GÜVENLİK VE AYARLAR ---
GMAIL_ADRESI = ""
GMAIL_SIFRESI = ""
try:
    if "GMAIL_ADRESI" in st.secrets:
        GMAIL_ADRESI = st.secrets["GMAIL_ADRESI"]
        GMAIL_SIFRESI = st.secrets["GMAIL_SIFRESI"]
except:
    pass

KULLANICI_DOSYASI = "kullanicilar.csv"
DOSYA_ADI = "etkinlik_veritabani.csv"

# --- 2. FONKSİYONLAR ---
def kullanicilari_yukle():
    if os.path.exists(KULLANICI_DOSYASI):
        return pd.read_csv(KULLANICI_DOSYASI, dtype=str)
    else:
        df = pd.DataFrame([["admin", "1234", "admin@universite.edu.tr"]], columns=["kullanici_adi", "sifre", "email"])
        df.to_csv(KULLANICI_DOSYASI, index=False)
        return df

def yeni_kullanici_kaydet(kadi, sifre, email):
    df = kullanicilari_yukle()
    if kadi in df["kullanici_adi"].values: return False, "Kullanıcı adı dolu!"
    if email in df["email"].values: return False, "Email kayıtlı!"
    yeni = pd.DataFrame([[kadi, sifre, email]], columns=["kullanici_adi", "sifre", "email"])
    df = pd.concat([df, yeni], ignore_index=True)
    df.to_csv(KULLANICI_DOSYASI, index=False)
    return True, "Kayıt başarılı!"

def giris_kontrol(kadi, sifre):
    df = kullanicilari_yukle()
    user = df[(df["kullanici_adi"] == kadi) & (df["sifre"] == str(sifre))]
    return not user.empty

def dogrulama_kodu_gonder(mail):
    if not GMAIL_ADRESI: return False, "Mail ayarı yok!"
    kod = str(random.randint(100000, 999999))
    msg = EmailMessage()
    msg.set_content(f"Kodunuz: {kod}")
    msg['Subject'] = 'Sifre Sifirlama'
    msg['From'] = GMAIL_ADRESI
    msg['To'] = mail
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(GMAIL_ADRESI, GMAIL_SIFRESI)
            smtp.send_message(msg)
        return True, kod
    except Exception as e:
        return False, str(e)

def sifre_guncelle(mail, yeni_sifre):
    df = kullanicilari_yukle()
    idx = df.index[df["email"] == mail].tolist()
    if idx:
        df.at[idx[0], "sifre"] = yeni_sifre
        df.to_csv(KULLANICI_DOSYASI, index=False)

def etkinlikleri_yukle():
    if os.path.exists(DOSYA_ADI): return pd.read_csv(DOSYA_ADI)
    return pd.DataFrame(columns=["Tarih", "Etkinlik Adı", "Sorumlu", "Puan", "Durum"])

def etkinlik_kaydet(veri):
    df = etkinlikleri_yukle()
    df = pd.concat([df, pd.DataFrame([veri])], ignore_index=True)
    df.to_csv(DOSYA_ADI, index=False)

# --- 3. EKRANLAR (GİRİŞ ve ANA UYGULAMA) ---

def giris_ekrani_goster():
    st.markdown("<h1 style='text-align: center;'>🎓 Kariyer Merkezi Giriş</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        t1, t2, t3 = st.tabs(["Giriş", "Kayıt", "Şifre Unuttum"])
        with t1:
            kadi = st.text_input("Kullanıcı Adı")
            sifre = st.text_input("Şifre", type="password")
            if st.button("Giriş Yap", type="primary", use_container_width=True):
                if giris_kontrol(kadi, sifre):
                    st.session_state['giris_yapildi'] = True
                    st.session_state['aktif_kullanici'] = kadi
                    st.rerun()
                else:
                    st.error("Hatalı Bilgi!")
        
        with t2:
            nkadi = st.text_input("Yeni Kullanıcı Adı")
            nmail = st.text_input("E-posta")
            nsifre = st.text_input("Yeni Şifre", type="password")
            if st.button("Kayıt Ol", use_container_width=True):
                d, m = yeni_kullanici_kaydet(nkadi, nsifre, nmail)
                if d: st.success(m)
                else: st.error(m)

        with t3:
            rmail = st.text_input("Mail Adresiniz")
            if st.button("Kod Gönder"):
                d, k = dogrulama_kodu_gonder(rmail)
                if d:
                    st.session_state['reset_kod'] = k
                    st.session_state['reset_email'] = rmail
                    st.success("Kod gönderildi!")
                else: st.error(f"Hata: {k}")
            
            if st.session_state.get('reset_kod'):
                ukod = st.text_input("Gelen Kod")
                npass = st.text_input("Yeni Şifreniz", type="password")
                if st.button("Şifreyi Değiştir"):
                    if ukod == st.session_state['reset_kod']:
                        sifre_guncelle(st.session_state['reset_email'], npass)
                        st.success("Başarılı! Giriş yapabilirsiniz.")
                        st.session_state['reset_kod'] = None
                    else: st.error("Kod Yanlış!")

def ana_uygulama_goster():
    # --- YAN MENÜ ---
    user = st.session_state['aktif_kullanici'].upper()
    with st.sidebar:
        st.success(f"👤 Aktif: {user}")
        if user == "ADMIN":
            with st.expander("Yönetici Paneli"):
                st.write("Verileri İndir:")
                st.download_button("Kullanıcılar (CSV)", kullanicilari_yukle().to_csv(index=False).encode('utf-8'), "users.csv")
                st.download_button("Etkinlikler (CSV)", etkinlikleri_yukle().to_csv(index=False).encode('utf-8'), "events.csv")
        
        if st.button("Çıkış Yap"):
            st.session_state['giris_yapildi'] = False
            st.rerun()
        st.divider()

        st.header("📝 Künye")
        e_adi = st.text_input("Etkinlik Adı")
        e_tarih = st.date_input("Tarih")
        st.info(f"Sorumlu: {user}")

        # İndirme Butonu
        if os.path.exists(DOSYA_ADI):
            csv = pd.read_csv(DOSYA_ADI).to_csv(index=False).encode('utf-8')
            st.download_button("📥 Raporları İndir", csv, "raporlar.csv", "text/csv")

    # --- ANA İÇERİK (SORULAR BURADA) ---
    st.title("PUKÖ Etkinlik Sistemi")
    
    t1, t2, t3 = st.tabs(["🟦 PLANLA", "🟧 KONTROL ET", "🟥 ÖNLEM AL"])

    with t1: # PLANLA
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("1. Amaç")
            p1 = st.checkbox("Amaç tanımlandı mı?")
            p2 = st.checkbox("Hedef kitle belli mi?")
            p3 = st.checkbox("Tür netleşti mi?")
            p4 = st.checkbox("Kazanımlar yazıldı mı?")
            st.subheader("2. Paydaşlar")
            p5 = st.checkbox("Konuşmacı belli mi?")
            p6 = st.checkbox("Davet gitti mi?")
            p7 = st.checkbox("Özgeçmiş alındı mı?")
            p8 = st.checkbox("İhtiyaçlar tam mı?")
        with c2:
            st.subheader("3. Zaman/Mekan")
            p9 = st.checkbox("Tarih/Saat kesin mi?")
            p10 = st.checkbox("Salon ayarlandı mı?")
            p11 = st.checkbox("Akış hazır mı?")
            p12 = st.checkbox("Görevlendirme yapıldı mı?")
            st.subheader("4. Teknik")
            p13 = st.checkbox("Ekipman test edildi mi?")
            p14 = st.checkbox("Yedekler hazır mı?")
            p15 = st.checkbox("Afiş hazır mı?")
            p16 = st.checkbox("Yoklama sistemi hazır mı?")
            p17 = st.checkbox("Kapanış ve teşekkür yapıldı mı?") # Teknik altına eklendi
        
        plan_list = [p1,p2,p3,p4,p5,p6,p7,p8,p9,p10,p11,p12,p13,p14,p15,p16,p17]

    with t2: # KONTROL
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("1. Veriler")
            k1 = st.checkbox("Katılımcı sayısı?")
            k2 = st.checkbox("Hedef kitle uygun muydu?")
            k3 = st.checkbox("İstatistikler?")
            st.subheader("2. Geri Bildirim")
            k4 = st.checkbox("Anket yapıldı mı?")
            k5 = st.checkbox("Konuşmacı değerlendirmesi?")
            k6 = st.checkbox("Teknik notlar?")
        with c2:
            st.subheader("3. Çıktılar")
            k7 = st.checkbox("Amaç gerçekleşti mi?")
            k8 = st.checkbox("Analiz yapıldı mı?")
            k9 = st.checkbox("Arşivlendi mi?")
        
        kontrol_list = [k1,k2,k3,k4,k5,k6,k7,k8,k9]

    with t3: # ÖNLEM
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("1. İyileştirme")
            o1 = st.checkbox("Aksayanlar belirlendi mi?")
            o2 = st.checkbox("Öneriler yazıldı mı?")
            o3 = st.checkbox("Planlama notları?")
        with c2:
            st.subheader("2. Raporlama")
            o4 = st.checkbox("Rapor hazır mı?")
            o5 = st.checkbox("Haber paylaşıldı mı?")
            o6 = st.checkbox("Arşive eklendi mi?")
        st.subheader("3. Sürdürülebilirlik")
        o7 = st.checkbox("Toplantı yapıldı mı?")
        o8 = st.checkbox("Kararlar işlendi mi?")
        
        onlem_list = [o1,o2,o3,o4,o5,o6,o7,o8]

    # --- HESAPLAMA ---
    hepsi = plan_list + kontrol_list + onlem_list
    if len(hepsi) > 0: score = int((sum(hepsi)/len(hepsi))*100)
    else: score = 0
    
    st.divider()
    c1, c2 = st.columns([3,1])
    c1.metric("Başarı Oranı", f"%{score}")
    c1.progress(score)
    
    if c2.button("💾 ETKİNLİĞİ KAYDET", type="primary", use_container_width=True):
        if not e_adi:
            st.error("Etkinlik Adı Giriniz!")
        else:
            data = {
                "Tarih": str(e_tarih), "Etkinlik Adı": e_adi, "Sorumlu": user,
                "Puan": score, "Durum": f"{sum(hepsi)}/{len(hepsi)} Madde"
            }
            etkinlik_kaydet(data)
            st.success("Kayıt Başarılı!")
            st.balloons()
    
    st.divider()
    st.subheader("Geçmiş Kayıtlar")
    st.dataframe(etkinlikleri_yukle(), use_container_width=True)

# --- 4. PROGRAM BAŞLANGICI ---
if 'giris_yapildi' not in st.session_state: st.session_state['giris_yapildi'] = False

if not st.session_state['giris_yapildi']:
    giris_ekrani_goster()
else:
    ana_uygulama_goster()