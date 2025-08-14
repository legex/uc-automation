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

load_dotenv()
SERVER = os.getenv('LDAP_SERVER')
LDAP_USERNAME = os.getenv('LDAPUSER')
LDAP_PASSWORD = os.getenv('LDAPPASS')
def update_contacts_num(userid, internal_extension):
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
			conn.modify(dnc,{'telephoneNumber': [(ldap3.MODIFY_REPLACE, [internal_extension])]})
			conn.unbind()
			return True
	except ConnectionError as er:
		print(f'Error encountered as {er}')
		return False
	except Exception as e:
		print(f"Error encountered: {e}")
		return False
