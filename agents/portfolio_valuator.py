from datetime import datetime
import pandas as pd
from agents.portfolio_fetcher import PortfolioFetcher
from agents.price_fetcher import PriceFetcher
from utils.logger import setup_logger
from sqlalchemy import text


class PortfolioValuator:
    def __init__(self):
        self.portfolio_fetcher = PortfolioFetcher()
        self.price_fetcher = PriceFetcher()
        self.engine = self.portfolio_fetcher.engine
        self.logger = setup_logger(__name__)

    def calculate_portfolio_value(self, owner=None):
        """Calculate current portfolio value for a specific owner"""
        try:
            if not owner:
                self.logger.error("Owner parameter is required")
                print("\n❌ Error: Owner parameter is required")
                return None

            self.logger.info(f"Starting portfolio value calculation for owner: {owner}")
            print(f"\n💰 Calculating Portfolio Value for {owner}...")
            print("=" * 50)

            # Get portfolio data and prices
            portfolio_data, prices_df = self._fetch_data(owner)
            if portfolio_data is None or prices_df is None:
                return None

            # Calculate and save portfolio values
            portfolio_values = self._calculate_portfolio_values(portfolio_data, prices_df)
            if portfolio_values:
                self._save_portfolio_values(portfolio_values)
                self._print_portfolio_summary(portfolio_values)
                return portfolio_values

            return None

        except Exception as e:
            self.logger.error(f"Error calculating portfolio value: {str(e)}", exc_info=True)
            return None

    def _fetch_data(self, owner):
        """Fetch required portfolio and price data"""
        try:
            # Get portfolio data
            portfolio_data = self.portfolio_fetcher.get_portfolio_data()
            if portfolio_data.empty:
                self.logger.warning("No portfolio data found")
                return None, None

            # Filter for owner
            portfolio_data = portfolio_data[portfolio_data['owner'] == owner]
            if portfolio_data.empty:
                self.logger.warning(f"No portfolio data found for owner: {owner}")
                return None, None

            # Get current prices
            symbols = portfolio_data['stockSymbol'].unique()
            self.logger.debug(f"Fetching prices for symbols: {symbols}")
            prices = self.price_fetcher.fetch_prices(symbols)
            
            if not prices:
                self.logger.warning("No price data available")
                return None, None

            # Convert prices dictionary to DataFrame
            prices_df = pd.DataFrame([
                {'stockSymbol': symbol, 'price': data['price']} 
                for symbol, data in prices.items()
            ])

            return portfolio_data, prices_df

        except Exception as e:
            self.logger.error(f"Error fetching data: {str(e)}")
            return None, None

    def _calculate_portfolio_values(self, portfolio_data, prices_df):
        """Calculate portfolio values"""
        try:
            valuation_date = datetime.now().date()
            
            # Merge portfolio data with prices
            merged_data = pd.merge(
                portfolio_data,
                prices_df,
                on='stockSymbol',
                how='left'
            )

            # Convert quantity columns to numeric
            merged_data['purchaseQty'] = pd.to_numeric(merged_data['purchaseQty'], errors='coerce')
            merged_data['additionalQty'] = pd.to_numeric(merged_data['additionalQty'], errors='coerce').fillna(0)

            # Group by portfolio and calculate total values
            portfolio_values = []
            for (portfolio_name, owner), group in merged_data.groupby(['portfolioName', 'owner']):
                total_value = (group['price'] * (group['purchaseQty'] + group['additionalQty'])).sum()
                
                portfolio_values.append({
                    'portfolioName': portfolio_name,
                    'owner': owner,
                    'value': round(total_value, 2),
                    'valuationDate': valuation_date
                })

            return portfolio_values

        except Exception as e:
            self.logger.error(f"Error calculating portfolio values: {str(e)}")
            return None

    def _save_portfolio_values(self, portfolio_values):
        """Save portfolio values to database"""
        try:
            query = """
                REPLACE INTO portfoliovalue (portfolioName, owner, value, valuationDate)
                VALUES (:portfolioName, :owner, :value, :valuationDate)
            """
            
            with self.engine.connect() as connection:
                connection.execute(text(query), portfolio_values)
                connection.commit()
                self.logger.info("Portfolio values updated successfully")

        except Exception as e:
            self.logger.error(f"Error saving portfolio values: {str(e)}")
            raise

    def _print_portfolio_summary(self, portfolio_values):
        """Print portfolio valuation summary"""
        print("\n📊 Portfolio Valuation Summary")
        print("=" * 80)
        print(f"{'Portfolio':<15} {'Owner':<15} {'Value':>20} {'Date':>15}")
        print("-" * 80)

        total_value = 0
        for val in portfolio_values:
            print(
                f"{val['portfolioName']:<15} "
                f"{val['owner']:<15} "
                f"₹{val['value']:>18,.2f} "
                f"{val['valuationDate'].strftime('%Y-%m-%d'):>15}"
            )
            total_value += val['value']

        print("-" * 80)
        print(f"{'Total Value:':<31} ₹{total_value:>18,.2f}")
