import os
import numpy as np
from flask import Flask, render_template, request, jsonify
import tensorflow as tf
# from google.cloud import storage
from tensorflow.keras.preprocessing import image
from PIL import Image
import io

app = Flask(_name_)

# Ganti dengan nama bucket dan model yang sesuai
bucket_name = 'cofflyze-model'
model_filename = 'my_model.h5'

# Fungsi untuk mengunduh model dari GCS
def download_model_from_gcs(bucket_name, model_filename):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(model_filename)
    model_file = io.BytesIO(blob.download_as_bytes())  # Unduh model sebagai bytes
    model = tf.keras.models.load_model(model_file)  # Memuat model dari bytes
    return model

# Download model dari GCS
model = download_model_from_gcs(bucket_name, model_filename)

# Fungsi untuk memproses gambar dan menyesuaikan dengan input model
def prepare_image(image_path):
    img = Image.open(image_path).convert('RGB')  # Membuka gambar
    img = img.resize((150, 150))  # Ubah ukuran menjadi 150x150 untuk model
    img_array = np.array(img)  # Mengubah gambar menjadi array numpy
    img_array = np.expand_dims(img_array, axis=0)  # Menambahkan dimensi batch
    img_array = img_array / 255.0  # Normalisasi jika diperlukan
    return img_array

# Fungsi untuk prediksi penyakit tanaman kopi
def predict_disease(image_path):
    img_array = prepare_image(image_path)
    prediction = model.predict(img_array)  # Melakukan prediksi
    predicted_class = np.argmax(prediction, axis=1)  # Kelas dengan skor tertinggi
    confidence = np.max(prediction)  # Skor tingkat kepercayaan tertinggi

    # Menentukan nama kelas penyakit
    class_names = ['miner','healthy', 'phoma', 'rust']
    predicted_class_name = class_names[predicted_class[0]]

    # Deskripsi untuk setiap kelas
    class_descriptions = {
        'miner': """Ciri-ciri penyakit miner pada daun kopi:
                    - Garis atau lorong berwarna putih hingga kekuningan pada permukaan daun, yang merupakan jalur makan larva.
                    - Daun menjadi lebih rentan terhadap serangan hama atau penyakit sekunder.
                    - Penurunan area hijau daun yang memengaruhi proses fotosintesis.
                    - Dalam kasus berat, daun bisa mengering dan gugur.""",
                
        'rust': """Ciri-ciri penyakit Rust pada daun kopi:
                    - Bercak berwarna kuning pucat hingga oranye cerah
                    - Bercak dapat berukuran kecil hingga besar, terlihat seperti karat pada permukaan daun
                    - Penyakit ini menyebabkan daun menguning dan kering jika tidak ditangani""",
        'phoma': """Ciri-ciri penyakit Phoma pada daun kopi:
                    - Bintik-bintik coklat atau kehitaman dengan batas yang jelas
                    - Bintik bisa berukuran kecil hingga sedang
                    - Pada beberapa kasus, daun juga menguning di sekitar bintik""",
        'healthy': """Ciri-ciri daun kopi yang sehat:
                      - Warna hijau cerah dan daun memiliki tekstur halus
                      - Tidak ada bercak atau perubahan warna pada permukaan daun
                      - Daun sehat menunjukkan pertumbuhan yang baik dan kuat"""
    }

    disease_description = class_descriptions.get(predicted_class_name, "Deskripsi tidak ditemukan")

    return predicted_class_name, confidence, disease_description

# Halaman utama (form upload gambar)
@app.route('/')
def index():
    return render_template('index.html')

# Menangani upload gambar dan melakukan prediksi
@app.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    
    # Simpan file gambar sementara
    file_path = os.path.join('static', file.filename)
    file.save(file_path)
    
    try:
        # Lakukan prediksi
        predicted_class, confidence, disease_description = predict_disease(file_path)
        
        # Kembalikan hasil prediksi, convert predicted_class to native string
        return jsonify({
            'predicted_class': predicted_class,  # Nama kelas penyakit
            'confidence': float(confidence),  # Tingkat kepercayaan
            'disease_description': disease_description,  # Deskripsi penyakit
            'image_url': file_path  # URL gambar yang diunggah
        })
    except Exception as e:
        # Tangani error saat prediksi
        print(f"Error during prediction: {e}")
        return jsonify({'error': 'Error during prediction'})

if name == 'main':
    app.run(debug=True, host="0.0.0.0", port=8080)