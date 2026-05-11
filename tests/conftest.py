import pytest
from app.app import app as flask_app, app_state


@pytest.fixture
def app():
    flask_app.config['TESTING'] = True
    yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def reset_app_state():
    app_state['sites'] = []
    app_state['links'] = []
    app_state['manual_links'] = []
    app_state['excluded_links'] = set()
    app_state['params'] = {
        'algorithm': 'mst_aug',
        'distance_max_km': None,
        'favor_shortest': True
    }
    app_state['parent_child_map'] = {}
    app_state['manual_link_counter'] = 0
    app_state['show_excluded'] = True
    app_state['circles'] = []
    yield


SAMPLE_SITES = [
    {
        'id': 'Paris',
        'lat_dms': "48°51'52.97''N",
        'lng_dms': "2°20'56.39''E",
        'lat': 48.864714,
        'lng': 2.349553,
        'min_links': 1,
        'max_links': 3,
        'link_ids': [],
        'status': 'ok',
    },
    {
        'id': 'Lyon',
        'lat_dms': "45°45'00''N",
        'lng_dms': "4°50'00''E",
        'lat': 45.75,
        'lng': 4.833333,
        'min_links': 1,
        'max_links': 3,
        'link_ids': [],
        'status': 'ok',
    },
    {
        'id': 'Marseille',
        'lat_dms': "43°17'47''N",
        'lng_dms': "5°22'12''E",
        'lat': 43.296389,
        'lng': 5.37,
        'min_links': 1,
        'max_links': 3,
        'link_ids': [],
        'status': 'ok',
    },
    {
        'id': 'Toulouse',
        'lat_dms': "43°36'16''N",
        'lng_dms': "1°26'38''E",
        'lat': 43.604444,
        'lng': 1.443889,
        'min_links': 0,
        'max_links': 2,
        'link_ids': [],
        'status': 'ok',
    },
]


@pytest.fixture
def sample_sites():
    return [s.copy() for s in SAMPLE_SITES]


@pytest.fixture
def sample_distances(sample_sites):
    from app.services.compute import GraphComputer
    return GraphComputer.calculate_all_distances(sample_sites)
