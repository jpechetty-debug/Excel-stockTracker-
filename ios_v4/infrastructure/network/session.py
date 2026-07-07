"""
Session Manager
Implements a reusable HTTP Session singleton to drastically improve performance.
"""

import requests
from typing import Optional
from infrastructure.logging.logger import logger


class SessionManager:
    """Manages a globally reusable requests Session."""
    
    _instance: Optional['SessionManager'] = None
    
    def __new__(cls) -> 'SessionManager':
        if cls._instance is None:
            cls._instance = super(SessionManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self) -> None:
        """Initializes the requests session."""
        self.session = requests.Session()
        
        # Add a default generic User-Agent since financial APIs often block default python-requests
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) IOS_v4.0"
        })
        logger.info("HTTP SessionManager initialized.")

    def get_session(self) -> requests.Session:
        """Returns the shared requests session."""
        return self.session

    def close(self) -> None:
        """Closes the active session."""
        if self.session:
            self.session.close()
            logger.info("HTTP SessionManager closed.")
