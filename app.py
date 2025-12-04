import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 1. SAYFA AYARLARI ---
st.set_page_config(page_title="Üniversite Etkinlik Takip Sistemi", layout="wide", page_icon="🎓")

# --- 2. DOSYA VE VERİTABANI İŞLEMLERİ ---
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

# --- 3. BAŞLIK VE YAN MENÜ ---
st.title("🎓 Üniversite Etkinlik Yönetim Sistemi (PUKÖ)")
st.info("Bu form, kalite standartlarına uygun olarak tüm süreçleri kapsar.")

with st.sidebar:
    st.header("📝 Etkinlik Künyesi")
    etkinlik_adi = st.text_input("Etkinlik Adı", placeholder="Örn: Kariyer Zirvesi 2024")
    sorumlu_kisi = st.text_input("Sorumlu Akademisyen/Personel")
    tarih = st.date_input("Etkinlik Tarihi")
    
    st.write("---")
    st.write("📂 **Veri İndirme**")
    if os.path.exists(DOSYA_ADI):
        df_indir = pd.read_csv(DOSYA_ADI)
        csv = df_indir.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Tüm Raporları İndir (CSV)",
            data=csv,
            file_name='etkinlik_raporlari.csv',
            mime='text/csv',
        )

# --- 4. SEKMELER VE MADDELER ---
tab1, tab2, tab3 = st.tabs(["🟦  PLANLA", "🟨  KONTROL ET", "🟩 ÖNLEM AL"])

# --- TAB 1: PLANLA ---
with tab1:
    st.header("PLANLA (Planlama Aşaması)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("1. Etkinlik Amacı ve Kapsamı")
        p1 = st.checkbox("Etkinliğin amacı tanımlandı mı?")
        p2 = st.checkbox("Hedef kitle (öğrenci/mezun/işveren/akademisyen) belirlendi mi?")
        p3 = st.checkbox("Etkinlik türü netleştirildi mi?")
        p4 = st.checkbox("Kazanımlar / beklenen çıktılar yazıldı mı?")

        st.subheader("2. Paydaş ve Konuşmacı Planlaması")
        p5 = st.checkbox("Konuşmacı veya işveren kurumu belirlendi.")
        p6 = st.checkbox("Resmî davet gönderildi.")
        p7 = st.checkbox("Konuşmacı özgeçmişi / etkinlik özeti alındı.")
        p8 = st.checkbox("Konuşmacı ihtiyaçları (sunum, ikram, teknik, transfer) planlandı.")

    with col2:
        st.subheader("3. Zaman – Mekân – Kaynak Planlaması")
        p9 = st.checkbox("Tarih ve saat kesinleşti.")
        p10 = st.checkbox("Salon/online platform rezervasyonu yapıldı.")
        p11 = st.checkbox("Etkinlik akışı ve zaman yönetimi oluşturuldu.")
        p12 = st.checkbox("İnsan kaynağı görevlendirmeleri yapıldı.")

        st.subheader("4. Teknik ve Materyal Hazırlığı")
        p13 = st.checkbox("Ses sistemi, projeksiyon, bilgisayar test edildi.")
        p14 = st.checkbox("Yedek teknik ekipmanlar hazır.")
        p15 = st.checkbox("Afiş, poster, banner, yönlendirmeler hazırlandı.")
        p16 = st.checkbox("Yoklama sistemi (QR, form, imza) hazırlandı.")
        # DÜZELTME: Bu madde buraya taşındı
        p17 = st.checkbox("Kapanış ve teşekkür gerçekleşti.") 

    plan_listesi = [p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11, p12, p13, p14, p15, p16, p17]

# --- TAB 2: KONTROL ET ---
with tab2:
    st.header("KONTROL ET (Değerlendirme ve İzleme)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("1. Katılımcı Verileri")
        k1 = st.checkbox("Katılımcı sayısı raporlandı.")
        k2 = st.checkbox("Hedef kitlenin uygunluğu değerlendirildi.")
        k3 = st.checkbox("Katılım istatistikleri kaydedildi.")
        
        st.subheader("2. Geri Bildirimler")
        k4 = st.checkbox("Katılımcı memnuniyet anketi uygulandı.")
        k5 = st.checkbox("Konuşmacı değerlendirmesi alındı.")
        k6 = st.checkbox("Teknik süreçlerin güçlü/zayıf yönleri kaydedildi.")

    with col2:
        st.subheader("3. Etkinlik Çıktıları")
        k7 = st.checkbox("Beklenen amaç ve kazanımlar gerçekleşti mi?")
        k8 = st.checkbox("Paydaş geri bildirimleri analiz edildi mi?")
        k9 = st.checkbox("Sunum ve materyaller arşivlendi mi?")

    kontrol_listesi = [k1, k2, k3, k4, k5, k6, k7, k8, k9]

# --- TAB 3: ÖNLEM AL ---
with tab3:
    st.header("ÖNLEM AL (İyileştirme ve Sonraki Süreç)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("1. İyileştirme Önerileri")
        o1 = st.checkbox("Eksik veya aksayan süreçler belirlendi.")
        o2 = st.checkbox("Bir sonraki etkinlik için iyileştirme önerileri yazıldı.")
        o3 = st.checkbox("Planlama sürecinde değişiklik gereken noktalar belirlendi.")
        
    with col2:
        st.subheader("2. Raporlama ve Arşiv")
        o4 = st.checkbox("Etkinlik raporu hazırlandı.")
        o5 = st.checkbox("Fotoğraflar ve haber metni paylaşıldı.")
        o6 = st.checkbox("Tüm dokümanlar arşive eklendi.")

    st.subheader("3. Sürdürülebilir İyileştirme")
    o7 = st.checkbox("Süreç değerlendirmesi toplantısı yapıldı mı?")
    o8 = st.checkbox("İyileştirme kararları uygulanmak üzere sisteme işlendi mi?")

    onlem_listesi = [o1, o2, o3, o4, o5, o6, o7, o8]

# --- 5. HESAPLAMA VE KAYDETME ---
tum_maddeler = plan_listesi + kontrol_listesi + onlem_listesi
tamamlanan = sum(tum_maddeler)
toplam = len(tum_maddeler)
if toplam > 0:
    basari_orani = int((tamamlanan / toplam) * 100)
else:
    basari_orani = 0

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
                "Sorumlu": sorumlu_kisi,
                "Puan": basari_orani,
                "Durum": f"{tamamlanan}/{toplam} Madde Tamamlandı"
            }
            veri_kaydet(kayit_verisi)
            st.balloons()
            st.success(f"✅ '{etkinlik_adi}' başarıyla kaydedildi!")

# --- 6. GEÇMİŞ TABLOSU ---
st.markdown("---")
st.subheader("🗂️ Geçmiş Etkinlikler Listesi")
df = veri_yukle()
st.dataframe(df, use_container_width=True, hide_index=True)