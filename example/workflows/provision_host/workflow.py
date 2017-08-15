
# extract target location
parent_dn = data['parentDn']
del data['parentDn']
move = False
move_successful = False

if reference_object is None:
    # create object
    if parent_dn is None:
        raise Exception("no parent dn defined")
    obj = openObject('object', parent_dn, 'Device')
    ref_uuid = obj['__jsonclass__'][1][1]
else:
    # open existing object
    obj = openObject('object', reference_object.dn)
    ref_uuid = obj['__jsonclass__'][1][1]

    if parent_dn is not None and dispatchObjectMethod(ref_uuid, "get_parent_dn") != parent_dn:
        move = True

if move:
    log.info("moving to %s" % parent_dn)
    move_successful = dispatchObjectMethod(ref_uuid, 'move', parent_dn)

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

# # change the cn (aka hostname) here to make it identifiable when foreman requests the OTP
domains = getForemanDomains()

if data['domain_id'] in domains:
    cn = "%s.%s" % (data['cn'], domains[data['domain_id']]['value'])
    setObjectProperty(ref_uuid, "cn", cn)
    log.info("hostname changed to '%s'" % cn)
    del data['cn']

for attr_name, value in data.items():
    setObjectProperty(ref_uuid, attr_name, value)

dispatchObjectMethod(ref_uuid, 'commit')
