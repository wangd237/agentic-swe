import pytest
from trio.testing import MockClock


def test_jump_rejects_nan_without_changing_time():
    clock = MockClock()
    clock.jump(1.5)
    with pytest.raises(ValueError):
        clock.jump(float("nan"))
    assert clock.current_time() == 1.5
    clock.jump(0.5)
    assert clock.current_time() == 2.0
