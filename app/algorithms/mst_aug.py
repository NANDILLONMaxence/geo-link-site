"""
Algorithme MST + Augmentation.
Construit un arbre couvrant minimum puis ajoute des arêtes pour satisfaire
les contraintes de connectivité.
"""
import networkx as nx
from typing import List, Dict, Tuple, Set
from ..services.compute import GraphComputer


class MSTAugmentation:
    """Algorithme MST avec augmentation pour k-connectivité."""

    def __init__(self):
        self.computer = GraphComputer()
        self.logs = []

    def generate(
        self,
        sites: List[Dict],
        distances: List[Dict],
        favor_shortest: bool = True,
        excluded_links: Set[str] = None
    ) -> Tuple[List[Dict], List[str], Dict[str, str]]:
        """
        Génère les liaisons en utilisant MST + augmentation.

        Args:
            sites: Liste des sites
            distances: Liste des distances possibles
            favor_shortest: Favoriser les distances courtes
            excluded_links: Set des IDs de liens à exclure

        Returns:
            (links, logs, parent_child_map)
        """
        self.logs = []
        excluded_links = excluded_links or set()

        # Créer dictionnaire des sites
        sites_dict = {s['id']: s for s in sites}

        # Filtrer les distances exclues
        available_distances = [
            d for d in distances
            if f"{d['site_a']}-{d['site_b']}" not in excluded_links and
               f"{d['site_b']}-{d['site_a']}" not in excluded_links
        ]

        if not available_distances:
            self.logs.append("Aucune distance disponible")
            return [], self.logs, {}

        # Trier par distance si demandé
        if favor_shortest:
            available_distances.sort(key=lambda x: x['distance_km'])

        self.logs.append(f"Sites: {len(sites)}, Distances possibles: {len(available_distances)}")

        # Étape 1: Construire le MST
        links, parent_child_map = self._build_mst(sites_dict, available_distances)
        self.logs.append(f"MST construit: {len(links)} liaisons")

        # Étape 2: Augmentation pour satisfaire min_links
        adj_list = self.computer.build_adjacency_list(links)
        links = self._augment_for_min_links(
            sites_dict,
            available_distances,
            links,
            adj_list,
            parent_child_map
        )

        self.logs.append(f"Après augmentation: {len(links)} liaisons totales")

        # Mettre à jour les link_ids des sites
        self._update_site_links(sites_dict, links)

        return links, self.logs, parent_child_map

    def _build_mst(
        self,
        sites_dict: Dict[str, Dict],
        distances: List[Dict]
    ) -> Tuple[List[Dict], Dict[str, str]]:
        """Construit un arbre couvrant minimum."""
        G = nx.Graph()

        # Ajouter tous les sites comme nœuds
        for site_id in sites_dict.keys():
            G.add_node(site_id)

        # Ajouter toutes les arêtes avec poids = distance
        for dist in distances:
            G.add_edge(
                dist['site_a'],
                dist['site_b'],
                weight=dist['distance_km'],
                distance_km=dist['distance_km']
            )

        # Calculer le MST
        try:
            mst = nx.minimum_spanning_tree(G, weight='weight')
        except nx.NetworkXException:
            self.logs.append("Impossible de créer MST (graphe non connexe)")
            return [], {}

        # Convertir en liste de liens
        links = []
        parent_child_map = {}

        # Parcours BFS pour définir parent/enfant
        if len(mst.nodes()) > 0:
            root = list(mst.nodes())[0]
            visited = {root}
            queue = [root]

            while queue:
                current = queue.pop(0)

                for neighbor in mst.neighbors(current):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)

                        # Définir relation parent-enfant
                        parent_child_map[neighbor] = current

                        # Créer le lien
                        edge_data = mst.get_edge_data(current, neighbor)
                        link = {
                            'id': self.computer.generate_edge_id(),
                            'site_a': current,
                            'site_b': neighbor,
                            'distance_km': edge_data['distance_km'],
                            'status': 'active'
                        }
                        links.append(link)

        return links, parent_child_map

    def _augment_for_min_links(
        self,
        sites_dict: Dict[str, Dict],
        distances: List[Dict],
        current_links: List[Dict],
        adj_list: Dict[str, Set[str]],
        parent_child_map: Dict[str, str]
    ) -> List[Dict]:
        """Augmente le graphe pour satisfaire min_links."""
        links = list(current_links)

        # Trier les distances par ordre croissant
        sorted_distances = sorted(distances, key=lambda x: x['distance_km'])

        # Identifier les sites qui ne satisfont pas min_links
        max_iterations = len(sorted_distances)
        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            added = False

            for site_id, site in sites_dict.items():
                if site.get('status') == 'error':
                    continue

                min_links = site.get('min_links', 0)
                current_degree = len(adj_list.get(site_id, set()))

                if current_degree < min_links:
                    # Chercher une arête à ajouter
                    for dist in sorted_distances:
                        if dist['site_a'] == site_id:
                            other = dist['site_b']
                        elif dist['site_b'] == site_id:
                            other = dist['site_a']
                        else:
                            continue

                        # Vérifier si on peut ajouter cette arête
                        if self.computer.can_add_edge(
                            site_id, other, sites_dict, adj_list, parent_child_map
                        ):
                            # Ajouter le lien
                            link = {
                                'id': self.computer.generate_edge_id(),
                                'site_a': site_id,
                                'site_b': other,
                                'distance_km': dist['distance_km'],
                                'status': 'active'
                            }
                            links.append(link)

                            # Mettre à jour l'adjacence
                            if site_id not in adj_list:
                                adj_list[site_id] = set()
                            if other not in adj_list:
                                adj_list[other] = set()
                            adj_list[site_id].add(other)
                            adj_list[other].add(site_id)

                            added = True
                            self.logs.append(
                                f"Ajout liaison {site_id}-{other} "
                                f"({dist['distance_km']:.2f} km) pour min_links"
                            )
                            break

            if not added:
                break

        return links

    def _update_site_links(self, sites_dict: Dict[str, Dict], links: List[Dict]):
        """Met à jour les link_ids dans chaque site."""
        # Réinitialiser
        for site in sites_dict.values():
            site['link_ids'] = []

        # Remplir
        for link in links:
            if link.get('status') == 'active':
                sites_dict[link['site_a']]['link_ids'].append(link['id'])
                sites_dict[link['site_b']]['link_ids'].append(link['id'])
