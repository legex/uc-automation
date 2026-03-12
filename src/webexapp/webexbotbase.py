"""Webex Bot Base Module.

This module provides the base class for Webex Bot operations,
handling authentication and message sending capabilities.

Classes:
    WebexbotBase: Abstract base class for Webex Bot API interactions.
"""
import os
from io import BytesIO
import json
import requests
from abc import ABC
from requests import HTTPError
from requests_toolbelt.multipart.encoder import MultipartEncoder
from dotenv import load_dotenv
from appdatainternal.config import get_webex_token
from utils.logger import setup_logger

# Load environment variables from .env file
load_dotenv()

# Initialize logger
logger = setup_logger('webexcalls', '/a/logs/webexcalls.log')

# Read API token from environment
AUTH_TOKEN = get_webex_token()
if not AUTH_TOKEN:
    raise RuntimeError("AUTHTOKEN environment variable must be set")

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

    def send_message_with_attachment(self, useremail: str, filename: str, message: str, csv_text: str) -> None:
        """
        Send a message with an attachment to a specified Webex room.

        Args:
            useremail (str): The email of the Webex user.
            filename (str): The name of the file to attach.
            message (str): The message content to send.
            csv_text (str): The CSV content to attach as a file.

        Raises:
            HTTPError: If the HTTP request to send the message fails.
        """
        url = "https://webexapis.com/v1/messages"
        multipartdata = MultipartEncoder({'toPersonEmail': useremail,
                      'text': message,
                      'files': (f"result_{filename}", BytesIO(csv_text.encode("utf-8")),
                      'text/csv')})
        headers = self.build_headers()
        headers['Content-Type'] = multipartdata.content_type

        response = requests.post(url, headers=headers, data=multipartdata, timeout=30)

        try:
            response.raise_for_status()
            logger.info("Message sent to user %s: %s", useremail, message)
        except HTTPError as http_err:
            logger.error("HTTP error occurred while sending message: %s", http_err)
            raise
