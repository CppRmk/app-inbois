import json
import os
import google.generativeai as genai
import pandas as pd
from PIL import Image
import streamlit as st

st.set_page_config(page_title="Imbasan Inbois AI", layout="wide")
st.title("🧾 Pengimbas Inbois Kastam Automatik")

# Input API Key di sidebar
st.sidebar.header("Tetapan AI")
api_key = st.sidebar.text_input(
    "Masukkan Gemini API Key anda:", type="password"
)

if api_key:
    genai.configure(api_key=api_key)

    # Ambil gambar / upload
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
                    # Cari model AI yang tersedia secara automatik
                    model_name = "gemini-1.5-flash-latest"
                    try:
                        for m in genai.list_models():
                            if (
                                "generateContent"
                                in m.supported_generation_methods
                            ):
                                if "flash" in m.name:
                                    model_name = m.name
                                    break
                    except:
                        pass

                    model = genai.GenerativeModel(model_name)
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

                    # Simpan data ke fail CSV local
                    df_new = pd.DataFrame([data])

                    if os.path.exists("rekod_inbois.csv"):
                        df_old = pd.read_csv("rekod_inbois.csv")
                        df_final = pd.concat([df_old, df_new], ignore_index=True)
                    else:
                        df_final = df_new

                    df_final.to_csv("rekod_inbois.csv", index=False)
                    st.success("✅ Data berjaya dibaca dan disimpan!")
                    st.rerun()

                except Exception as e:
                    st.error(f"Ralat: {e}")

# Paparkan jadual data
st.divider()
st.subheader("📊 Rekod Data Inbois Tersimpan")

if os.path.exists("rekod_inbois.csv"):
    df_data = pd.read_csv("rekod_inbois.csv")
    st.dataframe(df_data)

    # Butang Download Excel/CSV
    csv_bytes = df_data.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Muat Turun Fail CSV / Excel",
        data=csv_bytes,
        file_name="rekod_inbois_kastam.csv",
        mime="text/csv",
    )
else:
    st.info("Belum ada rekod disimpan. Imbas gambar pertama anda di atas!")
