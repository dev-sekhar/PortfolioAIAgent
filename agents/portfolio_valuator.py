from datetime import datetime
from sqlalchemy import text
import pandas as pd
from agents.portfolio_fetcher import PortfolioFetcher
from agents.price_fetcher import PriceFetcher


class PortfolioValuator:
    def __init__(self):
        self.portfolio_fetcher = PortfolioFetcher()
        self.price_fetcher = PriceFetcher()
        self.engine = self.portfolio_fetcher.engine

    def calculate_portfolio_value(self):
        """Calculate current portfolio value"""
        try:
            print("\n💰 Calculating Portfolio Value...")
            print("=" * 50)

            # Get portfolio data
            portfolio_data = self.portfolio_fetcher.get_portfolio_data()
            if portfolio_data.empty:
                print("⚠️ No portfolio data found")
                return False

            # Get current prices
            symbols = portfolio_data['stockSymbol'].unique()
            prices = self.price_fetcher.fetch_prices(symbols)

            if not prices:
                print("⚠️ No price data available")
                return False

            # Convert quantity columns to numeric, handling null values
            portfolio_data['purchaseQty'] = pd.to_numeric(
                portfolio_data['purchaseQty'], errors='coerce')
            portfolio_data['additionalQty'] = pd.to_numeric(
                portfolio_data['additionalQty'], errors='coerce').fillna(0)

            # Calculate total quantity
            portfolio_data['totalQuantity'] = portfolio_data['purchaseQty'] + \
                portfolio_data['additionalQty']

            # Calculate values
            valuation_date = datetime.now().date()
            portfolio_values = []

            for (portfolio_name, owner), group in portfolio_data.groupby(['portfolioName', 'owner']):
                total_value = 0
                print(f"\nCalculating value for {owner}'s {portfolio_name}:")

                for _, row in group.iterrows():
                    if row['stockSymbol'] in prices:
                        price = float(prices[row['stockSymbol']]['price'])
                        quantity = float(row['totalQuantity'])
                        stock_value = price * quantity
                        total_value += stock_value
                        print(f"  {row['stockSymbol']}: {
                              quantity} shares @ ₹{price:,.2f} = ₹{stock_value:,.2f}")
                        print(f"    (Purchase Qty: {int(row['purchaseQty'])}, "
                              f"Additional Qty: {int(row['additionalQty'])})")

                portfolio_values.append({
                    'portfolioName': portfolio_name,
                    'owner': owner,
                    'value': round(total_value, 2),
                    'valuationDate': valuation_date
                })

            # Update database
            if portfolio_values:
                self._update_portfolio_values(portfolio_values)

                # Print summary
                print("\n📊 Portfolio Valuation Summary:")
                for val in portfolio_values:
                    print(f"Portfolio: {val['portfolioName']}")
                    print(f"Owner: {val['owner']}")
                    print(f"Value: ₹{val['value']:,.2f}")
                    print(f"Date: {val['valuationDate']}")
                    print("-" * 30)
            else:
                print("\n⚠️ No portfolio values calculated")

            return True

        except Exception as e:
            print(f"❌ Error calculating portfolio value: {str(e)}")
            return False

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
