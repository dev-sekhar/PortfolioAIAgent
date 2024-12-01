from sqlalchemy import text
import pandas as pd
from datetime import datetime


class PortfolioFetcher:
    def __init__(self):
        from sqlalchemy import create_engine
        self.engine = create_engine('mysql+pymysql://root:root@localhost/portflionew')

    def update_stock_prices(self, prices_dict):
        """Update stock prices in database"""
        if not prices_dict:
            print("⚠️ No prices to update")
            return False

        try:
            # Convert dictionary to DataFrame
            prices_list = []
            for symbol, data in prices_dict.items():
                prices_list.append({
                    'stockSymbol': symbol,
                    'price': str(data['price']),  # Convert to string since price column is TEXT
                    'source': data['source'],
                    'priceDate': data['priceDate']
                })

            # Update prices using SQLAlchemy properly
            with self.engine.connect() as conn:
                for price_data in prices_list:
                    query = text("""
                        INSERT INTO stockprice (stockSymbol, price, priceDate, source)
                        VALUES (:symbol, :price, :date, :source)
                        ON DUPLICATE KEY UPDATE
                        price = VALUES(price),
                        priceDate = VALUES(priceDate),
                        source = VALUES(source)
                    """)
                    
                    conn.execute(query, {
                        'symbol': price_data['stockSymbol'],
                        'price': price_data['price'],
                        'date': price_data['priceDate'],
                        'source': price_data['source']
                    })
                conn.commit()
            
            print(f"✅ Successfully updated prices for {len(prices_dict)} stocks")
            return True

        except Exception as e:
            print(f"❌ Error updating prices: {str(e)}")
            return False

    def get_current_prices(self):
        """Get latest prices from database"""
        try:
            query = text("""
                SELECT 
                    stockSymbol,
                    price,
                    source,
                    priceDate
                FROM stockprice
                WHERE (stockSymbol, priceDate) IN (
                    SELECT 
                        stockSymbol,
                        MAX(priceDate)
                    FROM stockprice
                    GROUP BY stockSymbol
                )
            """)
            
            return pd.read_sql(query, self.engine)

        except Exception as e:
            print(f"❌ Error fetching current prices: {str(e)}")
            return pd.DataFrame()

    def get_portfolio_data(self):
        """Get portfolio data from database"""
        try:
            query = text("""
                SELECT * FROM portfolio
                ORDER BY owner, stockSymbol
            """)
            return pd.read_sql(query, self.engine)
        except Exception as e:
            print(f"❌ Error fetching portfolio data: {str(e)}")
            return pd.DataFrame()

    def get_unique_symbols(self):
        """Get unique stock symbols from portfolio"""
        try:
            query = text("SELECT DISTINCT stockSymbol FROM portfolio")
            df = pd.read_sql(query, self.engine)
            return df['stockSymbol'].tolist()
        except Exception as e:
            print(f"❌ Error fetching stock symbols: {str(e)}")
            return []
