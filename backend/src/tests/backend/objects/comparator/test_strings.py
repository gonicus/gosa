import unittest
from gosa.backend.objects.comparator.strings import *

class StringComparatorTests(unittest.TestCase):

    def test_like(self):
        comp = Like(None)
        (result, errors) = comp.process(None, None, ["test","test"], "test")
        assert result == True
        assert len(errors) == 0

        (result, errors) = comp.process(None, None, ["test", "test1"], "test")
        assert result == True
        assert len(errors) == 0

        (result, errors) = comp.process(None, None, ["test2", "test1"], "test")
        assert result == True
        assert len(errors) == 0

        (result, errors) = comp.process(None, None, ["test222", "test122"], "test")
        assert result == False
        assert len(errors) == 1

    def test_regex(self):
        comp = RegEx(None)
        (result, errors) = comp.process(None, None, ["test", "test"], "[\w]")
        assert result == True
        assert len(errors) == 0

        comp = RegEx(None)
        (result, errors) = comp.process(None, None, ["test", "1"], "[\d]")
        assert result == False
        assert len(errors) == 1

    def test_stringLength(self):
        comp = stringLength(None)
        (result, errors) = comp.process(None, None, ["test", "test"], 0, 5)
        assert result == True
        assert len(errors) == 0

        (result, errors) = comp.process(None, None, ["test", "test123"], 0, 5)
        assert result == False
        assert len(errors) == 1

        (result, errors) = comp.process(None, None, ["test5466", "test123"], 0, 5)
        assert result == False
        assert len(errors) == 1

        (result, errors) = comp.process(None, None, ["test", "test123"], 5, 15)
        assert result == False
        assert len(errors) == 1