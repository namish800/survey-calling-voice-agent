# universalagent/events/webhook_client.py
"""
Simple webhook client for sending events.
"""

import logging
import aiohttp
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class WebhookClient:
    """Simple client for sending data to webhook endpoints."""
    
    def __init__(self, webhook_url: str, headers: Optional[Dict[str, str]] = None):
        """Initialize webhook client.
        
        Args:
            webhook_url: URL to send data to
            headers: Optional HTTP headers
        """
        self.webhook_url = webhook_url
        self.headers = headers or {'Content-Type': 'application/json'}
        connector = aiohttp.TCPConnector(force_close=True)
        self._session = aiohttp.ClientSession(connector=connector)
    
    async def send_payload(self, payload: Dict[str, Any]) -> bool:
        """Send payload to webhook.
        
        Args:
            payload: Data to send
            
        Returns:
            True if successful, False otherwise
        """
        try:
            async with self._session.post(
                self.webhook_url,
                headers=self.headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    logger.info(f"Successfully sent data to webhook")
                    return True
                else:
                    logger.error(f"Failed to send data. Status: {response.status}, Response: {await response.text()}")
                    return False
        except Exception as e:
            logger.error(f"Error sending data to webhook: {e}")
            return False
    
    async def aclose(self) -> None:
        """Close the underlying ClientSession."""
        if not self._session.closed:
            await self._session.close()