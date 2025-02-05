# config.py

Central configuration file
Contains settings for:
- Logging
- Price sources (Yahoo/Google)
- Feature flags
  Price validation rules
  Email settings
  Database connection details

# utils/logger.py

Sets up consistent logging across the application
Uses settings from config.py
Used by all other classes for standardized logging

# agents/price_fetcher.py

Responsible for fetching stock prices
Uses multiple sources (Yahoo/Google)
Has fallback mechanism if primary source fails
Saves prices to database
Used by both PortfolioValuator and PerformanceCalculator

# agents/portfolio_fetcher.py

Handles database operations for portfolio data
Gets portfolio information
Updates stock prices
Gets current prices
Gets unique stock symbols
Used by PortfolioValuator, PerformanceCalculator, and PortfolioManager

# agents/portfolio_valuator.py

Calculates current portfolio value
Uses PortfolioFetcher to get portfolio data
Uses PriceFetcher to get current prices
Saves portfolio values to database
Prints portfolio summary

# agents/performance_calculator.py

Calculates portfolio performance metrics
Uses PortfolioFetcher for portfolio data
Uses PriceFetcher for current prices
Calculates gains/losses and performance percentages
Prints performance summary

# agents/notification_sender.py

Handles email notifications
Uses settings from config.py
Formats performance data into HTML email
Sends notifications when enabled in feature flags

# agents/portfolio_manager.py

High-level orchestrator
Coordinates between other components
Runs the complete portfolio analysis process:
Gets portfolio data
Fetches prices
Calculates performance
Sends notifications

# main.py

Entry point of the application
Handles command-line arguments
Executes either value calculation, performance calculation, or both
Triggers notifications if needed

# Flow of Data

A[main.py] --> B[PortfolioValuator]
A --> C[PerformanceCalculator]
B --> D[PortfolioFetcher]
B --> E[PriceFetcher]
C --> D
C --> E
B --> F[Database]
E --> F
D --> F
C --> G[NotificationSender]
G --> H[Email]
