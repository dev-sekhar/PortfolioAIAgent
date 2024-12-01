from agents.portfolio_fetcher import PortfolioFetcher
from agents.price_fetcher import PriceFetcher
from agents.performance_calculator import PerformanceCalculator
from agents.notification_sender import NotificationSender
from config import FEATURE_FLAGS
from datetime import date, datetime
import pandas as pd


class PortfolioManager:
    def __init__(self):
        self.portfolio_fetcher = PortfolioFetcher()
        self.price_fetcher = PriceFetcher()
        self.performance_calculator = PerformanceCalculator()
        self.notification_sender = NotificationSender()

    def run(self):
        try:
            # Get portfolio data
            portfolio_data = self.portfolio_fetcher.get_portfolio_data()
            stock_symbols = self.portfolio_fetcher.get_unique_symbols()

            # Fetch and update prices
            prices = self.price_fetcher.fetch_prices(stock_symbols)
            self.portfolio_fetcher.update_stock_prices(prices)

            # Calculate performance
            performance_data = self.performance_calculator.calculate_performance(
                portfolio_data,
                self.portfolio_fetcher.get_current_prices()
            )

            # Display results
            if performance_data is not None and not performance_data.empty:
                print("\n📈 Portfolio Performance:")
                
                # Format the display data
                display_data = performance_data.copy()
                
                # Format numeric columns
                pd.set_option('display.float_format', lambda x: '%.2f' % x)
                
                # Convert price_age_days to string representation
                display_data['price_age'] = display_data['price_age_days'].apply(
                    lambda x: f"{int(x)} days" if pd.notnull(x) else "N/A"
                )

                # Format dates as strings
                display_data['priceDate'] = display_data['priceDate'].apply(
                    lambda x: x.strftime('%Y-%m-%d') if isinstance(x, (date, datetime)) else str(x)
                )

                print(display_data[[
                    'stockSymbol', 
                    'owner', 
                    'portfolioName',
                    'purchasePrice', 
                    'price', 
                    'performance',
                    'source',
                    'priceDate',
                    'price_age'
                ]].to_string())

                # Add warning for old prices
                old_prices = performance_data[performance_data['price_age_days'] > 1]
                if not old_prices.empty:
                    print("\n⚠️ Warning: Some prices are more than 1 day old:")
                    for _, row in old_prices.iterrows():
                        print(f"   {row['stockSymbol']}: {row['price_age']}")

            # Send notifications only if enabled
            if FEATURE_FLAGS['enable_email_notifications']:
                print("\n📧 Email notifications are enabled")
                self.notification_sender.send_email_notification(performance_data)
            else:
                print("\n📧 Email notifications are disabled")

        except Exception as e:
            print(f"\n❌ Portfolio Manager Error:")
            print(f"   {str(e)}")


if __name__ == "__main__":
    manager = PortfolioManager()
    manager.run()
