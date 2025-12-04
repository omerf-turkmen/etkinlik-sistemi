import streamlit as st
import pandas as pd
import os
import time
import random
import smtplib
from email.message import EmailMessage

# --- 1. SAYFA AYARLARI ---
st.set_page_config(page_title="Üniversite Etkinlik Takip Sistemi", layout="wide", page_icon="🎓")

# ==============================================================================
# GÜVENLİK AYARI: Şifreleri artık kodun içine yazmıyoruz!
# Streamlit Cloud'daki "Secrets" alanından çekecek.
# ==============================================================================
try:
    GMAIL_ADRESI = st.secrets["GMAIL_ADRESI"]
    GMAIL_SIFRESI = st.secrets["GMAIL_SIFRESI"]
except:
    # Eğer bilgisayarında (local) çalıştırıyorsan hata vermemesi için uyarı:
    st.error("HATA: E-posta şifreleri bulunamadı. Bu uygulama Streamlit Cloud Secrets ayarlarıyla çalışır.")
    st.stop()

# --- 2. VERİTABANI İŞLEMLERİ ---
KULLANICI_DOSYASI = "kullanicilar.csv"

def kullanicilari_yukle():
    if os.path.exists(KULLANICI_DOSYASI):
        return pd.read_csv(KULLANICI_DOSYASI, dtype=str)
    else:
        df = pd.DataFrame([["admin", "1234", "admin@universite.edu.tr"]], 
                          columns=["kullanici_adi", "sifre", "email"])
        df.to_csv(KULLANICI_DOSYASI, index=False)
        return df

def yeni_kullanici_kaydet(kadi, sifre, email):
    df = kullanicilari_yukle()
    if kadi in df["kullanici_adi"].values:
        return False, "Bu kullanıcı adı zaten alınmış!"
    if email in df["email"].values:
        return False, "Bu e-posta adresi zaten kayıtlı!"
    
    yeni_veri = pd.DataFrame([[kadi, sifre, email]], columns=["kullanici_adi", "sifre", "email"])
    df = pd.concat([df, yeni_veri], ignore_index=True)
    df.to_csv(KULLANICI_DOSYASI, index=False)
    return True, "Kayıt başarılı! Giriş yapabilirsiniz."

def giris_kontrol(kadi, sifre):
    df = kullanicilari_yukle()
    kullanici = df[(df["kullanici_adi"] == kadi) & (df["sifre"] == str(sifre))]
    if not kullanici.empty:
        return True
    return False

def sifre_guncelle_emaille(email, yeni_sifre):
    df = kullanicilari_yukle()
    idx = df.index[df["email"] == email].tolist()
    if not idx:
        return False
    df.at[idx[0], "sifre"] = yeni_sifre
    df.to_csv(KULLANICI_DOSYASI, index=False)
    return True

# --- 3. E-POSTA GÖNDERME FONKSİYONU ---
def dogrulama_kodu_gonder(alici_email):
    kod = str(random.randint(100000, 999999))
    
    msg = EmailMessage()
    msg['Subject'] = 'Sifre Sifirlama Kodu - Etkinlik Sistemi' # Türkçe karakter sıkıntı olabilir diye ingilizce karakter
    msg['From'] = GMAIL_ADRESI
    msg['To'] = alici_email
    msg.set_content(f"Merhaba,\n\nSifre sifirlama kodunuz: {kod}\n\nBu kodu kimseyle paylasmayin.")

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(GMAIL_ADRESI, GMAIL_SIFRESI)
            smtp.send_message(msg)
        return True, kod
    except Exception as e:
        return False, str(e)

# --- 4. GİRİŞ VE KAYIT EKRANI ---
if 'giris_yapildi' not in st.session_state:
    st.session_state['giris_yapildi'] = False
if 'reset_kod' not in st.session_state:
    st.session_state['reset_kod'] = None
if 'reset_email' not in st.session_state:
    st.session_state['reset_email'] = None

def giris_kayit_ekrani():
    st.markdown("<div style='text-align: center; padding-top: 50px;'>", unsafe_allow_html=True)
    st.markdown("<h1>🎓 Kariyer Merkezi Paneli</h1>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        tab_giris, tab_kayit, tab_unuttum = st.tabs(["🔑 Giriş Yap", "📝 Kayıt Ol", "📧 Şifremi Unuttum"])

        # --- GİRİŞ YAP ---
        with tab_giris:
            kullanici_giris = st.text_input("Kullanıcı Adı", key="giris_kadi")
            sifre_giris = st.text_input("Şifre", type="password", key="giris_sifre")
            if st.button("Giriş Yap", type="primary", use_container_width=True):
                if giris_kontrol(kullanici_giris, sifre_giris):
                    st.success(f"Hoş geldin {kullanici_giris}! Yönlendiriliyorsunuz...")
                    st.session_state['giris_yapildi'] = True
                    st.session_state['aktif_kullanici'] = kullanici_giris
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Kullanıcı adı veya şifre hatalı!")

        # --- KAYIT OL ---
        with tab_kayit:
            yeni_kadi = st.text_input("Kullanıcı Adı Belirle", key="kayit_kadi")
            yeni_email = st.text_input("E-posta Adresi", key="kayit_email")
            yeni_sifre = st.text_input("Şifre Belirle", type="password", key="kayit_sifre")
            
            if st.button("Kayıt Ol", type="secondary", use_container_width=True):
                if not yeni_kadi or not yeni_sifre or not yeni_email:
                    st.warning("Lütfen tüm alanları doldurun.")
                elif "@" not in yeni_email:
                    st.warning("Geçerli bir e-posta adresi girin.")
                else:
                    durum, mesaj = yeni_kullanici_kaydet(yeni_kadi, yeni_sifre, yeni_email)
                    if durum:
                        st.success(mesaj)
                    else:
                        st.error(mesaj)

        # --- ŞİFREMİ UNUTTUM ---
        with tab_unuttum:
            st.write("Sıfırlama kodu almak için e-posta adresinizi girin.")
            reset_email_input = st.text_input("E-posta Adresiniz", key="reset_mail_input")
            
            if st.button("Doğrulama Kodu Gönder", type="primary", use_container_width=True):
                df = kullanicilari_yukle()
                if reset_email_input in df["email"].values:
                    with st.spinner("Kod gönderiliyor..."):
                        basari, sonuc = dogrulama_kodu_gonder(reset_email_input)
                        if basari:
                            st.session_state['reset_kod'] = sonuc
                            st.session_state['reset_email'] = reset_email_input
                            st.success("Kod gönderildi! Lütfen mail kutunuzu kontrol edin.")
                        else:
                            st.error(f"Mail gönderilemedi: {sonuc}")
                else:
                    st.error("Bu e-posta adresi sistemde kayıtlı değil.")

            if st.session_state['reset_kod']:
                st.markdown("---")
                girilen_kod = st.text_input("Mailinize Gelen 6 Haneli Kod", key="girilen_kod")
                yeni_sifre_reset = st.text_input("Yeni Şifreniz", type="password", key="new_pass_reset")
                
                if st.button("Şifreyi Onayla ve Değiştir", type="secondary", use_container_width=True):
                    if girilen_kod == st.session_state['reset_kod']:
                        if yeni_sifre_reset:
                            sifre_guncelle_emaille(st.session_state['reset_email'], yeni_sifre_reset)
                            st.success("Şifreniz başarıyla değiştirildi! Giriş yapabilirsiniz.")
                            st.session_state['reset_kod'] = None
                            st.session_state['reset_email'] = None
                        else:
                            st.warning("Lütfen yeni şifrenizi yazın.")
                    else:
                        st.error("Girdiğiniz kod hatalı!")

def cikis_yap():
    st.session_state['giris_yapildi'] = False
    st.session_state['aktif_kullanici'] = ""
    st.rerun()

# --- 5. ANA UYGULAMA AKIŞI ---
if not st.session_state['giris_yapildi']:
    giris_kayit_ekrani()
else:
    aktif_kisi = st.session_state['aktif_kullanici'].upper()

    with st.sidebar:
        st.success(f"👤 Aktif Kullanıcı:\n**{aktif_kisi}**")
        if st.button("🚪 Çıkış Yap"):
            cikis_yap()
        st.markdown("---")

    DOSYA_ADI = "etkinlik_veritabani.csv"

    def veri_yukle():
        if os.path.exists(DOSYA_ADI):
            return pd.read_csv(DOSYA_ADI)
        else:
            return pd.DataFrame(columns=["Tarih", "Etkinlik Adı", "Sorumlu", "Puan", "Durum"])

    def veri_kaydet(yeni_veri):
        df = veri_yukle()
        df = pd.concat([df, pd.DataFrame([yeni_veri])], ignore_index=True)
        df.to_csv(DOSYA_ADI, index=False)

    st.title("🎓 Üniversite Etkinlik Yönetim Sistemi (PUKÖ)")

    with st.sidebar:
        st.header("📝 Etkinlik Künyesi")
        etkinlik_adi = st.text_input("Etkinlik Adı", placeholder="Örn: Kariyer Zirvesi 2024")
        tarih = st.date_input("Etkinlik Tarihi")
        st.info(f"📌 Sorumlu: **{aktif_kisi}**")
        
        st.write("---")
        if os.path.exists(DOSYA_ADI):
            df_indir = pd.read_csv(DOSYA_ADI)
            csv = df_indir.to_csv(index=False).encode('utf-8')
            st.download_button(label="📥 Tüm Raporları İndir (CSV)", data=csv, file_name='etkinlik_raporlari.csv', mime='text/csv')

    tab1, tab2, tab3 = st.tabs(["🟦 PLANLA", "🟨 KONTROL ET", "🟩 ÖNLEM AL"])

    with tab1:
        st.header("P - PLANLA")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("1. Amaç ve Kapsam")
            p1 = st.checkbox("Etkinliğin amacı tanımlandı mı?")
            p2 = st.checkbox("Hedef kitle belirlendi mi?")
            p3 = st.checkbox("Etkinlik türü netleştirildi mi?")
            p4 = st.checkbox("Kazanımlar / çıktılar yazıldı mı?")
            st.subheader("2. Paydaşlar")
            p5 = st.checkbox("Konuşmacı/kurum belirlendi.")
            p6 = st.checkbox("Resmî davet gönderildi.")
            p7 = st.checkbox("Özgeçmiş/özet alındı.")
            p8 = st.checkbox("İhtiyaçlar planlandı.")
        with col2:
            st.subheader("3. Zaman – Mekân")
            p9 = st.checkbox("Tarih ve saat kesinleşti.")
            p10 = st.checkbox("Salon rezervasyonu yapıldı.")
            p11 = st.checkbox("Akış oluşturuldu.")
            p12 = st.checkbox("İK görevlendirmeleri yapıldı.")
            st.subheader("4. Teknik Hazırlık")
            p13 = st.checkbox("Teknik ekipman test edildi.")
            p14 = st.checkbox("Yedekler hazır.")
            p15 = st.checkbox("Görseller hazırlandı.")
            p16 = st.checkbox("Yoklama sistemi hazır.")
            p17 = st.checkbox("Kapanış ve teşekkür gerçekleşti.") 
        plan_listesi = [p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11, p12, p13, p14, p15, p16, p17]

    with tab2:
        st.header("K - KONTROL ET")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("1. Veriler")
            k1 = st.checkbox("Katılımcı sayısı raporlandı.")
            k2 = st.checkbox("Hedef kitle uygunluğu.")
            k3 = st.checkbox("İstatistikler kaydedildi.")
            st.subheader("2. Geri Bildirim")
            k4 = st.checkbox("Memnuniyet anketi yapıldı.")
            k5 = st.checkbox("Konuşmacı değerlendirmesi.")
            k6 = st.checkbox("Teknik notlar alındı.")
        with col2:
            st.subheader("3. Çıktılar")
            k7 = st.checkbox("Amaç gerçekleşti mi?")
            k8 = st.checkbox("Geri bildirim analizi.")
            k9 = st.checkbox("Materyaller arşivlendi.")
        kontrol_listesi = [k1, k2, k3, k4, k5, k6, k7, k8, k9]

    with tab3:
        st.header("Ö - ÖNLEM AL")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("1. İyileştirme")
            o1 = st.checkbox("Aksayan süreçler belirlendi.")
            o2 = st.checkbox("İyileştirme önerileri yazıldı.")
            o3 = st.checkbox("Planlama değişiklikleri not edildi.")
        with col2:
            st.subheader("2. Raporlama")
            o4 = st.checkbox("Rapor hazırlandı.")
            o5 = st.checkbox("Haber paylaşıldı.")
            o6 = st.checkbox("Arşive eklendi.")
        st.subheader("3. Sürdürülebilirlik")
        o7 = st.checkbox("Değerlendirme toplantısı yapıldı mı?")
        o8 = st.checkbox("Kararlar sisteme işlendi mi?")
        onlem_listesi = [o1, o2, o3, o4, o5, o6, o7, o8]

    tum_maddeler = plan_listesi + kontrol_listesi + onlem_listesi
    tamamlanan = sum(tum_maddeler)
    toplam = len(tum_maddeler)
    basari_orani = int((tamamlanan / toplam) * 100) if toplam > 0 else 0

    st.markdown("---")
    col_sol, col_sag = st.columns([3, 1])
    with col_sol:
        st.write(f"### 📈 Genel Başarı Oranı: %{basari_orani}")
        st.progress(basari_orani)

    with col_sag:
        st.write("") 
        if st.button("💾 RAPORU KAYDET", type="primary", use_container_width=True):
            if not etkinlik_adi:
                st.error("⚠️ Lütfen 'Etkinlik Adı' giriniz!")
            else:
                kayit_verisi = {
                    "Tarih": str(tarih),
                    "Etkinlik Adı": etkinlik_adi,
                    "Sorumlu": aktif_kisi,
                    "Puan": basari_orani,
                    "Durum": f"{tamamlanan}/{toplam} Madde"
                }
                veri_kaydet(kayit_verisi)
                st.balloons()
                st.success(f"✅ Kayıt Başarılı! Kaydeden: {aktif_kisi}")

    st.markdown("---")
    st.subheader("🗂️ Tüm Kayıtlar")
    df = veri_yukle()
    st.dataframe(df, use_container_width=True, hide_index=True)