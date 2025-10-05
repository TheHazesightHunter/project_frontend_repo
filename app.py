# app.py
from flask import Flask, render_template
import requests

app = Flask(__name__)

API_URL = "https://apaw.cspc.edu.ph/apawbalatanapi/APIv1/Weather"

# Site information (maps StationID to actual locations)
SITES = [
    {'id': 'St1', 'name': 'MDRRMO Office'},
    {'id': 'St2', 'name': 'Luluasan Station'},
    {'id': 'St3', 'name': 'Laganac Station'},
    {'id': 'St4', 'name': 'Mang-it Station'},
    {'id': 'St5', 'name': 'Cabanbanan Station'},
]


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


@app.context_processor
def inject_data():
    """Make sites available to all templates"""
    return {
        'sites': SITES
    }


@app.route('/')
def home():
    weather = fetch_weather()   # list[dict]
    # You can also pre-pick “latest” here if you want:
    latest = weather[0] if weather else None
    return render_template("home.html", weather=weather, latest=latest)


@app.route('/sites/<site_id>')
def site_detail(site_id):
    """Detailed view for a specific weather station"""
    # Find the site info
    site = next((s for s in SITES if s['id'] == site_id), None)
    if not site:
        return "Site not found", 404

    # Get all weather data
    weather = fetch_weather()

    # Filter readings for this specific station
    site_weather = [r for r in weather if r.get('StationID') == site_id]

    # Get latest reading for this station
    latest = site_weather[0] if site_weather else None

    return render_template('sites/site_detail.html',
                           site=site,
                           latest=latest,
                           weather=site_weather[:24],  # Last 24 readings
                           current_site_id=site_id)  # for active nav
@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')


@app.route('/contact')
def contact():
    """Contact page"""
    return render_template('contact.html')


if __name__ == '__main__':
    app.run(debug=True, port=5000)