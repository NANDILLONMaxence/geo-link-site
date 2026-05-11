import pytest
from app.services.convert import CoordinateConverter


@pytest.fixture
def conv():
    return CoordinateConverter()


class TestParseDMS:
    def test_standard_format(self, conv):
        # 47°50'44.56" = 47 + 50/60 + 44.56/3600
        result = conv.parse_dms("47°50'44.56\"")
        assert abs(result - 47.84571) < 0.0001

    def test_space_separated(self, conv):
        result = conv.parse_dms("47 50 44.56")
        assert abs(result - 47.84571) < 0.0001

    def test_degrees_only(self, conv):
        assert conv.parse_dms("47") == pytest.approx(47.0)

    def test_degrees_minutes(self, conv):
        result = conv.parse_dms("47°50'")
        assert abs(result - 47.8333) < 0.0001

    def test_double_quote_seconds(self, conv):
        result = conv.parse_dms("47°50'44.56''")
        assert abs(result - 47.84571) < 0.0001


class TestParseDMSCoordinate:
    def test_north(self, conv):
        result = conv.parse_dms_coordinate("48°51'52.97''N", 'lat')
        assert abs(result - 48.864714) < 0.0001

    def test_south_is_negative(self, conv):
        result = conv.parse_dms_coordinate("33°52'0''S", 'lat')
        assert result < 0

    def test_east(self, conv):
        result = conv.parse_dms_coordinate("2°20'56.39''E", 'lng')
        assert abs(result - 2.34900) < 0.0001

    def test_west_is_negative(self, conv):
        result = conv.parse_dms_coordinate("0°34'59''W", 'lng')
        assert result < 0

    def test_invalid_lat_direction(self, conv):
        with pytest.raises(ValueError):
            conv.parse_dms_coordinate("48°51'52.97''E", 'lat')

    def test_invalid_lng_direction(self, conv):
        with pytest.raises(ValueError):
            conv.parse_dms_coordinate("2°20'56''N", 'lng')

    def test_out_of_range_lat(self, conv):
        with pytest.raises(ValueError):
            conv.parse_dms_coordinate("91°0'0''N", 'lat')

    def test_out_of_range_lng(self, conv):
        with pytest.raises(ValueError):
            conv.parse_dms_coordinate("181°0'0''E", 'lng')


class TestDMSToDecimal:
    def test_paris_returns_lng_lat(self, conv):
        lng, lat = conv.dms_to_decimal("48°51'52.97''N", "2°20'56.39''E")
        assert abs(lat - 48.864714) < 0.001
        assert abs(lng - 2.349553) < 0.001

    def test_return_order_is_lng_lat(self, conv):
        # The method returns (lng, lat), not (lat, lng)
        lng, lat = conv.dms_to_decimal("45°45'0''N", "4°50'0''E")
        assert lat > 40  # latitude ~45.75
        assert lng > 4   # longitude ~4.83

    def test_western_longitude(self, conv):
        lng, lat = conv.dms_to_decimal("44°50'17''N", "0°34'59''W")
        assert lng < 0


class TestGeodesicDistance:
    def test_paris_to_lyon(self, conv):
        # Paris: lng=2.3490, lat=48.8647  Lyon: lng=4.8333, lat=45.75
        distance = conv.calculate_geodesic_distance(2.3490, 48.8647, 4.8333, 45.75)
        assert 380 < distance < 410

    def test_same_point_is_zero(self, conv):
        distance = conv.calculate_geodesic_distance(2.35, 48.86, 2.35, 48.86)
        assert distance < 0.001

    def test_symmetry(self, conv):
        d1 = conv.calculate_geodesic_distance(2.35, 48.86, 4.83, 45.75)
        d2 = conv.calculate_geodesic_distance(4.83, 45.75, 2.35, 48.86)
        assert abs(d1 - d2) < 0.001

    def test_positive_result(self, conv):
        distance = conv.calculate_geodesic_distance(2.35, 48.86, 5.37, 43.30)
        assert distance > 0


class TestDecimalToDMS:
    def test_north(self, conv):
        result = conv.decimal_to_dms(48.86, 'lat')
        assert 'N' in result
        assert '48' in result

    def test_south(self, conv):
        result = conv.decimal_to_dms(-33.86, 'lat')
        assert 'S' in result

    def test_west(self, conv):
        result = conv.decimal_to_dms(-0.583, 'lng')
        assert 'W' in result

    def test_east(self, conv):
        result = conv.decimal_to_dms(2.35, 'lng')
        assert 'E' in result

    def test_format_contains_degrees_symbol(self, conv):
        result = conv.decimal_to_dms(48.86, 'lat')
        assert '°' in result
