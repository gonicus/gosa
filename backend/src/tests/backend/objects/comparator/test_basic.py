import unittest
from gosa.backend.objects.comparator.basic import Equals, Greater, Smaller

class BasicComparatorTests(unittest.TestCase):

    def test_equals(self):
        comp = Equals(None)
        (result, errors) = comp.process(None, None, ["test","test"], "test")
        assert result == True
        assert len(errors) == 0

        (result, errors) = comp.process(None, None, ["test", "test1"], "test")
        assert result == False
        assert len(errors) == 1

        (result, errors) = comp.process(None, None, ["test2", "test1"], "test")
        assert result == False
        assert len(errors) == 1

        (result, errors) = comp.process(None, None, ["test", "test"], "Test", case_ignore=True)
        assert result == True
        assert len(errors) == 0

        (result, errors) = comp.process(None, None, ["test", "test1"], "Test", case_ignore=True)
        assert result == False
        assert len(errors) == 1

        (result, errors) = comp.process(None, None, ["test2", "test1"], "Test", case_ignore=True)
        assert result == False
        assert len(errors) == 1

    def test_greater(self):
        comp = Greater(None)
        (result, errors) = comp.process(None, None, [5, 6], 3)
        assert result == True
        assert len(errors) == 0

        (result, errors) = comp.process(None, None, [5, 1], 3)
        assert result == False
        assert len(errors) == 1

        (result, errors) = comp.process(None, None, [1, 2], 3)
        assert result == False
        assert len(errors) == 1

        # test string numbers
        (result, errors) = comp.process(None, None, ["5", "6"], "3")
        assert result == True
        assert len(errors) == 0

        (result, errors) = comp.process(None, None, ["5", "1"], "3")
        assert result == False
        assert len(errors) == 1

        (result, errors) = comp.process(None, None, ["1", "2"], "3")
        assert result == False
        assert len(errors) == 1

    def test_smaller(self):
        comp = Smaller(None)
        (result, errors) = comp.process(None, None, [5, 6], 13)
        assert result == True
        assert len(errors) == 0

        (result, errors) = comp.process(None, None, [5, 1], 3)
        assert result == False
        assert len(errors) == 1

        (result, errors) = comp.process(None, None, [5, 6], 3)
        assert result == False
        assert len(errors) == 1

        (result, errors) = comp.process(None, None, ["5", "6"], "13")
        assert result == True
        assert len(errors) == 0

        (result, errors) = comp.process(None, None, ["5", "1"], "3")
        assert result == False
        assert len(errors) == 1

        (result, errors) = comp.process(None, None, ["5", "6"], "3")
        assert result == False
        assert len(errors) == 1