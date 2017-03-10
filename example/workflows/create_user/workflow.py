# example for 'data'
# {
#   'mail': ['foo@bar.com', 'bar@foo.com'],
#   'sn': 'Doe',
#   'cn': None,
#   'homePhone': '123',
#   'parentDn': 'dc=example,dc=net',
#   'uid': 'Doe-J',
#   'givenName': 'John'
# }

# extract target location
parent_dn = data['parentDn']
del data['parentDn']

# create object
obj = openObject('object', parent_dn, 'User')
ref_uuid = obj['__jsonclass__'][1][1]
print(1)
dispatchObjectMethod(ref_uuid, 'extend', 'ZarafaAccount')
print(2)

data['zarafaResourceType'] = "0"

for attr_name, value in data.items():
    print('setting', attr_name, value)
    setObjectProperty(ref_uuid, attr_name, value)

print(3)
dispatchObjectMethod(ref_uuid, 'commit')
