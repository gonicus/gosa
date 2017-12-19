# import logging
# import cProfile
#
# import ldap
# from line_profiler import LineProfiler
# from unittest import TestCase
#
# from gosa.backend.objects import ObjectFactory, ObjectProxy
# from gosa.backend.objects.backend.registry import ObjectBackendRegistry
# from gosa.backend.utils.ldap import LDAPHandler
# from gosa.common import Environment
# from gosa.common.components import PluginRegistry
#
#
# def do_cprofile(func):
#     def profiled_func(*args, **kwargs):
#         profile = cProfile.Profile()
#         try:
#             profile.enable()
#             result = func(*args, **kwargs)
#             profile.disable()
#             return result
#         finally:
#             profile.print_stats()
#     return profiled_func
#
#
# def do_profile(follow=[]):
#     def inner(func):
#         def profiled_func(*args, **kwargs):
#             try:
#                 profiler = LineProfiler()
#                 profiler.add_function(func)
#                 for f in follow:
#                     profiler.add_function(f)
#                 profiler.enable_by_count()
#                 return func(*args, **kwargs)
#             finally:
#                 profiler.print_stats()
#         return profiled_func
#     return inner


# class IndexTestCase(TestCase):
#
#     def setUp(self):
#         super(IndexTestCase, self).setUp()
#         self.env = Environment.getInstance()
#         self.log = logging.getLogger(__name__)
#         self.factory = ObjectFactory.getInstance()
#
#     def resolve_children(self, dn):
#         self.log.debug("found object '%s'" % dn)
#         res = {}
#
#         children = self.factory.getObjectChildren(dn)
#         res = {**res, **children}
#
#         for chld in children.keys():
#             res = {**res, **self.resolve_children(chld)}
#
#         return res
#
#     @do_profile(follow=[resolve_children,
#                         ObjectFactory.getInstance().getObjectChildren,
#                         ObjectFactory.getInstance().identifyObject,
#                         ObjectBackendRegistry.getBackend('LDAP').identify,
#                         ObjectBackendRegistry.getBackend('LDAP').dn2uuid
#                         ])
#     def test_resolve_children(self):
#         self.resolve_children(self.env.base)
#         assert False
#
#     @do_profile(follow=[ObjectFactory.getInstance().getObjectChildren, ObjectFactory.getInstance().identifyObject])
#     def test_sync_index(self):
#         index = PluginRegistry.getInstance('ObjectIndex')
#         index.sync_index()
#         assert False
#
#     @do_profile(follow=[LDAPHandler.get_instance().get_connection().search_s])
#     def test_ldap_search(self):
#         lh = LDAPHandler.get_instance()
#         con = lh.get_connection()
#         uuid_entry = self.env.config.get("backend-ldap.uuid-attribute", "entryUUID")
#         res = con.search_s("cn=jwenzel,ou=groups,ou=GONICUS,dc=klingel,dc=test", ldap.SCOPE_BASE, '(objectClass=*)', [uuid_entry])
#         assert False
#
#     @do_profile(follow=[
#         ObjectProxy.__init__,
#         ObjectFactory.getInstance().getObject,
#         ObjectFactory.getInstance().getObjectMethods
#     ])
#     def test_open_proxy(self):
#         obj = ObjectProxy("cn=jwenzel,ou=groups,ou=GONICUS,dc=klingel,dc=test")
#
#         # second time should be faster
#         # obj = ObjectProxy("cn=jwenzel,ou=groups,ou=GONICUS,dc=klingel,dc=test")
#         assert False
