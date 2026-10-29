import csv
import json
from io import StringIO

from app import __version__
from app.services.storage import DataStorage

from tests.conftest import SAMPLE_SITES


AUTO_LINK = {
    'id': 'edge_1', 'site_a': 'Paris', 'site_b': 'Lyon',
    'distance_km': 392.2, 'status': 'active', 'type': 'auto',
}
MANUAL_LINK = {
    'id': 'manual_3', 'site_a': 'Lyon', 'site_b': 'Marseille',
    'distance_km': 277.5, 'status': 'excluded', 'type': 'manual',
}


def sites():
    return [dict(s) for s in SAMPLE_SITES]


class TestCsvExport:
    def test_export_with_sites_does_not_fail(self):
        content = DataStorage.export_csv_extended(sites(), [AUTO_LINK], [MANUAL_LINK])
        rows = list(csv.DictReader(StringIO(content)))
        assert len(rows) == len(SAMPLE_SITES) + 2

    def test_export_keeps_dms_coordinates(self):
        content = DataStorage.export_csv_extended(sites(), [], [])
        row = next(csv.DictReader(StringIO(content)))
        assert row['lat_dms'] == SAMPLE_SITES[0]['lat_dms']
        assert row['lng_dms'] == SAMPLE_SITES[0]['lng_dms']

    def test_roundtrip_preserves_sites_and_links(self):
        content = DataStorage.export_csv_extended(sites(), [AUTO_LINK], [MANUAL_LINK])
        parsed_sites, auto, manual, error = DataStorage.parse_csv_extended(content)
        assert error == ''
        assert [s['id'] for s in parsed_sites] == [s['id'] for s in SAMPLE_SITES]
        assert parsed_sites[0]['lat'] == SAMPLE_SITES[0]['lat']
        assert [lnk['id'] for lnk in auto] == ['edge_1']
        assert [lnk['id'] for lnk in manual] == ['manual_3']
        assert manual[0]['status'] == 'excluded'


class TestCsvImport:
    def test_decimal_fallback_when_no_dms(self):
        content = "type,id,lat,lng,min_links,max_links\nsite,A,45.5,-1.25,1,3\n"
        parsed_sites, _, _, error = DataStorage.parse_csv_extended(content)
        assert error == ''
        assert parsed_sites[0]['lat'] == 45.5
        assert parsed_sites[0]['lng_dms'].endswith('W')

    def test_invalid_site_row_reports_error(self):
        content = "type,id,lat_dms,lng_dms\nsite,A,abc,def\n"
        _, _, _, error = DataStorage.parse_csv_extended(content)
        assert 'Erreur site' in error

    def test_more_than_55_sites_rejected(self):
        rows = ''.join(f"site,S{i},45,2,0,2\n" for i in range(56))
        parsed_sites, _, _, error = DataStorage.parse_csv_extended("type,id,lat,lng,min_links,max_links\n" + rows)
        assert parsed_sites == []
        assert '55' in error


class TestGeoJson:
    def export(self):
        return DataStorage.export_json_extended(
            sites(), [AUTO_LINK], [MANUAL_LINK], {'algorithm': 'greedy'}, ['Lyon-Marseille']
        )

    def test_export_is_valid_feature_collection(self):
        data = json.loads(self.export())
        assert data['type'] == 'FeatureCollection'
        assert data['properties']['meta']['app_version'] == __version__
        geometries = [f['geometry']['type'] for f in data['features']]
        assert geometries.count('Point') == len(SAMPLE_SITES)
        assert geometries.count('LineString') == 2

    def test_roundtrip(self):
        s, auto, manual, params, excluded, error = DataStorage.parse_json_extended(self.export())
        assert error == ''
        assert len(s) == len(SAMPLE_SITES)
        assert auto[0]['id'] == 'edge_1'
        assert manual[0]['id'] == 'manual_3'
        assert params == {'algorithm': 'greedy'}
        assert excluded == ['Lyon-Marseille']

    def test_legacy_json_format(self):
        legacy = json.dumps({'sites': sites(), 'links': [AUTO_LINK], 'manual_links': [], 'params': {}})
        s, auto, _, _, _, error = DataStorage.parse_json_extended(legacy)
        assert error == ''
        assert len(s) == len(SAMPLE_SITES)
        assert len(auto) == 1

    def test_invalid_json(self):
        *_, error = DataStorage.parse_json_extended('{not json')
        assert error.startswith('Erreur parsing JSON')

    def test_non_object_json(self):
        *_, error = DataStorage.parse_json_extended('[1, 2]')
        assert error

    def test_site_without_id_rejected(self):
        legacy = json.dumps({'sites': [{'lat': 45, 'lng': 2}]})
        s, *_, error = DataStorage.parse_json_extended(legacy)
        assert s == []
        assert "'id'" in error

    def test_site_with_out_of_range_coordinates_rejected(self):
        legacy = json.dumps({'sites': [{'id': 'A', 'lat': 95, 'lng': 2}]})
        *_, error = DataStorage.parse_json_extended(legacy)
        assert 'hors limites' in error

    def test_link_without_sites_rejected(self):
        legacy = json.dumps({'sites': sites(), 'links': [{'id': 'x'}]})
        *_, error = DataStorage.parse_json_extended(legacy)
        assert 'site_a' in error


class TestHtmlExport:
    def test_contains_leaflet_with_integrity(self):
        html = DataStorage.export_html(sites(), [AUTO_LINK])
        assert 'leaflet.js' in html
        assert 'integrity="sha256-' in html

    def test_only_active_links_exported(self):
        html = DataStorage.export_html(sites(), [AUTO_LINK, MANUAL_LINK])
        assert 'edge_1' in html
        assert 'manual_3' not in html

    def test_site_name_cannot_break_out_of_script(self):
        evil = dict(SAMPLE_SITES[0], id='</script><script>alert(1)</script>')
        html = DataStorage.export_html([evil], [])
        assert '</script><script>alert(1)' not in html
        assert '\\u003c/script\\u003e' in html
