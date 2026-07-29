import json
import os
import google.generativeai as genai
import pandas as pd
from PIL import Image
import streamlit as st

st.set_page_config(page_title="Imbasan Inbois AI", layout="wide")
st.title("🧾 Pengimbas Inbois Kastam Automatik")

# 1. Ambil API Key dari Streamlit Secrets atau Sidebar
api_key = st.secrets.get("GEMINI_API_KEY", "")

if not api_key:
    api_key = st.sidebar.text_input(
        "Masukkan Gemini API Key (bermula AIzaSy...):", type="password"
    )

if api_key:
    clean_key = (
        str(api_key).strip().replace('"', "").replace("'", "").replace(" ", "")
    )
    genai.configure(api_key=clean_key)

    # Diagnostik Model AI pada akaun pengguna
    st.sidebar.subheader("🔍 Status Model AI Akaun Anda")
    all_models = []
    try:
        # Senaraikan semua model yang disokong oleh API Key ini
        for m in genai.list_models():
            if "generateContent" in m.supported_generation_methods:
                # Ambil nama model tanpa awalan 'models/'
                name_clean = m.name.replace("models/", "")
                all_models.append(name_clean)

        if all_models:
            selected_model_name = st.sidebar.selectbox(
                "Model AI yang Sah untuk Akaun Anda:", all_models
            )
            st.sidebar.success(
                f"✅ {len(all_models)} model ditemui pada akaun anda!"
            )
        else:
            selected_model_name = None
            st.sidebar.error(
                "⚠️ Tiada model ditemui! Akaun/API Key anda belum mengaktifkan Generative Language API di Google Cloud."
            )
    except Exception as e:
        selected_model_name = None
        st.sidebar.error(f"⚠️ Ralat Semakan API Key: {e}")

    st.subheader("1. Ambil Gambar Inbois")
    uploaded_file = st.file_uploader(
        "Pilih gambar atau snap guna kamera", type=["jpg", "jpeg", "png"]
    )

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Gambar Inbois", use_column_width=True)

        if st.button("🚀 Imbas & Simpan Data Automatik"):
            if not selected_model_name:
                st.error(
                    "Sila pastikan API Key sah dan model AI terpilih di sidebar."
                )
            else:
                with st.spinner(
                    f"AI ({selected_model_name}) sedang membaca data..."
                ):
                    try:
                        model = genai.GenerativeModel(selected_model_name)

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
