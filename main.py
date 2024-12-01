from agents.portfolio_valuator import PortfolioValuator


def main():
    try:
        # Initialize portfolio valuator
        valuator = PortfolioValuator()
        
        # Calculate and update portfolio values
        valuator.calculate_portfolio_value()
        
        # Optionally, show valuation history
        history = valuator.get_valuation_history(days=7)
        if not history.empty:
            print("\n📈 Recent Valuation History:")
            print(history.to_string())

    except Exception as e:
        print(f"❌ Error in main: {str(e)}")


if __name__ == "__main__":
    main()
