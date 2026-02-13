"""Webex Base Module.

This module provides the base class for Webex API operations, handling
authentication and common HTTP header construction.

Classes:
    WebexBase: Abstract base class providing authentication headers for Webex API calls.
"""
import os
import json
import requests
from abc import ABC
from requests import HTTPError
from dotenv import load_dotenv
from appdatainternal.config import get_webex_token
from utils.logger import setup_logger

# Load environment variables from .env file
load_dotenv()

# Initialize logger
logger = setup_logger('webexbaseheader', '/a/logs/webexbaseheader.log')
class WebexBase(ABC):
    def __init__(self):
        self.AUTH_TOKEN = get_webex_token()
        if not self.AUTH_TOKEN:
            raise RuntimeError("Webex API token could not be retrieved")

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
