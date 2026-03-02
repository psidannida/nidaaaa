import streamlit as st
import pandas as pd
import json
import os
import urllib.parse
from datetime import datetime
import plotly.express as px
import random

# --- 1. AYARLAR ---
VERI_DOSYASI = "nida_akademiv37_data.json"
HOCA_TEL = "905307368072"
SITE_URL = "https://egitimkocunidagomceli.streamlit.app"

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

# --- 2. MÜFREDAT ---
m_lgs = {"LGS Matematik": ["Çarpanlar Katlar", "Üslü", "Kareköklü", "Olasılık", "Cebirsel", "Denklemler", "Üçgenler", "Eşlik Benzerlik", "Dönüşüm", "Geometrik Cisimler"], "LGS Fen": ["Mevsimler", "DNA", "Basınç", "Madde", "Basit Makineler", "Enerji", "Elektrik"], "LGS Türkçe": ["Fiilimsiler", "Cümlenin Ögeleri", "Anlam Bilgisi", "Yazım-Noktalama"], "LGS Sosyal/Din/İng": ["İnkılap Tarihi", "Din Kültürü", "İngilizce"]}
m_yks = {"TYT Matematik": ["Temel Kavramlar", "Problemler", "Kümeler", "Fonksiyonlar", "Geometri"], "AYT Matematik": ["Polinom-Parabol", "Trigonometri", "Logaritma", "Diziler", "Limit-Türev-İntegral"], "TYT Türkçe": ["Paragraf", "Dil Bilgisi", "Yazım-Noktalama"], "YKS Fen": ["Fizik", "Kimya", "Biyoloji"], "YKS Sosyal/Ed": ["Edebiyat", "Tarih", "Coğrafya"]}

# --- 3. TASARIM ---
st.set_page_config(page_title="Nida Akademi v37", layout="wide")
st.markdown("<style>.stApp { background-color: #05070a; color: white; }</style>", unsafe_allow_html=True)

# --- 4. GİRİŞ ---
if "logged_in" not in st.session_state:
    st.title("🎓 Eğitim Koçu Nida GÖMCELİ")
    u = st.text_input("Ad Soyad")
    p = st.text_input("Şifre", type="password")
    if st.button("Giriş Yap"):
        if u == "admin" and p == "nida2024":
            st.session_state.update({"logged_in": True, "role": "admin"})
            st.rerun()
        elif u in st.session_state.db.get("ogrenciler", {}) and st.session_state.db["ogrenciler"][u].get("sifre") == p:
            st.session_state.update({"logged_in": True, "role": "ogrenci", "user": u})
            st.rerun()
        else: st.error("Bilgiler Hatalı!")

else:
    # --- 5. ADMIN PANELİ ---
    if st.session_state["role"] == "admin":
        st.sidebar.title("Nida Hocam")
        menu = st.sidebar.radio("Menü", ["Öğrenci Kaydı & Şifre", "Analiz & Veli Raporu"])
        if st.sidebar.button("Çıkış"): del st.session_state["logged_in"]; st.rerun()

        if menu == "Öğrenci Kaydı & Şifre":
            with st.expander("👤 Yeni Öğrenci Ekle"):
                c1, c2 = st.columns(2)
                ad = c1.text_input("Öğrenci Ad Soyad")
                g = c2.selectbox("Sınav", ["LGS", "YKS"])
                o_tel = c1.text_input("Öğrenci Tel (905...)")
                v_tel = c2.text_input("Veli Tel (905...)")
                h = st.number_input("Haftalık Hedef", 100)
                if st.button("Kaydet"):
                    sifre = str(random.randint(1000, 9999))
                    if "ogrenciler" not in st.session_state.db: st.session_state.db["ogrenciler"] = {}
                    st.session_state.db["ogrenciler"][ad] = {"soru": [], "denemeler": [], "sinav": g, "hedef": h, "o_tel": o_tel, "v_tel": v_tel, "sifre": sifre}
                    veri_kaydet(st.session_state.db); st.success(f"Kaydedildi! Şifre: {sifre}")

            st.subheader("📋 Şifre Gönder")
            for isim, detay in st.session_state.db.get("ogrenciler", {}).items():
                col1, col2 = st.columns([3, 1])
                col1.write(f"*{isim}* (Şifre: {detay['sifre']})")
                s_msg = f"Selam {isim}, Nida Akademi giriş şifren: {detay['sifre']}\nLink: {SITE_URL}"
                col2.markdown(f'[📲 Gönder](https://wa.me/{detay["o_tel"]}?text={urllib.parse.quote(s_msg)})')

        elif menu == "Analiz & Veli Raporu":
            if not st.session_state.db.get("ogrenciler"): st.warning("Henüz öğrenci yok.")
            else:
                sec = st.selectbox("Öğrenci Seç", list(st.session_state.db["ogrenciler"].keys()))
                o = st.session_state.db["ogrenciler"][sec]
                df = pd.DataFrame(o["soru"])
                h_toplam = df['Toplam'].sum() if not df.empty else 0
                st.subheader(f"🎯 Hedef: {h_toplam} / {o['hedef']}")
                st.progress(min(h_toplam / o['hedef'], 1.0) if o['hedef'] > 0 else 0)
                if o["denemeler"]:
                    st.info(f"🏆 Son Puan: {o['denemeler'][-1]['Puan']} | ⚠️ Yanlışlar: {o['denemeler'][-1].get('Yanlis_Konular','-')}")
                if not df.empty:
                    st.dataframe(df.groupby(['Ders', 'Konu'])['Toplam'].sum().reset_index(), use_container_width=True)
                v_msg = f"Sayın Velimiz, {sec} bu hafta {h_toplam} soru çözmüştür. - Nida GÖMCELİ"
                st.markdown(f'<a href="https://wa.me/{o["v_tel"]}?text={urllib.parse.quote(v_msg)}" target="_blank" style="background-color:#25D366; color:white; padding:10px; text-decoration:none; border-radius:5px;">📱 VELİYE RAPOR</a>', unsafe_allow_html=True)

    # --- 6. ÖĞRENCİ PANELİ ---
    else:
        u = st.session_state["user"]; o = st.session_state.db["ogrenciler"][u]
        m = m_lgs if o.get("sinav") == "LGS" else m_yks
        st.title(f"Selam {u} ✨")
        tab1, tab2, tab3 = st.tabs(["📝 Çalışma Girişi", "🏆 Deneme Analizi", "📊 Gelişimim"])
        with tab1:
            tur = st.selectbox("Tür", ["Soru Çözümü", "Özel Ders", "Video İzleme"])
            ders = st.selectbox("Ders", list(m.keys()))
            konu = st.selectbox("Konu", m[ders])
            if tur == "Soru Çözümü":
                d = st.number_input("Doğru", 0, key="d_in"); y = st.number_input("Yanlış", 0, key="y_in")
                if st.button("Kaydet"):
                    o["soru"].append({"Tarih": datetime.now().strftime("%d/%m"), "Ders": ders, "Konu": konu, "Toplam": d+y})
                    veri_kaydet(st.session_state.db); st.success("Kaydedildi!")
            else:
                birim = st.number_input("Dakika", 10, key="dak_in")
                if st.button("Çalışmayı İşle"):
                    o["soru"].append({"Tarih": datetime.now().strftime("%d/%m"), "Ders": ders, "Konu": konu, "Toplam": 0, "Tur": tur})
                    veri_kaydet(st.session_state.db); st.success("İşlendi!")
        with tab2:
            st.subheader("Deneme Analizi")
            yay = st.text_input("Yayın"); c1, c2 = st.columns(2)
            if o.get("sinav") == "LGS":
                tn = c1.number_input("Türkçe Net", 0.0); mn = c2.number_input("Mat. Net", 0.0); fn = c1.number_input("Fen Net", 0.0)
                puan = 200 + (mn*5) + (fn*4) + (tn*4)
            else:
                tyt = c1.number_input("TYT Net", 0.0); ayt = c2.number_input("AYT Net", 0.0)
                puan = 100 + (tyt*1.5) + (ayt*3)
            y_konu = st.text_area("Yanlış Konuların")
            if st.button("Denemeyi Kaydet"):
                o["denemeler"].append({"Tarih": datetime.now().strftime("%d/%m"), "Yayin": yay, "Puan": round(puan, 2), "Yanlis_Konular": y_konu})
                veri_kaydet(st.session_state.db); st.success(f"Puan: {round(puan,2)}")
        with tab3:
            df_o = pd.DataFrame(o["soru"])
            if not df_o.empty: st.plotly_chart(px.bar(df_o.groupby("Ders")["Toplam"].sum().reset_index(), x="Ders", y="Toplam"))
            st.markdown(f'<a href="https://wa.me/{HOCA_TEL}?text=Raporum Hazır!" target="_blank" style="background-color:#007bff; color:white; padding:10px; text-decoration:none; border-radius:5px;">📤 HOCAMA GÖNDER</a>', unsafe_allow_html=True)
