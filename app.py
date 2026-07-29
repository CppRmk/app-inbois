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

    st.sidebar.subheader("🔍 Status Model AI Akaun Anda")
    all_models = []
    try:
        for m in genai.list_models():
            if "generateContent" in m.supported_generation_methods:
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
            st.sidebar.error("⚠️ Tiada model ditemui!")
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
                st.error("Sila pilih model AI di sidebar.")
            else:
                with st.spinner("AI sedang membaca dan memisahkan barang..."):
                    try:
                        model = genai.GenerativeModel(selected_model_name)

                        prompt = """
                        Analisis gambar inbois/resit ini. Ekstrak data dan kembalikan HANYA format JSON berikut (tanpa tanda markdown/backticks):
                        {
                          "Tarikh Inbois": "tarikh",
                          "No Inbois": "nombor inbois",
                          "Nama Pembeli": "nama pembeli",
                          "No Pasport": "nombor pasport",
                          "Jumlah Bersih Inbois (RM)": "jumlah grand total inbois",
                          "No Kastam": "nombor kenderaan/pegawai/cop kastam",
                          "Senarai Barang": [
                             {
                               "Nama Barang": "nama/deskripsi barang",
                               "Kuantiti": "kuantiti",
                               "Harga Seunit (RM)": "harga seunit",
                               "Jumlah (RM)": "jumlah harga barang ini"
                             }
                          ]
                        }
                        """

                        response = model.generate_content([prompt, image])
                        clean_json = (
                            response.text.replace("```json", "")
                            .replace("```", "")
                            .strip()
                        )
                        data = json.loads(clean_json)

                        # Pecahkan setiap item barang menjadi baris tersendiri
                        items = data.get("Senarai Barang", [])
                        rows = []

                        if isinstance(items, list) and len(items) > 0:
                            for item in items:
                                row = {
                                    "Tarikh Inbois": data.get(
                                        "Tarikh Inbois", ""
                                    ),
                                    "No Inbois": str(data.get("No Inbois", "")),
                                    "Nama Pembeli": data.get(
                                        "Nama Pembeli", ""
                                    ),
                                    "No Pasport": data.get("No Pasport", ""),
                                    "Nama Barang": item.get("Nama Barang", ""),
                                    "Kuantiti": item.get("Kuantiti", ""),
                                    "Harga Seunit (RM)": item.get(
                                        "Harga Seunit (RM)", ""
                                    ),
                                    "Jumlah Barang (RM)": item.get(
                                        "Jumlah (RM)", ""
                                    ),
                                    "Jumlah Bersih Inbois (RM)": data.get(
                                        "Jumlah Bersih Inbois (RM)", ""
                                    ),
                                    "No Kastam": data.get("No Kastam", ""),
                                }
                                rows.append(row)
                            df_new = pd.DataFrame(rows)
                        else:
                            df_new = pd.DataFrame([data])

                        if os.path.exists("rekod_inbois.csv"):
                            df_old = pd.read_csv("rekod_inbois.csv")
                            df_final = pd.concat(
                                [df_old, df_new], ignore_index=True
                            )
                        else:
                            df_final = df_new

                        df_final.to_csv("rekod_inbois.csv", index=False)
                        st.success(
                            "✅ Data dan senarai barang berjaya dipisahkan & disimpan!"
                        )
                        st.rerun()

                    except Exception as e:
                        st.error(f"Ralat Pemprosesan: {e}")
else:
    st.warning("⚠️ API Key belum dikesan.")

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
    st.info("Belum ada rekod disimpan.")
