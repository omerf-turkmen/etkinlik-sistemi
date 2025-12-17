import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time

st.set_page_config(page_title="KAPUM Takip Sistemi", layout="wide", page_icon="🎓")

# - AYARLAR -
SHEET_ID = "19NnN6bC_kbfrtViB80REjtqvSKr7OO727i2h7cx8Z0M"
MAX_KULLANICI = 6

# -SORU LİSTELERİ-
SORULAR = {
    "PLANLA": [
        ("p1", "Etkinliğin amacı tanımlandı mı?"),
        ("p2", "Hedef kitle belirlendi mi?"),
        ("p3", "Etkinlik türü netleşti mi?"),
        ("p4", "Kazanımlar/beklenen çıktılar yazıldı mı?"),
        ("p5", "Konuşmacı ve işveren kurumu belli mi?"),
        ("p6", "Resmî davet gönderildi"),
        ("p7", "Konuşmacı özgeçmişi/etkinlik özeti alındı"),
        ("p8", "Konuşmacı ihtiyaçları planlandı"),
        ("p9", "Tarih/Saat kesinleşti"),
        ("p10", "Salon/online platform rezervasyonu yapıldı"),
        ("p11", "Etkinlik akış ve zaman yönetimi oluşturuldu"),
        ("p12", "İnsan kaynağı görevlendirmeleri yapıldı"),
        ("p13", "Ses sistemi, projeksiyon, bilgisayar test edildi"),
        ("p14", "Yedek teknik ekipmanlar hazır"),
        ("p15", "Afiş, poster, banner hazırlandı"),
        ("p16", "Yoklama sistemi hazırlandı"),
        ("p17", "Kapanış ve teşekkür gerçekleştirildi")
    ],
    "KONTROL": [
        ("k1", "Katılımcı sayısı raporlandı"),
        ("k2", "Hedef kitlenin uygunluğu değerlendirildi"),
        ("k3", "Katılım istatistikleri kaydedildi"),
        ("k4", "Katılımcı memnuniyet anketi yapıldı"),
        ("k5", "Konuşmacı değerlendirmesi alındı"),
        ("k6", "Teknik süreçlerin güçlü/zayıf yönleri kaydedildi"),
        ("k7", "Beklenen amaç ve kazanımlar gerçekleşti mi?"),
        ("k8", "Paydaş geri bildirimleri analiz edildi mi?"),
        ("k9", "Sunum ve materyaller arşivlendi mi?")
    ],
    "ONLEM": [
        ("o1", "Eksik ve aksayanlar belirlendi"),
        ("o2", "İyileştirme önerileri yazıldı"),
        ("o3", "Planlama sürecinde değişiklik gerekenler belirlendi"),
        ("o4", "Etkinlik raporu hazırlandı"),
        ("o5", "Fotoğraf ve haber metni paylaşıldı"),
        ("o6", "Tüm dokümanlar arşive eklendi"),
        ("o7", "Süreç değerlendirme toplantısı yapıldı mı?"),
        ("o8", "İyileştirme kararları işlendi mi?")
    ]
}

# Tüm kodları tek listede topluyoruz.
TUM_KODLAR = [kod for liste in SORULAR.values() for kod, metin in liste]

# - GOOGLE SHEET BAĞLANTISI -
def get_gspread_client():
    try:
        if "gcp_service_account" not in st.secrets:
            st.error("Secrets ayarları bulunamadı!")
            st.stop()
            
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"Google Bağlantı Hatası: {e}")
        st.stop()

# - VERİTABANI İŞLEMLERİ (ÖNBELLEKLİ) -
@st.cache_data(ttl=10) 
def veri_cek(sayfa_adi):
    client = get_gspread_client()
    try:
        sheet = client.open_by_key(SHEET_ID).worksheet(sayfa_adi)
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Hata ({sayfa_adi}): {e}")
        st.stop()

def temizle_cache():
    st.cache_data.clear()

def veri_ekle(sayfa_adi, veri_listesi):
    client = get_gspread_client()
    sheet = client.open_by_key(SHEET_ID).worksheet(sayfa_adi)
    sheet.append_row(veri_listesi)
    temizle_cache()

def veri_guncelle(sayfa_adi, etkinlik_adi, yeni_veri):
    client = get_gspread_client()
    sheet = client.open_by_key(SHEET_ID).worksheet(sayfa_adi)
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    try:
        idx = df.index[df['Etkinlik Adı'] == etkinlik_adi].tolist()[0]
        row_num = idx + 2
        sheet.delete_rows(row_num)
        sheet.append_row(yeni_veri)
        temizle_cache()
        return True
    except:
        return False

def veri_sil(sayfa_adi, etkinlik_adi):
    client = get_gspread_client()
    sheet = client.open_by_key(SHEET_ID).worksheet(sayfa_adi)
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    try:
        idx = df.index[df['Etkinlik Adı'] == etkinlik_adi].tolist()[0]
        row_num = idx + 2
        sheet.delete_rows(row_num)
        temizle_cache()
        return True
    except:
        return False

# --- 3. KULLANICI İŞLEMLERİ ---
def kullanici_kontrol(kadi, sifre):
    df = veri_cek("Kullanicilar")
    if df.empty: return False
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
    st.markdown("<h1 style='text-align: center;'>🎓 PUKÖ Giriş</h1>", unsafe_allow_html=True)
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
                    st.error("Hatalı Bilgi.")
        with tab2:
            nkadi = st.text_input("Yeni Kullanıcı Adı")
            nmail = st.text_input("E-posta")
            nsifre = st.text_input("Yeni Şifre", type="password")
            if st.button("Kayıt Ol", use_container_width=True):
                durum, mesaj = yeni_kullanici_kaydet(nkadi, nsifre, nmail)
                if durum: st.success(mesaj)
                else: st.error(mesaj)

# - ANA UYGULAMA -
def ana_uygulama():
    user = st.session_state['user'].upper()
    
    with st.sidebar:
        st.success(f"👤 Aktif: {user}")
        if st.button("Çıkış Yap"):
            st.session_state['giris_yapildi'] = False
            st.rerun()
        st.divider()
        
        mode = st.radio("İşlem:", ["Yeni Kayıt", "Düzenle / Sil"])
        secilen_veri = {}
        eski_ad = None
        
        df_etkinlikler = veri_cek("Etkinlikler")
        
        if mode == "Düzenle / Sil" and not df_etkinlikler.empty:
            liste = df_etkinlikler["Etkinlik Adı"].tolist()
            eski_ad = st.selectbox("Etkinlik Seç:", liste)
            if eski_ad:
                secilen_veri = df_etkinlikler[df_etkinlikler["Etkinlik Adı"] == eski_ad].iloc[0].to_dict()
        
        # --- DURUM SIFIRLAMA ---
        if 'last_mode' not in st.session_state: st.session_state['last_mode'] = None
        if 'last_event' not in st.session_state: st.session_state['last_event'] = None

        reset_needed = False
        if mode != st.session_state['last_mode']:
            reset_needed = True
            st.session_state['last_mode'] = mode
        
        if mode == "Düzenle / Sil" and eski_ad != st.session_state['last_event']:
            reset_needed = True
            st.session_state['last_event'] = eski_ad

        if reset_needed:
            for kod in TUM_KODLAR:
                if mode == "Yeni Kayıt":
                    st.session_state[kod] = False
                elif mode == "Düzenle / Sil" and secilen_veri:
                    st.session_state[kod] = bool(secilen_veri.get(kod, False))

    st.title("KAPUM Etkinlik Takip Sistemi ve Yönetimi")
    
    c1, c2 = st.columns(2)
    with c1:
        e_adi = st.text_input("Etkinlik Adı", value=secilen_veri.get("Etkinlik Adı", ""))
    with c2:
        mevcut_tarih = None
        if "Tarih" in secilen_veri:
            try: mevcut_tarih = pd.to_datetime(secilen_veri["Tarih"]).date()
            except: pass
        e_tarih = st.date_input("Tarih", value=mevcut_tarih)

    # --- SEKMELER ---
    t1, t2, t3 = st.tabs(["🟦 PLANLA", "🟧 KONTROL ET", "🟥 ÖNLEM AL"])
    
    def create_checkbox_group(soru_listesi):
        for kod, metin in soru_listesi:
            if kod not in st.session_state:
                st.session_state[kod] = False
            st.checkbox(metin, key=kod)

    with t1:
        st.subheader("Planlama Süreci")
        create_checkbox_group(SORULAR["PLANLA"])
    with t2:
        st.subheader("Kontrol Süreci")
        create_checkbox_group(SORULAR["KONTROL"])
    with t3:
        st.subheader("Önlem Alma Süreci")
        create_checkbox_group(SORULAR["ONLEM"])

    st.divider()
    
    # - TÜMÜNÜ İŞARETLE (DOĞRU YÖNTEM - CALLBACK) -
    def tumunu_isaretle():
        for kod in TUM_KODLAR:
            st.session_state[kod] = True
            
    col_all, col_space = st.columns([1, 4])
    with col_all:
        st.button("✅ Tümünü İşaretle", on_click=tumunu_isaretle)

    st.subheader("📄 Etkinlik Notları")
    mevcut_not = str(secilen_veri.get("Notlar", ""))
    ekstra_not = st.text_area("Özel notlar:", value=mevcut_not, height=100)

    # Puan Hesapla
    soru_degerleri = [1 if st.session_state[kod] else 0 for kod in TUM_KODLAR]
    tamamlanan = sum(soru_degerleri)
    toplam_soru = len(TUM_KODLAR)
    score = int((tamamlanan/toplam_soru)*100)
    
    st.divider()
    c1_btn, c2_btn = st.columns([3,1])
    c1_btn.metric("Başarı Oranı", f"%{score}")
    c1_btn.progress(score)
    
    btn_text = "🔄 GÜNCELLE" if mode == "Düzenle / Sil" else "💾 KAYDET"
    
    if c2_btn.button(btn_text, type="primary", use_container_width=True):
        if not e_adi:
            st.error("Lütfen Etkinlik Adı giriniz!")
        else:
            # Kaydedilecek satır (Afiş Linki YOK)
            yeni_satir = [
                str(e_tarih), e_adi, user, score,
                f"{tamamlanan}/{toplam_soru} Madde", ekstra_not
            ] + soru_degerleri 
            
            with st.spinner("İşlem yapılıyor..."):
                if mode == "Düzenle / Sil":
                    basari = veri_guncelle("Etkinlikler", eski_ad, yeni_satir)
                    msg = "Güncellendi!"
                else:
                    veri_ekle("Etkinlikler", yeni_satir)
                    basari = True
                    msg = "Kaydedildi!"
            
            if basari:
                st.success(f"✅ {msg}")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Hata oluştu!")

    if mode == "Düzenle / Sil" and eski_ad:
        st.divider()
        st.warning("⚠️ Dikkat: Silinen etkinlik geri getirilemez!")
        if st.button("🗑️ BU ETKİNLİĞİ SİL", use_container_width=True):
            with st.spinner("Siliniyor..."):
                basari = veri_sil("Etkinlikler", eski_ad)
                if basari:
                    st.success("Silindi!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Hata!")

    st.divider()
    st.subheader("Geçmiş Kayıtlar")
    # Afiş sütunu olmasa da hata vermesin diye try-except ile gösteriyoruz
    try:
        st.dataframe(df_etkinlikler.drop(columns=["Afiş Linki"], errors='ignore'))
    except:
        st.dataframe(df_etkinlikler)

if 'giris_yapildi' not in st.session_state:
    st.session_state['giris_yapildi'] = False

if not st.session_state['giris_yapildi']:
    giris_ekrani()
else:
    ana_uygulama()