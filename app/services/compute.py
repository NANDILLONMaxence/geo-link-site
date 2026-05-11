"""
Service de calculs pour la génération de graphes et de liaisons.
"""
import uuid
from typing import List, Dict, Tuple, Set
from .convert import converter


class GraphComputer:
    """Calculateur de graphes et distances."""

    @staticmethod
    def generate_edge_id() -> str:
        """Génère un ID unique pour une arête."""
        return f"edge_{uuid.uuid4().hex[:8]}"

    @staticmethod
    def calculate_all_distances(sites: List[Dict]) -> List[Dict]:
        """
        Calcule toutes les distances possibles entre sites.

        Args:
            sites: Liste des sites avec coordonnées WGS84

        Returns:
            Liste de dictionnaires {site_a, site_b, distance_km}
        """
        distances = []
        n = len(sites)

        for i in range(n):
            for j in range(i + 1, n):
                site_a = sites[i]
                site_b = sites[j]

                try:
                    distance = converter.calculate_geodesic_distance(
                        site_a['lng'], site_a['lat'],
                        site_b['lng'], site_b['lat']
                    )

                    distances.append({
                        'site_a': site_a['id'],
                        'site_b': site_b['id'],
                        'distance_km': round(distance, 3)
                    })
                except Exception as e:
                    print(f"Erreur calcul distance {site_a['id']}-{site_b['id']}: {e}")
                    continue

        return distances

    @staticmethod
    def filter_by_distance(
        distances: List[Dict],
        max_distance_km: float = None
    ) -> List[Dict]:
        """
        Filtre les distances selon une distance maximale.

        Args:
            distances: Liste des distances
            max_distance_km: Distance maximale autorisée (None = pas de limite)

        Returns:
            Liste filtrée
        """
        if max_distance_km is None:
            return distances

        return [d for d in distances if d['distance_km'] <= max_distance_km]

    @staticmethod
    def check_site_feasibility(
        site: Dict,
        all_sites: List[Dict],
        filtered_distances: List[Dict],
        parent_child_map: Dict[str, str]
    ) -> Tuple[bool, int]:
        """
        Vérifie si les contraintes d'un site sont réalisables.

        Args:
            site: Le site à vérifier
            all_sites: Tous les sites
            filtered_distances: Distances filtrées
            parent_child_map: Mapping parent -> enfant

        Returns:
            (feasible, possible_neighbors_count)
        """
        site_id = site['id']
        min_links = site.get('min_links', 0)

        # Trouver le parent et les enfants
        parent = parent_child_map.get(site_id)
        children = [child for child, par in parent_child_map.items() if par == site_id]

        # Compter les voisins possibles
        forbidden = set([parent] + children) if parent else set(children)
        forbidden.discard(None)

        possible_neighbors = set()
        for dist in filtered_distances:
            if dist['site_a'] == site_id and dist['site_b'] not in forbidden:
                possible_neighbors.add(dist['site_b'])
            elif dist['site_b'] == site_id and dist['site_a'] not in forbidden:
                possible_neighbors.add(dist['site_a'])

        possible_count = len(possible_neighbors)
        feasible = min_links <= possible_count

        return feasible, possible_count

    @staticmethod
    def build_adjacency_list(links: List[Dict]) -> Dict[str, Set[str]]:
        """
        Construit une liste d'adjacence à partir des liens.

        Args:
            links: Liste des liens actifs

        Returns:
            Dict {site_id: set(voisins)}
        """
        adj = {}

        for link in links:
            if link.get('status') != 'active':
                continue

            site_a = link['site_a']
            site_b = link['site_b']

            if site_a not in adj:
                adj[site_a] = set()
            if site_b not in adj:
                adj[site_b] = set()

            adj[site_a].add(site_b)
            adj[site_b].add(site_a)

        return adj

    @staticmethod
    def get_site_degree(site_id: str, adj_list: Dict[str, Set[str]]) -> int:
        """Retourne le degré (nombre de liaisons) d'un site."""
        return len(adj_list.get(site_id, set()))

    @staticmethod
    def can_add_edge(
        site_a: str,
        site_b: str,
        sites_dict: Dict[str, Dict],
        adj_list: Dict[str, Set[str]],
        parent_child_map: Dict[str, str]
    ) -> bool:
        """
        Vérifie si une arête peut être ajoutée.

        Args:
            site_a, site_b: IDs des sites
            sites_dict: Dictionnaire des sites
            adj_list: Liste d'adjacence courante
            parent_child_map: Mapping parent -> enfant

        Returns:
            True si l'arête peut être ajoutée
        """
        # Vérifier que les deux sites existent
        if site_a not in sites_dict or site_b not in sites_dict:
            return False

        # Vérifier max_links
        degree_a = len(adj_list.get(site_a, set()))
        degree_b = len(adj_list.get(site_b, set()))

        max_a = sites_dict[site_a].get('max_links', float('inf'))
        max_b = sites_dict[site_b].get('max_links', float('inf'))

        if degree_a >= max_a or degree_b >= max_b:
            return False

        # Vérifier relation parent-enfant
        parent_a = parent_child_map.get(site_a)
        parent_b = parent_child_map.get(site_b)

        # A ne peut pas être lié à son parent ou ses enfants
        if parent_a == site_b or parent_b == site_a:
            return False

        # Vérifier si déjà connecté
        if site_b in adj_list.get(site_a, set()):
            return False

        return True
