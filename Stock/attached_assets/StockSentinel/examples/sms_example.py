# Copyright © 2025 Sami Singh. All rights reserved.

from utils.sms_notifications import SMSNotifier

def example_usage():
    """
    Example of how to use the SMS notification system.
    Note: Requires valid Twilio credentials in environment variables:
    - TWILIO_ACCOUNT_SID
    - TWILIO_AUTH_TOKEN
    - TWILIO_PHONE_NUMBER
    """
    
    # Initialize the notifier
    notifier = SMSNotifier()
    
    # Check if SMS is enabled (requires Twilio credentials)
    if not notifier.is_enabled():
        print("SMS notifications are not enabled. Please set up Twilio credentials first.")
        return
    
    # Example phone number (replace with actual number)
    to_number = "+1234567890"
    
    # Send a test message
    print("Sending test message...")
    if notifier.send_test_message(to_number):
        print("Test message sent successfully!")
    else:
        print("Failed to send test message")
    
    # Example price alert
    print("\nSending price alert...")
    if notifier.send_price_alert(
        to_number=to_number,
        symbol="AAPL",
        price=150.25,
        alert_type="above",
        target_price=150.00
    ):
        print("Price alert sent successfully!")
    else:
        print("Failed to send price alert")

if __name__ == "__main__":
    example_usage()
