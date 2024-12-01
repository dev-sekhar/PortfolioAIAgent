# Price Source Configuration
PRICE_SOURCES = {
    'yahoo_finance': {
        'enabled': True,
        'priority': 1,  # Lower number = higher priority
        'retry_count': 3,
        'retry_delay': 1  # seconds
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
    'enable_fallback_sources': True,  # Enable/disable fallback to secondary sources
    'validate_prices': True,          # Enable/disable price validation
    'enable_email_notifications': False  # Disabled by default
}

# Price Validation Settings
PRICE_VALIDATION = {
    'min_price': 0,
    'max_price': 1000000,  # Adjust as needed
}

# Email Configuration (only used if notifications are enabled)
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'sender_email': 'your_email@gmail.com',
    'sender_password': 'your_16_digit_app_password',
    'recipient_email': 'recipient@gmail.com'
}

# Database Configuration
DB_CONFIG = {
    'user': 'root',
    'password': 'root',
    'host': 'localhost',
    'database': 'portflionew'
} 