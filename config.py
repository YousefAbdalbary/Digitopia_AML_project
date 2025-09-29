import os
from datetime import timedelta

class Config:
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'aml-detection-secret-key-2024'
    
    # MongoDB Configuration
    MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb://10.234.22.151:27017/aml_detection2024'
    MONGO_DBNAME = 'aml_detection2024'
    
    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-aml-2024'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    # Upload Configuration
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}
    
    # Security Configuration
    BCRYPT_LOG_ROUNDS = 12
    
    # Analytics Configuration
    RISK_THRESHOLD = 0.7
    SUSPICIOUS_AMOUNT_THRESHOLD = 10000  # USD
    
    # Currency Configuration
    SUPPORTED_CURRENCIES = ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD']
    
    # AI Model Configuration
    MODEL_PATH = 'models/aml_model.pkl'
    
class DevelopmentConfig(Config):
    DEBUG = True
    MONGO_URI = 'mongodb://10.234.22.151:27017/aml_detection_dev'

class ProductionConfig(Config):
    DEBUG = False
    MONGO_URI = os.environ.get('MONGO_URI')

class TestingConfig(Config):
    TESTING = True
    MONGO_URI = 'mongodb://10.234.22.151:27017/aml_detection_test'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}