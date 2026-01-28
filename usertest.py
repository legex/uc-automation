"""LDAP User DID Retrieval Module.

This module provides functions to retrieve user details including DID numbers
from Active Directory via LDAP queries.

Functions:
    user_details: Fetch user contact and DID information from LDAP.
"""
import os
from dotenv import load_dotenv
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

load_dotenv("src/.env")
SERVER = os.getenv('LDAP_SERVER')
LDAP_USERNAME = os.getenv('LDAPUSER')
LDAP_PASSWORD = os.getenv('LDAPPASS')
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
		server = Server(SERVER, get_info=ALL)
		conn = Connection(server, user=LDAP_USERNAME, password=LDAP_PASSWORD, authentication=NTLM)
		server_uri = f'ldaps://{SERVER}'
		search_base = 'dc=corp,dc=akamai,dc=com'
		attrs = ['*']
		# Using ldap3
		server = ldap3.Server(server_uri)

		with ldap3.Connection(server,
							user=LDAP_USERNAME,
							password=LDAP_PASSWORD,
							authentication=NTLM) as conn:
			conn.search(search_base, f'(&(objectcategory=user)(samaccountname={userid})(!(|(userAccountControl=514)(employeeNumber=88888)(userAccountControl=66050))))',attributes=['sAMAccountName','employeeNumber','cn', 'givenName','telephonenumber','department','division','othertelephone','distinguishedname','objectguid','akaLegalLastName','akaLegalFirstName', 'co'])
					#=conn.search(search_base, '	(&(objectcategory=user)(employeenumber=*)(!(|(userAccountControl=514)(employeeNumber=88888)(userAccountControl=66050))))',attributes=['department'])
			for entry in range(len(conn.entries)):
					pprint(conn.entries[entry])
					json_data_emp = json.loads(conn.entries[entry].entry_to_json())
					telephone_num = json_data_emp.get('attributes', {}).get("telephoneNumber", [])
					othertelephone = json_data_emp.get('attributes', {}).get("AKA-phoneExtension", [])
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

def update_contacts_num_withDID(userid, internal_extension
								):
	"""
	Update LDAP contact information with both internal extension and external DID number.
	
	This function updates three LDAP attributes:
	- telephoneNumber: Set to the external_number
	- AKA-phoneExtension: Set to the internal_extension
	- otherTelephone: Cleared (set to empty)
	
	Args:
		userid (str): The sAMAccountName of the user in Active Directory.
		internal_extension (str): The internal phone extension number.
		external_number (str): The external/DID phone number.
	
	Returns:
		bool: True if update successful, False if an error occurs.
	
	Raises:
		ConnectionError: If LDAP connection fails.
		Exception: For other errors during the update process.
	"""
	try:
		server = Server(SERVER, get_info=ALL)
		conn = Connection(server, user=LDAP_USERNAME, password=LDAP_PASSWORD, authentication=NTLM)
		server_uri = f'ldaps://{SERVER}'
		search_base = 'dc=corp,dc=akamai,dc=com'
		attrs = ['*']
		# Using ldap3
		server = ldap3.Server(server_uri)

		with ldap3.Connection(server,
							user=LDAP_USERNAME,
							password=LDAP_PASSWORD,
							authentication=NTLM) as conn:
		#use a outpout to confirm if a user exists
			a=conn.search(search_base, f'(&(objectcategory=user)(samaccountname={userid})(!(|(userAccountControl=514)(employeeNumber=88888)(userAccountControl=66050))))',attributes=['sAMAccountName','employeeNumber','cn', 'givenName','telephonenumber','department','division','othertelephone','distinguishedname','objectguid','akaLegalLastName','akaLegalFirstName'])
					#=conn.search(search_base, '	(&(objectcategory=user)(employeenumber=*)(!(|(userAccountControl=514)(employeeNumber=88888)(userAccountControl=66050))))',attributes=['department'])
			pprint(conn.entries)
			a=conn.entries[0]		
			#print('ldap_writer_telephonefield try block')


			user_id =a.sAMAccountName[0]
			dnc= a.distinguishedName[0]
			employee_badge_number= a.employeeNumber[0]
			conn.bind()
			conn.modify(dnc,{'telephoneNumber': [(ldap3.MODIFY_REPLACE, [])]})
			conn.modify(dnc,{'AKA-phoneExtension': [(ldap3.MODIFY_REPLACE, [internal_extension])]})
			conn.modify(dnc,{'otherTelephone': [(ldap3.MODIFY_REPLACE, [])]})
			conn.unbind()
			return True
	except ConnectionError as er:
		print(f'Error encountered as {er}')
		return False
	except Exception as e:
		print(f"Error encountered: {e}")
		return False

update_contacts_num_withDID("ytange", "5551132011")
print(user_details("ytange"))