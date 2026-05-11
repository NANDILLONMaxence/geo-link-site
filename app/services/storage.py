"""
Service de gestion des données : import/export CSV et JSON.
VERSION ÉTENDUE avec support liaisons manuelles
"""
import json
import csv
from io import StringIO
from datetime import datetime
from typing import Dict, List, Tuple
from .convert import converter


class DataStorage:
    """Gestionnaire de stockage et d'import/export."""

    @staticmethod
    def parse_csv(csv_content: str) -> Tuple[List[Dict], List[Dict], str]:
        """Parse CSV basique (rétrocompatibilité)."""
        sites, links, manual_links, error = DataStorage.parse_csv_extended(csv_content)
        # Fusionner tous les liens
        all_links = links + manual_links
        return sites, all_links, error

    @staticmethod
    def parse_csv_extended(csv_content: str) -> Tuple[List[Dict], List[Dict], List[Dict], str]:
        """
        Parse un CSV combiné contenant sites et links (auto + manuels).

        Returns:
            (sites, auto_links, manual_links, error_message)
        """
        sites = []
        auto_links = []
        manual_links = []
        errors = []

        try:
            reader = csv.DictReader(StringIO(csv_content))

            for row in reader:
                row_type = row.get('type', '').strip()

                if row_type == 'site':
                    try:
                        # Essayer de lire les coordonnées DMS
                        lat_dms = row.get('lat_dms', '').strip()
                        lng_dms = row.get('lng_dms', '').strip()

                        if lat_dms and lng_dms:
                            # Coordonnées DMS disponibles
                            lng, lat = converter.dms_to_decimal(lat_dms, lng_dms)
                        else:
                            # Fallback: coordonnées décimales
                            lat = float(row.get('lat', 0))
                            lng = float(row.get('lng', 0))
                            lat_dms = converter.decimal_to_dms(lat, 'lat')
                            lng_dms = converter.decimal_to_dms(lng, 'lng')

                        site = {
                            'id': row.get('id', row.get('name', '')).strip(),
                            'lat_dms': lat_dms,
                            'lng_dms': lng_dms,
                            'lat': round(lat, 6),
                            'lng': round(lng, 6),
                            'min_links': int(row.get('min_links', 0)),
                            'max_links': int(row.get('max_links', 2)),
                            'link_ids': [],
                            'status': 'ok'
                        }
                        sites.append(site)
                    except Exception as e:
                        errors.append(f"Erreur site ligne {reader.line_num}: {e}")

                elif row_type == 'link':
                    try:
                        link_type = row.get('link_type', 'auto').strip()
                        is_manual = row.get('manual', 'false').strip().lower() == 'true'

                        link = {
                            'id': row.get('id', '').strip(),
                            'site_a': row.get('site_a', '').strip(),
                            'site_b': row.get('site_b', '').strip(),
                            'distance_km': float(row.get('distance_km', 0)),
                            'status': row.get('status', 'active').strip(),
                            'type': link_type if link_type else ('manual' if is_manual else 'auto')
                        }

                        # Déterminer si manuel ou auto
                        if link['type'] == 'manual' or is_manual or link['id'].startswith('manual_'):
                            manual_links.append(link)
                        else:
                            auto_links.append(link)

                    except Exception as e:
                        errors.append(f"Erreur link ligne {reader.line_num}: {e}")

            if len(sites) > 55:
                return [], [], [], "Erreur: Maximum 55 sites autorisés"

            error_msg = "; ".join(errors) if errors else ""
            return sites, auto_links, manual_links, error_msg

        except Exception as e:
            return [], [], [], f"Erreur parsing CSV: {str(e)}"

    @staticmethod
    def export_csv_extended(sites: List[Dict], auto_links: List[Dict], manual_links: List[Dict]) -> str:
        """
        Exporte les données en format CSV combiné étendu.

        Args:
            sites: Liste des sites
            auto_links: Liste des liens automatiques
            manual_links: Liste des liens manuels

        Returns:
            Contenu CSV
        """
        output = StringIO()

        fieldnames = [
            'type', 'id', 'name', 'x_l93', 'y_l93', 'lat', 'lng',
            'min_links', 'max_links', 'link_ids',
            'site_a', 'site_b', 'distance_km', 'status', 'link_type', 'manual', 'excluded'
        ]

        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        # Écrire les sites
        for site in sites:
            link_ids_str = ';'.join(site.get('link_ids', []))
            writer.writerow({
                'type': 'site',
                'id': site['id'],
                'name': site['id'],
                'lat_dms': site.get('lat_dms', ''),
                'lng_dms': site.get('lng_dms', ''),
                'lat': site['lat'],
                'lng': site['lng'],
                'min_links': site.get('min_links', 0),
                'max_links': site.get('max_links', 2),
                'link_ids': link_ids_str,
                'site_a': '',
                'site_b': '',
                'distance_km': '',
                'status': site.get('status', 'ok'),
                'link_type': '',
                'manual': '',
                'excluded': ''
            })

        # Écrire les liens auto
        for link in auto_links:
            writer.writerow({
                'type': 'link',
                'id': link['id'],
                'name': '',
                'x_l93': '',
                'y_l93': '',
                'lat': '',
                'lng': '',
                'min_links': '',
                'max_links': '',
                'link_ids': '',
                'site_a': link['site_a'],
                'site_b': link['site_b'],
                'distance_km': link['distance_km'],
                'status': link.get('status', 'active'),
                'link_type': 'auto',
                'manual': 'false',
                'excluded': 'true' if link.get('status') == 'excluded' else 'false'
            })

        # Écrire les liens manuels
        for link in manual_links:
            writer.writerow({
                'type': 'link',
                'id': link['id'],
                'name': '',
                'x_l93': '',
                'y_l93': '',
                'lat': '',
                'lng': '',
                'min_links': '',
                'max_links': '',
                'link_ids': '',
                'site_a': link['site_a'],
                'site_b': link['site_b'],
                'distance_km': link['distance_km'],
                'status': link.get('status', 'active'),
                'link_type': 'manual',
                'manual': 'true',
                'excluded': 'true' if link.get('status') == 'excluded' else 'false'
            })

        return output.getvalue()

    @staticmethod
    def parse_json_extended(json_content: str) -> Tuple[List[Dict], List[Dict], List[Dict], Dict, List[str], str]:
        """
        Parse un fichier JSON/GeoJSON de sauvegarde étendu.
        Supporte à la fois l'ancien format JSON et le nouveau format GeoJSON.

        Returns:
            (sites, auto_links, manual_links, params, excluded_links, error_message)
        """
        try:
            data = json.loads(json_content)

            # Déterminer le format (GeoJSON ou ancien JSON)
            if data.get('type') == 'FeatureCollection':
                # Nouveau format GeoJSON
                return DataStorage._parse_geojson(data)
            else:
                # Ancien format JSON (rétrocompatibilité)
                sites = data.get('sites', [])
                auto_links = data.get('links', data.get('auto_links', []))
                manual_links = data.get('manual_links', [])
                params = data.get('params', {})
                excluded_links = data.get('exclusions', {}).get('links', [])

                if len(sites) > 55:
                    return [], [], [], {}, [], "Erreur: Maximum 55 sites autorisés"

                return sites, auto_links, manual_links, params, excluded_links, ""

        except Exception as e:
            return [], [], [], {}, [], f"Erreur parsing JSON: {str(e)}"

    @staticmethod
    def _parse_geojson(geojson_data: Dict) -> Tuple[List[Dict], List[Dict], List[Dict], Dict, List[str], str]:
        """
        Parse un GeoJSON et extrait sites, liens, paramètres.

        Returns:
            (sites, auto_links, manual_links, params, excluded_links, error_message)
        """
        sites = []
        auto_links = []
        manual_links = []

        features = geojson_data.get('features', [])

        for feature in features:
            geom_type = feature.get('geometry', {}).get('type')
            props = feature.get('properties', {})

            if geom_type == 'Point':
                # C'est un site
                coords = feature['geometry']['coordinates']  # [lng, lat]

                site = {
                    'id': props.get('id'),
                    'lat_dms': props.get('lat_dms', ''),
                    'lng_dms': props.get('lng_dms', ''),
                    'lat': coords[1],
                    'lng': coords[0],
                    'min_links': props.get('min_links', 0),
                    'max_links': props.get('max_links', 2),
                    'link_ids': props.get('link_ids', []),
                    'status': props.get('status', 'ok')
                }
                sites.append(site)

            elif geom_type == 'LineString':
                # C'est une liaison
                link = {
                    'id': props.get('id'),
                    'site_a': props.get('site_a'),
                    'site_b': props.get('site_b'),
                    'distance_km': props.get('distance_km'),
                    'status': props.get('status', 'active'),
                    'type': props.get('link_type', 'auto')
                }

                if props.get('link_type') == 'manual' or props.get('manual') is True:
                    manual_links.append(link)
                else:
                    auto_links.append(link)

        # Extraire les métadonnées
        params = geojson_data.get('properties', {}).get('params', {})
        excluded_links = geojson_data.get('properties', {}).get('exclusions', {}).get('links', [])
        if len(sites) > 55:
            return [], [], [], {}, [], "Erreur: Maximum 55 sites autorisés"

        return sites, auto_links, manual_links, params, excluded_links, ""

    @staticmethod
    def export_json_extended(
        sites: List[Dict],
        auto_links: List[Dict],
        manual_links: List[Dict],
        params: Dict,
        exclusions: List[str]
    ) -> str:
        """
        Exporte les données en format GeoJSON.
        Compatible avec QGIS, ArcGIS, et autres outils SIG.

        Args:
            sites: Liste des sites
            auto_links: Liste des liens automatiques
            manual_links: Liste des liens manuels
            params: Paramètres de génération
            exclusions: Liste des IDs de liens exclus

        Returns:
            Contenu GeoJSON
        """
        features = []

        # Ajouter les sites comme features Point
        for site in sites:
            feature = {
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [site['lng'], site['lat']]
                },
                'properties': {
                    'id': site['id'],
                    'lat_dms': site.get('lat_dms', ''),
                    'lng_dms': site.get('lng_dms', ''),
                    'min_links': site.get('min_links', 0),
                    'max_links': site.get('max_links', 2),
                    'link_ids': site.get('link_ids', []),
                    'status': site.get('status', 'ok'),
                    'feature_type': 'site'
                }
            }
            features.append(feature)

        # Créer un dictionnaire des sites pour les coordonnées
        sites_dict = {s['id']: s for s in sites}

        # Ajouter les liens auto comme features LineString
        for link in auto_links:
            site_a = sites_dict.get(link['site_a'])
            site_b = sites_dict.get(link['site_b'])

            if site_a and site_b:
                feature = {
                    'type': 'Feature',
                    'geometry': {
                        'type': 'LineString',
                        'coordinates': [
                            [site_a['lng'], site_a['lat']],
                            [site_b['lng'], site_b['lat']]
                        ]
                    },
                    'properties': {
                        'id': link['id'],
                        'site_a': link['site_a'],
                        'site_b': link['site_b'],
                        'distance_km': link['distance_km'],
                        'status': link.get('status', 'active'),
                        'link_type': 'auto',
                        'manual': False,
                        'excluded': link.get('status') == 'excluded',
                        'feature_type': 'link'
                    }
                }
                features.append(feature)

        # Ajouter les liens manuels comme features LineString
        for link in manual_links:
            site_a = sites_dict.get(link['site_a'])
            site_b = sites_dict.get(link['site_b'])

            if site_a and site_b:
                feature = {
                    'type': 'Feature',
                    'geometry': {
                        'type': 'LineString',
                        'coordinates': [
                            [site_a['lng'], site_a['lat']],
                            [site_b['lng'], site_b['lat']]
                        ]
                    },
                    'properties': {
                        'id': link['id'],
                        'site_a': link['site_a'],
                        'site_b': link['site_b'],
                        'distance_km': link['distance_km'],
                        'status': link.get('status', 'active'),
                        'link_type': 'manual',
                        'manual': True,
                        'excluded': link.get('status') == 'excluded',
                        'feature_type': 'link'
                    }
                }
                features.append(feature)

        # Construire le GeoJSON complet
        geojson = {
            'type': 'FeatureCollection',
            'properties': {
                'meta': {
                    'created': datetime.now().isoformat(),
                    'app_version': '2.0',
                    'format': 'GeoJSON',
                    'crs': 'EPSG:4326'
                },
                'params': params,
                'exclusions': {
                    'links': exclusions
                },
                'statistics': {
                    'total_sites': len(sites),
                    'total_auto_links': len(auto_links),
                    'total_manual_links': len(manual_links),
                    'active_auto_links': sum(1 for lnk in auto_links if lnk.get('status') == 'active'),
                    'active_manual_links': sum(1 for lnk in manual_links if lnk.get('status') == 'active'),
                    'excluded_links': len(exclusions)
                }
            },
            'features': features
        }

        return json.dumps(geojson, indent=2, ensure_ascii=False)

    @staticmethod
    def export_html(sites: List[Dict], links: List[Dict]) -> str:
        """
        Génère un fichier HTML statique avec la carte.
        Affiche uniquement les liaisons actives.
        """
        features = []

        # Ajouter les sites comme points
        for site in sites:
            # Compter les liaisons actives
            active_links_count = sum(1 for lnk in links if lnk.get('status') == 'active' and (lnk['site_a'] == site['id'] or lnk['site_b'] == site['id']))

            features.append({
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [site['lng'], site['lat']]
                },
                'properties': {
                    'id': site['id'],
                    'type': 'site',
                    'status': site.get('status', 'ok'),
                    'min_links': site.get('min_links', 0),
                    'max_links': site.get('max_links', 2),
                    'active_links': active_links_count
                }
            })

        # Ajouter les liens comme lignes (UNIQUEMENT ACTIFS)
        sites_dict = {s['id']: s for s in sites}
        for link in links:
            if link.get('status') != 'active':
                continue

            site_a = sites_dict.get(link['site_a'])
            site_b = sites_dict.get(link['site_b'])

            if site_a and site_b:
                # Déterminer la couleur selon le type
                link_type = link.get('type', 'auto')
                color = '#0066cc' if link_type == 'manual' else '#000'

                features.append({
                    'type': 'Feature',
                    'geometry': {
                        'type': 'LineString',
                        'coordinates': [
                            [site_a['lng'], site_a['lat']],
                            [site_b['lng'], site_b['lat']]
                        ]
                    },
                    'properties': {
                        'id': link['id'],
                        'type': 'link',
                        'link_type': link_type,
                        'distance_km': link['distance_km'],
                        'site_a': link['site_a'],
                        'site_b': link['site_b'],
                        'color': color
                    }
                })

        geojson_data = json.dumps({
            'type': 'FeatureCollection',
            'features': features
        })

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Carte Geo Site - Export</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body {{ margin: 0; padding: 0; }}
        #map {{ position: absolute; top: 0; bottom: 0; width: 100%; }}
        .site-label {{
            background: white;
            border: 1px solid #333;
            border-radius: 3px;
            padding: 2px 5px;
            font-size: 11px;
            font-weight: bold;
        }}
        .legend {{
            position: absolute;
            bottom: 30px;
            right: 10px;
            background: white;
            padding: 10px;
            border-radius: 5px;
            box-shadow: 0 0 15px rgba(0,0,0,0.2);
            z-index: 1000;
        }}
        .legend-item {{
            margin: 5px 0;
            display: flex;
            align-items: center;
        }}
        .legend-line {{
            width: 30px;
            height: 3px;
            margin-right: 8px;
        }}
    </style>
</head>
<body>
    <div id="map"></div>
    <div class="legend">
        <div class="legend-item">
            <div class="legend-line" style="background:#000"></div>
            <span>Liaison auto</span>
        </div>
        <div class="legend-item">
            <div class="legend-line" style="background:#0066cc"></div>
            <span>Liaison manuelle</span>
        </div>
    </div>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        var map = L.map('map').setView([46.5, 2.5], 6);

        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '© OpenStreetMap contributors'
        }}).addTo(map);

        var geojsonData = {geojson_data};

        L.geoJSON(geojsonData, {{
            pointToLayer: function(feature, latlng) {{
                if (feature.properties.type === 'site') {{
                    var marker = L.circleMarker(latlng, {{
                        radius: 6,
                        fillColor: feature.properties.status === 'error' ? '#ff0000' : '#ff0000',
                        color: '#000',
                        weight: 1,
                        opacity: 1,
                        fillOpacity: 0.8
                    }});

                    marker.bindTooltip(feature.properties.id, {{
                        permanent: true,
                        direction: 'right',
                        className: 'site-label'
                    }});

                    // Popup avec informations détaillées
                    var popupContent = '<div style="font-size:12px;">' +
                        '<strong>' + feature.properties.id + '</strong><br>' +
                        'Lat: ' + latlng.lat.toFixed(6) + '<br>' +
                        'Lng: ' + latlng.lng.toFixed(6) + '<br>' +
                        'Min/Max liens: ' + feature.properties.min_links + '/' + feature.properties.max_links + '<br>' +
                        'Liaisons actives: ' + feature.properties.active_links +
                        '</div>';
                    marker.bindPopup(popupContent);

                    return marker;
                }}
            }},
            style: function(feature) {{
                if (feature.geometry.type === 'LineString') {{
                    return {{
                        color: feature.properties.color || '#000',
                        weight: 2,
                        opacity: 0.7
                    }};
                }}
            }},
            onEachFeature: function(feature, layer) {{
                if (feature.properties.type === 'link') {{
                    var midpoint = L.latLngBounds(layer.getLatLngs()).getCenter();
                    var distance = feature.properties.distance_km;
                    var linkType = feature.properties.link_type === 'manual' ? ' (M)' : '';

                    // Label distance
                    L.marker(midpoint, {{
                        icon: L.divIcon({{
                            className: 'distance-label',
                            html: '<div style="background:white;padding:2px 4px;border:1px solid #666;border-radius:3px;font-size:10px;">' +
                                  distance.toFixed(1) + ' km' + linkType + '</div>',
                            iconSize: [70, 20]
                        }})
                    }}).addTo(map);

                    // Popup détaillé pour la liaison
                    var typeText = feature.properties.link_type === 'manual' ? 'Manuelle' : 'Automatique';
                    var popupContent = '<div style="font-size:12px;">' +
                        '<strong>ID:</strong> ' + feature.properties.id + '<br>' +
                        '<strong>Type:</strong> ' + typeText + '<br>' +
                        '<strong>Site A:</strong> ' + feature.properties.site_a + '<br>' +
                        '<strong>Site B:</strong> ' + feature.properties.site_b + '<br>' +
                        '<strong>Distance:</strong> ' + distance.toFixed(2) + ' km<br>' +
                        '<strong>Statut:</strong> Actif' +
                        '</div>';
                    layer.bindPopup(popupContent);
                }}
            }}
        }}).addTo(map);

        if (geojsonData.features.length > 0) {{
            var bounds = L.geoJSON(geojsonData).getBounds();
            map.fitBounds(bounds, {{ padding: [50, 50] }});
        }}
    </script>
</body>
</html>"""

        return html


# Instance globale
storage = DataStorage()
