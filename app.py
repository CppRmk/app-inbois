import json
import os
import google.generativeai as genai
import pandas as pd
from PIL import Image
import streamlit as st

st.set_page_config(page_title="Imbasan Inbois AI", layout="wide")
st.title("🧾 Pengimbas Inbois Kastam Automatik")

# 1. Ambil API Key secara automatik dari Secrets
api_key = st.secrets.get("GEMINI_API_KEY", "")

# Fallback jika Secrets belum diisi
if not api_key:
    api_key = st.sidebar.text_input(
        "Masukkan Gemini API Key (bermula AIzaSy...):", type="password"
    )

if api_key:
    api_key = api_key.strip()
    genai.configure(api_key=api_key)

    st.subheader("1. Ambil Gambar Inbois")
    uploaded_file = st.file_uploader(
        "Pilih gambar atau snap guna kamera", type=["jpg", "jpeg", "png"]
    )

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Gambar Inbois", use_column_width=True)

        if st.button("🚀 Imbas & Simpan Data Automatik"):
            with st.spinner("AI sedang membaca data..."):
                try:
                    # Model standard rasmi
                    model = genai.GenerativeModel("gemini-1.5-flash")

                    prompt = """
                    Analisis gambar inbois/resit ini. Ekstrak data dan kembalikan HANYA format JSON berikut (tanpa tanda markdown/backticks):
                    {
                      "Tarikh Inbois": "tarikh",
                      "No Inbois": "nombor inbois",
                      "Nama Pembeli": "nama pembeli",
                      "No Pasport": "nombor pasport",
                      "Senarai Barang": "ringkasan barang dan kuantiti",
                      "Jumlah Bersih (RM)": "jumlah grand total",
                      "No Kastam": "nombor kenderaan/pegawai kastam"
                    }
                    """

                    response = model.generate_content([prompt, image])
                    clean_json = (
                        response.text.replace("```json", "")
                        .replace("```", "")
                        .strip()
                    )
                    data = json.loads(clean_json)

                    # Simpan data ke fail CSV
                    df_new = pd.DataFrame([data])

                    if os.path.exists("rekod_inbois.csv"):
                        df_old = pd.read_csv("rekod_inbois.csv")
                        df_final = pd.concat(
                            [df_old, df_new], ignore_index=True
                        )
                    else:
                        df_final = df_new

                    df_final.to_csv("rekod_inbois.csv", index=False)
                    st.success("✅ Data berjaya dibaca dan disimpan!")
                    st.rerun()

                except Exception as e:
                    st.error(f"Ralat Pemprosesan: {e}")
else:
    st.warning(
        "⚠️ API Key belum dikesan. Sila masukkan GEMINI_API_KEY di Streamlit Secrets atau Sidebar."
    )

# Paparkan jadual data
st.divider()
st.subheader("📊 Rekod Data Inbois Tersimpan")

if os.path.exists("rekod_inbois.csv"):
    df_data = pd.read_csv("rekod_inbois.csv")
    st.dataframe(df_data)

    csv_bytes = df_data.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Muat Turun Fail CSV / Excel",
        data=csv_bytes,
        file_name="rekod_inbois_kastam.csv",
        mime="text/csv",
    )
else:
    st.info("Belum ada rekod disimpan. Imbas gambar pertama anda di atas!")
