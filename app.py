# app.py
"""
Flask application - Routes and request handling only
NO business logic here!
"""

from flask import Flask, render_template
from config import config
from services.weather_service import WeatherService
from services.metrics_service import MetricsService, AlertThresholds
from utils.formatters import format_datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app(config_name='development'):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize services
    weather_service = WeatherService(
        api_url=app.config['API_URL'],
        timeout=app.config['API_TIMEOUT']
    )
    
    metrics_service = MetricsService(
        thresholds=AlertThresholds(),
        sites=app.config['SITES']
    )
    
    # Context processor: inject global template variables
    @app.context_processor
    def inject_globals():
        """Make data available to all templates"""
        return {
            'sites': app.config['SITES'],
            'format_datetime': format_datetime
        }
    
    # ============================================
    # ROUTES - Thin controllers, delegate to services
    # ============================================
    
    @app.route('/')
    def home():
        """
        Dashboard home page
        Shows metrics and current weather conditions
        """
        # Fetch data using service
        weather_data = weather_service.fetch_weather_data()
        
        # Process data using services
        latest = weather_service.get_latest_reading(weather_data)
        stations = weather_service.get_latest_per_station(weather_data)
        metrics = metrics_service.calculate_dashboard_metrics(stations)
        
        # Render template with processed data
        return render_template(
            'home.html',
            weather=weather_data,
            latest=latest,
            metrics=metrics
        )
    
    @app.route('/sites/<site_id>')
    def site_detail(site_id):
        """
        Individual station detail page
        
        Args:
            site_id: Station identifier from URL
        """
        # Validate site exists
        site = next((s for s in app.config['SITES'] if s['id'] == site_id), None)
        if not site:
            return "Site not found", 404
        
        # Fetch and filter data using service
        weather_data = weather_service.fetch_weather_data()
        site_weather = weather_service.filter_by_station(weather_data, site_id)
        latest = weather_service.get_latest_reading(site_weather)
        
        return render_template(
            'sites/site_detail.html',
            site=site,
            latest=latest,
            weather=site_weather[:24],
            current_site_id=site_id
        )
    
    @app.route('/about')
    def about():
        """About page"""
        return render_template('about.html')
    
    @app.route('/contact')
    def contact():
        """Contact page"""
        return render_template('contact.html')
    
    @app.route('/test-dashboard')
    def test_dashboard():
    
        """Test dashboard with fake data"""
        
        fake_stations = {
            'St1': {
                'StationID': 'St1',
                'WaterLevel': 11.5,     # Critical
                'HourlyRain': 35.0,     # Intense rain!
                'WindSpeed': 15,
            },
            'St2': {
                'StationID': 'St2',
                'WaterLevel': 9.8,      # Warning
                'HourlyRain': 20.0,     # Heavy rain
                'WindSpeed': 12,
            },
            'St3': {
                'StationID': 'St3',
                'WaterLevel': 8.3,      # Alert
                'HourlyRain': 10.0,     # Moderate rain
                'WindSpeed': 8,
            },
            'St4': {
                'StationID': 'St4',
                'WaterLevel': 7.2,      # Advisory
                'HourlyRain': 5.0,      # Light rain
                'WindSpeed': 6,
            },
            'St5': {
                'StationID': 'St5',
                'WaterLevel': 6.1,      # Normal
                'HourlyRain': 1.0,      # Light rain
                'WindSpeed': 4,
            }
        }
    
        metrics = metrics_service.calculate_dashboard_metrics(fake_stations)
        
        logger.info("="*60)
        logger.info("TEST DASHBOARD METRICS:")
        logger.info(f"  Highest Alert: {metrics.highest_alert_level} ({metrics.highest_alert_count})")
        logger.info(f"  Stations Needing Attention: {len(metrics.attention_stations)}/5")
        logger.info(f"  Online: {metrics.online_sensors}/5")
        logger.info("="*60)
        
        latest = fake_stations['St1']
        weather_list = list(fake_stations.values())
        
        return render_template(
            'home.html',
            weather=weather_list,
            latest=latest,
            metrics=metrics
        )
    
    # ============================================
    # ERROR HANDLERS
    # ============================================
    
    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def server_error(error):
        logger.error(f"Server error: {error}")
        return render_template('errors/500.html'), 500
    
    return app


# Create app instance
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
