"""LDAP User DID Retrieval Module.

This module provides functions to retrieve user details including DID numbers
from Active Directory via LDAP queries.

Functions:
    user_details: Fetch user contact and DID information from LDAP.
"""
import ldap3
from pprint import pprint
from ldap3 import (Server,
				   Connection,
				   ALL,
				   NTLM,
				   )
from requests import Session
from requests.auth import HTTPBasicAuth
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning
import json
from appdatainternal.config import get_ldap_creds

ldap_creds = get_ldap_creds()
ADSERVER = ldap_creds["SERVER"]
ADLDAP_USERNAME = ldap_creds["LDAP_USERNAME"]
ADLDAP_PASSWORD = ldap_creds["LDAP_PASSWORD"]
def user_details(userid):
	"""
	Retrieve detailed user information from Active Directory.
	
	Queries LDAP for user details including name, email, phone numbers,
	employee ID, and country.
	
	Args:
		userid (str): The sAMAccountName of the user to query.
	
	Returns:
		dict: Dictionary containing user details with keys:
			- Name: Full name
			- Email: Email address
			- UserId: sAMAccountName
			- Emp_ID: Employee number
			- Country: Country code
			- extension: Extension/other telephone number
			- DID: Main telephone number
	
	Raises:
		ConnectionError: If LDAP connection fails.
	"""
	try:
		server = Server(ADSERVER, get_info=ALL)
		conn = Connection(server, user=ADLDAP_USERNAME, password=ADLDAP_PASSWORD, authentication=NTLM)
		server_uri = f'ldaps://{ADSERVER}'
		search_base = 'dc=corp,dc=akamai,dc=com'
		attrs = ['*']
		# Using ldap3
		server = ldap3.Server(server_uri)

		with ldap3.Connection(server,
							user=ADLDAP_USERNAME,
							password=ADLDAP_PASSWORD,
							authentication=NTLM) as conn:
			conn.search(search_base, f'(&(objectcategory=user)(samaccountname={userid})(!(|(userAccountControl=514)(employeeNumber=88888)(userAccountControl=66050))))',attributes=['sAMAccountName','employeeNumber','cn', 'givenName','telephonenumber','department','division','othertelephone','distinguishedname','objectguid','akaLegalLastName','akaLegalFirstName', 'co'])
					#=conn.search(search_base, '	(&(objectcategory=user)(employeenumber=*)(!(|(userAccountControl=514)(employeeNumber=88888)(userAccountControl=66050))))',attributes=['department'])
			for entry in range(len(conn.entries)):
					json_data_emp = json.loads(conn.entries[entry].entry_to_json())
					telephone_num = json_data_emp.get('attributes', {}).get("telephoneNumber", [])
					othertelephone = json_data_emp.get('attributes', {}).get("otherTelephone", [])
					dict_emp = {}
					dict_emp.update({"Name": json_data_emp['attributes']["cn"][0]})
					dict_emp.update({"Email": json_data_emp['attributes']["sAMAccountName"][0]+"@akamai.com"})
					dict_emp.update({"UserId": json_data_emp['attributes']["sAMAccountName"][0]})
					dict_emp.update({"Emp_ID": json_data_emp['attributes']["employeeNumber"][0]})
					dict_emp.update({"Country": json_data_emp['attributes']["co"][0]})
					if othertelephone:
						extension = othertelephone[0].strip("\t\\")
					else:
						extension = ''
					if telephone_num:
						contact = telephone_num[0].strip("\t\\")
					else:
						contact = ''
					dict_emp.update({"ContactNumber": contact })
					dict_emp.update({"Extension": extension})
					return dict_emp
	except ConnectionError as er:
		print(f'Error encountered as {er}')
