import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from config import EMAIL_CONFIG, FEATURE_FLAGS


class NotificationSender:
    def __init__(self):
        self.config = EMAIL_CONFIG
        print("\n📧 Initializing NotificationSender...")
        print(f"Email notifications enabled: {FEATURE_FLAGS['enable_email_notifications']}")
        print(f"SMTP Server: {self.config['smtp_server']}")
        print(f"From Email: {self.config['sender_email']}")
        print(f"To Email: {self.config['recipient_email']}")

    def send_email_notification(self, performance_data):
        """Send email notification about portfolio performance"""
        print("\n📧 Attempting to send email notification...")
        
        if not FEATURE_FLAGS['enable_email_notifications']:
            print("📧 Email notifications are disabled in FEATURE_FLAGS")
            return

        if performance_data is None or performance_data.empty:
            print("⚠️ No performance data to send")
            return

        try:
            print("Creating email message...")
            msg = self._create_email_message(performance_data)

            print(f"Connecting to SMTP server: {self.config['smtp_server']}:{self.config['smtp_port']}")
            with smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port']) as server:
                print("Starting TLS...")
                server.starttls()
                
                print("Attempting login...")
                if not self.config['sender_password']:
                    print("❌ Error: Email password is not set in configuration")
                    return
                    
                server.login(self.config['sender_email'], self.config['sender_password'])
                
                print("Sending message...")
                server.send_message(msg)
                print("\n✉️ Performance notification sent successfully")

        except smtplib.SMTPAuthenticationError as e:
            print(f"\n❌ SMTP Authentication Error:")
            print(f"   Please check your email and app password")
            print(f"   Error: {str(e)}")
        except Exception as e:
            print(f"\n❌ Error sending notification:")
            print(f"   Type: {type(e).__name__}")
            print(f"   Error: {str(e)}")

    def _create_email_message(self, performance_data):
        """Create formatted email message"""
        msg = MIMEMultipart()
        msg['From'] = self.config['sender_email']
        msg['To'] = self.config['recipient_email']
        msg['Subject'] = f"Portfolio Performance Update - {datetime.now().strftime('%Y-%m-%d')}"

        print(f"Creating email body with {len(performance_data)} records...")
        email_body = self._format_email_body(performance_data)
        msg.attach(MIMEText(email_body, 'html'))

        return msg

    def _format_email_body(self, performance_data):
        """Format the email body with performance data"""
        try:
            avg_performance = performance_data['performance'].mean()
            print(f"Average performance calculated: {avg_performance:.2f}%")
            
            return """
            <html>
            <body>
                <h2>Portfolio Performance Summary</h2>
                <p>Average Performance: {:.2f}%</p>
                
                <h3>Performance Details:</h3>
                <table border="1">
                    <tr>
                        <th>Stock</th>
                        <th>Owner</th>
                        <th>Portfolio</th>
                        <th>Purchase Price</th>
                        <th>Current Price</th>
                        <th>Performance</th>
                    </tr>
                    {}
                </table>
                <p><small>Generated on {}</small></p>
            </body>
            </html>
            """.format(
                avg_performance,
                self._format_table_rows(performance_data),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
        except Exception as e:
            print(f"❌ Error formatting email body: {str(e)}")
            raise

    def _format_table_rows(self, performance_data):
        """Format table rows for email"""
        try:
            rows = ""
            for _, row in performance_data.iterrows():
                rows += f"""
                    <tr>
                        <td>{row['stockSymbol']}</td>
                        <td>{row['owner']}</td>
                        <td>{row['portfolioName']}</td>
                        <td>₹{row['purchasePrice']:,.2f}</td>
                        <td>₹{row['price']:,.2f}</td>
                        <td>{row['performance']:.2f}%</td>
                    </tr>
                """
            return rows
        except Exception as e:
            print(f"❌ Error formatting table rows: {str(e)}")
            raise
