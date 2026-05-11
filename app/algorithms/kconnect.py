"""
Algorithme d'approximation k-connectivity.
Augmente progressivement la connectivité du graphe.
"""
import networkx as nx
from typing import List, Dict, Tuple, Set
from ..services.compute import GraphComputer


class KConnectivityApproximation:
    """Algorithme d'approximation pour k-connectivité."""
    
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
        Génère les liaisons en visant la k-connectivité.
        
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
        
        # Trier par distance
        if favor_shortest:
            available_distances.sort(key=lambda x: x['distance_km'])
        
        self.logs.append(f"Sites: {len(sites)}, Distances possibles: {len(available_distances)}")
        
        # Phase 1: Construire graphe de base connexe
        links, parent_child_map = self._build_connected_graph(
            sites_dict, available_distances
        )
        
        self.logs.append(f"Graphe connexe: {len(links)} liaisons")
        
        # Phase 2: Augmenter la connectivité
        adj_list = self.computer.build_adjacency_list(links)
        links = self._augment_connectivity(
            sites_dict, available_distances, links, adj_list, parent_child_map
        )
        
        self.logs.append(f"Après augmentation: {len(links)} liaisons")
        
        # Mettre à jour les link_ids des sites
        self._update_site_links(sites_dict, links)
        
        return links, self.logs, parent_child_map
    
    def _build_connected_graph(
        self,
        sites_dict: Dict[str, Dict],
        distances: List[Dict]
    ) -> Tuple[List[Dict], Dict[str, str]]:
        """Construit un graphe connexe de base."""
        G = nx.Graph()
        
        for site_id in sites_dict.keys():
            G.add_node(site_id)
        
        for dist in distances:
            G.add_edge(
                dist['site_a'],
                dist['site_b'],
                weight=dist['distance_km'],
                distance_km=dist['distance_km']
            )
        
        # MST pour connexité minimale
        try:
            mst = nx.minimum_spanning_tree(G, weight='weight')
        except nx.NetworkXException:
            self.logs.append("Impossible de créer graphe connexe")
            return [], {}
        
        # Convertir en liste de liens avec parent-child
        links = []
        parent_child_map = {}
        
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
                        parent_child_map[neighbor] = current
                        
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
    
    def _augment_connectivity(
        self,
        sites_dict: Dict[str, Dict],
        distances: List[Dict],
        current_links: List[Dict],
        adj_list: Dict[str, Set[str]],
        parent_child_map: Dict[str, str]
    ) -> List[Dict]:
        """Augmente la connectivité du graphe."""
        links = list(current_links)
        
        # Créer un graphe NetworkX pour analyser la connectivité
        G = nx.Graph()
        for link in links:
            G.add_edge(link['site_a'], link['site_b'])
        
        # Calculer la connectivité actuelle
        try:
            current_connectivity = nx.node_connectivity(G)
            self.logs.append(f"Connectivité initiale: {current_connectivity}")
        except:
            current_connectivity = 0
        
        # Trier distances par ordre croissant
        sorted_distances = sorted(distances, key=lambda x: x['distance_km'])
        
        # Ajouter des arêtes pour améliorer la connectivité
        target_connectivity = min(3, len(sites_dict) - 1)  # Viser k=3 si possible
        
        for dist in sorted_distances:
            site_a = dist['site_a']
            site_b = dist['site_b']
            
            # Vérifier si l'arête existe déjà
            if G.has_edge(site_a, site_b):
                continue
            
            # Vérifier si on peut l'ajouter
            if not self.computer.can_add_edge(
                site_a, site_b, sites_dict, adj_list, parent_child_map
            ):
                continue
            
            # Tester si l'ajout améliore la connectivité
            G_test = G.copy()
            G_test.add_edge(site_a, site_b)
            
            try:
                new_connectivity = nx.node_connectivity(G_test)
            except:
                new_connectivity = current_connectivity
            
            # Vérifier aussi si cela aide à satisfaire min_links
            degree_a = len(adj_list.get(site_a, set()))
            degree_b = len(adj_list.get(site_b, set()))
            min_a = sites_dict[site_a].get('min_links', 0)
            min_b = sites_dict[site_b].get('min_links', 0)
            
            needs_more = degree_a < min_a or degree_b < min_b
            improves_connectivity = new_connectivity > current_connectivity
            
            if improves_connectivity or needs_more:
                # Ajouter le lien
                link = {
                    'id': self.computer.generate_edge_id(),
                    'site_a': site_a,
                    'site_b': site_b,
                    'distance_km': dist['distance_km'],
                    'status': 'active'
                }
                links.append(link)
                
                # Mettre à jour les structures
                G.add_edge(site_a, site_b)
                if site_a not in adj_list:
                    adj_list[site_a] = set()
                if site_b not in adj_list:
                    adj_list[site_b] = set()
                adj_list[site_a].add(site_b)
                adj_list[site_b].add(site_a)
                
                if improves_connectivity:
                    current_connectivity = new_connectivity
                    self.logs.append(
                        f"Connectivité améliorée à {current_connectivity} "
                        f"via {site_a}-{site_b}"
                    )
                
                # Arrêter si objectif atteint
                if current_connectivity >= target_connectivity:
                    # Continuer pour satisfaire min_links mais pas au-delà
                    all_satisfied = all(
                        len(adj_list.get(s['id'], set())) >= s.get('min_links', 0)
                        for s in sites_dict.values()
                    )
                    if all_satisfied:
                        break
        
        return links
    
    def _update_site_links(self, sites_dict: Dict[str, Dict], links: List[Dict]):
        """Met à jour les link_ids dans chaque site."""
        for site in sites_dict.values():
            site['link_ids'] = []
        
        for link in links:
            if link.get('status') == 'active':
                sites_dict[link['site_a']]['link_ids'].append(link['id'])
                sites_dict[link['site_b']]['link_ids'].append(link['id'])
