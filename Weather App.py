import requests
import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# Firebase setup
cred = credentials.Certificate("weather-app-fc258-firebase-adminsdk-fbsvc-4a4f219d7c.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

API_KEY = "57f174ec3bcd27a812f995205591aa20"  # Replace with your OpenWeatherMap API key


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/weather', methods=['GET'])
def get_weather():
    location = request.args.get('location')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if not location or not start_date or not end_date:
        return jsonify({"error": "Location and date range are required."}), 400

    try:
        query = f"q={location}" if not location.isdigit() else f"zip={location},IN"
        url = f"https://api.openweathermap.org/data/2.5/forecast?{query}&units=metric&appid={API_KEY}"
        response = requests.get(url)
        data = response.json()

        if response.status_code != 200:
            return jsonify({"error": "Invalid location or API error."}), 404

        forecast_list = []
        for item in data['list']:
            date = item['dt_txt'].split(" ")[0]
            if start_date <= date <= end_date:
                forecast_list.append({
                    "date": date,
                    "temperature": f"{item['main']['temp']}°C",
                    "description": item['weather'][0]['description'].capitalize(),
                    "icon": f"http://openweathermap.org/img/wn/{item['weather'][0]['icon']}@2x.png"
                })

        weather_record = {
            "location": data['city']['name'],
            "country": data['city']['country'],
            "start_date": start_date,
            "end_date": end_date,
            "forecast": forecast_list
        }

        db.collection("weather_records").add(weather_record)
        return jsonify(weather_record)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/weather_records', methods=['GET'])
def get_weather_records():
    records = db.collection("weather_records").stream()
    return jsonify([{**doc.to_dict(), "id": doc.id} for doc in records])


@app.route('/update_weather/<record_id>', methods=['PUT'])
def update_weather(record_id):
    updates = request.json
    db.collection("weather_records").document(record_id).update(updates)
    return jsonify({"success": True, "message": "Record updated successfully."})


@app.route('/delete_weather/<record_id>', methods=['DELETE'])
def delete_weather(record_id):
    db.collection("weather_records").document(record_id).delete()
    return jsonify({"success": True, "message": "Record deleted successfully."})


if __name__ == '__main__':
    app.run(debug=True)
