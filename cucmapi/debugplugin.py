"""Zeep SOAP Debugging Plugin.

This module provides a Zeep plugin for logging SOAP request and response messages
with pretty-printed XML formatting for debugging purposes.

Classes:
    MyLoggingPlugin: Plugin that logs SOAP messages during egress and ingress.
"""
from lxml import etree
from zeep import Plugin

class MyLoggingPlugin(Plugin):
    """
    Zeep plugin for logging SOAP request/response messages.
    
    Logs HTTP headers and XML body for both outgoing (egress) and
    incoming (ingress) SOAP messages with pretty-printed formatting.
    """

    def egress(self, envelope, http_headers, operation, binding_options):
        """
        Log outgoing SOAP request.
        
        Args:
            envelope: SOAP envelope being sent.
            http_headers: HTTP headers for the request.
            operation: SOAP operation being called.
            binding_options: Binding options for the operation.
        """

        # Format the request body as pretty printed XML
        xml = etree.tostring(envelope, pretty_print=True, encoding='unicode')

        print(
            f'\nRequest\n-------\nHeaders:\n{ http_headers }\n\nBody:\n{ xml }')

    def ingress(self, envelope, http_headers, operation):
        """
        Log incoming SOAP response.
        
        Args:
            envelope: SOAP envelope received.
            http_headers: HTTP headers from the response.
            operation: SOAP operation that was called.
        """

        # Format the response body as pretty printed XML
        xml = etree.tostring(envelope, pretty_print=True, encoding='unicode')

        print(
            f'\nResponse\n-------\nHeaders:\n{ http_headers }\n\nBody:\n{ xml }')
