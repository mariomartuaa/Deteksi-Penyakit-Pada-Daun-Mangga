import streamlit as st
from ultralytics import YOLO
from PIL import Image
import io
import sqlite3

conn = sqlite3.connect('database.db')
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS images
             (id INTEGER PRIMARY KEY AUTOINCREMENT, 
              tab TEXT, 
              image BLOB)''')
conn.commit()

buffer = io.BytesIO()
buffer2 = io.BytesIO()

model = YOLO("best.pt")

def prediction(image, conf):
    result = model.predict(image, conf=conf)
    res_plotted = result[0].plot()[:, :, ::-1]
    return res_plotted

def delete_image(image_id):
    c.execute("DELETE FROM images WHERE id=?", (image_id,))
    conn.commit()
    st.experimental_rerun()

def login_page():
    st.title('Login')
    username = st.text_input('Username')
    password = st.text_input('Password', type='password')
    
    if st.button('Login'):
        if username == "admin" and password == "admin":
            st.success('Login berhasil!')
            st.session_state['logged_in'] = True
            st.session_state['page'] = 'Home'
        else:
            st.error('Username atau password salah')

def main_page():
    st.title('Deteksi Penyakit Pada Daun Mangga')
    values = st.slider('Pilih Confidence', value=1.0)
    st.write('Confidence', values)

    tab1, tab2 = st.tabs(['Kamera', 'Upload'])

    with tab1:
        image = st.camera_input('Ambil Foto')
        if image:
            image = Image.open(image)
            pred = prediction(image, values)
            im = Image.fromarray(pred)
            im.save(buffer, format="PNG")
            img_bytes = buffer.getvalue()
            c.execute("INSERT INTO images (tab, image) VALUES (?, ?)", ('camera', img_bytes))
            conn.commit()

    with tab2:
        image2 = st.file_uploader('Upload', type=['jpg', 'jpeg', 'png'])
        if image2:
            image2 = Image.open(image2)
            pred = prediction(image2, values)
            im = Image.fromarray(pred)
            im.save(buffer2, format="PNG")
            img_bytes = buffer2.getvalue()
            c.execute("INSERT INTO images (tab, image) VALUES (?, ?)", ('upload', img_bytes))
            conn.commit()

def view_results_page():
    st.title('Hasil Deteksi')
    images = c.execute("SELECT id, image FROM images ORDER BY id DESC").fetchall()
    for image_id, img in images:
        st.image(img, caption=f'Hasil Deteksi #{image_id}')
        col1, col2 = st.columns([1, 1])
        with col1:
            st.download_button("Download", img, file_name=f"Deteksi_Penyakit_{image_id}.png", mime="image/png")
        with col2:
            if st.button("Delete", key=f"delete_{image_id}"):
                delete_image(image_id)

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'page' not in st.session_state:
    st.session_state['page'] = 'Home'

if st.session_state['logged_in']:
    st.sidebar.title('Navigasi')
    if st.sidebar.button('Home'):
        st.session_state['page'] = 'Home'
    if st.sidebar.button('Hasil Deteksi'):
        st.session_state['page'] = 'Hasil Deteksi'

    if st.session_state['page'] == 'Home':
        main_page()
    elif st.session_state['page'] == 'Hasil Deteksi':
        view_results_page()
else:
    login_page()
    
conn.close()
