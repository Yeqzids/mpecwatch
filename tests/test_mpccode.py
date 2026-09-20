import pytest

from mpccode import normalize_longitude


@pytest.mark.parametrize(
    "longitude, expected",
    [
        (314.58361, pytest.approx(-45.41639, abs=1e-5)),
        (-45.41639, pytest.approx(-45.41639, abs=1e-5)),
        (0.0, pytest.approx(0.0, abs=1e-9)),
        (180.0, pytest.approx(180.0, abs=1e-9)),
    ],
)
def test_normalize_longitude(longitude, expected):
    assert normalize_longitude(longitude) == expected
