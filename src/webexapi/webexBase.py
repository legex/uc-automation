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
from utils.logger import setup_logger

# Load environment variables from .env file
load_dotenv()

# Initialize logger
logger = setup_logger('webexbaseheader', '/a/logs/webexbaseheader.log')
tokenfile = "/a/secrets/app/webex_token/webex_token.opaque"
# Read API token from environment
mode = "Prod"
# if mode == "Prod":
#     AUTH_TOKEN = os.getenv('AUTHTOKEN')
# else:
#     AUTH_TOKEN = os.getenv('AUTHTOKEN_DEV')
# if not AUTH_TOKEN:
#     raise RuntimeError("AUTHTOKEN environment variable must be set")

class WebexBase(ABC):
    def __init__(self):
        self.AUTH_TOKEN = self.get_token()
        if not self.AUTH_TOKEN:
            raise RuntimeError("Webex API token could not be retrieved")

    def get_token(self) -> str:
        """
        Retrieve the Webex API token.

        Returns:
            str: The Webex API token.
        """
        with open(tokenfile, 'r') as tf:
            token = tf.read().strip()
            print("Read Webex token from file")
        return token

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
