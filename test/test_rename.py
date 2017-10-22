from io import StringIO
import sys

from rename_show import rename


def test_user_decision():
    values = ["test1", "test2", "test3", "test4"]
    numbers = range(0, 4)
    sys.stdin = StringIO("1")
    decision = rename.get_user_decision(values=values, numbered=numbers, type_cast_f=lambda x: int(x))

    assert (decision == "test2")


def test_user_decision_custom():
    values = ["test1", "test2", "test3", "test4"]
    numbers = range(0, 4)
    sys.stdin = StringIO("3")
    decision = rename.get_user_decision(values=values, numbered=numbers, type_cast_f=lambda x: int(x),
                                        allow_custom=True)

    assert (decision == "test4")
