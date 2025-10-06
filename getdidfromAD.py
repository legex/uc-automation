from ldapapi.getuserdid import user_details
import pandas as pd


users = pd.read_csv("userlist.csv")
emp = []

#print(user_details("abshukla"))
for i, row in users.iterrows():
    username = row["users"]
    print(f"Working for {username}, iteration {i}")
    user_dict = user_details(username)
    emp.append(user_dict)

df = pd.DataFrame(emp)
df.to_excel('linodeusers.xlsx',index=False)