from lxml import etree
from zeep import Plugin

class MyLoggingPlugin(Plugin):

    def egress(self, envelope, http_headers, operation, binding_options):

        # Format the request body as pretty printed XML
        xml = etree.tostring(envelope, pretty_print=True, encoding='unicode')

        print(
            f'\nRequest\n-------\nHeaders:\n{ http_headers }\n\nBody:\n{ xml }')

    def ingress(self, envelope, http_headers, operation):

        # Format the response body as pretty printed XML
        xml = etree.tostring(envelope, pretty_print=True, encoding='unicode')

        print(
            f'\nResponse\n-------\nHeaders:\n{ http_headers }\n\nBody:\n{ xml }')
