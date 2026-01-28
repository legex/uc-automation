import os
from dotenv import load_dotenv
import ldap3
from pprint import pprint
import ldap3
from ldap3 import (Server,
				   Connection,
				   ALL,
				   NTLM,
				   )
from requests import Session
from requests.auth import HTTPBasicAuth
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning
import pandas as pd
import json

load_dotenv()
SERVER = os.getenv('LDAP_SERVER')
LDAP_USERNAME = os.getenv('LDAPUSER')
LDAP_PASSWORD = os.getenv('LDAPPASS')
def get_employee_data_countrywise(country):
	try:
		server = Server(SERVER, get_info=ALL)
		conn = Connection(server, user=LDAP_USERNAME, password=LDAP_PASSWORD, authentication=NTLM)
		server_uri = f'ldaps://{SERVER}'
		search_base = 'dc=corp,dc=akamai,dc=com'
		attrs = ['*']
		emp=[]
		# Using ldap3
		server = ldap3.Server(server_uri)

		with ldap3.Connection(server,
							user=LDAP_USERNAME,
							password=LDAP_PASSWORD,
							authentication=NTLM) as conn:
		#use a outpout to confirm if a user exists
			#a=conn.search(search_base, f'(&(|(location={userid}))(!(|(userAccountControl=514)(employeeNumber=88888)(userAccountControl=66050))))',attributes=['sAMAccountName','employeeNumber','cn', 'givenName','telephonenumber','department','division','othertelephone','distinguishedname','objectguid','akaLegalLastName','akaLegalFirstName','location'])
			conn.search(search_base, f'(&(objectcategory=user)(co=*{country}*)(!(|(userAccountControl=514)(employeeNumber=88888)(userAccountControl=66050))))',attributes=['sAMAccountName','employeeNumber','cn','telephoneNumber','department','division','othertelephone','location'])
			try:	
				for entry in range(len(conn.entries)):
					json_data_emp = json.loads(conn.entries[entry].entry_to_json())
					telephone_num = json_data_emp.get('attributes', {}).get("telephoneNumber", [])
					dict_emp = {}
					dict_emp.update({"Name": json_data_emp['attributes']["cn"][0]})
					dict_emp.update({"Email": json_data_emp['attributes']["sAMAccountName"][0]+"@akamai.com"})
					dict_emp.update({"UserId": json_data_emp['attributes']["sAMAccountName"][0]})
					dict_emp.update({"Emp_ID": json_data_emp['attributes']["employeeNumber"][0]})
					dict_emp.update({"Region": json_data_emp['attributes']["location"][0]})
					if telephone_num:
						contact = telephone_num[0].strip("\t")
					else:
						contact = ''
					dict_emp.update({"ContactNumber": contact })
					emp.append(dict_emp)
					print(dict_emp)

				df = pd.DataFrame(emp)
				df.to_csv(f'{country}_postwebex.csv',index=False)
				return emp

			except Exception as e:
				print("Error raised: ", e)

	except ConnectionError as er:
		print(f'Error encountered as {er}')
if __name__== "__main__":
	employee_list = get_employee_data_countrywise("Denmark")
