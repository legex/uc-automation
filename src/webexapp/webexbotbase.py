"""Webex Bot Base Module.

This module provides the base class for Webex Bot operations,
handling authentication and message sending capabilities.

Classes:
    WebexbotBase: Abstract base class for Webex Bot API interactions.
"""
import os
import json
import requests
from abc import ABC
from requests import HTTPError
from dotenv import load_dotenv
from src.utils.logger import setup_logger

# Load environment variables from .env file
load_dotenv()

# Initialize logger
logger = setup_logger('webexcalls', '/a/logs/webexcalls.log')

# Read API token from environment
AUTH_TOKEN = os.getenv('WEBEXBOTTOKEN')
if not AUTH_TOKEN:
    raise RuntimeError("WEBEXBOTTOKEN environment variable must be set")

class WebexbotBase(ABC):
    def __init__(self):
        self.AUTH_TOKEN = AUTH_TOKEN

    def build_headers(self) -> dict:
        """
        Build authorization and content headers for Webex API calls.

        Returns:
            dict: HTTP headers containing:
                - Authorization: Bearer token fetched from AUTHTOKEN env var.
                - Content-Type: application/json
                - Accept: application/json

        Raises:
            RuntimeError: If AUTHTOKEN is not set in the environment.
        """
        return {
            "Authorization": f"Bearer {self.AUTH_TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def send_message(self, roomId: str, message: str) -> None:
        """
        Send a message to a specified Webex room.

        Args:
            roomId (str): The ID of the Webex room.
            message (str): The message content to send.

        Raises:
            HTTPError: If the HTTP request to send the message fails.
        """
        url = "https://webexapis.com/v1/messages"
        payload = {
            "roomId": roomId,
            "text": message
        }
        headers = self.build_headers()

        response = requests.post(url, headers=headers, json=payload, timeout=30)

        try:
            response.raise_for_status()
            logger.info("Message sent to room %s: %s", roomId, message)
        except HTTPError as http_err:
            logger.error("HTTP error occurred while sending message: %s", http_err)
            raise
