# services/metrics_service.py
"""
Metrics Service - Calculates dashboard metrics and alert states
"""

from typing import List, Dict
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class AlertThresholds:
    """
    Alert threshold configuration for LGU Balatan
    Based on PAGASA and local flood risk assessment
    """
    # Water level thresholds (meters)
    water_level_critical: float = 11.0   # >= 11.0m - Immediate evacuation
    water_level_warning: float = 9.0     # >= 9.0m - Prepare to evacuate
    water_level_alert: float = 8.0       # >= 8.0m - High alert
    water_level_advisory: float = 7.0    # >= 7.0m - Stay vigilant
    
    # Rainfall thresholds (mm/hour) - PAGASA Standard
    rainfall_intense: float = 30.0       # Red warning - Severe flooding
    rainfall_heavy: float = 15.0         # Orange warning - Flooding expected
    rainfall_moderate: float = 7.5       # Yellow warning - Possible flooding
    rainfall_light: float = 0.1          # No warning - Minimal impact
    
    # Wind speed thresholds (m/s)
    wind_speed_critical: float = 25.0    # Dangerous winds (90 km/h)
    wind_speed_warning: float = 17.0     # Strong winds (61 km/h)
    wind_speed_alert: float = 13.0       # Moderate winds (47 km/h)
    wind_speed_advisory: float = 10.0    # Light-moderate winds (36 km/h)


@dataclass
class DashboardMetrics:
    """Overall dashboard metrics"""
    # Flood alert counts
    critical_count: int
    warning_count: int
    alert_count: int
    advisory_count: int
    
    # Highest priority alert level
    highest_alert_level: str          # 'critical', 'warning', 'alert', 'advisory', 'normal'
    highest_alert_count: int          # Number of stations at highest level
    
    # Rainfall forecast
    rainfall_forecast: dict           # Classification from classify_rainfall()
    
    # Station status
    attention_stations: List[str]
    online_sensors: int
    total_sensors: int


class MetricsService:
    """Service for calculating dashboard metrics"""
    
    def __init__(self, thresholds: AlertThresholds = None, sites: List[Dict] = None):
        """
        Initialize the metrics service
        
        Args:
            thresholds: Alert threshold configuration
            sites: List of monitoring stations
        """
        self.thresholds = thresholds or AlertThresholds()
        self.sites = sites or []
    
    def calculate_dashboard_metrics(self, stations_data: Dict[str, Dict]) -> DashboardMetrics:
        """
        Calculate all dashboard metrics from station data
        """
        if not stations_data:
            return DashboardMetrics(
                critical_count=0,
                warning_count=0,
                alert_count=0,
                advisory_count=0,
                highest_alert_level='normal',
                highest_alert_count=0,
                rainfall_forecast=self.classify_rainfall(0),
                attention_stations=[],
                online_sensors=0,
                total_sensors=len(self.sites)
            )
        
        critical_count = 0
        warning_count = 0
        alert_count = 0
        advisory_count = 0
        attention_stations = []
        
        # ✅ Calculate AVERAGE rainfall across all online stations
        total_rainfall = 0.0
        station_count = 0
        
        # Analyze each station
        for station_id, reading in stations_data.items():
            water_level = self._safe_float(reading.get('WaterLevel', 0))
            rainfall = self._safe_float(reading.get('HourlyRain', 0))
            wind_speed = self._safe_float(reading.get('WindSpeed', 0))
            
            # ✅ Sum up rainfall for average calculation
            total_rainfall += rainfall
            station_count += 1
            
            # Determine alert level
            alert_level = self._determine_alert_level(water_level, rainfall, wind_speed)
            
            if alert_level == 'critical':
                critical_count += 1
                attention_stations.append(self._get_station_name(station_id))
            elif alert_level == 'warning':
                warning_count += 1
                attention_stations.append(self._get_station_name(station_id))
            elif alert_level == 'alert':
                alert_count += 1
                attention_stations.append(self._get_station_name(station_id))
            elif alert_level == 'advisory':
                advisory_count += 1
                attention_stations.append(self._get_station_name(station_id))
        
        # ✅ Calculate average rainfall
        average_rainfall = total_rainfall / station_count if station_count > 0 else 0.0
        
        # Determine highest priority alert level
        if critical_count > 0:
            highest_alert_level = 'critical'
            highest_alert_count = critical_count
        elif warning_count > 0:
            highest_alert_level = 'warning'
            highest_alert_count = warning_count
        elif alert_count > 0:
            highest_alert_level = 'alert'
            highest_alert_count = alert_count
        elif advisory_count > 0:
            highest_alert_level = 'advisory'
            highest_alert_count = advisory_count
        else:
            highest_alert_level = 'normal'
            highest_alert_count = 0
        
        # Classify average rainfall across municipality
        rainfall_forecast = self.classify_rainfall(average_rainfall)
        
        return DashboardMetrics(
            critical_count=critical_count,
            warning_count=warning_count,
            alert_count=alert_count,
            advisory_count=advisory_count,
            highest_alert_level=highest_alert_level,
            highest_alert_count=highest_alert_count,
            rainfall_forecast=rainfall_forecast,
            attention_stations=attention_stations,
            online_sensors=len(stations_data),
            total_sensors=len(self.sites)
        )   
    
    def classify_rainfall(self, rainfall_mm_per_hour: float) -> dict:
        """
        Classify rainfall intensity based on PAGASA standards
        
        Args:
            rainfall_mm_per_hour: Rainfall in mm/hour
            
        Returns:
            Dict with classification, color, icon, and description
        """
        if rainfall_mm_per_hour >= self.thresholds.rainfall_intense:
            return {
                'level': 'Intense',
                'color': '#DC2626',
                'icon': 'fa-cloud-showers-heavy',
                'warning': 'RED'
            }
        elif rainfall_mm_per_hour >= self.thresholds.rainfall_heavy:
            return {
                'level': 'Heavy',
                'color': '#F59E0B',
                'icon': 'fa-cloud-rain',
                'warning': 'ORANGE'
            }
        elif rainfall_mm_per_hour >= self.thresholds.rainfall_moderate:
            return {
                'level': 'Moderate',
                'color': '#409AC7',
                'icon': 'fa-cloud-drizzle',
                'warning': 'YELLOW'
            }
        elif rainfall_mm_per_hour >= self.thresholds.rainfall_light:
            return {
                'level': 'Light',
                'color': '#409AC7',
                'icon': 'fa-cloud-drizzle',
                'warning': 'NONE'
            }
        else:
            return {
                'level': 'No Rain',
                'color': '#409AC7',
                'icon': 'fa-sun',
                'warning': 'NONE'
            }
    
    def _determine_alert_level(self, water_level: float, rainfall: float, wind_speed: float) -> str:
        """
        Determine overall alert level for station based on ALL parameters
        
        Args:
            water_level: Water level in meters
            rainfall: Hourly rainfall in mm
            wind_speed: Wind speed in m/s
            
        Returns:
            'critical', 'warning', 'alert', 'advisory', or 'normal'
        """
        # Check CRITICAL (highest priority)
        if (water_level >= self.thresholds.water_level_critical or
            rainfall >= self.thresholds.rainfall_intense or
            wind_speed >= self.thresholds.wind_speed_critical):
            return 'critical'
        
        # Check WARNING
        if (water_level >= self.thresholds.water_level_warning or
            rainfall >= self.thresholds.rainfall_heavy or
            wind_speed >= self.thresholds.wind_speed_warning):
            return 'warning'
        
        # Check ALERT
        if (water_level >= self.thresholds.water_level_alert or
            rainfall >= self.thresholds.rainfall_moderate or
            wind_speed >= self.thresholds.wind_speed_alert):
            return 'alert'
        
        # Check ADVISORY
        if (water_level >= self.thresholds.water_level_advisory or
            rainfall >= self.thresholds.rainfall_light or
            wind_speed >= self.thresholds.wind_speed_advisory):
            return 'advisory'
        
        # All parameters below advisory threshold = NORMAL
        return 'normal'
    
    def _get_station_name(self, station_id: str) -> str:
        """Get human-readable station name"""
        site = next((s for s in self.sites if s['id'] == station_id), None)
        return site['name'] if site else station_id
    
    @staticmethod
    def _safe_float(value, default: float = 0.0) -> float:
        """Safely convert value to float"""
        try:
            return float(value)
        except (ValueError, TypeError):
            return default