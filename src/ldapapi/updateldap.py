"""
LDAP Contact Number Update Module.

This module provides functions to update user contact information in Active Directory
via LDAP. It supports updating internal extensions, external DID numbers, and various
combinations for both general and ACD (Automatic Call Distribution) users.

Environment Variables Required:
    LDAP_SERVER: The LDAP server hostname
    LDAPUSER: LDAP username for authentication
    LDAPPASS: LDAP password for authentication
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
from appdatainternal.config import get_ldap_creds

ldap_creds = get_ldap_creds()
ADSERVER = ldap_creds["SERVER"]
ADLDAP_USERNAME = ldap_creds["LDAP_USERNAME"]
ADLDAP_PASSWORD = ldap_creds["LDAP_PASSWORD"]
def update_contacts_num_withDID(userid, internal_extension,
								external_number
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
			if external_number:
				conn.modify(dnc,{'telephoneNumber': [(ldap3.MODIFY_REPLACE, [external_number])]})
			else:
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


def update_contacts_num(userid, internal_extension):
	"""
	Update LDAP contact with internal extension only.
	
	This function updates the telephoneNumber LDAP attribute with the
	provided internal extension.
	
	Args:
		userid (str): The sAMAccountName of the user in Active Directory.
		internal_extension (str): The internal phone extension number.
	
	Returns:
		bool: True if update successful, False if an error occurs.
	
	Raises:
		ConnectionError: If LDAP connection fails.
		Exception: For other errors during the update process.
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
			conn.modify(dnc,{'telephoneNumber': [(ldap3.MODIFY_REPLACE, [internal_extension])]})
			conn.modify(dnc,{'AKA-phoneExtension': [(ldap3.MODIFY_REPLACE, [])]})
			conn.modify(dnc,{'otherTelephone': [(ldap3.MODIFY_REPLACE, [])]})
			conn.unbind()
			return True
	except ConnectionError as er:
		print(f'Error encountered as {er}')
		return False
	except Exception as e:
		print(f"Error encountered: {e}")
		return False
	
def update_acdcontacts_num(userid, internal_extension):
	"""
	Update LDAP ACD contact with internal extension.
	
	This function updates the AKA-phoneExtension LDAP attribute with the
	provided internal extension for ACD (Automatic Call Distribution) users.
	
	Args:
		userid (str): The sAMAccountName of the user in Active Directory.
		internal_extension (str): The internal phone extension number.
	
	Returns:
		bool: True if update successful, False if an error occurs.
	
	Raises:
		ConnectionError: If LDAP connection fails.
		Exception: For other errors during the update process.
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
			conn.modify(dnc,{'AKA-phoneExtension': [(ldap3.MODIFY_REPLACE, [internal_extension])]})
			conn.unbind()
			return True
	except ConnectionError as er:
		print(f'Error encountered as {er}')
		return False
	except Exception as e:
		print(f"Error encountered: {e}")
		return False
	
def update_general_contacts_num_withDID(userid,external_number, internal_extension):
	"""
	Update LDAP general contact with extension and external number.
	
	This function updates three LDAP attributes for general users:
	- telephoneNumber: Set to the internal_extension
	- AKA-phoneExtension: Cleared (set to empty)
	- otherTelephone: Set to the external_number
	
	Args:
		userid (str): The sAMAccountName of the user in Active Directory.
		external_number (str): The external/DID phone number.
		internal_extension (str): The internal phone extension number.
	
	Returns:
		bool: True if update successful, False if an error occurs.
	
	Raises:
		ConnectionError: If LDAP connection fails.
		Exception: For other errors during the update process.
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
			conn.modify(dnc,{'telephoneNumber': [(ldap3.MODIFY_REPLACE, [internal_extension])]})
			conn.modify(dnc,{'AKA-phoneExtension': [(ldap3.MODIFY_REPLACE, [])]})
			conn.modify(dnc,{'otherTelephone': [(ldap3.MODIFY_REPLACE, [external_number])]})
			conn.unbind()
			return True
	except ConnectionError as er:
		print(f'Error encountered as {er}')
		return False
	except Exception as e:
		print(f"Error encountered: {e}")
		return False
	

def update_general_contacts_num_with_multiple_DID(userid,external_number, internal_extension, other_external_number):
	"""
	Update LDAP general contact with extension and external number.
	
	This function updates three LDAP attributes for general users:
	- telephoneNumber: Set to the internal_extension
	- AKA-phoneExtension: Cleared (set to empty)
	- otherTelephone: Set to the external_number
	
	Args:
		userid (str): The sAMAccountName of the user in Active Directory.
		external_number (str): The external/DID phone number.
		internal_extension (str): The internal phone extension number.
	
	Returns:
		bool: True if update successful, False if an error occurs.
	
	Raises:
		ConnectionError: If LDAP connection fails.
		Exception: For other errors during the update process.
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
			conn.modify(dnc,{'telephoneNumber': [(ldap3.MODIFY_REPLACE, [external_number])]})
			conn.modify(dnc,{'AKA-phoneExtension': [(ldap3.MODIFY_REPLACE, [internal_extension])]})
			conn.modify(dnc,{'otherTelephone': [(ldap3.MODIFY_REPLACE, [other_external_number])]})
			conn.unbind()
			return True
	except ConnectionError as er:
		print(f'Error encountered as {er}')
		return False
	except Exception as e:
		print(f"Error encountered: {e}")
		return False
