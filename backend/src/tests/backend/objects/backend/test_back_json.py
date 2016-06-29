# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import unittest
import pytest
from json import loads, dumps
from gosa.backend.objects.backend.back_json import *

class JsonBackendTestCase(unittest.TestCase):

    @unittest.mock.patch.object(Environment, "getInstance")
    def test_no_path(self, mockedEnv):
        env = unittest.mock.MagicMock(autoSpec=True, create=True)
        env.config.get.side_effect = [None,'/tmp/unittest-back.json']
        mockedEnv.return_value = env
        with pytest.raises(BackendError):
            JSON()

        m = unittest.mock.mock_open()
        with unittest.mock.patch('gosa.backend.objects.backend.back_json.open', m, create=True):
            JSON()
            m.assert_called_once_with('/tmp/unittest-back.json', 'w')
            handle = m()
            handle.write.assert_called_once_with('{}')

    def test_load(self):
        json = {
            'uuid': {
                'obj1': {
                    'attr1':'val'
                },
                'obj2': {
                    'attr2': 'val'
                }
            }
        }
        m = unittest.mock.mock_open(read_data=dumps(json))
        with unittest.mock.patch('gosa.backend.objects.backend.back_json.open', m, create=True):
            back = JSON()
            res = back.load('uuid','info')
            assert res == {'attr1':'val','attr2':'val'}

    def test_identify(self):
        json = {
            'uuid1': {
                'obj1': {
                    'attr1': True,
                    'type': 'bool',
                    'dn': 'dn1'
                },
            },
            'uuid2': {
                'obj2': {
                    'attr2': 'val',
                    'type': 'str',
                    'dn': 'dn2'
                }
            }
        }
        m = unittest.mock.mock_open(read_data=dumps(json))
        with unittest.mock.patch('gosa.backend.objects.backend.back_json.open', m, create=True):
            back = JSON()
            assert back.identify('dn1',{'type':'bool'}) is True
            assert back.identify('dn1', {'type': 'str'}) is False

    def test_retract(self):
        json = {
            'uuid1': {
                'obj1': {
                    'attr1': 'val',
                },
                'obj2': {
                    'attr2': 'val',
                    'type': 'obj2',
                    'dn': 'dn2'
                }
            }
        }
        m = unittest.mock.mock_open(read_data=dumps(json))
        with unittest.mock.patch('gosa.backend.objects.backend.back_json.open', m, create=True):
            back = JSON()
            back.retract('uuid1', None, {'type': 'obj2'})
            handle = m()
            args, kwargs = handle.write.call_args_list[0]
            written = loads(args[0])
            assert written == {
                'uuid1': {
                    'obj1': {
                        'attr1': 'val',
                    }
                }
            }

    def test_extend(self):
        json = {
            'uuid1': {
                'obj1': {
                    'attr1': 'val',
                }
            }
        }
        m = unittest.mock.mock_open(read_data=dumps(json))
        with unittest.mock.patch('gosa.backend.objects.backend.back_json.open', m, create=True):
            back = JSON()
            back.extend('uuid1', {'attr2':{'value':'val'},'dn':{'value':'dn2'}}, {'type': 'obj2'},None)
            handle = m()
            args, kwargs = handle.write.call_args_list[0]
            written = loads(args[0])
            assert written == {
                'uuid1': {
                    'obj1': {
                        'attr1': 'val',
                    },
                    'obj2': {
                        'attr2': 'val',
                        'type': 'obj2',
                        'dn': 'dn2'
                    }
                }
            }
            assert handle.write.called

            m.reset_mock()

            # new uuid
            back.extend('uuid2', {'attr2': {'value': 'val'}, 'dn': {'value': 'dn2'}}, {'type': 'obj2'}, None)
            handle = m()
            args, kwargs = handle.write.call_args_list[0]
            written = loads(args[0])
            assert written == {
                'uuid1': {
                    'obj1': {
                        'attr1': 'val',
                    }
                },
                'uuid2': {
                    'obj2': {
                        'attr2': 'val',
                        'type': 'obj2',
                        'dn': 'dn2'
                    }
                }
            }

    def test_uuid2dn(self):
        json = {
            'uuid1': {
                'obj1': {
                    'attr1': 'val',
                },
                'obj2': {
                    'attr2': 'val',
                    'type': 'obj2',
                    'dn': 'dn2'
                }
            }
        }
        m = unittest.mock.mock_open(read_data=dumps(json))
        with unittest.mock.patch('gosa.backend.objects.backend.back_json.open', m, create=True):
            back = JSON()
            assert back.uuid2dn('uuid1') == "dn2"
            assert back.uuid2dn('uuid2') is None


    def test_query(self):
        json = {
            'uuid1': {
                'obj1': {
                    'attr1': 'val',
                    'parentDN':'OU=Sales,DC=Fabrikam,DC=COM',
                    'dn':'CN=Jeff Smith,OU=Sales,DC=Fabrikam,DC=COM'
                },
                'obj2': {
                    'attr2': 'val',
                    'type': 'obj2',
                    'parentDN':'OU=Sales,DC=Fabrikam,DC=COM',
                    'dn':'CN=Someone Else,OU=Sales,DC=Fabrikam,DC=COM'
                }
            }
        }
        m = unittest.mock.mock_open(read_data=dumps(json))
        with unittest.mock.patch('gosa.backend.objects.backend.back_json.open', m, create=True):
            back = JSON()
            found = back.query('OU=Sales,DC=Fabrikam,DC=COM',ldap.SCOPE_ONELEVEL,{})
            assert len(found) == 2
            assert 'CN=Jeff Smith,OU=Sales,DC=Fabrikam,DC=COM' in found
            assert 'CN=Someone Else,OU=Sales,DC=Fabrikam,DC=COM'in found

            found = back.query('CN=Jeff Smith,OU=Sales,DC=Fabrikam,DC=COM', ldap.SCOPE_BASE, {})
            assert len(found) == 1
            assert found[0] == 'CN=Jeff Smith,OU=Sales,DC=Fabrikam,DC=COM'

            found = back.query('DC=COM', ldap.SCOPE_SUBTREE, {})
            assert len(found) == 2
            assert 'CN=Jeff Smith,OU=Sales,DC=Fabrikam,DC=COM' in found
            assert 'CN=Someone Else,OU=Sales,DC=Fabrikam,DC=COM' in found

            found = back.query('DC=Fabrikam', ldap.SCOPE_SUBTREE, {})
            assert len(found) == 0

    def test_create(self):

        json = {
            'uuid1': {
                'obj2': {
                    'attr2': 'val',
                    'type': 'obj2',
                    'parentDN': 'OU=Sales,DC=Fabrikam,DC=COM',
                    'dn': 'CN=Someone Else,OU=Sales,DC=Fabrikam,DC=COM'
                }
            }
        }
        m = unittest.mock.mock_open(read_data=dumps(json))
        now = datetime.datetime(2016,1,1)


        with unittest.mock.patch('gosa.backend.objects.backend.back_json.open', m, create=True), \
             unittest.mock.patch.object(uuid,'uuid1', create=True, return_value='uuid2'), \
             unittest.mock.patch.object(datetime, "datetime", unittest.mock.Mock(wraps=datetime.datetime)) as mockedDt:
            mockedDt.now.return_value = now
            back = JSON()

            with pytest.raises(RDNNotSpecified):
                back.create("DC=COM",{'attr1':'val'},{})

            back.create("DC=COM",{
                'attr1': {
                    'value': ["val"]
                },
                'CN=Jeff Smith': {
                    "value": ['Test']
                },
                'DC=Fabrikam': {
                    "value": ['Test1']
                },
                'DC=COM': {
                    "value": ['Test2']
                },
                'OU=Sales':{
                    "value": ['Test2']
                }
            },{
                'rdn': 'CN=Jeff Smith,OU=Sales,DC=Fabrikam',
                'type':'obj1'
            })
            handle = m()
            args, kwargs = handle.write.call_args_list[0]

            written = loads(args[0])
            assert written == {
                'uuid1': {
                    'obj2': {
                        'attr2': 'val',
                        'type': 'obj2',
                        'parentDN': 'OU=Sales,DC=Fabrikam,DC=COM',
                        'dn': 'CN=Someone Else,OU=Sales,DC=Fabrikam,DC=COM'
                    }
                },
                'uuid2': {
                    'obj1': {
                        'attr1': ['val'],
                        'type': 'obj1',
                        'parentDN': 'DC=COM',
                        'dn': 'CN=Jeff Smith=Test,DC=COM',
                        'CN=Jeff Smith': ['Test'],
                        'DC=Fabrikam': ['Test1'],
                        'DC=COM': ['Test2'],
                        'OU=Sales': ['Test2'],
                        'createTimestamp': now.isoformat(),
                        'modifyTimestamp': now.isoformat()
                    }
                }
            }

            # not uniq dn free
            with pytest.raises(DNGeneratorError),unittest.mock.patch.object(back,"get_uniq_dn",return_value=None):
                back.create("DC=COM", {
                    'attr1': {
                        'value': ["val"]
                    },
                    'CN=Jeff Smith': {
                        "value": ['Test']
                    },
                    'DC=Fabrikam': {
                        "value": ['Test1']
                    },
                    'DC=COM': {
                        "value": ['Test2']
                    },
                    'OU=Sales': {
                        "value": ['Test2']
                    }
                }, {
                    'rdn': 'CN=Jeff Smith,OU=Sales,DC=Fabrikam',
                    'type': 'obj1'
                })

    def test_get_timestamps(self):
        create = datetime.datetime(2016, 1, 1, 0, 0, 0, 1)
        modify = datetime.datetime(2016, 1, 2, 0, 0, 0, 1)
        json = {
            'uuid1': {
                'obj2': {
                    'attr2': 'val',
                    'type': 'obj2',
                    'parentDN': 'OU=Sales,DC=Fabrikam,DC=COM',
                    'dn': 'CN=Someone Else,OU=Sales,DC=Fabrikam,DC=COM',
                    'createTimestamp': create.isoformat(),
                    'modifyTimestamp': modify.isoformat()
                }
            }
        }

        m = unittest.mock.mock_open(read_data=dumps(json))
        with unittest.mock.patch('gosa.backend.objects.backend.back_json.open', m, create=True):
            back = JSON()
            (ctime, mtime) = back.get_timestamps("CN=Someone Else,OU=Sales,DC=Fabrikam,DC=COM")
            assert ctime == create
            assert mtime == modify

    def test_get_uniq_id(self):
        json = {
            'uuid1': {
                'obj2': {
                    'attr2': 'val',
                    'type': 'obj2',
                    'parentDN': 'OU=Sales,DC=Fabrikam,DC=COM',
                    'dn': 'CN=Jeff Smith=Test,DC=COM'
                }
            }
        }

        m = unittest.mock.mock_open(read_data=dumps(json))
        with unittest.mock.patch('gosa.backend.objects.backend.back_json.open', m, create=True):
            back = JSON()
            assert back.get_uniq_dn(["CN=Jeff Smith"], "DC=COM", {'CN=Jeff Smith': {
                        "value": ['Test']
                    },
                    'DC=Fabrikam': {
                        "value": ['Test1']
                    },
                    'DC=COM': {
                        "value": ['Test2']
                    },
                    'OU=Sales': {
                        "value": ['Test2']
                    }}, None) is None

    def test_remove(self):
        json = {
            'uuid1': {
                'obj2': {
                    'attr2': 'val',
                    'type': 'obj2',
                    'parentDN': 'OU=Sales,DC=Fabrikam,DC=COM',
                    'dn': 'CN=Jeff Smith=Test,DC=COM'
                }
            }
        }

        m = unittest.mock.mock_open(read_data=dumps(json))
        with unittest.mock.patch('gosa.backend.objects.backend.back_json.open', m, create=True):
            back = JSON()
            assert back.remove("uuid1",None,None)
            handle = m()
            handle.write.assert_called_once_with("{}")
            assert not back.remove("uuid2", None, None)

    def test_exists(self):
        json = {
            'uuid1': {
                'obj2': {
                    'attr2': 'val',
                    'type': 'obj2',
                    'parentDN': 'OU=Sales,DC=Fabrikam,DC=COM',
                    'dn': 'CN=Jeff Smith=Test,DC=COM'
                }
            },
            'objects': {
                'uuid1': {
                    'test':'val'
                }
            }
        }

        m = unittest.mock.mock_open(read_data=dumps(json))
        with unittest.mock.patch('gosa.backend.objects.backend.back_json.open', m), \
             unittest.mock.patch('gosa.backend.objects.backend.back_json.is_uuid', side_effect = [False, True, True, False]) as muu:
            back = JSON()
            assert back.exists("CN=Jeff Smith=Test,DC=COM") is True
            assert back.exists("uuid1") is True
            assert back.exists("uuid2") is False
            assert back.exists("CN=Someone Else=Test,DC=COM") is False

    def test_is_uniq(self):
        json = {
            'uuid1': {
                'obj2': {
                    'attr2': 'val',
                    'type': 'obj2',
                    'parentDN': 'OU=Sales,DC=Fabrikam,DC=COM',
                    'dn': 'CN=Jeff Smith=Test,DC=COM'
                }
            },
            'objects': {
                'uuid1': {
                    'test': 'val'
                }
            }
        }

        with unittest.mock.patch('gosa.backend.objects.backend.back_json.open', unittest.mock.mock_open(read_data=dumps(json))):
            back = JSON()
            assert back.is_uniq("attr2","val", None) is False
            assert back.is_uniq("attr2","val1", None) is True
            assert back.is_uniq("attr1","val", None) is True

    def test_update(self):
        json = {
            'uuid1': {
                'obj2': {
                    'attr2': ['val'],
                    'type': 'obj2'
                }
            }
        }

        m = unittest.mock.mock_open(read_data=dumps(json))
        with unittest.mock.patch('gosa.backend.objects.backend.back_json.open',m):
            back = JSON()
            assert back.update("uuid1",{'attr2':{ "value": ["val2"] } }, {'type': 'obj2'}) is True
            handle = m()
            args, kwargs = handle.write.call_args_list[0]
            written = loads(args[0])
            assert written == {
                 'uuid1': {
                    'obj2': {
                        'attr2': ['val2'],
                        'type': 'obj2'
                    }
                }
            }

            m.reset_mock()
            assert back.update("uuid2", {'attr2': {"value": ["val2"]}}, {'type': 'obj2'}) is True
            handle = m()
            args, kwargs = handle.write.call_args_list[0]
            written = loads(args[0])
            assert written == {
                'uuid1': {
                    'obj2': {
                        'attr2': ['val'],
                        'type': 'obj2'
                    }
                },
                'uuid2': {
                    'obj2': {
                        'attr2': ['val2'],
                        'type': 'obj2'
                    }
                }
            }

    def test_move_extension(self):
        with unittest.mock.patch('gosa.backend.objects.backend.back_json.open', unittest.mock.mock_open(read_data='{}')):
            back = JSON()
            # just for the sake of completeness
            assert back.move_extension(None, None) is True

    def test_move(self):
        json = {
            'uuid1': {
                'obj2': {
                    'attr2': 'val',
                    'type': 'obj2',
                    'parentDN': 'DC=COM',
                    'dn': 'CN=Jeff Smith=Test,DC=COM'
                }
            },
            'uuid2': {
                'obj2': {
                    'attr2': 'val',
                    'type': 'obj2',
                    'parentDN': 'DC=NET',
                    'dn': 'CN=Jeff Smith=Test,DC=NET'
                }
            }
        }
        m = unittest.mock.mock_open(read_data=dumps(json))
        with unittest.mock.patch('gosa.backend.objects.backend.back_json.open',m):
            back = JSON()
            assert back.move("uuid1","DC=ORG") is True
            handle = m()
            args, kwargs = handle.write.call_args_list[0]
            written = loads(args[0])
            assert written == {
                'uuid1': {
                    'obj2': {
                        'attr2': 'val',
                        'type': 'obj2',
                        'parentDN': 'DC=ORG',
                        'dn': 'CN=Jeff Smith=Test,DC=ORG'
                    }
                },
                'uuid2': {
                    'obj2': {
                        'attr2': 'val',
                        'type': 'obj2',
                        'parentDN': 'DC=NET',
                        'dn': 'CN=Jeff Smith=Test,DC=NET'
                    }
                }
            }
            m.reset_mock()
            assert back.move("uuid3", "DC=ORG") is False

            with pytest.raises(BackendError):
                back.move("uuid1", "DC=NET")

