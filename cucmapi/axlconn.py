"""CUCM AXL Connection Module.

This module provides connection management for Cisco CUCM AXL API
using the Zeep SOAP client with proper authentication and SSL handling.

Classes:
    ConnectionAXL: Manages SOAP client connection to CUCM AXL API.
"""
import os
import urllib3
from dotenv import load_dotenv
from requests import Session
from requests.auth import HTTPBasicAuth
from zeep import Client, Settings
from zeep.transports import Transport
from cucmapi.debugplugin import MyLoggingPlugin
from utils.logger import setup_logger

load_dotenv()

logger = setup_logger('axlconnection', 'log/axlconnection.log')

DEBUG = False
mode = "Dev"  # Change to "Dev" for development environment
if mode == "Dev":
    AXL_USERNAME = os.getenv("DEVAXL_USERNAME")
    AXL_PASSWORD = os.getenv("DEVAXL_PASSWORD")
    CUCM_ADDRESS = os.getenv("DEVCUCM_ADDRESS")
else:
    AXL_USERNAME = os.getenv("AXL_USERNAME")
    AXL_PASSWORD = os.getenv("AXL_PASSWORD")
    CUCM_ADDRESS = os.getenv("CUCM_ADDRESS")
class ConnectionAXL:
    """
    Manages a connection to Cisco CUCM AXL API using the Zeep SOAP client.

    Attributes:
        WSDL_FILE (str): Path to the AXL API WSDL file.
    """
    WSDL_FILE = 'axlsqltoolkit/schema/14.0/AXLAPI.wsdl'

    def __init__(self):
        """
        Initializes the HTTP session with CUCM credentials and disables SSL verification warnings.
        """
        self.session = Session()
        self.session.verify = False
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        self.session.auth = HTTPBasicAuth(
            AXL_USERNAME,
            AXL_PASSWORD
        )

        self._client = None
        self._service = None
        logger.info("Initialized AXL session")

    def _settransport(self):
        """
        Creates a Zeep Transport object with session and timeout configuration.

        Returns:
            Transport: Zeep transport instance for SOAP requests.

        Raises:
            RuntimeError: If transport creation fails.
        """
        try:
            transport = Transport(session=self.session, timeout=10)
            logger.debug("Zeep transport created successfully")
            return transport
        except Exception as e:
            logger.error("Error creating transport: %s", e)
            raise RuntimeError("Error creating transport: ") from e

    def _getsetting(self):
        """
        Returns Zeep client settings to allow large XML and relaxed validation.

        Returns:
            Settings: Zeep Settings instance.
        """
        return Settings(strict=False, xml_huge_tree=True)

    def _getplugin(self):
        """
        Returns Zeep logging plugin if debug mode is enabled.

        Returns:
            list: A list containing MyLoggingPlugin or empty list.
        """
        return [MyLoggingPlugin()] if DEBUG else []

    def _clientcreate(self):
        """
        Creates a Zeep SOAP client using WSDL, settings, transport, and plugins.

        Returns:
            Client: Zeep SOAP client instance.
        """
        if not self._client:
            logger.info("Creating Zeep client from WSDL")
            self._client = Client(
                wsdl=self.WSDL_FILE,
                settings=self._getsetting(),
                transport=self._settransport(),
                plugins=self._getplugin()
            )
            logger.debug("Zeep client created")
        return self._client

    def service(self):
        """
        Returns the AXL API service binding to perform API calls.

        Returns:
            ServiceProxy: Zeep service proxy to interact with AXL.
        """
        if not self._service:
            logger.info("Creating AXL service binding")
            client = self._clientcreate()
            self._service = client.create_service(
                '{http://www.cisco.com/AXLAPIService/}AXLAPIBinding',
                f'https://{CUCM_ADDRESS}:8443/axl/'
            )
            logger.debug("AXL service binding created")
        return self._service
