# Copyright © 2025 Sami Singh. All rights reserved.

import os
from typing import Optional
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

class SMSNotifier:
    """
    SMS notification handler using Twilio.
    Note: Requires Twilio account and valid credentials to function.
    Visit https://www.twilio.com/pricing for current pricing information.
    """
    
    def __init__(self):
        """Initialize Twilio client if credentials are available"""
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.from_number = os.getenv('TWILIO_PHONE_NUMBER')
        self.enabled = all([self.account_sid, self.auth_token, self.from_number])
        self.client = Client(self.account_sid, self.auth_token) if self.enabled else None

    def is_enabled(self) -> bool:
        """Check if SMS notifications are enabled"""
        return self.enabled

    def send_price_alert(self, to_number: str, symbol: str, price: float, 
                        alert_type: str, target_price: Optional[float] = None) -> bool:
        """
        Send price alert SMS
        
        Args:
            to_number: Recipient's phone number (format: +1234567890)
            symbol: Stock symbol
            price: Current price
            alert_type: Type of alert ('above' or 'below')
            target_price: Target price that triggered the alert
            
        Returns:
            bool: True if message sent successfully, False otherwise
        """
        if not self.enabled:
            print("SMS notifications are not enabled. Missing Twilio credentials.")
            return False

        try:
            message = (
                f"🔔 Stock Alert: {symbol}\n"
                f"Current Price: ${price:.2f}\n"
            )
            
            if target_price:
                message += f"Target Price: ${target_price:.2f}\n"
                message += f"Price is now {alert_type} target."
            
            self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=to_number
            )
            return True
            
        except TwilioRestException as e:
            print(f"Failed to send SMS: {str(e)}")
            return False
        except Exception as e:
            print(f"Unexpected error sending SMS: {str(e)}")
            return False

    def send_test_message(self, to_number: str) -> bool:
        """
        Send a test message to verify SMS functionality
        
        Args:
            to_number: Recipient's phone number (format: +1234567890)
            
        Returns:
            bool: True if test message sent successfully, False otherwise
        """
        if not self.enabled:
            print("SMS notifications are not enabled. Missing Twilio credentials.")
            return False

        try:
            message = (
                "🔔 Test Alert\n"
                "Your stock alerts are now configured correctly!"
            )
            
            self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=to_number
            )
            return True
            
        except TwilioRestException as e:
            print(f"Failed to send test SMS: {str(e)}")
            return False
        except Exception as e:
            print(f"Unexpected error sending test SMS: {str(e)}")
            return False
