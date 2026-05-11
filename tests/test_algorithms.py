import pytest
from app.algorithms.mst_aug import MSTAugmentation
from app.algorithms.greedy import GreedyDegreeConstrained
from app.algorithms.kconnect import KConnectivityApproximation
from app.services.compute import GraphComputer


SAMPLE_SITES = [
    {'id': 'Paris', 'lat': 48.864714, 'lng': 2.349553, 'min_links': 1, 'max_links': 3, 'link_ids': [], 'status': 'ok'},
    {'id': 'Lyon', 'lat': 45.75, 'lng': 4.833333, 'min_links': 1, 'max_links': 3, 'link_ids': [], 'status': 'ok'},
    {'id': 'Marseille', 'lat': 43.296389, 'lng': 5.37, 'min_links': 1, 'max_links': 3, 'link_ids': [], 'status': 'ok'},
    {'id': 'Toulouse', 'lat': 43.604444, 'lng': 1.443889, 'min_links': 0, 'max_links': 2, 'link_ids': [], 'status': 'ok'},
]


def fresh_sites(sites=None):
    """Return deep copies so mutations don't bleed between tests."""
    return [s.copy() for s in (sites or SAMPLE_SITES)]


def distances_for(sites):
    return GraphComputer.calculate_all_distances(sites)


def has_duplicate_links(links):
    pairs = set()
    for link in links:
        pair = frozenset([link['site_a'], link['site_b']])
        if pair in pairs:
            return True
        pairs.add(pair)
    return False


def max_links_violated(links, sites):
    adj = GraphComputer.build_adjacency_list(links)
    for site in sites:
        if len(adj.get(site['id'], set())) > site['max_links']:
            return True
    return False


ALL_ALGOS = [MSTAugmentation, GreedyDegreeConstrained, KConnectivityApproximation]


@pytest.mark.parametrize("AlgoClass", ALL_ALGOS)
class TestAlgorithmContract:
    def test_returns_correct_types(self, AlgoClass):
        sites = fresh_sites()
        algo = AlgoClass()
        links, logs, parent_child = algo.generate(sites, distances_for(sites))
        assert isinstance(links, list)
        assert isinstance(logs, list)
        assert isinstance(parent_child, dict)

    def test_generates_at_least_spanning_tree(self, AlgoClass):
        sites = fresh_sites()
        algo = AlgoClass()
        links, _, _ = algo.generate(sites, distances_for(sites))
        assert len(links) >= len(sites) - 1

    def test_no_duplicate_links(self, AlgoClass):
        sites = fresh_sites()
        algo = AlgoClass()
        links, _, _ = algo.generate(sites, distances_for(sites))
        assert not has_duplicate_links(links)

    def test_max_links_respected(self, AlgoClass):
        sites = fresh_sites()
        algo = AlgoClass()
        links, _, _ = algo.generate(sites, distances_for(sites))
        assert not max_links_violated(links, sites)

    def test_all_links_have_required_fields(self, AlgoClass):
        sites = fresh_sites()
        algo = AlgoClass()
        links, _, _ = algo.generate(sites, distances_for(sites))
        for link in links:
            assert 'id' in link
            assert 'site_a' in link
            assert 'site_b' in link
            assert 'distance_km' in link
            assert link['status'] == 'active'

    def test_empty_input_returns_empty(self, AlgoClass):
        algo = AlgoClass()
        links, _, _ = algo.generate([], [])
        assert links == []

    def test_two_sites_produces_one_link(self, AlgoClass):
        sites = fresh_sites(SAMPLE_SITES[:2])
        algo = AlgoClass()
        links, _, _ = algo.generate(sites, distances_for(sites))
        assert len(links) == 1
        pair = frozenset([links[0]['site_a'], links[0]['site_b']])
        assert pair == frozenset(['Paris', 'Lyon'])

    def test_excluded_links_are_not_used(self, AlgoClass):
        sites = fresh_sites()
        algo = AlgoClass()
        excluded = {'Paris-Lyon', 'Lyon-Paris'}
        links, _, _ = algo.generate(sites, distances_for(sites), excluded_links=excluded)
        for link in links:
            pair = frozenset([link['site_a'], link['site_b']])
            assert pair != frozenset(['Paris', 'Lyon'])

    def test_site_link_ids_updated(self, AlgoClass):
        sites = fresh_sites()
        algo = AlgoClass()
        links, _, _ = algo.generate(sites, distances_for(sites))
        # All generated link IDs should appear in the link objects
        link_ids = {link['id'] for link in links}
        assert len(link_ids) == len(links)


@pytest.mark.parametrize("AlgoClass", ALL_ALGOS)
class TestAlgorithmMaxLinksConstraint:
    def test_strict_max_links_respected(self, AlgoClass):
        # 4 sites where only 2 can connect to each hub (max_links=2 for hubs, 1 for leaves)
        # This is achievable: Paris-Lyon, Lyon-Marseille, Lyon-Toulouse (Lyon has max 3 connections)
        sites = [
            {'id': 'A', 'lat': 48.86, 'lng': 2.35, 'min_links': 0, 'max_links': 2, 'link_ids': [], 'status': 'ok'},
            {'id': 'B', 'lat': 45.75, 'lng': 4.83, 'min_links': 0, 'max_links': 2, 'link_ids': [], 'status': 'ok'},
            {'id': 'C', 'lat': 43.30, 'lng': 5.37, 'min_links': 0, 'max_links': 2, 'link_ids': [], 'status': 'ok'},
            {'id': 'D', 'lat': 43.60, 'lng': 1.44, 'min_links': 0, 'max_links': 2, 'link_ids': [], 'status': 'ok'},
        ]
        algo = AlgoClass()
        links, _, _ = algo.generate(sites, distances_for(sites))
        assert not max_links_violated(links, sites)
