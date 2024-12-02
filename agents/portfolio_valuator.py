from datetime import datetime
from sqlalchemy import text
import pandas as pd
from agents.portfolio_fetcher import PortfolioFetcher
from agents.price_fetcher import PriceFetcher
from agents.notification_sender import NotificationSender
from agents.performance_calculator import PerformanceCalculator
from utils.logger import setup_logger


class PortfolioValuator:
    def __init__(self):
        self.portfolio_fetcher = PortfolioFetcher()
        self.price_fetcher = PriceFetcher()
        self.engine = self.portfolio_fetcher.engine
        self.notification_sender = NotificationSender()
        self.performance_calculator = PerformanceCalculator()
        self.logger = setup_logger(__name__)

    def calculate_portfolio_value(self):
        """Calculate current portfolio value"""
        try:
            self.logger.info("Starting portfolio value calculation")
            self.logger.debug("Initializing portfolio value calculation process")

            # Get portfolio data
            portfolio_data = self.portfolio_fetcher.get_portfolio_data()
            if portfolio_data.empty:
                self.logger.warning("No portfolio data found")
                return False

            # Convert quantity columns to numeric
            portfolio_data['purchaseQty'] = pd.to_numeric(portfolio_data['purchaseQty'], errors='coerce')
            portfolio_data['additionalQty'] = pd.to_numeric(portfolio_data['additionalQty'], errors='coerce').fillna(0)

            # Get current prices
            symbols = portfolio_data['stockSymbol'].unique()
            self.logger.debug(f"Fetching prices for symbols: {symbols}")
            prices = self.price_fetcher.fetch_prices(symbols)

            if not prices:
                self.logger.warning("No price data available")
                return False

            # Convert prices dictionary to DataFrame
            prices_df = pd.DataFrame([
                {'stockSymbol': symbol, 'price': data['price']}
                for symbol, data in prices.items()
            ])

            # Calculate performance
            self.logger.info("Calculating stock performance")
            performance_data = self.performance_calculator.calculate_performance(
                portfolio_data, prices_df)

            if performance_data is not None:
                # Sort and display performance data
                performance_data = performance_data.sort_values(
                    by='performance', ascending=False)
                self._print_performance_summary(performance_data)

                # Calculate and update portfolio values
                self.logger.debug("Calculating portfolio values")
                portfolio_values = self._calculate_portfolio_values(portfolio_data, prices)

                if portfolio_values:
                    self._update_portfolio_values(portfolio_values)
                    self._print_portfolio_summary(portfolio_values)

                    # Send notification
                    self.logger.info("Sending performance notification")
                    self.notification_sender.send_email_notification(
                        performance_data)

            return True

        except Exception as e:
            self.logger.error(f"Error calculating portfolio value: {str(e)}", exc_info=True)
            return False

    def _print_performance_summary(self, performance_data):
        """Print performance summary in tabular format"""
        self.logger.info("\nStock Performance Summary:")
        print("=" * 120)

        # Print header
        print(f"{'Symbol':<12} {'Portfolio':<12} {'Owner':<10} {'Purchase':>12} {'Current':>12} "
              f"{'Performance':>12} {'Quantity':>10} {'Value':>15} {'P/L':>15}")
        print("-" * 120)

        # Print each row
        for _, row in performance_data.iterrows():
            total_qty = float(row['purchaseQty']) + float(row['additionalQty'])
            current_value = float(row['price']) * total_qty
            purchase_value = float(row['purchasePrice']) * total_qty
            profit_loss = current_value - purchase_value

            print(
                f"{row['stockSymbol']:<12} "
                f"{row['portfolioName']:<12} "
                f"{row['owner']:<10} "
                f"₹{float(row['purchasePrice']):>10,.2f} "
                f"₹{float(row['price']):>10,.2f} "
                f"{row['performance']:>10.2f}% "
                f"{total_qty:>10.0f} "
                f"₹{current_value:>13,.2f} "
                f"{'📈' if profit_loss > 0 else '📉'} ₹{abs(profit_loss):>10,.2f}"
            )

        # Print summary statistics
        print("-" * 120)
        self._print_summary_statistics(performance_data)

    def _update_portfolio_values(self, portfolio_values):
        """Update portfolio values in database"""
        try:
            with self.engine.connect() as conn:
                for value_data in portfolio_values:
                    # Check if record exists
                    check_query = text("""
                        SELECT id FROM portfoliovalue 
                        WHERE portfolioName = :portfolio 
                        AND owner = :owner 
                        AND valuationDate = :date
                    """)

                    result = conn.execute(check_query, {
                        'portfolio': value_data['portfolioName'],
                        'owner': value_data['owner'],
                        'date': value_data['valuationDate']
                    }).fetchone()

                    if result:
                        # Update existing record
                        update_query = text("""
                            UPDATE portfoliovalue 
                            SET value = :value
                            WHERE id = :id
                        """)
                        conn.execute(update_query, {
                            'value': value_data['value'],
                            'id': result[0]
                        })
                    else:
                        # Insert new record
                        insert_query = text("""
                            INSERT INTO portfoliovalue 
                                (portfolioName, owner, value, valuationDate)
                            VALUES 
                                (:portfolio, :owner, :value, :date)
                        """)
                        conn.execute(insert_query, {
                            'portfolio': value_data['portfolioName'],
                            'owner': value_data['owner'],
                            'value': value_data['value'],
                            'date': value_data['valuationDate']
                        })

                conn.commit()

            print("✅ Portfolio values updated successfully")
            return True

        except Exception as e:
            print(f"❌ Error updating portfolio values: {str(e)}")
            return False

    def get_valuation_history(self, days=30):
        """Get historical portfolio valuations"""
        try:
            query = text("""
                SELECT 
                    portfolioName,
                    owner,
                    value,
                    valuationDate
                FROM portfoliovalue
                WHERE valuationDate >= DATE_SUB(CURRENT_DATE, INTERVAL :days DAY)
                ORDER BY valuationDate DESC, portfolioName, owner
            """)

            df = pd.read_sql(query, self.engine, params={'days': days})

            if not df.empty:
                print("\n📈 Valuation History:")
                for _, row in df.iterrows():
                    print(f"Portfolio: {row['portfolioName']}")
                    print(f"Owner: {row['owner']}")
                    print(f"Value: ₹{float(row['value']):,.2f}")
                    print(f"Date: {row['valuationDate']}")
                    print("-" * 30)
            else:
                print("ℹ️ No valuation history found")

            return df

        except Exception as e:
            print(f"❌ Error fetching valuation history: {str(e)}")
            return pd.DataFrame()

    def _print_summary_statistics(self, performance_data):
        """Print summary statistics for portfolio performance"""
        try:
            self.logger.debug("Calculating summary statistics")
            
            print(f"\nSummary Statistics:")
            
            # Best and worst performers
            best_performer = performance_data.iloc[0]
            worst_performer = performance_data.iloc[-1]
            
            print(f"Best Performer: {best_performer['stockSymbol']} "
                  f"({best_performer['performance']:.2f}%)")
            print(f"Worst Performer: {worst_performer['stockSymbol']} "
                  f"({worst_performer['performance']:.2f}%)")
            
            # Average performance
            avg_performance = performance_data['performance'].mean()
            print(f"Average Performance: {avg_performance:.2f}%")
            
            # Total profit/loss
            total_pl = sum(
                (float(row['price']) - float(row['purchasePrice'])) * 
                (float(row['purchaseQty']) + float(row['additionalQty'])) 
                for _, row in performance_data.iterrows()
            )
            
            # Portfolio value
            total_value = sum(
                float(row['price']) * 
                (float(row['purchaseQty']) + float(row['additionalQty'])) 
                for _, row in performance_data.iterrows()
            )
            
            print(f"Total Portfolio Value: ₹{total_value:,.2f}")
            print(f"Total P/L: {'📈' if total_pl > 0 else '📉'} ₹{abs(total_pl):,.2f} "
                  f"({(total_pl/total_value)*100:.2f}%)")

        except Exception as e:
            self.logger.error(f"Error printing summary statistics: {str(e)}")
            raise

    def _calculate_portfolio_values(self, portfolio_data, prices):
        """Calculate portfolio values from portfolio data and current prices"""
        try:
            self.logger.debug("Calculating portfolio values")
            portfolio_values = []
            valuation_date = datetime.now().date()

            # Group by portfolio and owner
            for (portfolio_name, owner), group in portfolio_data.groupby(['portfolioName', 'owner']):
                total_value = 0
                for _, row in group.iterrows():
                    if row['stockSymbol'] in prices:
                        price = float(prices[row['stockSymbol']]['price'])
                        quantity = float(row['purchaseQty']) + float(row['additionalQty'])
                        total_value += price * quantity

                portfolio_values.append({
                    'portfolioName': portfolio_name,
                    'owner': owner,
                    'value': round(total_value, 2),
                    'valuationDate': valuation_date
                })

            self.logger.debug(f"Calculated values for {len(portfolio_values)} portfolios")
            return portfolio_values

        except Exception as e:
            self.logger.error(f"Error calculating portfolio values: {str(e)}")
            raise

    def _print_portfolio_summary(self, portfolio_values):
        """Print summary of portfolio valuations"""
        try:
            self.logger.info("\n📊 Portfolio Valuation Summary:")
            print("=" * 80)
            
            # Print header
            print(f"{'Portfolio':<15} {'Owner':<15} {'Value':>20} {'Date':>15}")
            print("-" * 80)

            # Print each portfolio's value
            total_value = 0
            for val in portfolio_values:
                print(
                    f"{val['portfolioName']:<15} "
                    f"{val['owner']:<15} "
                    f"₹{val['value']:>18,.2f} "
                    f"{val['valuationDate'].strftime('%Y-%m-%d'):>15}"
                )
                total_value += val['value']

            # Print total
            print("-" * 80)
            print(f"{'Total Portfolio Value:':<31} ₹{total_value:>18,.2f}")
            
            # Print timestamp
            print(f"\nValuation completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        except Exception as e:
            self.logger.error(f"Error printing portfolio summary: {str(e)}")
            raise
