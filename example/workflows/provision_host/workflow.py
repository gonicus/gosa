
# extract target location
parent_dn = data['parentDn']
del data['parentDn']
move = False

if reference_object is None:
    # create object
    if parent_dn is None:
        raise Exception("no parent dn defined")
    obj = openObject('object', parent_dn, 'Device')
else:
    # open existing object
    obj = openObject('object', reference_object.dn)
    if parent_dn is not None and not reference_object.dn.endswith(parent_dn):
        # TODO this check is not reliable
        move = True

ref_uuid = obj['__jsonclass__'][1][1]

if not dispatchObjectMethod(ref_uuid, 'is_extended_by', 'ForemanHost'):
    dispatchObjectMethod(ref_uuid, 'extend', 'ForemanHost')

if 'mac' in data and data['mac'] is not None:
    if not dispatchObjectMethod(ref_uuid, 'is_extended_by', 'ieee802Device'):
        dispatchObjectMethod(ref_uuid, 'extend', 'ieee802Device')
    data['macAddress'] = data['mac']
    del data['mac']

if 'ip' in data and data['ip'] is not None:
    if not dispatchObjectMethod(ref_uuid, 'is_extended_by', 'IpHost'):
        dispatchObjectMethod(ref_uuid, 'extend', 'IpHost')
    data['ipHostNumber'] = data['ip']
    del data['ip']

# create cn from hostname+domain
# domains = getForemanDomains()
# retrieve the discovered_host id and store it
# id = getForemanDiscoveredHostId(obj.cn)
# cn = data["cn"]
#
# # remove all domain parts from cn
# for domain_id, domain in domains.items():
#     if cn.endswith(domain["value"]):
#         cn = cn[0:-(len(domain["value"])+1)]
#
# # now append the selected domain to the cn
# cn = "%s.%s" % (data["cn"], domains[data["domain_id"]]["value"])
# setObjectProperty(ref_uuid, "cn", cn)
# del data["cn"]
del data["domain_id"]

for attr_name, value in data.items():
    print('setting', attr_name, value)
    setObjectProperty(ref_uuid, attr_name, value)

if move:
    print("moving to %s" % parent_dn)
    dispatchObjectMethod(ref_uuid, 'move', parent_dn)

dispatchObjectMethod(ref_uuid, 'commit')
