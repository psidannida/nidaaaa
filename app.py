import streamlit as st
import pandas as pd
import json
import os
import urllib.parse
from datetime import datetime
import plotly.express as px

# --- 1. AYARLAR VE VERİ ---
# Yeni bir veri dosyası ismi verdim ki eski hatalı verilerle çakışmasın.
VERI_DOSYASI = "nida_kocluk_final_v32.json"
HOCA_TEL = "905307368072"

def veri_yukle():
    if os.path.exists(VERI_DOSYASI):
        try:
            with open(VERI_DOSYASI, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return {"ogrenciler": {}}
    return {"ogrenciler": {}}

def veri_kaydet(veri):
    with open(VERI_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=4)

if 'db' not in st.session_state:
    st.session_state.db = veri_yukle()

# --- 2. MÜFREDAT LİSTESİ ---
m_lgs = {
    "LGS Matematik": ["Çarpanlar Katlar", "Üslü İfadeler", "Kareköklü İfadeler", "Veri Analizi", "Olasılık", "Cebirsel İfadeler", "Doğrusal Denklemler", "Eşitsizlikler", "Üçgenler", "Eşlik ve Benzerlik", "Dönüşüm Geometrisi", "Geometrik Cisimler"],
    "LGS Fen": ["Mevsimler ve İklim", "DNA ve Genetik Kod", "Basınç", "Madde ve Endüstri", "Basit Makineler", "Enerji Dönüşümleri", "Elektrik Yükleri"],
    "LGS Türkçe": ["Fiilimsiler", "Cümlenin Ögeleri", "Sözcükte Anlam", "Cümlede Anlam", "Paragraf", "Yazım-Noktalama", "Söz Sanatları"],
    "LGS Sosyal/Din/İng": ["İnkılap Tarihi", "Din Kültürü", "İngilizce"]
}

m_yks = {
    "TYT Matematik": ["Temel Kavramlar", "Sayı Basamakları", "Bölme-Bölünebilme", "EBOB-EKOK", "Rasyonel Sayılar", "Denklemler", "Mutlak Değer", "Üslü-Köklü", "Çarpanlara Ayırma", "Oran-Orantı", "Problemler", "Kümeler", "Fonksiyonlar", "Permütasyon-Kombinasyon", "Olasılık", "Veri-İstatistik"],
    "AYT Matematik": ["Polinomlar", "2. Dereceden Denklemler", "Karmaşık Sayılar", "Parabol", "Eşitsizlikler", "Trigonometri", "Logaritma", "Diziler", "Limit", "Türev", "İntegral"],
    "TYT Türkçe": ["Sözcükte Anlam", "Cümlede Anlam", "Paragraf", "Dil Bilgisi", "Yazım-Noktalama"],
    "YKS Fen": ["Fizik", "Kimya", "Biyoloji"],
    "YKS Sosyal/Ed": ["Edebiyat", "Tarih", "Coğrafya", "Felsefe", "Din Kültürü"]
}

# --- 3. TASARIM ---
st.set_page_config(page_title="Eğitim Koçu Nida GÖMCELİ", layout="wide")
st.markdown("<style>.stApp { background-color: #05070a; color: white; }</style>", unsafe_allow_html=True)

# --- 4. GİRİŞ VE ŞİFRE ---
if "logged_in" not in st.session_state:
    st.title("🎓 Eğitim Koçu Nida GÖMCELİ")
    t1, t2 = st.tabs(["🔐 Giriş Yap", "🆕 İlk Şifremi Belirle"])
    
    with t1:
        u = st.text_input("Ad Soyad")
        p = st.text_input("Şifre", type="password")
        if st.button("Sisteme Giriş"):
            if u == "admin" and p == "nida2024":
                st.session_state.update({"logged_in": True, "role": "admin"})
                st.rerun()
            elif u in st.session_state.db["ogrenciler"] and st.session_state.db["ogrenciler"][u].get("sifre") == p:
                st.session_state.update({"logged_in": True, "role": "ogrenci", "user": u})
                st.rerun()
            else: st.error("Bilgiler hatalı!")

    with t2:
        nu = st.text_input("Sistemdeki Adınız")
        np = st.text_input("Yeni Şifre", type="password")
        if st.button("Şifremi Kaydet"):
            if nu in st.session_state.db["ogrenciler"]:
                st.session_state.db["ogrenciler"][nu]["sifre"] = np
                veri_kaydet(st.session_state.db); st.success("Şifre oluşturuldu! Artık giriş yapabilirsiniz.")
            else: st.error("İsminiz sistemde bulunamadı.")

else:
    # --- 5. ADMIN PANELİ ---
    if st.session_state["role"] == "admin":
        st.sidebar.title("Nida Hocam")
        menu = st.sidebar.radio("Menü", ["Öğrenci Kaydı", "Gelişim & WhatsApp"])
        if st.sidebar.button("Güvenli Çıkış"): del st.session_state["logged_in"]; st.rerun()

        if menu == "Öğrenci Kaydı":
            with st.expander("👤 Yeni Öğrenci Ekle"):
                ad = st.text_input("Öğrenci Ad Soyad")
                g = st.selectbox("Sınav Grubu", ["LGS", "YKS"])
                t = st.text_input("Veli Tel (905...)")
                h = st.number_input("Haftalık Soru Hedefi", 100)
                if st.button("Kaydet"):
                    st.session_state.db["ogrenciler"][ad] = {"soru": [], "denemeler": [], "sinav": g, "hedef": h, "tel": t, "sifre": None}
                    veri_kaydet(st.session_state.db); st.success("Öğrenci eklendi!")

        elif menu == "Gelişim & WhatsApp":
            sec = st.selectbox("Öğrenci Seç", list(st.session_state.db["ogrenciler"].keys()))
            o = st.session_state.db["ogrenciler"][sec]
            df = pd.DataFrame(o["soru"])
            bugun = datetime.now().strftime("%d/%m")
            bugun_df = df[df["Tarih"] == bugun] if not df.empty else pd.DataFrame()
            g_toplam = bugun_df["Toplam"].sum() if not bugun_df.empty else 0
            
            st.subheader(f"📊 {sec} Gelişim Raporu")
            c1, c2 = st.columns(2)
            c1.metric("Bugün", f"{g_toplam} Soru")
            c2.metric("Haftalık Hedef", f"{df['Toplam'].sum() if not df.empty else 0} / {o['hedef']}")
            
            if not df.empty:
                st.plotly_chart(px.line(df, x="Tarih", y="Toplam", title="İlerleme Grafiği"))
            
            msg = f"Sayın Velimiz, {sec} bugün toplam {g_toplam} soru çözmüştür. İyi çalışmalar. - Eğitim Koçu Nida GÖMCELİ"
            url = f"https://wa.me/{o.get('tel','')}?text={urllib.parse.quote(msg)}"
            st.markdown(f'<a href="{url}" target="_blank" style="background-color:#25D366; color:white; padding:12px; text-decoration:none; border-radius:5px; font-weight:bold;">📱 Veliye WhatsApp Gönder</a>', unsafe_allow_html=True)

    # --- 6. ÖĞRENCİ PANELİ ---
    else:
        u = st.session_state["user"]; o = st.session_state.db["ogrenciler"][u]
        m = m_lgs if o["sinav"] == "LGS" else m_yks
        st.title(f"Hoş Geldin, {u}")
        tab1, tab2, tab3 = st.tabs(["📝 Veri Girişi", "🏆 Deneme Kaydı", "📈 Benim Gelişimim"])
        
        with tab1:
            tur = st.selectbox("Tür", ["Soru Çözümü", "Video İzleme", "Konu Tekrarı"])
            ders = st.selectbox("Ders", list(m.keys()))
            konu = st.selectbox("Konu", m[ders])
            if tur == "Soru Çözümü":
                d = st.number_input("Doğru", 0); y = st.number_input("Yanlış", 0)
                if st.button("Kaydet"):
                    o["soru"].append({"Tarih": datetime.now().strftime("%d/%m"), "Ders": ders, "Konu": konu, "Toplam": d+y, "Net": d-(y/4 if o["sinav"]=="YKS" else y/3)})
                    veri_kaydet(st.session_state.db); st.success("Kaydedildi!")
            else:
                if st.button("Çalışmayı Kaydet"):
                    o["soru"].append({"Tarih": datetime.now().strftime("%d/%m"), "Ders": ders, "Konu": konu, "Toplam": 0, "Detay": tur})
                    veri_kaydet(st.session_state.db); st.success("Kaydedildi!")

        with tab2:
            st.subheader("Deneme Neti Gir")
            yay = st.text_input("Yayın Adı")
            c1, c2 = st.columns(2)
            dn = c1.number_input("Doğru Sayısı", 0); yn = c2.number_input("Yanlış Sayısı", 0)
            if st.button("Denemeyi İşle"):
                net = dn - (yn/4 if o["sinav"]=="YKS" else yn/3)
                o["denemeler"].append({"Tarih": datetime.now().strftime("%d/%m"), "Yayin": yay, "Net": net})
                veri_kaydet(st.session_state.db); st.success(f"Deneme kaydedildi! Netin: {round(net, 2)}")

        with tab3:
            df_o = pd.DataFrame(o["soru"])
            bugun_s = df_o[df_o["Tarih"] == datetime.now().strftime("%d/%m")]["Toplam"].sum() if not df_o.empty else 0
            st.metric("Bugünkü Toplam Sorun", f"{bugun_s}")
            if not df_o.empty:
                st.plotly_chart(px.pie(df_o, values='Toplam', names='Ders', title="Ders Dağılımın"))
            rapor_msg = f"Nida Hocam Merhaba, Ben {u}. Bugün toplam {bugun_s} soru çözdüm. Raporum sistemde hazır!"
            st.markdown(f'<a href="https://wa.me/{HOCA_TEL}?text={urllib.parse.quote(rapor_msg)}" target="_blank" style="background-color:#007bff; color:white; padding:15px; text-decoration:none; border-radius:10px; font-weight:bold;">📤 Hocama Rapor Gönder</a>', unsafe_allow_html=True)