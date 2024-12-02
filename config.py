from dotenv import load_dotenv
import os
import logging

# Load environment variables
load_dotenv()

# Logging Configuration
LOG_CONFIG = {
    'level': os.getenv('LOG_LEVEL', 'INFO').upper(),  # Default to INFO if not set
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'date_format': '%Y-%m-%d %H:%M:%S'
}

# Logging level mapping
LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

# Price Source Configuration
PRICE_SOURCES = {
    'yahoo_finance': {
        'enabled': True,
        'priority': 1,
        'retry_count': 3,
        'retry_delay': 1
    },
    'google_finance': {
        'enabled': True,
        'priority': 2,
        'retry_count': 2,
        'retry_delay': 1
    }
}

# Feature Flags
FEATURE_FLAGS = {
    'enable_fallback_sources': True,
    'validate_prices': True,
    'enable_email_notifications': False
}

# Price Validation Settings
PRICE_VALIDATION = {
    'min_price': 0,
    'max_price': 1000000,
}

# Email Configuration
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'sender_email': os.getenv('SENDER_EMAIL'),
    'sender_password': os.getenv('EMAIL_PASSWORD'),
    'recipient_email': os.getenv('RECIPIENT_EMAIL')
}

# Database Configuration
DB_CONFIG = {
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'database': os.getenv('DB_NAME')
}
