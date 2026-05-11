"""
Algorithmes de génération de liaisons réseau.

- MST + Augmentation : arbre couvrant minimal puis augmentation pour
  satisfaire les contraintes de degré minimum.
- Greedy : ajout glouton des arêtes les plus courtes sous contraintes.
- K-Connectivity : approximation visant une k-connectivité de nœud.
"""

from .mst_aug import MSTAugmentation
from .greedy import GreedyDegreeConstrained
from .kconnect import KConnectivityApproximation

__all__ = [
    'MSTAugmentation',
    'GreedyDegreeConstrained',
    'KConnectivityApproximation',
]
