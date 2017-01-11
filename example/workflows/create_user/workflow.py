given_name = data["givenName"].lower()
surname = data["sn"].lower()

test = dict(cn="%s %s" % (data["givenName"], data["sn"]), uid="%s_%s" % (given_name, surname), mail="%s.%s@eyjafjallajökull.is" % (given_name, surname))

print("---------------------------------------------")
print(data)
print(test)
print(getWorkflows())
print("---------------------------------------------")
