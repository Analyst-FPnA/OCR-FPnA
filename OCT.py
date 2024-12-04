import streamlit as st
from PIL import Image
import pytesseract
import zipfile
import pandas as pd
import cv2
import numpy as np
import io
import os
import re
from difflib import get_close_matches

# Set path Tesseract untuk Windows (opsional)
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def process_image(image):
    """Preprocess image for better OCR results."""
    # Convert to OpenCV format
    img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    
    # Convert to grayscale
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    
    # Apply thresholding
    _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    
    return binary

def extract_text_from_images(zip_file):
    """Extract text from images inside a ZIP file."""
    text_data = []
    
    with zipfile.ZipFile(zip_file, 'r') as zf:
        # List all files in the ZIP
        file_list = zf.namelist()
        
        for file_name in file_list:
            if file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
                # Read image from ZIP
                with zf.open(file_name) as image_file:
                    image = Image.open(image_file)
                    
                    # Preprocess image
                    processed_image = process_image(image)
                    
                    # Extract text using Tesseract
                    text = pytesseract.image_to_string(processed_image, lang='eng')
                    
                    # Append result to list
                    text_data.append({'File Name': file_name, 'Extracted Text': text})
    
    return text_data

# Fungsi untuk mencocokkan menu berdasarkan kemiripan
def match_menu(menu, original_menus):
    matches = get_close_matches(menu, original_menus, n=1, cutoff=0.75)  # Cutoff menentukan tingkat kemiripan minimal
    return matches[0] if matches else menu  # Jika tidak ada kecocokan, kembalikan menu asli

# Fungsi untuk memisahkan Qty dan Harga
def split_qty_harga(qty_harga):
    # Menangkap Qty (angka sebelum 'x' atau '@')
    qty_match = re.match(r'(\d+)', qty_harga)
    qty = qty_match.group(1) if qty_match else ''
    
    # Menangkap Harga (angka setelah '@')
    harga_match = re.search(r'@ ([\d,]+)', qty_harga)
    harga = harga_match.group(1) if harga_match else ''
    
    return qty, harga

# Streamlit app
st.title("OCR Engine-FPnA")
st.write("Upload a ZIP file containing images")

uploaded_zip = st.file_uploader("Upload ZIP File", type="zip")

if uploaded_zip:
    st.info("Processing the uploaded ZIP file...")
    
    # Extract text from images
    extracted_data = extract_text_from_images(uploaded_zip)
    
    if extracted_data:
        # Convert extracted data to DataFrame
        df = pd.DataFrame(extracted_data)
        
        # Display the extracted text
        #st.write("Extracted Text:")
        #st.dataframe(df)
        
        # Read menu database
        database_file = "assets/databasemenu.xlsx"  # Ganti dengan path database menu Anda
        menu_database = pd.read_excel(database_file)
        
        # Pastikan database memiliki kolom 'Original Menu'
        if "Original Menu" in menu_database.columns:
            original_menus = menu_database["Original Menu"].tolist()

            # Proses data hasil ekstraksi
            results = []
            for _, row in df.iterrows():
                file_name = row["File Name"]
                raw_text = row["Extracted Text"]

                if pd.notna(raw_text):  # Abaikan baris kosong
                    lines = raw_text.strip().splitlines()
                    menu = ""

                    # Proses teks baris per baris
                    for line in lines:
                        if "@" in line:  # Cari baris dengan '@'
                            qty = line.strip()
                            results.append({"File Name": file_name, "Menu": menu, "Qty": qty})
                        else:
                            menu = line.strip()  # Update nama menu

            # Buat DataFrame dari hasil
            df_processed = pd.DataFrame(results, columns=["File Name", "Menu", "Qty"])

            # Terapkan pencocokan menu
            df_processed["Corrected Menu"] = df_processed["Menu"].apply(lambda x: match_menu(x, original_menus))
            df_processed = df_processed.drop(columns="Menu")
            df_processed = df_processed.rename(columns={'Corrected Menu': 'Menu'})
            df_processed = df_processed.loc[:, ['File Name', 'Menu', 'Qty']]

            # Menerapkan pemisahan Qty dan Harga
            df_processed[['Qty', 'Harga']] = df_processed['Qty'].apply(lambda x: pd.Series(split_qty_harga(x)))
            df_processed['Harga'] = df_processed['Harga'].str.replace(',', '')

            process_show = pd.DataFrame(df_processed)
            st.dataframe(process_show)
            
            # Convert DataFrame to Excel and download
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_processed.to_excel(writer, index=False, sheet_name='Processed_Data')
            st.download_button(
                label="Download Extracted Data",
                data=output.getvalue(),
                file_name="Processed_Data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("Kolom 'Original Menu' tidak ditemukan di database menu.")
    else:
        st.warning("No valid images found in the ZIP file.")