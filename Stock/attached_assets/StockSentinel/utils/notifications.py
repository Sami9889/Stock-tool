"""
Simple notification system for stock alerts
Copyright © 2025 Sami Singh. All rights reserved.
"""
from abc import ABC, abstractmethod
from typing import Optional
import logging
from datetime import datetime
import desktop_notifier
import asyncio

# Configure logging with more details
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NotificationProvider(ABC):
    """Abstract base class for notification providers"""

    @abstractmethod
    def send_notification(self, message: str) -> bool:
        """Send a notification message"""
        pass

class SystemNotification(NotificationProvider):
    """System notification provider using native desktop notifications"""

    def __init__(self):
        """Initialize the desktop notifier with error handling"""
        try:
            self.notifier = desktop_notifier.DesktopNotifier()
            logger.info("Desktop notifier initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize desktop notifier: {str(e)}")
            self.notifier = None

    def send_notification(self, message: str) -> bool:
        """Send system notification with fallback"""
        if not self.notifier:
            logger.error("Desktop notifier not initialized, falling back to console")
            return self._fallback_notification(message)

        try:
            # Send notification using desktop-notifier
            self.notifier.send_sync(
                title="Stock Alert",
                message=message,
                urgency=desktop_notifier.Urgency.Critical
            )
            logger.info(f"System notification sent: {message}")
            return True
        except Exception as e:
            logger.error(f"Failed to send system notification: {str(e)}")
            return self._fallback_notification(message)

    def _fallback_notification(self, message: str) -> bool:
        """Fallback to console notification if desktop notification fails"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] ALERT: {message}")
            logger.info("Fallback notification sent to console")
            return True
        except Exception as e:
            logger.error(f"Fallback notification failed: {str(e)}")
            return False

class StockAlertManager:
    """Manages stock price alerts and notifications"""

    def __init__(self, notification_provider: NotificationProvider):
        self.notification_provider = notification_provider
        logger.info("StockAlertManager initialized")

    def send_price_alert(self, symbol: str, current_price: float, 
                        alert_type: str, target_price: Optional[float] = None) -> bool:
        """
        Send a price alert notification

        Args:
            symbol: Stock symbol
            current_price: Current stock price
            alert_type: Type of alert ('above' or 'below')
            target_price: Optional target price that triggered the alert
        """
        try:
            logger.info(f"Preparing price alert for {symbol}")
            message = f"Stock Alert: {symbol} is at ${current_price:.2f}"
            if target_price:
                message += f"\nTarget: ${target_price:.2f}"
                message += f"\nPrice is now {alert_type} target!"

            success = self.notification_provider.send_notification(message)
            if success:
                logger.info("Price alert sent successfully")
            else:
                logger.error("Failed to send price alert")
            return success

        except Exception as e:
            logger.error(f"Error sending price alert: {str(e)}")
            return False