"""
Algorithme Greedy avec contraintes de degré.
Ajoute les arêtes les plus courtes tout en respectant les contraintes.
"""
from typing import List, Dict, Tuple, Set
from ..services.compute import GraphComputer


class GreedyDegreeConstrained:
    """Algorithme glouton avec contraintes de degré."""
    
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
        Génère les liaisons en mode greedy.
        
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
        
        sites_dict = {s['id']: s for s in sites}
        
        available_distances = [
            d for d in distances 
            if f"{d['site_a']}-{d['site_b']}" not in excluded_links and
               f"{d['site_b']}-{d['site_a']}" not in excluded_links
        ]
        
        if not available_distances:
            self.logs.append("Aucune distance disponible")
            return [], self.logs, {}
        
        if favor_shortest:
            available_distances.sort(key=lambda x: x['distance_km'])
        
        self.logs.append(f"Sites: {len(sites)}, Distances possibles: {len(available_distances)}")
        
        links = []
        adj_list = {}
        parent_child_map = {}
        
        self._ensure_connectivity(
            sites_dict, available_distances, links, adj_list, parent_child_map
        )
        
        self.logs.append(f"Après connectivité: {len(links)} liaisons")
        
        self._greedy_augmentation(
            sites_dict, available_distances, links, adj_list, parent_child_map
        )
        
        self.logs.append(f"Total final: {len(links)} liaisons")
        
        self._update_site_links(sites_dict, links)
        
        return links, self.logs, parent_child_map
    
    def _ensure_connectivity(
        self,
        sites_dict: Dict[str, Dict],
        distances: List[Dict],
        links: List[Dict],
        adj_list: Dict[str, Set[str]],
        parent_child_map: Dict[str, str]
    ):
        """Assure que tous les sites sont connectés."""
        connected = set()
        
        for dist in distances:
            site_a = dist['site_a']
            site_b = dist['site_b']
            
            needs_connection = (
                site_a not in connected or 
                site_b not in connected
            )
            
            if needs_connection:
                if self.computer.can_add_edge(
                    site_a, site_b, sites_dict, adj_list, parent_child_map
                ):
                    link = {
                        'id': self.computer.generate_edge_id(),
                        'site_a': site_a,
                        'site_b': site_b,
                        'distance_km': dist['distance_km'],
                        'status': 'active'
                    }
                    links.append(link)
                    
                    if site_a not in adj_list:
                        adj_list[site_a] = set()
                    if site_b not in adj_list:
                        adj_list[site_b] = set()
                    adj_list[site_a].add(site_b)
                    adj_list[site_b].add(site_a)
                    
                    if site_b not in connected and site_a in connected:
                        parent_child_map[site_b] = site_a
                    elif site_a not in connected and site_b in connected:
                        parent_child_map[site_a] = site_b
                    elif site_a not in connected and site_b not in connected:
                        parent_child_map[site_b] = site_a
                    
                    connected.add(site_a)
                    connected.add(site_b)
            
            if len(connected) == len(sites_dict):
                break
    
    def _greedy_augmentation(
        self,
        sites_dict: Dict[str, Dict],
        distances: List[Dict],
        links: List[Dict],
        adj_list: Dict[str, Set[str]],
        parent_child_map: Dict[str, str]
    ):
        """Ajoute des arêtes de manière gloutonne."""
        for dist in distances:
            site_a = dist['site_a']
            site_b = dist['site_b']
            
            if site_b in adj_list.get(site_a, set()):
                continue
            
            if self.computer.can_add_edge(
                site_a, site_b, sites_dict, adj_list, parent_child_map
            ):
                degree_a = len(adj_list.get(site_a, set()))
                degree_b = len(adj_list.get(site_b, set()))
                min_a = sites_dict[site_a].get('min_links', 0)
                min_b = sites_dict[site_b].get('min_links', 0)
                
                helps_min_links = (degree_a < min_a or degree_b < min_b)
                
                if helps_min_links or (degree_a < min_a + 1 and degree_b < min_b + 1):
                    link = {
                        'id': self.computer.generate_edge_id(),
                        'site_a': site_a,
                        'site_b': site_b,
                        'distance_km': dist['distance_km'],
                        'status': 'active'
                    }
                    links.append(link)
                    
                    if site_a not in adj_list:
                        adj_list[site_a] = set()
                    if site_b not in adj_list:
                        adj_list[site_b] = set()
                    adj_list[site_a].add(site_b)
                    adj_list[site_b].add(site_a)
                    
                    self.logs.append(
                        f"Ajout greedy {site_a}-{site_b} ({dist['distance_km']:.2f} km)"
                    )
    
    def _update_site_links(self, sites_dict: Dict[str, Dict], links: List[Dict]):
        """Met à jour les link_ids dans chaque site."""
        for site in sites_dict.values():
            site['link_ids'] = []
        
        for link in links:
            if link.get('status') == 'active':
                sites_dict[link['site_a']]['link_ids'].append(link['id'])
                sites_dict[link['site_b']]['link_ids'].append(link['id'])
