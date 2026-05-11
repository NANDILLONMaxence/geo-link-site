import pytest
from app.services.compute import GraphComputer


SITES = [
    {'id': 'A', 'lat': 48.86, 'lng': 2.35, 'min_links': 1, 'max_links': 3, 'link_ids': [], 'status': 'ok'},
    {'id': 'B', 'lat': 45.75, 'lng': 4.83, 'min_links': 1, 'max_links': 3, 'link_ids': [], 'status': 'ok'},
    {'id': 'C', 'lat': 43.30, 'lng': 5.37, 'min_links': 1, 'max_links': 3, 'link_ids': [], 'status': 'ok'},
]


class TestGenerateEdgeId:
    def test_unique_ids(self):
        ids = {GraphComputer.generate_edge_id() for _ in range(100)}
        assert len(ids) == 100

    def test_starts_with_edge_prefix(self):
        edge_id = GraphComputer.generate_edge_id()
        assert edge_id.startswith('edge_')

    def test_is_string(self):
        assert isinstance(GraphComputer.generate_edge_id(), str)


class TestCalculateAllDistances:
    def test_count_for_n_sites(self):
        result = GraphComputer.calculate_all_distances(SITES)
        assert len(result) == 3  # n*(n-1)/2 = 3*2/2

    def test_has_required_keys(self):
        result = GraphComputer.calculate_all_distances(SITES)
        for d in result:
            assert 'site_a' in d
            assert 'site_b' in d
            assert 'distance_km' in d

    def test_all_distances_positive(self):
        result = GraphComputer.calculate_all_distances(SITES)
        for d in result:
            assert d['distance_km'] > 0

    def test_empty_sites(self):
        assert GraphComputer.calculate_all_distances([]) == []

    def test_single_site(self):
        assert GraphComputer.calculate_all_distances(SITES[:1]) == []

    def test_two_sites(self):
        result = GraphComputer.calculate_all_distances(SITES[:2])
        assert len(result) == 1
        assert result[0]['site_a'] == 'A'
        assert result[0]['site_b'] == 'B'


class TestFilterByDistance:
    def test_no_limit_returns_all(self):
        distances = [
            {'site_a': 'A', 'site_b': 'B', 'distance_km': 100},
            {'site_a': 'A', 'site_b': 'C', 'distance_km': 500},
        ]
        assert len(GraphComputer.filter_by_distance(distances, None)) == 2

    def test_max_distance_filters(self):
        distances = [
            {'site_a': 'A', 'site_b': 'B', 'distance_km': 100},
            {'site_a': 'A', 'site_b': 'C', 'distance_km': 500},
        ]
        result = GraphComputer.filter_by_distance(distances, 200)
        assert len(result) == 1
        assert result[0]['site_b'] == 'B'

    def test_exact_boundary_included(self):
        distances = [{'site_a': 'A', 'site_b': 'B', 'distance_km': 100}]
        result = GraphComputer.filter_by_distance(distances, 100)
        assert len(result) == 1

    def test_all_filtered_returns_empty(self):
        distances = [{'site_a': 'A', 'site_b': 'B', 'distance_km': 500}]
        assert GraphComputer.filter_by_distance(distances, 100) == []


class TestBuildAdjacencyList:
    def test_active_links_added(self):
        links = [
            {'site_a': 'A', 'site_b': 'B', 'status': 'active'},
            {'site_a': 'B', 'site_b': 'C', 'status': 'active'},
        ]
        adj = GraphComputer.build_adjacency_list(links)
        assert 'B' in adj['A']
        assert 'A' in adj['B']
        assert 'C' in adj['B']

    def test_excluded_links_ignored(self):
        links = [{'site_a': 'A', 'site_b': 'B', 'status': 'excluded'}]
        adj = GraphComputer.build_adjacency_list(links)
        assert 'B' not in adj.get('A', set())

    def test_symmetric(self):
        links = [{'site_a': 'A', 'site_b': 'B', 'status': 'active'}]
        adj = GraphComputer.build_adjacency_list(links)
        assert 'B' in adj['A']
        assert 'A' in adj['B']

    def test_empty_links(self):
        assert GraphComputer.build_adjacency_list([]) == {}


class TestGetSiteDegree:
    def test_degree_zero_for_unknown_site(self):
        assert GraphComputer.get_site_degree('X', {}) == 0

    def test_degree_matches_neighbors(self):
        adj = {'A': {'B', 'C'}}
        assert GraphComputer.get_site_degree('A', adj) == 2


class TestCanAddEdge:
    def test_basic_valid_edge(self):
        sites_dict = {'A': {'max_links': 3}, 'B': {'max_links': 3}}
        assert GraphComputer.can_add_edge('A', 'B', sites_dict, {}, {})

    def test_site_a_at_max_links(self):
        sites_dict = {'A': {'max_links': 1}, 'B': {'max_links': 3}}
        adj_list = {'A': {'C'}}  # A already has 1 link
        assert not GraphComputer.can_add_edge('A', 'B', sites_dict, adj_list, {})

    def test_site_b_at_max_links(self):
        sites_dict = {'A': {'max_links': 3}, 'B': {'max_links': 1}}
        adj_list = {'B': {'C'}}
        assert not GraphComputer.can_add_edge('A', 'B', sites_dict, adj_list, {})

    def test_already_connected(self):
        sites_dict = {'A': {'max_links': 3}, 'B': {'max_links': 3}}
        adj_list = {'A': {'B'}, 'B': {'A'}}
        assert not GraphComputer.can_add_edge('A', 'B', sites_dict, adj_list, {})

    def test_parent_child_blocked(self):
        sites_dict = {'A': {'max_links': 3}, 'B': {'max_links': 3}}
        parent_child_map = {'B': 'A'}  # A is parent of B
        assert not GraphComputer.can_add_edge('A', 'B', sites_dict, {}, parent_child_map)

    def test_missing_site_blocked(self):
        sites_dict = {'A': {'max_links': 3}}
        assert not GraphComputer.can_add_edge('A', 'B', sites_dict, {}, {})
