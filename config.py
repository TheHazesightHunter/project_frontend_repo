# config.py
"""Application configuration"""

import os


class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    API_URL = 'https://apaw.cspc.edu.ph/apawbalatanapi/APIv1/Weather'
    API_TIMEOUT = 8
    
    SITES = [
        {'id': 'St1', 'name': 'MDRRMO Office'},
        {'id': 'St2', 'name': 'Luluasan Station'},
        {'id': 'St3', 'name': 'Laganac Station'},
        {'id': 'St4', 'name': 'Mang-it Station'},
        {'id': 'St5', 'name': 'Cabanbanan Station'},
    ]


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
