import streamlit as st
import pandas as pd
import os
import time
import random
import smtplib
from email.message import EmailMessage

st.set_page_config(page_title="Üniversite Etkinlik Takip Sistemi", layout="wide", page_icon="🎓")

# --- AYARLAR ---
MAX_KULLANICI_SAYISI = 6  # 1 Admin + 5 Kullanıcı

# --- GÜVENLİK (SECRETS) ---
# Kodun içine şifre yazmıyoruz. Her şeyi gizli kasadan (secrets) çekeceğiz.
GMAIL_ADRESI = ""
GMAIL_SIFRESI = ""
ADMIN_KADI = "admin" # Varsayılan (Eğer secrets girilmezse devreye girer)
ADMIN_SIFRE = "1234"
ADMIN_MAIL = "admin@sistem.com"

try:
    # 1. Gmail Bilgilerini Çek
    if "GMAIL_ADRESI" in st.secrets:
        GMAIL_ADRESI = st.secrets["GMAIL_ADRESI"]
        GMAIL_SIFRESI = st.secrets["GMAIL_SIFRESI"]
    
    # 2. Admin Bilgilerini Çek (SENİN HESABIN)
    if "ADMIN_KADI" in st.secrets:
        ADMIN_KADI = st.secrets["ADMIN_KADI"]
        ADMIN_SIFRE = st.secrets["ADMIN_SIFRE"]
        ADMIN_MAIL = st.secrets["ADMIN_MAIL"]
except:
    pass # Localde çalışırken secrets yoksa hata vermesin diye

# --- DOSYA İSİMLERİ ---
KULLANICI_DOSYASI = "kullanicilar.csv"
DOSYA_ADI = "etkinlik_veritabani.csv"

# --- SORU ID LİSTESİ ---
SORU_KODLARI = [
    'p1','p2','p3','p4','p5','p6','p7','p8','p9','p10','p11','p12','p13','p14','p15','p16','p17',
    'k1','k2','k3','k4','k5','k6','k7','k8','k9',
    'o1','o2','o3','o4','o5','o6','o7','o8'
]

# --- KULLANICI FONKSİYONLARI ---
def kullanicilari_yukle():
    if os.path.exists(KULLANICI_DOSYASI):
        return pd.read_csv(KULLANICI_DOSYASI, dtype=str)
    else:
        # DOSYA YOKSA İLK KULLANICIYI (ADMİNİ) OLUŞTUR
        # Buradaki bilgiler koddan değil, yukarıda Secrets'tan çekilen değişkenlerden gelir.
        df = pd.DataFrame([[ADMIN_KADI, ADMIN_SIFRE, ADMIN_MAIL]], columns=["kullanici_adi", "sifre", "email"])
        df.to_csv(KULLANICI_DOSYASI, index=False)
        return df

def yeni_kullanici_kaydet(kadi, sifre, email):
    df = kullanicilari_yukle()
    
    # LİMİT KONTROLÜ
    mevcut_sayi = len(df)
    if mevcut_sayi >= MAX_KULLANICI_SAYISI:
        return False, f"⚠️ Maksimum kullanıcı sınırına ({MAX_KULLANICI_SAYISI} Kişi) ulaşıldı! Yeni kayıt yapılamaz."
    
    if kadi in df["kullanici_adi"].values: return False, "Bu kullanıcı adı zaten alınmış!"
    if email in df["email"].values: return False, "Bu e-posta adresi zaten kayıtlı!"
    
    yeni = pd.DataFrame([[kadi, sifre, email]], columns=["kullanici_adi", "sifre", "email"])
    df = pd.concat([df, yeni], ignore_index=True)
    df.to_csv(KULLANICI_DOSYASI, index=False)
    return True, "Kayıt başarılı! Giriş yapabilirsiniz."

def giris_kontrol(kadi, sifre):
    df = kullanicilari_yukle()
    user = df[(df["kullanici_adi"] == kadi) & (df["sifre"] == str(sifre))]
    return not user.empty

def dogrulama_kodu_gonder(mail):
    if not GMAIL_ADRESI: return False, "Mail ayarı (Secrets) yapılmamış!"
    kod = str(random.randint(100000, 999999))
    msg = EmailMessage()
    msg.set_content(f"Sifirlama Kodunuz: {kod}")
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

# --- ETKİNLİK FONKSİYONLARI ---
def etkinlikleri_yukle():
    if os.path.exists(DOSYA_ADI): 
        return pd.read_csv(DOSYA_ADI)
    cols = ["Tarih", "Etkinlik Adı", "Sorumlu", "Puan", "Durum", "Notlar"] + SORU_KODLARI
    return pd.DataFrame(columns=cols)

def etkinlik_kaydet_veya_guncelle(veri, eski_ad=None):
    df = etkinlikleri_yukle()
    if eski_ad:
        df = df[df["Etkinlik Adı"] != eski_ad]
    df = pd.concat([df, pd.DataFrame([veri])], ignore_index=True)
    df.to_csv(DOSYA_ADI, index=False)

# --- EKRANLAR ---
def giris_ekrani_goster():
    st.markdown("<h1 style='text-align: center;'>🎓 Kariyer Merkezi Giriş</h1>", unsafe_allow_html=True)
    
    try:
        mevcut = len(kullanicilari_yukle())
        st.caption(f"Sistemdeki Kullanıcı Sayısı: {mevcut}/{MAX_KULLANICI_SAYISI}")
    except:
        pass

    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        t1, t2, t3 = st.tabs(["🚪 Giriş", "🧾 Kayıt", "📧 Şifre Unuttum"])
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
    user = st.session_state['aktif_kullanici'].upper()
    
    # 🕵️ GÜVENLİK AYARI: Giriş yapan kişi Secrets'taki Admin mi?
    # Kodu büyük harfe çevirip kıyaslıyoruz
    IS_ADMIN = (user == ADMIN_KADI.upper())
    
    df_etkinlikler = etkinlikleri_yukle()

    with st.sidebar:
        st.success(f"👤 Aktif: {user}")
        
        # SADECE ADMIN GÖREBİLİR
        if IS_ADMIN:
            with st.expander("Yönetici Paneli"):
                st.write(f"Yönetici: {ADMIN_KADI}")
                st.download_button("Kullanıcılar (CSV)", kullanicilari_yukle().to_csv(index=False).encode('utf-8'), "users.csv")
                st.download_button("Etkinlikler (CSV)", df_etkinlikler.to_csv(index=False).encode('utf-8'), "events.csv")
        
        if st.button("Çıkış Yap"):
            st.session_state['giris_yapildi'] = False
            st.rerun()
        st.divider()

        mode = st.radio("İşlem Seçiniz:", ["Yeni Kayıt Oluştur", "Mevcut Kaydı Düzenle"])
        secilen_veri = {}
        eski_ad = None

        if mode == "Mevcut Kaydı Düzenle":
            etkinlik_listesi = df_etkinlikler["Etkinlik Adı"].tolist() if not df_etkinlikler.empty else []
            secilen_ad = st.selectbox("Düzenlenecek Etkinliği Seç:", etkinlik_listesi)
            if secilen_ad:
                secilen_veri = df_etkinlikler[df_etkinlikler["Etkinlik Adı"] == secilen_ad].iloc[0].to_dict()
                eski_ad = secilen_ad
                st.info(f"🛠️ Düzenleniyor: **{secilen_ad}**")

        st.header("📝 Künye")
        e_adi = st.text_input("Etkinlik Adı", value=secilen_veri.get("Etkinlik Adı", ""))
        try: varsayilan_tarih = pd.to_datetime(secilen_veri.get("Tarih", "today")).date()
        except: varsayilan_tarih = None
        e_tarih = st.date_input("Tarih", value=varsayilan_tarih)
        st.info(f"Sorumlu: {user}")

    st.title("PUKÖ Etkinlik Sistemi")
    
    def get_val(kod):
        if mode == "Mevcut Kaydı Düzenle" and kod in secilen_veri:
            return bool(secilen_veri[kod])
        return False

    t1, t2, t3 = st.tabs(["🟦 PLANLA", "🟧 KONTROL ET", "🟥 ÖNLEM AL"])
    cevaplar = {}

    with t1:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("1. Amaç")
            cevaplar['p1'] = st.checkbox("Etkinliğin amacı tanımlandı mı?", value=get_val('p1'))
            cevaplar['p2'] = st.checkbox("Hedef kitle belirlendi mi?", value=get_val('p2'))
            cevaplar['p3'] = st.checkbox("Etkinlik türü netleşti mi?", value=get_val('p3'))
            cevaplar['p4'] = st.checkbox("Kazanımlar/beklenen çıktılar yazıldı mı?", value=get_val('p4'))
            st.subheader("2. Paydaş ve Konuşmacı Planlaması")
            cevaplar['p5'] = st.checkbox("Konuşmacı ve işveren kurumu belli mi?", value=get_val('p5'))
            cevaplar['p6'] = st.checkbox("Resmî davet gönderildi", value=get_val('p6'))
            cevaplar['p7'] = st.checkbox("Konuşmacı özgeçmişi/etkinlik özeti alındı", value=get_val('p7'))
            cevaplar['p8'] = st.checkbox("Konuşmacı ihtiyaçları planlandı", value=get_val('p8'))
        with c2:
            st.subheader("3. Zaman/Mekan Kaynak Planlaması")
            cevaplar['p9'] = st.checkbox("Tarih/Saat kesinleşti", value=get_val('p9'))
            cevaplar['p10'] = st.checkbox("Salon/online platform rezervasyonu yapıldı", value=get_val('p10'))
            cevaplar['p11'] = st.checkbox("Etkinlik akış ve zaman yönetimi oluşturuldu", value=get_val('p11'))
            cevaplar['p12'] = st.checkbox("İnsan kaynağı görevlendirmeleri yapıldı", value=get_val('p12'))
            st.subheader("4. Teknik ve Materyal Hazırlığı")
            cevaplar['p13'] = st.checkbox("Ses sistemi, projeksiyon, bilgisayar test edildi", value=get_val('p13'))
            cevaplar['p14'] = st.checkbox("Yedek teknik ekipmanlar hazır", value=get_val('p14'))
            cevaplar['p15'] = st.checkbox("Afiş, poster, banner, yönlendirmeler hazırlandı", value=get_val('p15'))
            cevaplar['p16'] = st.checkbox("Yoklama sistemi (QR, form, imza) hazırlandı", value=get_val('p16'))
            cevaplar['p17'] = st.checkbox("Kapanış ve teşekkür gerçekleştirildi", value=get_val('p17'))

    with t2:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("1. Veriler")
            cevaplar['k1'] = st.checkbox("Katılımcı sayısı raporlandı", value=get_val('k1'))
            cevaplar['k2'] = st.checkbox("Hedef kitlenin uygunluğu değerlendirildi", value=get_val('k2'))
            cevaplar['k3'] = st.checkbox("Katılım istatistikleri kaydedildi", value=get_val('k3'))
            st.subheader("2. Geri Bildirim")
            cevaplar['k4'] = st.checkbox("Katılımcı memnuniyet anketi yapıldı", value=get_val('k4'))
            cevaplar['k5'] = st.checkbox("Konuşmacı değerlendirmesi alındı", value=get_val('k5'))
            cevaplar['k6'] = st.checkbox("Teknik süreçlerin güçlü/zayıf yönleri kaydedildi", value=get_val('k6'))
        with c2:
            st.subheader("3. Etkinlik Çıktılar")
            cevaplar['k7'] = st.checkbox("Beklenen amaç ve kazanımlar gerçekleşti mi?", value=get_val('k7'))
            cevaplar['k8'] = st.checkbox("Paydaş geri bildirimleri analiz edildi mi?", value=get_val('k8'))
            cevaplar['k9'] = st.checkbox("Sunum ve materyaller arşivlendi mi?", value=get_val('k9'))

    with t3:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("1. İyileştirme Önerileri")
            cevaplar['o1'] = st.checkbox("Eksik ve aksayanlar belirlendi", value=get_val('o1'))
            cevaplar['o2'] = st.checkbox("Bir sonraki etkinlikler için iyileştirme önerileri yazıldı", value=get_val('o2'))
            cevaplar['o3'] = st.checkbox("Planlama sürecinde değişiklik gereken noktalar belirlendi", value=get_val('o3'))
        with c2:
            st.subheader("2. Raporlama ve Arşiv")
            cevaplar['o4'] = st.checkbox("Etkinlik raporu hazırlandı", value=get_val('o4'))
            cevaplar['o5'] = st.checkbox("Fotoğraf ve haber metni paylaşıldı", value=get_val('o5'))
            cevaplar['o6'] = st.checkbox("Tüm dökümanlar arşive eklendi", value=get_val('o6'))
            st.subheader("3. Sürdürülebilir İyileştirme")
            cevaplar['o7'] = st.checkbox("Süreç değerlendirme toplantısı yapıldı mı?", value=get_val('o7'))
            cevaplar['o8'] = st.checkbox("İyileştirme kararları uygulanmak üzere sisteme işlendi mi?", value=get_val('o8'))

    tamamlanan = sum(cevaplar.values())
    toplam_soru = len(cevaplar)
    score = int((tamamlanan/toplam_soru)*100) if toplam_soru > 0 else 0
    
    st.divider()
    st.subheader("📄 Etkinlik Notları")
    mevcut_not = secilen_veri.get("Notlar", "") if mode == "Mevcut Kaydı Düzenle" else ""
    ekstra_not = st.text_area("Bu etkinlik için eklemek istediğiniz özel notlar:", value=str(mevcut_not), height=100)
    
    st.divider()
    c1, c2 = st.columns([3,1])
    c1.metric("Başarı Oranı", f"%{score}")
    c1.progress(score)
    
    btn_text = "🔄 GÜNCELLE" if mode == "Mevcut Kaydı Düzenle" else "💾 KAYDET"
    if c2.button(btn_text, type="primary", use_container_width=True):
        if not e_adi: st.error("Etkinlik Adı Giriniz!")
        else:
            kayit_verisi = {
                "Tarih": str(e_tarih), "Etkinlik Adı": e_adi, "Sorumlu": user,
                "Puan": score, "Durum": f"{tamamlanan}/{toplam_soru} Madde", "Notlar": ekstra_not
            }
            kayit_verisi.update(cevaplar)
            etkinlik_kaydet_veya_guncelle(kayit_verisi, eski_ad)
            action_msg = "Güncellendi" if eski_ad else "Kaydedildi"
            st.success(f"Başarıyla {action_msg}!")
            time.sleep(1)
            st.rerun()
    
    st.divider()
    st.subheader("Geçmiş Kayıtlar")
    st.dataframe(df_etkinlikler.drop(columns=SORU_KODLARI, errors='ignore'), use_container_width=True)

if 'giris_yapildi' not in st.session_state: st.session_state['giris_yapildi'] = False
if not st.session_state['giris_yapildi']: giris_ekrani_goster()
else: ana_uygulama_goster()