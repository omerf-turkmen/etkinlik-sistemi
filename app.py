import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time

st.set_page_config(page_title="PUKÖ Takip Sistemi", layout="wide", page_icon="🎓")

# --- AYARLAR ---
SHEET_ADI = "Etkinlik Sistemi"  # Google Drive'daki dosya adın
MAX_KULLANICI = 6

# --- SORU KODLARI LİSTESİ (Sıralama Önemli) ---
SORU_KODLARI = [
    'p1','p2','p3','p4','p5','p6','p7','p8','p9','p10','p11','p12','p13','p14','p15','p16','p17',
    'k1','k2','k3','k4','k5','k6','k7','k8','k9',
    'o1','o2','o3','o4','o5','o6','o7','o8'
]

# --- 1. GOOGLE SHEETS BAĞLANTISI ---
def get_gspread_client():
    try:
        if "gcp_service_account" not in st.secrets:
            st.error("Secrets ayarları bulunamadı!")
            st.stop()
            
        creds_dict = dict(st.secrets["gcp_service_account"])
        # Private key içindeki \n karakterlerini düzelt
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"Google Bağlantı Hatası: {e}")
        st.stop()

# --- 2. VERİTABANI İŞLEMLERİ ---
def veri_cek(sayfa_adi):
    """Veriyi çeker ve DataFrame'e çevirir"""
    client = get_gspread_client()
    try:
        sheet = client.open(SHEET_ADI).worksheet(sayfa_adi)
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except gspread.exceptions.WorksheetNotFound:
        st.error(f"'{sayfa_adi}' isimli sayfa bulunamadı! Lütfen Google Sheet'te oluşturun.")
        st.stop()

def veri_ekle(sayfa_adi, veri_listesi):
    """Yeni satır ekler"""
    client = get_gspread_client()
    sheet = client.open(SHEET_ADI).worksheet(sayfa_adi)
    sheet.append_row(veri_listesi)

def veri_guncelle(sayfa_adi, etkinlik_adi, yeni_veri):
    """Satırı bulur, siler ve güncel halini ekler"""
    client = get_gspread_client()
    sheet = client.open(SHEET_ADI).worksheet(sayfa_adi)
    
    # Tüm veriyi çekip index bulma
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    
    try:
        # Etkinlik adına göre satır numarasını bul (Sheet index 2'den başlar)
        idx = df.index[df['Etkinlik Adı'] == etkinlik_adi].tolist()[0]
        row_num = idx + 2
        
        sheet.delete_rows(row_num) # Eski satırı sil
        sheet.append_row(yeni_veri) # Yeni satırı ekle
        return True
    except:
        return False

# --- 3. KULLANICI İŞLEMLERİ ---
def kullanici_kontrol(kadi, sifre):
    df = veri_cek("Kullanicilar")
    # Verileri string'e çevirip kontrol et
    df['kullanici_adi'] = df['kullanici_adi'].astype(str)
    df['sifre'] = df['sifre'].astype(str)
    
    user = df[(df["kullanici_adi"] == kadi) & (df["sifre"] == str(sifre))]
    return not user.empty

def yeni_kullanici_kaydet(kadi, sifre, email):
    df = veri_cek("Kullanicilar")
    
    if len(df) >= MAX_KULLANICI:
        return False, f"Kullanıcı Sınırı Doldu! (Max {MAX_KULLANICI})"
    
    if kadi in df["kullanici_adi"].values:
        return False, "Bu kullanıcı adı alınmış."
        
    veri_ekle("Kullanicilar", [kadi, sifre, email])
    return True, "Kayıt Başarılı!"

# --- 4. GİRİŞ EKRANI ---
def giris_ekrani():
    st.markdown("<h1 style='text-align: center;'>🎓 PUKÖ Etkinlik Sistemi </h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        tab1, tab2 = st.tabs(["Giriş Yap", "Kayıt Ol"])
        
        with tab1:
            kadi = st.text_input("Kullanıcı Adı")
            sifre = st.text_input("Şifre", type="password")
            if st.button("Giriş Yap", use_container_width=True):
                if kullanici_kontrol(kadi, sifre):
                    st.session_state['giris_yapildi'] = True
                    st.session_state['user'] = kadi
                    st.success("Giriş Başarılı!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Kullanıcı adı veya şifre hatalı.")
        
        with tab2:
            nkadi = st.text_input("Yeni Kullanıcı Adı")
            nmail = st.text_input("E-posta")
            nsifre = st.text_input("Yeni Şifre", type="password")
            if st.button("Kayıt Ol", use_container_width=True):
                durum, mesaj = yeni_kullanici_kaydet(nkadi, nsifre, nmail)
                if durum: st.success(mesaj)
                else: st.error(mesaj)

# --- 5. ANA UYGULAMA ---
def ana_uygulama():
    user = st.session_state['user'].upper()
    
    # Yan Menü
    with st.sidebar:
        st.success(f"👤 Aktif: {user}")
        if st.button("Çıkış Yap"):
            st.session_state['giris_yapildi'] = False
            st.rerun()
        st.divider()
        
        # Mod Seçimi
        mode = st.radio("İşlem:", ["Yeni Kayıt", "Düzenle"])
        
        secilen_veri = {}
        eski_ad = None
        
        # Verileri Google Sheet'ten Çek
        df_etkinlikler = veri_cek("Etkinlikler")
        
        if mode == "Düzenle" and not df_etkinlikler.empty:
            liste = df_etkinlikler["Etkinlik Adı"].tolist()
            eski_ad = st.selectbox("Düzenlenecek Etkinlik:", liste)
            if eski_ad:
                secilen_veri = df_etkinlikler[df_etkinlikler["Etkinlik Adı"] == eski_ad].iloc[0].to_dict()

    # Ana Sayfa Formu
    st.title("PUKÖ Döngüsü Yönetimi")
    
    c1, c2 = st.columns(2)
    with c1:
        e_adi = st.text_input("Etkinlik Adı", value=secilen_veri.get("Etkinlik Adı", ""))
    with c2:
        # Tarih verisini düzgün çekme
        mevcut_tarih = None
        if "Tarih" in secilen_veri:
            try: mevcut_tarih = pd.to_datetime(secilen_veri["Tarih"]).date()
            except: pass
        e_tarih = st.date_input("Tarih", value=mevcut_tarih)

    # --- SORULAR ---
    # Yardımcı fonksiyon: Seçilen veride varsa değerini (1/0) al, yoksa False
    def val(kod):
        if mode == "Düzenle" and kod in secilen_veri:
            return bool(secilen_veri[kod])
        return False

    t1, t2, t3 = st.tabs(["🟦 PLANLA", "🟧 KONTROL ET", "🟥 ÖNLEM AL"])
    cevaplar = {}

    with t1:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("1. Amaç")
            cevaplar['p1'] = st.checkbox("Etkinliğin amacı tanımlandı mı?", value=val('p1'))
            cevaplar['p2'] = st.checkbox("Hedef kitle belirlendi mi?", value=val('p2'))
            cevaplar['p3'] = st.checkbox("Etkinlik türü netleşti mi?", value=val('p3'))
            cevaplar['p4'] = st.checkbox("Kazanımlar/beklenen çıktılar yazıldı mı?", value=val('p4'))
            st.subheader("2. Paydaş ve Konuşmacı")
            cevaplar['p5'] = st.checkbox("Konuşmacı ve işveren kurumu belli mi?", value=val('p5'))
            cevaplar['p6'] = st.checkbox("Resmî davet gönderildi", value=val('p6'))
            cevaplar['p7'] = st.checkbox("Konuşmacı özgeçmişi/etkinlik özeti alındı", value=val('p7'))
            cevaplar['p8'] = st.checkbox("Konuşmacı ihtiyaçları planlandı", value=val('p8'))
        with c2:
            st.subheader("3. Zaman/Mekan")
            cevaplar['p9'] = st.checkbox("Tarih/Saat kesinleşti", value=val('p9'))
            cevaplar['p10'] = st.checkbox("Salon/online platform rezervasyonu yapıldı", value=val('p10'))
            cevaplar['p11'] = st.checkbox("Etkinlik akış ve zaman yönetimi oluşturuldu", value=val('p11'))
            cevaplar['p12'] = st.checkbox("İnsan kaynağı görevlendirmeleri yapıldı", value=val('p12'))
            st.subheader("4. Teknik Hazırlık")
            cevaplar['p13'] = st.checkbox("Ses sistemi, projeksiyon, bilgisayar test edildi", value=val('p13'))
            cevaplar['p14'] = st.checkbox("Yedek teknik ekipmanlar hazır", value=val('p14'))
            cevaplar['p15'] = st.checkbox("Afiş, poster, banner hazırlandı", value=val('p15'))
            cevaplar['p16'] = st.checkbox("Yoklama sistemi hazırlandı", value=val('p16'))
            cevaplar['p17'] = st.checkbox("Kapanış ve teşekkür gerçekleştirildi", value=val('p17'))

    with t2:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("1. Veriler")
            cevaplar['k1'] = st.checkbox("Katılımcı sayısı raporlandı", value=val('k1'))
            cevaplar['k2'] = st.checkbox("Hedef kitlenin uygunluğu değerlendirildi", value=val('k2'))
            cevaplar['k3'] = st.checkbox("Katılım istatistikleri kaydedildi", value=val('k3'))
            st.subheader("2. Geri Bildirim")
            cevaplar['k4'] = st.checkbox("Katılımcı memnuniyet anketi yapıldı", value=val('k4'))
            cevaplar['k5'] = st.checkbox("Konuşmacı değerlendirmesi alındı", value=val('k5'))
            cevaplar['k6'] = st.checkbox("Teknik süreçlerin güçlü/zayıf yönleri kaydedildi", value=val('k6'))
        with c2:
            st.subheader("3. Çıktılar")
            cevaplar['k7'] = st.checkbox("Beklenen amaç ve kazanımlar gerçekleşti mi?", value=val('k7'))
            cevaplar['k8'] = st.checkbox("Paydaş geri bildirimleri analiz edildi mi?", value=val('k8'))
            cevaplar['k9'] = st.checkbox("Sunum ve materyaller arşivlendi mi?", value=val('k9'))

    with t3:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("1. İyileştirme")
            cevaplar['o1'] = st.checkbox("Eksik ve aksayanlar belirlendi", value=val('o1'))
            cevaplar['o2'] = st.checkbox("İyileştirme önerileri yazıldı", value=val('o2'))
            cevaplar['o3'] = st.checkbox("Planlama sürecinde değişiklik gerekenler belirlendi", value=val('o3'))
        with c2:
            st.subheader("2. Raporlama")
            cevaplar['o4'] = st.checkbox("Etkinlik raporu hazırlandı", value=val('o4'))
            cevaplar['o5'] = st.checkbox("Fotoğraf ve haber metni paylaşıldı", value=val('o5'))
            cevaplar['o6'] = st.checkbox("Tüm dokümanlar arşive eklendi", value=val('o6'))
            st.subheader("3. Sürdürülebilirlik")
            cevaplar['o7'] = st.checkbox("Süreç değerlendirme toplantısı yapıldı mı?", value=val('o7'))
            cevaplar['o8'] = st.checkbox("İyileştirme kararları işlendi mi?", value=val('o8'))

    # Not Alanı
    st.divider()
    st.subheader("📄 Etkinlik Notları")
    mevcut_not = str(secilen_veri.get("Notlar", ""))
    ekstra_not = st.text_area("Özel notlar ve hatırlatmalar:", value=mevcut_not, height=100)

    # Hesaplama
    soru_degerleri = []
    # Soru kodları sırasıyla 1 veya 0 olarak listeye eklenir
    for kod in SORU_KODLARI:
        deger = 1 if cevaplar[kod] else 0
        soru_degerleri.append(deger)
    
    tamamlanan = sum(soru_degerleri)
    toplam_soru = len(SORU_KODLARI)
    score = int((tamamlanan/toplam_soru)*100)
    
    st.divider()
    c1, c2 = st.columns([3,1])
    c1.metric("Başarı Oranı", f"%{score}")
    c1.progress(score)
    
    # Buton
    btn_text = "🔄 GÜNCELLE" if mode == "Düzenle" else "💾 KAYDET"
    if c2.button(btn_text, type="primary", use_container_width=True):
        if not e_adi:
            st.error("Lütfen Etkinlik Adı giriniz!")
        else:
            # Google Sheets'e gidecek satır formatı:
            # [Tarih, Etkinlik Adı, Sorumlu, Puan, Durum, Notlar, p1, p2, ..., o8]
            yeni_satir = [
                str(e_tarih),
                e_adi,
                user,
                score,
                f"{tamamlanan}/{toplam_soru} Madde",
                ekstra_not
            ] + soru_degerleri # Listeleri birleştir
            
            with st.spinner("Google Sheets'e kaydediliyor..."):
                if mode == "Düzenle":
                    # Güncelleme mantığı: Eskiyi sil, yeniyi ekle
                    basari = veri_guncelle("Etkinlikler", eski_ad, yeni_satir)
                    msg = "Etkinlik Güncellendi!"
                else:
                    # Yeni kayıt
                    veri_ekle("Etkinlikler", yeni_satir)
                    basari = True
                    msg = "Etkinlik Kaydedildi!"
            
            if basari:
                st.success(f"✅ {msg}")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Bir hata oluştu, kayıt yapılamadı.")

    # Tablo Gösterimi
    st.divider()
    st.subheader("Geçmiş Kayıtlar (Bulut)")
    st.dataframe(df_etkinlikler)

# --- BAŞLANGIÇ ---
if 'giris_yapildi' not in st.session_state:
    st.session_state['giris_yapildi'] = False

if not st.session_state['giris_yapildi']:
    giris_ekrani()
else:
    ana_uygulama()