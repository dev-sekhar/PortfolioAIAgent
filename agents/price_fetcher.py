import yfinance as yf
import requests
from bs4 import BeautifulSoup
import time
from config import PRICE_SOURCES, FEATURE_FLAGS, PRICE_VALIDATION
from datetime import datetime

class PriceFetcher:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.sources = self._get_enabled_sources()

    def _get_enabled_sources(self):
        """Get enabled price sources sorted by priority"""
        return sorted(
            [(k, v) for k, v in PRICE_SOURCES.items() if v['enabled']],
            key=lambda x: x[1]['priority']
        )

    def fetch_prices(self, symbols):
        """Fetch current prices from configured sources"""
        prices = {}
        current_date = datetime.now().date()
        print("\n📊 Fetching Stock Prices...")
        print("=" * 50)

        for symbol in symbols:
            price_data = self._fetch_single_price(symbol)
            if price_data:
                # Store all necessary fields including date
                prices[symbol] = {
                    'stockSymbol': symbol,
                    'price': price_data['price'],
                    'source': price_data['source'],
                    'priceDate': current_date
                }

        if not prices:
            print("⚠️ Could not fetch any stock prices")
        else:
            print(f"✅ Successfully fetched {len(prices)} stock prices")

        return prices

    def _fetch_single_price(self, symbol):
        """Fetch price for a single stock from available sources"""
        for source_name, config in self.sources:
            for attempt in range(config['retry_count']):
                try:
                    if source_name == 'yahoo_finance':
                        price_data = self._fetch_yahoo_price(symbol)
                    elif source_name == 'google_finance':
                        price_data = self._fetch_google_price(symbol)

                    if price_data and self._validate_price(price_data['price']):
                        print(f"✅ Fetched {symbol}: ₹{price_data['price']:,.2f} from {price_data['source']}")
                        return price_data

                except Exception as e:
                    if attempt == config['retry_count'] - 1:
                        print(f"❌ {source_name} error for {symbol}: {str(e)}")
                    
                if attempt < config['retry_count'] - 1:
                    print(f"⚠️ Retry {attempt + 1} for {symbol} using {source_name}")
                    time.sleep(config['retry_delay'])

            if not FEATURE_FLAGS['enable_fallback_sources']:
                break

        print(f"❌ Failed to fetch price for {symbol} from all available sources")
        return None

    def _fetch_yahoo_price(self, symbol):
        """Fetch price from Yahoo Finance"""
        ticker = yf.Ticker(symbol)
        info = ticker.info
        if 'regularMarketPrice' in info and info['regularMarketPrice'] is not None:
            return {
                'price': info['regularMarketPrice'],
                'source': 'Yahoo Finance'
            }
        
        # Try historical data if current price is not available
        hist = ticker.history(period='1d')
        if not hist.empty:
            return {
                'price': hist['Close'].iloc[-1],
                'source': 'Yahoo Finance (Historical)'
            }
        return None

    def _fetch_google_price(self, symbol):
        """Fetch price from Google Finance"""
        google_symbol = symbol.replace('.NS', ':NSE')
        url = f"https://www.google.com/finance/quote/{google_symbol}"
        
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        price_div = soup.find('div', {'class': 'YMlKec fxKbKc'})
        
        if price_div:
            price_text = price_div.text.replace('₹', '').replace(',', '').strip()
            return {
                'price': float(price_text),
                'source': 'Google Finance'
            }
        return None

    def _validate_price(self, price):
        """Validate if price is reasonable"""
        if not FEATURE_FLAGS['validate_prices']:
            return True
            
        return (price is not None and 
                price >= PRICE_VALIDATION['min_price'] and 
                price <= PRICE_VALIDATION['max_price'])
