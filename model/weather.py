from flask import Flask, request, jsonify
import requests
import numpy as np
from datetime import datetime

app = Flask(__name__)
API_KEY = "36348dfbd98b2079294eda793549ee2a"

def ambil_data_dasarian(lat=-7.1568, lon=112.6511):
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    print(f"🔄 Request DASARIAN forecast: {url}")
    response = requests.get(url)

    if response.status_code != 200:
        print("❌ Gagal ambil dasarian:", response.text)
        raise Exception(f"Error fetching dasarian forecast data: {response.status_code}")

    data = response.json()
    list_data = data.get("list", [])
    if not list_data:
        raise Exception("Forecast list kosong")

    suhu, hujan, kelembapan, angin_kcptn, angin_arah = [], [], [], [], []

    for item in list_data:
        suhu.append(item["main"]["temp"])
        kelembapan.append(item["main"]["humidity"])
        angin_kcptn.append(item["wind"]["speed"])
        angin_arah.append(item["wind"]["deg"])
        hujan.append(item.get("rain", {}).get("3h", 0.0))

    return [
        np.mean(suhu),
        np.sum(hujan),
        np.mean(kelembapan),
        np.mean(angin_kcptn),
        np.mean(angin_arah)
    ]

def calculate_rainfall_probabilities(forecast_list):
    morning_probs, afternoon_probs, night_probs = [], [], []
    for item in forecast_list[:8]:
        dt = datetime.fromtimestamp(item["dt"])
        hour = dt.hour
        pop = item.get("pop", 0) * 100
        if 6 <= hour < 12:
            morning_probs.append(pop)
        elif 12 <= hour < 18:
            afternoon_probs.append(pop)
        else:
            night_probs.append(pop)
    return {
        "morning": round(np.mean(morning_probs) if morning_probs else 0, 0),
        "afternoon": round(np.mean(afternoon_probs) if afternoon_probs else 0, 0),
        "night": round(np.mean(night_probs) if night_probs else 0, 0)
    }

def get_precipitation_from_forecast(forecast_list):
    total_rain = 0
    for item in forecast_list[:8]:
        total_rain += item.get("rain", {}).get("3h", 0.0)
    return total_rain

def ambil_data_cuaca_detail(lat, lon):
    print(f"📍 Ambil data cuaca untuk koordinat: lat={lat}, lon={lon}")

    current_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"

    current_response = requests.get(current_url)
    forecast_response = requests.get(forecast_url)

    if current_response.status_code != 200:
        print("❌ Gagal current weather:", current_response.text)
        raise Exception(f"Error current weather: {current_response.status_code}")

    if forecast_response.status_code != 200:
        print("❌ Gagal forecast weather:", forecast_response.text)
        raise Exception(f"Error forecast weather: {forecast_response.status_code}")

    current_data = current_response.json()
    forecast_data = forecast_response.json()

    main = current_data["main"]
    weather = current_data["weather"][0]
    wind = current_data["wind"]

    condition_mapping = {
        "Clear": "sunny", "Clouds": "cloudy", "Rain": "rainy",
        "Drizzle": "rainy", "Thunderstorm": "stormy", "Snow": "cloudy",
        "Mist": "cloudy", "Fog": "cloudy", "Haze": "cloudy"
    }
    condition = condition_mapping.get(weather["main"], "cloudy")
    rainfall_probs = calculate_rainfall_probabilities(forecast_data.get("list", []))
    dasarian_features = ambil_data_dasarian(lat, lon)

    alerts = []
    if main["temp"] > 35:
        alerts.append("Suhu sangat tinggi, hindari aktivitas luar ruangan")
    if wind.get("speed", 0) > 10:
        alerts.append("Angin kencang, waspada saat berkendara")
    if weather["main"] in ["Thunderstorm", "Rain"] and any(prob > 70 for prob in rainfall_probs.values()):
        alerts.append("Potensi hujan tinggi, siapkan payung")

    return {
        "temperature": round(main["temp"], 1),
        "feelsLike": round(main["feels_like"], 1),
        "humidity": main["humidity"],
        "windSpeed": round(wind.get("speed", 0) * 3.6, 1),
        "windDirection": wind.get("deg", 0),
        "pressure": main["pressure"],
        "condition": condition,
        "description": weather["description"].title(),
        "precipitation": round(get_precipitation_from_forecast(forecast_data["list"]), 1),
        "rainfall": rainfall_probs,
        "alerts": alerts,
        "location": {
            "name": current_data.get("name", "Unknown"),
            "country": current_data["sys"]["country"],
            "lat": lat,
            "lon": lon
        },
        "dasarian_features": {
            "avg_temperature": round(dasarian_features[0], 1),
            "total_rainfall": round(dasarian_features[1], 1),
            "avg_humidity": round(dasarian_features[2], 1),
            "avg_wind_speed": round(dasarian_features[3], 1),
            "avg_wind_direction": round(dasarian_features[4], 1)
        },
        "timestamp": datetime.now().isoformat()
    }

@app.route("/weather-data")
def get_weather_data():
    try:
        lat = float(request.args.get("lat", "-7.1568"))
        lon = float(request.args.get("lon", "112.6511"))
        print(f"🌐 Request masuk: /weather-data?lat={lat}&lon={lon}")
        data = ambil_data_cuaca_detail(lat, lon)
        return jsonify(data)
    except Exception as e:
        print("🔥 ERROR:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
