"""
Service de conversion de coordonnées DMS vers WGS84 décimal
et calculs de distances géodésiques.
"""
from pyproj import Geod
from typing import Tuple
import re


class CoordinateConverter:
    """Convertisseur de coordonnées et calculateur de distances."""
    
    def __init__(self):
        # Calculateur de distances géodésiques
        self.geod = Geod(ellps="WGS84")
    
    def parse_dms(self, dms_string: str) -> float:
        """
        Parse une chaîne DMS et retourne une valeur décimale.
        
        Formats acceptés :
        - 47°50'44.56"
        - 47° 50' 44.56"
        - 47 50 44.56
        - 47°50'44.56''
        
        Args:
            dms_string: Chaîne au format DMS
            
        Returns:
            Valeur décimale (float)
        """
        # Nettoyer la chaîne
        dms_string = dms_string.strip()
        
        # Remplacer les séparateurs par des espaces
        dms_string = re.sub(r'[°\'"\s]+', ' ', dms_string)
        dms_string = dms_string.strip()
        
        # Séparer les composants
        parts = dms_string.split()
        
        if len(parts) < 1:
            raise ValueError("Format DMS invalide")
        
        try:
            degrees = float(parts[0])
            minutes = float(parts[1]) if len(parts) > 1 else 0
            seconds = float(parts[2]) if len(parts) > 2 else 0
            
            # Calculer la valeur décimale
            decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
            
            return decimal
            
        except (ValueError, IndexError) as e:
            raise ValueError(f"Erreur de parsing DMS: {str(e)}")
    
    def parse_dms_coordinate(self, dms_string: str, coord_type: str) -> float:
        """
        Parse une coordonnée DMS complète avec direction (N/S/E/W).
        
        Args:
            dms_string: Chaîne comme "47°50'44.56''N" ou "2°20'30''E"
            coord_type: 'lat' ou 'lng'
            
        Returns:
            Valeur décimale avec signe approprié
        """
        dms_string = dms_string.strip().upper()
        
        # Détecter la direction
        direction = None
        if dms_string[-1] in ['N', 'S', 'E', 'W']:
            direction = dms_string[-1]
            dms_string = dms_string[:-1]
        
        # Parser la valeur
        decimal = self.parse_dms(dms_string)
        
        # Appliquer le signe selon la direction
        if direction in ['S', 'W']:
            decimal = -decimal
        
        # Validation
        if coord_type == 'lat':
            if abs(decimal) > 90:
                raise ValueError(f"Latitude invalide: {decimal} (doit être entre -90 et 90)")
            if direction and direction not in ['N', 'S']:
                raise ValueError(f"Direction latitude invalide: {direction} (doit être N ou S)")
        elif coord_type == 'lng':
            if abs(decimal) > 180:
                raise ValueError(f"Longitude invalide: {decimal} (doit être entre -180 et 180)")
            if direction and direction not in ['E', 'W']:
                raise ValueError(f"Direction longitude invalide: {direction} (doit être E ou W)")
        
        return decimal
    
    def decimal_to_dms(self, decimal: float, coord_type: str) -> str:
        """
        Convertit une valeur décimale en format DMS.
        
        Args:
            decimal: Valeur décimale
            coord_type: 'lat' ou 'lng'
            
        Returns:
            Chaîne formatée comme "47°50'44.56''N"
        """
        # Déterminer la direction
        if coord_type == 'lat':
            direction = 'N' if decimal >= 0 else 'S'
        else:
            direction = 'E' if decimal >= 0 else 'W'
        
        # Travailler avec la valeur absolue
        decimal = abs(decimal)
        
        # Extraire degrés, minutes, secondes
        degrees = int(decimal)
        minutes_decimal = (decimal - degrees) * 60
        minutes = int(minutes_decimal)
        seconds = (minutes_decimal - minutes) * 60
        
        # Formater
        return f"{degrees}°{minutes:02d}'{seconds:05.2f}''{direction}"
    
    def dms_to_decimal(self, lat_dms: str, lng_dms: str) -> Tuple[float, float]:
        """
        Convertit des coordonnées DMS en décimales WGS84.
        
        Args:
            lat_dms: Latitude DMS (ex: "47°50'44.56''N")
            lng_dms: Longitude DMS (ex: "2°20'30''E")
            
        Returns:
            Tuple (longitude, latitude) en décimal
        """
        try:
            lat = self.parse_dms_coordinate(lat_dms, 'lat')
            lng = self.parse_dms_coordinate(lng_dms, 'lng')
            return lng, lat
        except Exception as e:
            raise ValueError(f"Erreur de conversion DMS: {str(e)}")
    
    def calculate_geodesic_distance(
        self, 
        lon1: float, 
        lat1: float, 
        lon2: float, 
        lat2: float
    ) -> float:
        """
        Calcule la distance géodésique entre deux points WGS84.
        
        Args:
            lon1, lat1: Coordonnées du premier point (décimales)
            lon2, lat2: Coordonnées du second point (décimales)
            
        Returns:
            Distance en kilomètres (float)
        """
        try:
            # azimuth1, azimuth2, distance en mètres
            _, _, distance_m = self.geod.inv(lon1, lat1, lon2, lat2)
            # Convertir en km
            return distance_m / 1000.0
        except Exception as e:
            raise ValueError(f"Erreur de calcul de distance: {str(e)}")
    
    def calculate_distance_from_dms(
        self,
        lat1_dms: str,
        lng1_dms: str,
        lat2_dms: str,
        lng2_dms: str
    ) -> float:
        """
        Calcule la distance entre deux points donnés en DMS.
        
        Args:
            lat1_dms, lng1_dms: Coordonnées DMS du premier point
            lat2_dms, lng2_dms: Coordonnées DMS du second point
            
        Returns:
            Distance en kilomètres (float)
        """
        # Convertir les deux points
        lon1, lat1 = self.dms_to_decimal(lat1_dms, lng1_dms)
        lon2, lat2 = self.dms_to_decimal(lat2_dms, lng2_dms)
        
        # Calculer la distance géodésique
        return self.calculate_geodesic_distance(lon1, lat1, lon2, lat2)


# Instance globale
converter = CoordinateConverter()
