# services/weather_service.py
"""
Weather Service Layer
Handles all weather data fetching and processing
"""

import requests
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class WeatherService:
    """Service for fetching and processing weather data"""
    
    def __init__(self, api_url: str, timeout: int = 8):
        self.api_url = api_url
        self.timeout = timeout
    
    def fetch_weather_data(self) -> List[Dict]:
        """
        Fetch weather data from external API
        
        Returns:
            List of weather reading dictionaries
            Empty list on error
        """
        try:
            response = requests.get(self.api_url, timeout=self.timeout)
            response.raise_for_status()
            
            payload = response.json()
            
            # Normalize API response format
            if isinstance(payload, dict) and "data" in payload:
                return payload["data"]
            return payload if isinstance(payload, list) else []
            
        except requests.Timeout:
            logger.error(f"API timeout after {self.timeout}s")
            return []
        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            return []
        except ValueError as e:
            logger.error(f"Invalid JSON response: {e}")
            return []
    
    def get_latest_reading(self, weather_data: List[Dict]) -> Optional[Dict]:
        """
        Get most recent weather reading
        
        Args:
            weather_data: List of weather readings
            
        Returns:
            Latest reading dict or None
        """
        return weather_data[0] if weather_data else None
    
    def get_latest_per_station(self, weather_data: List[Dict]) -> Dict[str, Dict]:
        """
        Get most recent reading for each unique station
        
        Args:
            weather_data: List of all weather readings
            
        Returns:
            Dict mapping StationID to latest reading
        """
        stations = {}
        for reading in weather_data:
            station_id = reading.get('StationID')
            if station_id and station_id not in stations:
                stations[station_id] = reading
        return stations
    
    def filter_by_station(self, weather_data: List[Dict], station_id: str) -> List[Dict]:
        """
        Filter readings for specific station
        
        Args:
            weather_data: List of all readings
            station_id: Station identifier to filter by
            
        Returns:
            List of readings for that station
        """
        return [r for r in weather_data if r.get('StationID') == station_id]