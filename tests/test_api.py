import json
import pytest
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
