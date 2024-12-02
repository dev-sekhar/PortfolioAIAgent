import pandas as pd
from datetime import datetime, date
from agents.portfolio_fetcher import PortfolioFetcher
from agents.price_fetcher import PriceFetcher
from agents.logger import setup_logger


class PerformanceCalculator:
    def __init__(self):
        self.portfolio_fetcher = PortfolioFetcher()
        self.price_fetcher = PriceFetcher()
        self.logger = setup_logger(__name__)

    def calculate_performance_for_owner(self, owner):
        """Calculate performance for a specific owner"""
        try:
            self.logger.info(f"Calculating performance for owner: {owner}")

            # Fetch required data
            portfolio_data, prices_df = self._fetch_data(owner)
            if portfolio_data is None or prices_df is None:
                return None

            # Calculate performance
            performance_data = self._calculate_performance(
                portfolio_data, prices_df)
            if performance_data is not None:
                self._print_performance_summary(performance_data)

            return performance_data

        except Exception as e:
            self.logger.error(f"Error calculating performance: {str(e)}")
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
                self.logger.warning(
                    f"No portfolio data found for owner: {owner}")
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

    def _calculate_performance(self, portfolio_data, prices_df):
        """Calculate performance metrics"""
        try:
            # Convert numeric columns
            portfolio_data['purchasePrice'] = pd.to_numeric(
                portfolio_data['purchasePrice'], errors='coerce')
            portfolio_data['purchaseQty'] = pd.to_numeric(
                portfolio_data['purchaseQty'], errors='coerce')
            portfolio_data['additionalQty'] = pd.to_numeric(
                portfolio_data['additionalQty'], errors='coerce').fillna(0)
            prices_df['price'] = pd.to_numeric(
                prices_df['price'], errors='coerce')

            # Merge portfolio with latest prices
            performance_data = pd.merge(
                portfolio_data,
                prices_df,
                on='stockSymbol',
                how='left'
            )

            # Calculate performance
            mask = (performance_data['price'].notna() &
                    performance_data['purchasePrice'].notna())

            performance_data['performance'] = None
            if mask.any():
                performance_data.loc[mask, 'performance'] = (
                    (performance_data.loc[mask, 'price'] -
                     performance_data.loc[mask, 'purchasePrice']) /
                    performance_data.loc[mask, 'purchasePrice'] * 100
                ).round(2)

            return performance_data.sort_values(
                by='performance',
                ascending=False,
                na_position='last'
            )

        except Exception as e:
            self.logger.error(
                f"Error calculating performance metrics: {str(e)}")
            return None

    def _print_performance_summary(self, performance_data):
        """Print performance summary"""
        print("\n📊 Performance Summary")
        print("=" * 120)

        # Print header
        print(f"{'Symbol':<12} {'Portfolio':<12} {'Purchase':>12} {'Current':>12} "
              f"{'Performance':>12} {'Quantity':>10} {'Value':>15} {'P/L':>15}")
        print("-" * 120)

        # Print each row
        for _, row in performance_data.iterrows():
            total_qty = row['purchaseQty'] + row['additionalQty']
            current_value = row['price'] * total_qty
            purchase_value = row['purchasePrice'] * total_qty
            profit_loss = current_value - purchase_value

            print(
                f"{row['stockSymbol']:<12} "
                f"{row['portfolioName']:<12} "
                f"₹{row['purchasePrice']:>10,.2f} "
                f"₹{row['price']:>10,.2f} "
                f"{row['performance']:>10.2f}% "
                f"{total_qty:>10.0f} "
                f"₹{current_value:>13,.2f} "
                f"{'📈' if profit_loss > 0 else '📉'} ₹{
                    abs(profit_loss):>10,.2f}"
            )

        self._print_summary_statistics(performance_data)

    def _print_summary_statistics(self, performance_data):
        """Print summary statistics"""
        print("\nSummary Statistics:")
        print("-" * 50)

        avg_performance = performance_data['performance'].mean()
        total_value = (performance_data['price'] *
                       (performance_data['purchaseQty'] + performance_data['additionalQty'])).sum()
        total_cost = (performance_data['purchasePrice'] *
                      (performance_data['purchaseQty'] + performance_data['additionalQty'])).sum()
        total_pl = total_value - total_cost

        print(f"Average Performance: {avg_performance:.2f}%")
        print(f"Total Portfolio Value: ₹{total_value:,.2f}")
        print(f"Total P/L: {'📈' if total_pl > 0 else '📉'} ₹{abs(total_pl):,.2f} "
              f"({(total_pl/total_cost)*100:.2f}%)")
