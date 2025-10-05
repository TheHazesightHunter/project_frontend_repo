# app.py
from flask import Flask, render_template
import requests

app = Flask(__name__)

API_URL = "https://apaw.cspc.edu.ph/apawbalatanapi/APIv1/Weather"

def fetch_weather():
    try:
        r = requests.get(API_URL, timeout=8)
        r.raise_for_status()
        payload = r.json()
        # normalize: some APIs return {"data":[...]}, others return [...]
        if isinstance(payload, dict) and "data" in payload:
            return payload["data"]
        return payload
    except Exception as e:
        # log in real apps; here we just return empty
        return []

@app.route("/")
def home():
    weather = fetch_weather()   # list[dict]
    # You can also pre-pick “latest” here if you want:
    latest = weather[0] if weather else None
    return render_template("index.html", weather=weather, latest=latest)

if __name__ == "__main__":
    app.run(debug=True, port=5001)
