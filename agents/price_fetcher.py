import yfinance as yf
import requests
from bs4 import BeautifulSoup
import time
from config import PRICE_SOURCES, FEATURE_FLAGS, PRICE_VALIDATION, DB_CONFIG
from datetime import datetime
from sqlalchemy import create_engine, text
from agents.logger import setup_logger

class PriceFetcher:
    def __init__(self):
        self.logger = setup_logger(__name__)
        self.engine = create_engine(
            f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
            f"{DB_CONFIG['host']}/{DB_CONFIG['database']}"
        )
        self.sources = ['yahoo', 'google']
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def fetch_prices(self, symbols):
        """Fetch current prices for given symbols"""
        try:
            self.logger.info("\n📊 Fetching Stock Prices...")
            print("=" * 50)
            
            prices = {}
            for symbol in symbols:
                price = None
                source_used = None

                # Try Yahoo Finance first
                price, source_used = self._fetch_price_yahoo(symbol)
                
                # If Yahoo fails, try Google Finance
                if price is None:
                    price, source_used = self._fetch_price_google(symbol)
                
                if price:
                    prices[symbol] = {
                        'price': price,
                        'source': source_used
                    }
                    print(f"✅ Fetched {symbol}: ₹{price:,.2f} from {source_used}")
                else:
                    print(f"❌ Failed to fetch price for {symbol} from all sources")
            
            if prices:
                print(f"✅ Successfully fetched {len(prices)} stock prices")
                self._update_prices_in_db(prices)
            else:
                print("❌ No prices could be fetched")
            
            return prices

        except Exception as e:
            self.logger.error(f"Error fetching prices: {str(e)}")
            return None

    def _fetch_price_yahoo(self, symbol):
        """Fetch price from Yahoo Finance"""
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period="1d")
            if not hist.empty:
                return float(hist['Close'].iloc[-1]), "yahoo"
            return None, None

        except Exception as e:
            self.logger.error(f"Error fetching from Yahoo Finance for {symbol}: {str(e)}")
            return None, None

    def _fetch_price_google(self, symbol):
        """Fetch price from Google Finance"""
        try:
            google_symbol = f"NSE:{symbol.replace('.NS', '')}"
            url = f"https://www.google.com/finance/quote/{google_symbol}"
            
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                price_div = soup.find('div', {'class': 'YMlKec fxKbKc'})
                
                if price_div:
                    price_text = price_div.text.replace('₹', '').replace(',', '')
                    return float(price_text), "google"
            
            return None, None

        except Exception as e:
            self.logger.error(f"Error fetching from Google Finance for {symbol}: {str(e)}")
            return None, None

    def _update_prices_in_db(self, prices):
        """Update stock prices in database"""
        try:
            query = """
                REPLACE INTO stockprice (stockSymbol, price, priceDate, source)
                VALUES (:stockSymbol, :price, :priceDate, :source)
            """
            
            current_date = datetime.now().date()
            price_data = [
                {
                    'stockSymbol': symbol,
                    'price': data['price'],
                    'priceDate': current_date,
                    'source': data['source']
                }
                for symbol, data in prices.items()
            ]

            with self.engine.connect() as connection:
                connection.execute(text(query), price_data)
                connection.commit()
                self.logger.info(f"Updated prices for {len(price_data)} stocks in database")

        except Exception as e:
            self.logger.error(f"Error updating prices in database: {str(e)}")
            raise

    def _add_delay(self):
        """Add delay between requests to avoid rate limiting"""
        time.sleep(1)
