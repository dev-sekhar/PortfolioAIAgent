from agents.portfolio_valuator import PortfolioValuator
from agents.performance_calculator import PerformanceCalculator
from agents.notification_sender import NotificationSender
import argparse

def main():
    # Create argument parser
    parser = argparse.ArgumentParser(description='Portfolio Analysis Tools')
    parser.add_argument('--owner', type=str, required=True, 
                       help='Owner name for analysis')
    parser.add_argument('--action', type=str, choices=['value', 'performance', 'both'],
                       default='both', help='Type of analysis to perform')

    args = parser.parse_args()

    if args.action in ['value', 'both']:
        # Calculate portfolio value
        valuator = PortfolioValuator()
        portfolio_values = valuator.calculate_portfolio_value(args.owner)

    if args.action in ['performance', 'both']:
        # Calculate performance
        calculator = PerformanceCalculator()
        performance_data = calculator.calculate_performance_for_owner(args.owner)
        
        # Send notification if performance was calculated
        if performance_data is not None:
            notifier = NotificationSender()
            notifier.send_email_notification(performance_data)

if __name__ == "__main__":
    main()
