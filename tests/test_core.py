import pytest
from fbchat._core import Enum


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_enum_extend_if_invalid():
    class TestEnum(Enum):
        A = 1
        B = 2

    assert TestEnum._extend_if_invalid(1) == TestEnum.A
    assert TestEnum._extend_if_invalid(3) == TestEnum.UNKNOWN_3
    assert TestEnum._extend_if_invalid(3) == TestEnum.UNKNOWN_3
    assert TestEnum(3) == TestEnum.UNKNOWN_3
