import pandas as pd
from datetime import datetime, date

class PerformanceCalculator:
    def calculate_performance(self, portfolio_data, current_prices):
        """Calculate portfolio performance"""
        try:
            if portfolio_data.empty or current_prices.empty:
                print("⚠️ No data available for performance calculation")
                return None

            # Convert price columns to float
            portfolio_data['purchasePrice'] = pd.to_numeric(portfolio_data['purchasePrice'], errors='coerce')
            current_prices['price'] = pd.to_numeric(current_prices['price'], errors='coerce')

            # Merge portfolio with latest prices
            performance_data = pd.merge(
                portfolio_data,
                current_prices,
                on='stockSymbol',
                how='left',
                suffixes=('', '_current')
            )

            # Calculate performance only for valid numeric prices
            mask = (performance_data['price'].notna() & 
                    performance_data['purchasePrice'].notna())
            
            performance_data['performance'] = None
            if mask.any():
                performance_data.loc[mask, 'performance'] = (
                    (performance_data.loc[mask, 'price'] - 
                     performance_data.loc[mask, 'purchasePrice']) / 
                    performance_data.loc[mask, 'purchasePrice'] * 100
                ).round(2)

            # Handle date calculations safely
            today = date.today()
            
            # Convert priceDate to datetime safely
            try:
                if 'priceDate' in performance_data.columns:
                    # Convert to datetime if it's not already
                    if not pd.api.types.is_datetime64_any_dtype(performance_data['priceDate']):
                        performance_data['priceDate'] = pd.to_datetime(performance_data['priceDate'])
                    
                    # Convert to date object
                    performance_data['priceDate'] = performance_data['priceDate'].dt.date
                    
                    # Calculate age in days
                    performance_data['price_age_days'] = performance_data['priceDate'].apply(
                        lambda x: (today - x).days if pd.notnull(x) else None
                    )
                else:
                    performance_data['priceDate'] = today
                    performance_data['price_age_days'] = 0
            except Exception as e:
                print(f"⚠️ Warning: Error processing dates: {str(e)}")
                performance_data['priceDate'] = today
                performance_data['price_age_days'] = 0

            return performance_data.sort_values(
                by='performance', 
                ascending=False,
                na_position='last'
            )

        except Exception as e:
            print(f"❌ Error calculating performance: {str(e)}")
            return None 