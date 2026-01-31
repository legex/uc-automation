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
from src.utils.logger import setup_logger

# Load environment variables from .env file
load_dotenv()

# Initialize logger
logger = setup_logger('webexbaseheader', 'temp/a/logs/webexbaseheader.log')

# Read API token from environment
mode = "Prod"
if mode == "Prod":
    AUTH_TOKEN = os.getenv('AUTHTOKEN')
else:
    AUTH_TOKEN = os.getenv('AUTHTOKEN_DEV')
if not AUTH_TOKEN:
    raise RuntimeError("AUTHTOKEN environment variable must be set")

class WebexBase(ABC):
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
