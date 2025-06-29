from flask import Flask, request, jsonify
import joblib
import numpy as np
import os
from flask_cors import CORS
from model.lvq_module import LVQClassifier
from model.weather import ambil_data_dasarian
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Load model dan scaler
model = joblib.load("lvq_modelGresik1.joblib")
scaler = joblib.load("scalerGresik1.joblib")

@app.route("/")
def index():
    return "Backend LVQ API is running!"

# =====================
# PREDIKSI MANUAL (POST)
# =====================
@app.route("/predict", methods=["POST"])
def predict():
    data = request.json
    input_fitur = data.get("features", [])

    if not input_fitur or len(input_fitur) != 5:
        return jsonify({"error": "Input fitur harus terdiri dari 5 nilai"}), 400

    print("Input diterima:", input_fitur)

    # Normalisasi input
    input_scaled = scaler.transform([input_fitur])

    # Prediksi
    hasil = model.predict(input_scaled)
    print("Hasil prediksi:", hasil[0])

    return jsonify({"prediction": int(hasil[0])})

# =============================
# PREDIKSI OTOMATIS OPENWEATHER
# =============================
@app.route("/predict-live", methods=["GET"])
def predict_from_openweather():
    try:
        # Ambil parameter lat dan lon dari query string
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        
        if lat is None or lon is None:
            return jsonify({"error": "Parameter lat dan lon diperlukan"}), 400
        
        # Ambil data weather berdasarkan koordinat yang diberikan
        fitur = ambil_data_dasarian(lat, lon)
        print(f"Fitur dasarian dari OpenWeather untuk lat={lat}, lon={lon}:", fitur)

        input_scaled = scaler.transform([fitur])
        hasil = model.predict(input_scaled)

        mangsa_tanggal = mapping_pranata_mangsa_by_date()

        return jsonify({
            "features": fitur,
            "prediction_ai": int(hasil[0]),
            "prediction_by_date": mangsa_tanggal,
            "used_by_frontend": mangsa_tanggal,
            "location": {"lat": lat, "lon": lon}
        })
    except Exception as e:
        print(f"Error in predict_from_openweather: {str(e)}")
        return jsonify({"error": str(e)}), 500

# =============================
# ENDPOINT UNTUK MENDAPATKAN DATA CUACA DETAIL
# =============================
@app.route("/weather-data", methods=["GET"])
def get_weather_data():
    try:
        # Ambil parameter lat dan lon dari query string
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        
        if lat is None or lon is None:
            return jsonify({"error": "Parameter lat dan lon diperlukan"}), 400
        
        # Ambil data weather detail berdasarkan koordinat
        from weather import ambil_data_cuaca_detail
        weather_data = ambil_data_cuaca_detail(lat, lon)
        
        return jsonify(weather_data)
    except Exception as e:
        print(f"Error in get_weather_data: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ===============================
# KONVERSI TANGGAL KE MANGSA JAWA
# ===============================
def mapping_pranata_mangsa_by_date():
    today = datetime.today()

    mangsa_list = [
        ((6, 22), (8, 1), 1),     # Mangsa Kasa
        ((8, 2), (9, 24), 2),     # Mangsa Karo
        ((9, 25), (10, 12), 3),   # Mangsa Katelu
        ((10, 13), (11, 2), 4),   # Mangsa Kapat
        ((11, 3), (11, 25), 5),   # Mangsa Kalima
        ((11, 26), (12, 18), 6),  # Mangsa Kanem
        ((12, 19), (1, 10), 7),   # Mangsa Kapitu
        ((1, 11), (2, 2), 8),     # Mangsa Kawolu
        ((2, 3), (2, 25), 9),     # Mangsa Kasanga
        ((2, 26), (3, 20), 10),   # Mangsa Sadasa
        ((3, 21), (4, 13), 11),   # Mangsa Desta
        ((4, 14), (6, 21), 12),   # Mangsa Sadha
    ]

    for (start_m, start_d), (end_m, end_d), mangsa_ke in mangsa_list:
        start = datetime(today.year, start_m, start_d)
        end = datetime(today.year + (1 if end_m < start_m else 0), end_m, end_d)
        if start <= today <= end:
            return mangsa_ke
    return None

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)