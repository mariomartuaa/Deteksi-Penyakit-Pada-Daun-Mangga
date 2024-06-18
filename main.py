import streamlit as st
from ultralytics import YOLO
from PIL import Image
import io
import sqlite3
import hashlib

# Inisialisasi database SQLite
conn = sqlite3.connect('database.db')
c = conn.cursor()

# Membuat tabel untuk menyimpan pengguna
c.execute('''CREATE TABLE IF NOT EXISTS users
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT UNIQUE,
              password TEXT)''')
conn.commit()

# Membuat tabel untuk menyimpan gambar
c.execute('''CREATE TABLE IF NOT EXISTS images
             (id INTEGER PRIMARY KEY AUTOINCREMENT, 
              tab TEXT, 
              image BLOB)''')
conn.commit()

buffer = io.BytesIO()
buffer2 = io.BytesIO()

model = YOLO("best.pt")

def prediction(image, conf):
    result = model.predict(image, conf = conf)
    boxes = result[0].boxes
    res_plotted = result[0].plot()[:, :, ::-1]
    return res_plotted

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login_user(username, password):
    c.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, hash_password(password)))
    return c.fetchone()

def create_user(username, password):
    try:
        c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hash_password(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def delete_image(image_id):
    c.execute("DELETE FROM images WHERE id=?", (image_id,))
    conn.commit()
    st.experimental_rerun()

# Halaman login
def login_page():
    st.title('Login')
    username = st.text_input('Username')
    password = st.text_input('Password', type='password')
    if st.button('Login'):
        user = login_user(username, password)
        if user:
            st.session_state['logged_in'] = True
            st.session_state['username'] = username
            st.experimental_rerun()
        else:
            st.error('Username atau password salah')

# Halaman registrasi
def register_page():
    st.title('Register')
    username = st.text_input('Username')
    password = st.text_input('Password', type='password')
    if st.button('Register'):
        if create_user(username, password):
            st.success('Registrasi berhasil, silakan login')
        else:
            st.error('Username sudah ada')

# Halaman utama
def main_page():
    st.title('Deteksi Penyakit Pada Daun Mangga')

    values = st.slider(
        label='Pilih Confidence',
        value=(1.0))
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

        st.subheader("Hasil Deteksi")
        c.execute("SELECT id, image FROM images WHERE tab='camera' ORDER BY id DESC")
        images = c.fetchall()
        for image_id, img in images:
            st.image(img)
            col1, col2 = st.columns([1, 1])
            with col1:
                st.download_button(
                    key=f"download_camera_{image_id}",
                    label="Download",
                    data=img,
                    file_name=f"Deteksi_Penyakit_{image_id}.png",
                    mime="image/png",
                )
            with col2:
                if st.button(f"Delete", key=f"delete_camera_{image_id}"):
                    delete_image(image_id)

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

        st.subheader("Hasil Deteksi")
        c.execute("SELECT id, image FROM images WHERE tab='upload' ORDER BY id DESC")
        images = c.fetchall()
        for image_id, img in images:
            st.image(img)
            col1, col2 = st.columns([1, 1])
            with col1:
                st.download_button(
                    key=f"download_upload_{image_id}",
                    label="Download",
                    data=img,
                    file_name=f"Deteksi_Penyakit_{image_id}.png",
                    mime="image/png",
                )
            with col2:
                if st.button(f"Delete", key=f"delete_upload_{image_id}"):
                    delete_image(image_id)

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if st.session_state['logged_in']:
    main_page()
else:
    option = st.sidebar.selectbox('Menu', ['Login', 'Register'])
    if option == 'Login':
        login_page()
    elif option == 'Register':
        register_page()

conn.close()
