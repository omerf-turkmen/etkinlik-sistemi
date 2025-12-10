import streamlit as st
import pandas as pd
import os
import time
import random
import smtplib
from email.message import EmailMessage

st.set_page_config(page_title="Üniversite Etkinlik Takip Sistemi", layout="wide", page_icon="🎓")

# --- GÜVENLİK AYARLARI (Secrets) ---
try:
    GMAIL_ADRESI = st.secrets["GMAIL_ADRESI"]
    GMAIL_SIFRESI = st.secrets["GMAIL_SIFRESI"]
except:
    st.error("HATA: E-posta şifreleri bulunamadı. (Secrets ayarı yapılmalı)")
    st.stop()

# --- VERİTABANI İŞLEMLERİ ---
KULLANICI_DOSYASI = "kullanicilar.csv"
DOSYA_ADI = "etkinlik_veritabani.csv"

def kullanicilari_yukle():
    if os.path.exists(KULLANICI_DOSYASI):
        return pd.read_csv(KULLANICI_DOSYASI, dtype=str)
    else:
        # Varsayılan admin
        df = pd.DataFrame([["admin", "1234", "admin@universite.edu.tr"]], columns=["kullanici_adi", "sifre", "email"])
        df.to_csv(KULLANICI_DOSYASI, index=False)
        return df

def yeni_kullanici_kaydet(kadi, sifre, email):
    df = kullanicilari_yukle()
    if kadi in df["kullanici_adi"].values:
        return False, "Bu kullanıcı adı alınmış!"
    if email in df["email"].values:
        return False, "Bu e-posta kayıtlı!"
    
    yeni_veri = pd.DataFrame([[kadi, sifre, email]], columns=["kullanici_adi", "sifre", "email"])
    df = pd.concat([df, yeni_veri], ignore_index=True)
    df.to_csv(KULLANICI_DOSYASI, index=False)
    return True, "Kayıt başarılı!"

def giris_kontrol(kadi, sifre):
    df = kullanicilari_yukle()
    kullanici = df[(df["kullanici_adi"] == kadi) & (df["sifre"] == str(sifre))]
    if not kullanici.empty:
        return True
    return False

def sifre_guncelle_emaille(email, yeni_sifre):
    df = kullanicilari_yukle()
    idx = df.index[df["email"] == email].tolist()
    if not idx: return False
    df.at[idx[0], "sifre"] = yeni_sifre
    df.to_csv(KULLANICI_DOSYASI, index=False)
    return True

# --- ETKİNLİK FONKSİYONLARI ---
def etkinlikleri_yukle():
    if os.path.exists(DOSYA_ADI):
        return pd.read_csv(DOSYA_ADI)
    return pd.DataFrame(columns=["Tarih", "Etkinlik Adı", "Sorumlu", "Puan", "Durum"])

def etkinlik_kaydet(yeni_veri):
    df = etkinlikleri_yukle()
    df = pd.concat([df, pd.DataFrame([yeni_veri])], ignore_index=True)
    df.to_csv(DOSYA_ADI, index=False)

# --- E-POSTA ---
def dogrulama_kodu_gonder(alici_email):
    kod = str(random.randint(100000, 999999))
    msg = EmailMessage()
    msg['Subject'] = 'Sifre Sifirlama Kodu'
    msg['From'] = GMAIL_ADRESI
    msg['To'] = alici_email
    msg.set_content(f"Kodunuz: {kod}")
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(GMAIL_ADRESI, GMAIL_SIFRESI)
            smtp.send_message(msg)
        return True, kod
    except Exception as e:
        return False, str(e)

# --- ANA UYGULAMA MANTIĞI ---
if 'giris_yapildi' not in st.session_state:
    st.session_state['giris_yapildi'] = False
if 'reset_kod' not in st.session_state:
    st.session_state['reset_kod'] = None
if 'reset_email' not in st.session_state:
    st.session_state['reset_email'] = None

# --- GİRİŞ / KAYIT EKRANI ---
if not st.session_state['giris_yapildi']:
    st.markdown("<h1 style='text-align: center;'>🎓 Kariyer Merkezi Paneli</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        tab1, tab2, tab3 = st.tabs(["🔑 Giriş", "📝 Kayıt", "📧 Şifre Unuttum"])
        
        with tab1: # Giriş
            kadi = st.text_input("Kullanıcı Adı", key="giris_kadi")
            sifre = st.text_input("Şifre", type="password", key="giris_sifre")
            if st.button("Giriş Yap", type="primary", use_container_width=True):
                if giris_kontrol(kadi, sifre):
                    st.success("Giriş Başarılı!")
                    st.session_state['giris_yapildi'] = True
                    st.session_state['aktif_kullanici'] = kadi
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Hatalı bilgi!")

        with tab2: # Kayıt
            nkadi = st.text_input("Kullanıcı Adı", key="kayit_kadi")
            nmail = st.text_input("E-posta", key="kayit_mail")
            nsifre = st.text_input("Şifre", type="password", key="kayit_sifre")
            if st.button("Kayıt Ol", type="secondary", use_container_width=True):
                if nkadi and nmail and nsifre:
                    durum, msj = yeni_kullanici_kaydet(nkadi, nsifre, nmail)
                    if durum: st.success(msj)
                    else: st.error(msj)
                else:
                    st.warning("Alanları doldurun.")

        with tab3: # Şifre Reset
            rmail = st.text_input("E-posta Adresiniz", key="reset_mail")
            if st.button("Kod Gönder"):
                durum, kod = dogrulama_kodu_gonder(rmail)
                if durum:
                    st.session_state['reset_kod'] = kod
                    st.session_state['reset_email'] = rmail
                    st.success("Kod gönderildi!")
                else:
                    st.error(f"Hata: {kod}")
            
            if st.session_state['reset_kod']:
                ukod = st.text_input("Kod", key="user_kod")
                ysifre = st.text_input("Yeni Şifre", type="password", key="new_pass")
                if st.button("Onayla"):
                    if ukod == st.session_state['reset_kod']:
                        sifre_guncelle_emaille(st.session_state['reset_email'], ysifre)
                        st.success("Şifre değişti!")
                        st.session_state['reset_kod'] = None
                    else:
                        st.error("Kod yanlış!")

else:
    # --- GİRİŞ SONRASI PANEL ---
    aktif_kisi = st.session_state['aktif_kullanici']
    
    with st.sidebar:
        st.success(f"👤 Aktif: {aktif_kisi.upper()}")
        
        # --- ÖZEL ADMIN PANELİ (SADECE ADMIN GÖRÜR) ---
        if aktif_kisi == "admin":
            with st.expander("🕵️ YÖNETİCİ PANELİ (GİZLİ)"):
                st.write("**Tüm Veritabanı Yönetimi**")
                
                # 1. Kullanıcıları İndir
                kullanicilar_df = kullanicilari_yukle()
                st.download_button(
                    label="👥 Kullanıcı Listesini İndir (CSV)",
                    data=kullanicilar_df.to_csv(index=False).encode('utf-8'),
                    file_name="guncel_kullanicilar.csv",
                    mime="text/csv"
                )
                
                # 2. Etkinlikleri İndir
                etkinlikler_df = etkinlikleri_yukle()
                st.download_button(
                    label="📊 Etkinlikleri İndir (CSV)",
                    data=etkinlikler_df.to_csv(index=False).encode('utf-8'),
                    file_name="guncel_etkinlikler.csv",
                    mime="text/csv"
                )
                
                # 3. Anlık Görüntüle
                if st.checkbox("Kullanıcıları Tabloda Göster"):
                    st.dataframe(kullanicilar_df)
        
        if st.button("Çıkış Yap"):
            st.session_state['giris_yapildi'] = False
            st.rerun()

    # --- ANA İÇERİK ---
    st.title("🎓 PUKÖ Etkinlik Sistemi")
    
    with st.sidebar:
        st.write("---")
        e_adi = st.text_input("Etkinlik Adı")
        e_tarih = st.date_input("Tarih")
    
    # Basit sekmeler (Önceki kodun aynısı)
    t1, t2, t3 = st.tabs(["PLANLA", "KONTROL", "ÖNLEM"])
    with t1:
        p1 = st.checkbox("Planlama yapıldı mı?")
    with t2:
        k1 = st.checkbox("Kontroller tamam mı?")
        k2 = st.checkbox("Kapanış ve teşekkür gerçekleşti.")
    with t3:
        o1 = st.checkbox("Önlemler alındı mı?")
    
    # Kaydet Butonu
    if st.button("💾 Kaydet", type="primary"):
        puan = 100 # Örnek hesaplama
        veri = {
            "Tarih": str(e_tarih),
            "Etkinlik Adı": e_adi,
            "Sorumlu": aktif_kisi,
            "Puan": puan,
            "Durum": "Tamamlandı"
        }
        etkinlik_kaydet(veri)
        st.success("Kaydedildi!")

    st.write("---")
    st.subheader("Geçmiş Kayıtlar")
    st.dataframe(etkinlikleri_yukle(), use_container_width=True)