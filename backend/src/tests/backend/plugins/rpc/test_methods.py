import unittest
from gosa.backend.plugins.rpc.methods import *

class RpcMethodsTestCase(unittest.TestCase):

    def setUp(self):
        self.rpc = RPCMethods()

