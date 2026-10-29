import io
import json
from app.app import app_state


PARIS = {
    'id': 'Paris',
    'lat_dms': "48°51'52.97''N",
    'lng_dms': "2°20'56.39''E",
    'lat': 48.864714,
    'lng': 2.349553,
    'min_links': 1,
    'max_links': 3,
    'link_ids': [],
    'status': 'ok',
}
LYON = {
    'id': 'Lyon',
    'lat_dms': "45°45'00''N",
    'lng_dms': "4°50'00''E",
    'lat': 45.75,
    'lng': 4.833333,
    'min_links': 1,
    'max_links': 3,
    'link_ids': [],
    'status': 'ok',
}
MARSEILLE = {
    'id': 'Marseille',
    'lat_dms': "43°17'47''N",
    'lng_dms': "5°22'12''E",
    'lat': 43.296389,
    'lng': 5.37,
    'min_links': 1,
    'max_links': 3,
    'link_ids': [],
    'status': 'ok',
}


class TestIndex:
    def test_returns_200(self, client):
        assert client.get('/').status_code == 200


class TestStatus:
    def test_returns_json_with_expected_keys(self, client):
        data = json.loads(client.get('/status').data)
        assert 'sites' in data
        assert 'links' in data
        assert 'manual_links' in data
        assert 'params' in data

    def test_initial_state_is_empty(self, client):
        data = json.loads(client.get('/status').data)
        assert data['sites'] == []
        assert data['links'] == []
        assert data['manual_links'] == []


class TestAddSite:
    def test_add_valid_site(self, client):
        response = client.post('/add_site', json={
            'id': 'TestSite',
            'lat_dms': "48°51'52.97''N",
            'lng_dms': "2°20'56.39''E",
        })
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['site']['id'] == 'TestSite'

    def test_site_appears_in_status(self, client):
        client.post('/add_site', json={
            'id': 'TestSite',
            'lat_dms': "48°51'52.97''N",
            'lng_dms': "2°20'56.39''E",
        })
        status = json.loads(client.get('/status').data)
        assert any(s['id'] == 'TestSite' for s in status['sites'])

    def test_add_duplicate_returns_400(self, client):
        payload = {
            'id': 'TestSite',
            'lat_dms': "48°51'52.97''N",
            'lng_dms': "2°20'56.39''E",
        }
        client.post('/add_site', json=payload)
        assert client.post('/add_site', json=payload).status_code == 400

    def test_missing_id_returns_400(self, client):
        assert client.post('/add_site', json={
            'lat_dms': "48°51'52.97''N",
            'lng_dms': "2°20'56.39''E",
        }).status_code == 400

    def test_invalid_coords_returns_400(self, client):
        assert client.post('/add_site', json={
            'id': 'BadSite',
            'lat_dms': 'not_a_coord',
            'lng_dms': "2°20'56.39''E",
        }).status_code == 400

    def test_coordinates_converted_correctly(self, client):
        client.post('/add_site', json={
            'id': 'Paris',
            'lat_dms': "48°51'52.97''N",
            'lng_dms': "2°20'56.39''E",
        })
        status = json.loads(client.get('/status').data)
        paris = next(s for s in status['sites'] if s['id'] == 'Paris')
        assert abs(paris['lat'] - 48.864714) < 0.001
        assert abs(paris['lng'] - 2.349553) < 0.001


class TestDeleteSite:
    def test_delete_removes_site(self, client):
        client.post('/add_site', json={
            'id': 'ToDelete',
            'lat_dms': "48°51'52.97''N",
            'lng_dms': "2°20'56.39''E",
        })
        client.post('/delete_site', json={'id': 'ToDelete'})
        status = json.loads(client.get('/status').data)
        assert not any(s['id'] == 'ToDelete' for s in status['sites'])

    def test_delete_returns_success(self, client):
        client.post('/add_site', json={
            'id': 'ToDelete',
            'lat_dms': "48°51'52.97''N",
            'lng_dms': "2°20'56.39''E",
        })
        data = json.loads(client.post('/delete_site', json={'id': 'ToDelete'}).data)
        assert data['success'] is True


class TestGenerateLinks:
    def test_generate_with_loaded_sites(self, client):
        app_state['sites'] = [PARIS.copy(), LYON.copy(), MARSEILLE.copy()]
        response = client.post('/generate', json={
            'algorithm': 'mst_aug',
            'favor_shortest': True,
        })
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['links']) >= 2

    def test_generate_requires_two_sites(self, client):
        assert client.post('/generate', json={'algorithm': 'mst_aug'}).status_code == 400

    def test_generate_unknown_algorithm_returns_400(self, client):
        app_state['sites'] = [PARIS.copy(), LYON.copy()]
        assert client.post('/generate', json={'algorithm': 'unknown'}).status_code == 400

    def test_greedy_algorithm_works(self, client):
        app_state['sites'] = [PARIS.copy(), LYON.copy(), MARSEILLE.copy()]
        data = json.loads(client.post('/generate', json={'algorithm': 'greedy'}).data)
        assert data['success'] is True

    def test_kconnect_algorithm_works(self, client):
        app_state['sites'] = [PARIS.copy(), LYON.copy(), MARSEILLE.copy()]
        data = json.loads(client.post('/generate', json={'algorithm': 'kconnect'}).data)
        assert data['success'] is True


class TestCreateManualLink:
    def test_create_manual_link(self, client):
        app_state['sites'] = [PARIS.copy(), LYON.copy()]
        response = client.post('/create_manual_link', json={
            'site_a': 'Paris',
            'site_b': 'Lyon',
        })
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['link']['type'] == 'manual'

    def test_self_link_returns_400(self, client):
        app_state['sites'] = [PARIS.copy()]
        assert client.post('/create_manual_link', json={
            'site_a': 'Paris',
            'site_b': 'Paris',
        }).status_code == 400

    def test_nonexistent_site_returns_404(self, client):
        assert client.post('/create_manual_link', json={
            'site_a': 'Paris',
            'site_b': 'DoesNotExist',
        }).status_code == 404


class TestResetAll:
    def test_reset_clears_all_state(self, client):
        app_state['sites'] = [PARIS.copy(), LYON.copy()]
        app_state['links'] = [{'id': 'e1', 'site_a': 'Paris', 'site_b': 'Lyon', 'distance_km': 392, 'status': 'active'}]

        data = json.loads(client.post('/reset_all').data)
        assert data['success'] is True

        status = json.loads(client.get('/status').data)
        assert status['sites'] == []
        assert status['links'] == []


class TestToggleLink:
    def test_toggle_active_link_to_excluded(self, client):
        app_state['sites'] = [PARIS.copy(), LYON.copy()]
        app_state['links'] = [{
            'id': 'link1', 'site_a': 'Paris', 'site_b': 'Lyon',
            'distance_km': 392, 'status': 'active'
        }]
        data = json.loads(client.post('/toggle_link', json={'link_id': 'link1'}).data)
        assert data['link']['status'] == 'excluded'

    def test_toggle_excluded_link_to_active(self, client):
        app_state['sites'] = [PARIS.copy(), LYON.copy()]
        app_state['links'] = [{
            'id': 'link1', 'site_a': 'Paris', 'site_b': 'Lyon',
            'distance_km': 392, 'status': 'excluded'
        }]
        data = json.loads(client.post('/toggle_link', json={'link_id': 'link1'}).data)
        assert data['link']['status'] == 'active'


class TestDeleteLink:
    def test_delete_removes_link_and_its_exclusions(self, client):
        app_state['sites'] = [PARIS.copy(), LYON.copy()]
        app_state['links'] = [{
            'id': 'link1', 'site_a': 'Paris', 'site_b': 'Lyon',
            'distance_km': 392, 'status': 'excluded'
        }]
        app_state['excluded_links'] = {'Paris-Lyon', 'Lyon-Paris', 'Other-Site'}

        assert client.post('/delete_link', json={'link_id': 'link1'}).status_code == 200
        assert app_state['links'] == []
        assert app_state['excluded_links'] == {'Other-Site'}

    def test_unknown_link_returns_404(self, client):
        assert client.post('/delete_link', json={'link_id': 'nope'}).status_code == 404


class TestInputValidation:
    def test_non_json_body_returns_400(self, client):
        response = client.post('/add_site', data='x', content_type='text/plain')
        assert response.status_code == 400

    def test_non_integer_min_links_returns_400(self, client):
        response = client.post('/add_site', json={
            'id': 'A', 'lat_dms': "47°N", 'lng_dms': "2°E", 'min_links': 'abc'
        })
        assert response.status_code == 400
        assert app_state['sites'] == []

    def test_negative_max_links_returns_400(self, client):
        response = client.post('/add_site', json={
            'id': 'A', 'lat_dms': "47°N", 'lng_dms': "2°E", 'max_links': -1
        })
        assert response.status_code == 400

    def test_too_long_site_id_returns_400(self, client):
        response = client.post('/add_site', json={'id': 'x' * 101, 'lat_dms': "47°N", 'lng_dms': "2°E"})
        assert response.status_code == 400

    def test_edit_with_invalid_constraint_leaves_site_untouched(self, client):
        app_state['sites'] = [PARIS.copy()]
        response = client.post('/edit_site', json={
            'id': 'Paris', 'lat_dms': "10°N", 'lng_dms': "10°E", 'max_links': 'abc'
        })
        assert response.status_code == 400
        assert app_state['sites'][0]['lat'] == PARIS['lat']

    def test_invalid_radius_returns_400(self, client):
        app_state['sites'] = [PARIS.copy()]
        for radius in ('abc', -5, 0, 'nan'):
            assert client.post('/add_circle', json={'site_id': 'Paris', 'radius_km': radius}).status_code == 400

    def test_invalid_distance_max_returns_400(self, client):
        app_state['sites'] = [PARIS.copy(), LYON.copy()]
        response = client.post('/generate', json={'algorithm': 'mst_aug', 'distance_max_km': 'abc'})
        assert response.status_code == 400


class TestImport:
    def upload(self, client, url, content, name):
        return client.post(url, data={'file': (io.BytesIO(content), name)}, content_type='multipart/form-data')

    def test_csv_import_with_bom(self, client):
        content = "﻿type,id,lat,lng,min_links,max_links\nsite,A,45,2,0,2\n".encode('utf-8')
        response = self.upload(client, '/import_csv', content, 'f.csv')
        assert response.status_code == 200
        assert app_state['sites'][0]['id'] == 'A'

    def test_manual_link_without_numbered_id(self, client):
        content = (
            "type,id,lat,lng,min_links,max_links,site_a,site_b,distance_km,link_type\n"
            "site,A,45,2,0,2,,,,\nsite,B,46,2,0,2,,,,\n"
            "link,custom,,,,,A,B,111,manual\n"
        ).encode('utf-8')
        response = self.upload(client, '/import_csv', content, 'f.csv')
        assert response.status_code == 200
        assert app_state['manual_link_counter'] == 0

    def test_manual_counter_follows_imported_ids(self, client):
        content = (
            "type,id,lat,lng,min_links,max_links,site_a,site_b,distance_km,link_type\n"
            "site,A,45,2,0,3,,,,\nsite,B,46,2,0,3,,,,\nsite,C,47,2,0,3,,,,\n"
            "link,manual_7,,,,,A,B,111,manual\n"
        ).encode('utf-8')
        self.upload(client, '/import_csv', content, 'f.csv')
        data = client.post('/create_manual_link', json={'site_a': 'B', 'site_b': 'C'}).get_json()
        assert data['link']['id'] == 'manual_8'

    def test_non_utf8_file_returns_400(self, client):
        response = self.upload(client, '/import_csv', b'\xff\xfe\x00', 'f.csv')
        assert response.status_code == 400

    def test_missing_file_returns_400(self, client):
        assert client.post('/import_json', data={}).status_code == 400

    def test_invalid_json_returns_400(self, client):
        assert self.upload(client, '/import_json', b'{oops', 'f.json').status_code == 400


class TestExport:
    def test_csv_export_with_sites(self, client):
        app_state['sites'] = [PARIS.copy(), LYON.copy()]
        response = client.get('/export_csv')
        assert response.status_code == 200
        assert 'Paris' in response.get_data(as_text=True)

    def test_json_export_reimports(self, client):
        app_state['sites'] = [PARIS.copy(), LYON.copy()]
        client.post('/create_manual_link', json={'site_a': 'Paris', 'site_b': 'Lyon'})
        exported = client.get('/export_json').data

        client.post('/reset_all')
        response = client.post('/import_json', data={'file': (io.BytesIO(exported), 's.geojson')},
                               content_type='multipart/form-data')
        assert response.status_code == 200
        assert len(app_state['sites']) == 2
        assert len(app_state['manual_links']) == 1

    def test_html_export(self, client):
        app_state['sites'] = [PARIS.copy()]
        response = client.get('/export_html')
        assert response.status_code == 200
        assert response.mimetype == 'text/html'


class TestSecurity:
    def test_security_headers(self, client):
        response = client.get('/')
        assert response.headers['X-Content-Type-Options'] == 'nosniff'
        assert response.headers['X-Frame-Options'] == 'DENY'

    def test_internal_errors_do_not_leak_details(self, client, monkeypatch):
        from app import app as app_module

        def boom(*args, **kwargs):
            raise RuntimeError('secret internal detail')

        monkeypatch.setattr(app_module.storage, 'export_html', boom)
        response = client.get('/export_html')
        assert response.status_code == 500
        assert 'secret' not in response.get_data(as_text=True)
