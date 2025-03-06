"""
Example usage of the notification system
Copyright © 2025 Sami Singh. All rights reserved.
"""
from utils.notifications import ConsoleNotification, StockAlertManager

def test_notifications():
    """Test the notification system"""
    # Initialize with console notification provider
    notification_provider = ConsoleNotification()
    alert_manager = StockAlertManager(notification_provider)
    
    # Test price alert
    print("Testing price alert notification...")
    success = alert_manager.send_price_alert(
        symbol="AAPL",
        current_price=150.25,
        alert_type="above",
        target_price=150.00
    )
    
    if success:
        print("✓ Price alert sent successfully!")
    else:
        print("✗ Failed to send price alert")

if __name__ == "__main__":
    test_notifications()
