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
from appdatainternal.config import get_cucm_credentials, cucm_servers
from appdatainternal.environment import get_env_config
env = get_env_config()
load_dotenv()

axl_creds = get_cucm_credentials()
CUCM_ADDRESSES = cucm_servers()
logger = setup_logger('axlconnection', '/a/logs/axlconnection.log')
DEBUG = False
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
            axl_creds["AXL_USERNAME"],
            axl_creds["AXL_PASSWORD"]
        )

        self._client = None
        self._service = None
        logger.info("Initialized AXL session")

    def getcredentials(self):
        """
        Returns the CUCM AXL credentials.

        Returns:
            tuple: A tuple containing (username, password).
        """
        passfile = "/a/secrets/app/cucm_user/cucm_user.opaque"
        with open(passfile, 'r') as pf:
            axlpass = pf.read().strip()
            print("Read password from file")
        return axlpass

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

    def service(self, is_india=False):
        """
        Returns the AXL API service binding to perform API calls.
        
        Note: This creates a new service binding each time to ensure the correct
        CUCM endpoint (US or India) is used based on the is_india parameter.
        Services are lightweight and the overhead is minimal compared to
        maintaining region-specific cached instances.

        Args:
            is_india (bool): If True, connect to India CUCM; otherwise US CUCM.

        Returns:
            ServiceProxy: Zeep service proxy to interact with AXL.
        """
        if is_india:
            logger.info("Creating AXL service binding for India CUCM")
            ucm_address = CUCM_ADDRESSES["india"]
        else:
            logger.info("Creating AXL service binding for US CUCM")
            ucm_address = CUCM_ADDRESSES["us"]
        
        client = self._clientcreate()
        service = client.create_service(
            '{http://www.cisco.com/AXLAPIService/}AXLAPIBinding',
            f'https://{ucm_address}:8443/axl/'
        )
        logger.debug("AXL service binding created for %s", ucm_address)
        return service
