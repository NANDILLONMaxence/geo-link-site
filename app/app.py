"""
Application Flask principale pour Geo Site - VERSION ÉTENDUE
Avec gestion des liaisons manuelles et exclusions avancées
"""
from flask import Flask, render_template, request, jsonify, send_file
from io import BytesIO

from .services.convert import converter
from .services.compute import GraphComputer
from .services.storage import storage
from .algorithms.mst_aug import MSTAugmentation
from .algorithms.greedy import GreedyDegreeConstrained
from .algorithms.kconnect import KConnectivityApproximation


app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max

# État de l'application (en mémoire)
app_state = {
    'sites': [],
    'links': [],  # Liaisons générées automatiquement
    'manual_links': [],  # Liaisons créées manuellement
    'excluded_links': set(),  # IDs des liaisons exclues
    'params': {
        'algorithm': 'mst_aug',
        'distance_max_km': None,
        'favor_shortest': True
    },
    'parent_child_map': {},
    'manual_link_counter': 0,  # Compteur pour IDs manuels
    'show_excluded': True,  # Toggle affichage exclusions
    'circles': []  # Liste des cercles {site_id, radius_km}
}


def get_all_active_links():
    """Retourne toutes les liaisons actives (auto + manuelles non exclues)."""
    all_links = []

    # Liaisons auto
    for link in app_state['links']:
        if link.get('status') == 'active':
            all_links.append(link)

    # Liaisons manuelles
    for link in app_state['manual_links']:
        if link.get('status') == 'active':
            all_links.append(link)

    return all_links


def get_all_links_including_excluded():
    """Retourne toutes les liaisons y compris exclues."""
    return app_state['links'] + app_state['manual_links']


@app.route('/')
def index():
    """Page principale."""
    return render_template('index.html')


@app.route('/status', methods=['GET'])
def get_status():
    """Retourne l'état actuel de l'application."""
    return jsonify({
        'sites': app_state['sites'],
        'links': app_state['links'],
        'manual_links': app_state['manual_links'],
        'excluded_links': list(app_state['excluded_links']),
        'params': app_state['params'],
        'show_excluded': app_state['show_excluded'],
        'circles': app_state['circles']
    })


@app.route('/import_csv', methods=['POST'])
def import_csv():
    """Importe un fichier CSV combiné."""
    try:
        file = request.files.get('file')
        if not file:
            return jsonify({'error': 'Aucun fichier fourni'}), 400

        csv_content = file.read().decode('utf-8')
        sites, links, manual_links, error_msg = storage.parse_csv_extended(csv_content)

        if error_msg:
            return jsonify({'error': error_msg}), 400

        if len(sites) > 55:
            return jsonify({'error': 'Maximum 55 sites autorisés'}), 400

        # Vérifier unicité des noms
        names = [s['id'] for s in sites]
        if len(names) != len(set(names)):
            return jsonify({'error': 'Noms de sites en double détectés'}), 400

        app_state['sites'] = sites
        app_state['links'] = links
        app_state['manual_links'] = manual_links
        app_state['excluded_links'] = set()

        # Mettre à jour le compteur manuel
        if manual_links:
            max_id = max([int(lnk['id'].replace('manual_', '')) for lnk in manual_links if lnk['id'].startswith('manual_')])
            app_state['manual_link_counter'] = max_id

        return jsonify({
            'success': True,
            'sites': sites,
            'links': links,
            'manual_links': manual_links,
            'message': f'{len(sites)} sites, {len(links)} liaisons auto et {len(manual_links)} liaisons manuelles importés'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/import_json', methods=['POST'])
def import_json():
    """Importe un fichier JSON de sauvegarde."""
    try:
        file = request.files.get('file')
        if not file:
            return jsonify({'error': 'Aucun fichier fourni'}), 400

        json_content = file.read().decode('utf-8')
        sites, links, manual_links, params, excluded, error_msg = storage.parse_json_extended(json_content)

        if error_msg:
            return jsonify({'error': error_msg}), 400

        if len(sites) > 55:
            return jsonify({'error': 'Maximum 55 sites autorisés'}), 400

        # Charger les données
        app_state['sites'] = sites
        app_state['links'] = links
        app_state['manual_links'] = manual_links
        app_state['params'].update(params)
        app_state['excluded_links'] = set(excluded)

        # Mettre à jour le compteur manuel
        if manual_links:
            max_id = max([int(lnk['id'].replace('manual_', '')) for lnk in manual_links if lnk['id'].startswith('manual_')])
            app_state['manual_link_counter'] = max_id

        return jsonify({
            'success': True,
            'sites': sites,
            'links': links,
            'manual_links': manual_links,
            'params': app_state['params'],
            'message': f'{len(sites)} sites, {len(links)} liaisons auto et {len(manual_links)} liaisons manuelles restaurés'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/add_site', methods=['POST'])
def add_site():
    """Ajoute un nouveau site."""
    try:
        data = request.get_json()

        site_id = data.get('id', '').strip()
        if not site_id:
            return jsonify({'error': 'ID manquant'}), 400

        # Vérifier unicité
        if any(s['id'] == site_id for s in app_state['sites']):
            return jsonify({'error': f'Site "{site_id}" existe déjà'}), 400

        if len(app_state['sites']) >= 55:
            return jsonify({'error': 'Maximum 55 sites atteint'}), 400

        lat_dms = data.get('lat_dms', '').strip()
        lng_dms = data.get('lng_dms', '').strip()

        # Conversion DMS vers décimal
        try:
            lng, lat = converter.dms_to_decimal(lat_dms, lng_dms)
        except ValueError as e:
            return jsonify({'error': f'Coordonnées invalides: {str(e)}'}), 400

        site = {
            'id': site_id,
            'lat_dms': lat_dms,
            'lng_dms': lng_dms,
            'lat': round(lat, 6),
            'lng': round(lng, 6),
            'min_links': int(data.get('min_links', 0)),
            'max_links': int(data.get('max_links', 2)),
            'link_ids': [],
            'status': 'ok'
        }

        app_state['sites'].append(site)

        return jsonify({
            'success': True,
            'site': site,
            'message': f'Site "{site_id}" ajouté'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/edit_site', methods=['POST'])
def edit_site():
    """Édite un site existant."""
    try:
        data = request.get_json()
        site_id = data.get('id', '').strip()

        # Trouver le site
        site = next((s for s in app_state['sites'] if s['id'] == site_id), None)
        if not site:
            return jsonify({'error': f'Site "{site_id}" introuvable'}), 404

        # Mettre à jour
        if 'lat_dms' in data and 'lng_dms' in data:
            lat_dms = data['lat_dms'].strip()
            lng_dms = data['lng_dms'].strip()

            try:
                lng, lat = converter.dms_to_decimal(lat_dms, lng_dms)
            except ValueError as e:
                return jsonify({'error': f'Coordonnées invalides: {str(e)}'}), 400

            site['lat_dms'] = lat_dms
            site['lng_dms'] = lng_dms
            site['lat'] = round(lat, 6)
            site['lng'] = round(lng, 6)

        if 'min_links' in data:
            site['min_links'] = int(data['min_links'])
        if 'max_links' in data:
            site['max_links'] = int(data['max_links'])

        return jsonify({
            'success': True,
            'site': site,
            'message': f'Site "{site_id}" mis à jour'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/delete_site', methods=['POST'])
def delete_site():
    """Supprime un site."""
    try:
        data = request.get_json()
        site_id = data.get('id', '').strip()

        # Supprimer le site
        app_state['sites'] = [s for s in app_state['sites'] if s['id'] != site_id]

        # Supprimer les liens associés (auto et manuels)
        app_state['links'] = [
            lnk for lnk in app_state['links']
            if lnk['site_a'] != site_id and lnk['site_b'] != site_id
        ]
        app_state['manual_links'] = [
            lnk for lnk in app_state['manual_links']
            if lnk['site_a'] != site_id and lnk['site_b'] != site_id
        ]

        return jsonify({
            'success': True,
            'message': f'Site "{site_id}" supprimé'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/create_manual_link', methods=['POST'])
def create_manual_link():
    """Crée une liaison manuelle entre deux sites."""
    try:
        data = request.get_json()
        site_a_id = data.get('site_a')
        site_b_id = data.get('site_b')

        if not site_a_id or not site_b_id:
            return jsonify({'error': 'Sites manquants'}), 400

        if site_a_id == site_b_id:
            return jsonify({'error': 'Un site ne peut pas être lié à lui-même'}), 400

        # Vérifier que les sites existent
        sites_dict = {s['id']: s for s in app_state['sites']}
        if site_a_id not in sites_dict or site_b_id not in sites_dict:
            return jsonify({'error': 'Un des sites n\'existe pas'}), 404

        # Vérifier qu'une liaison n'existe pas déjà
        all_links = get_all_links_including_excluded()
        for link in all_links:
            if (link['site_a'] == site_a_id and link['site_b'] == site_b_id) or \
               (link['site_a'] == site_b_id and link['site_b'] == site_a_id):
                return jsonify({'error': 'Liaison déjà existante'}), 400

        # Calculer la distance
        site_a = sites_dict[site_a_id]
        site_b = sites_dict[site_b_id]

        distance = converter.calculate_geodesic_distance(
            site_a['lng'], site_a['lat'],
            site_b['lng'], site_b['lat']
        )

        # Compter le nombre TOTAL de liaisons actives (auto + manuelles)
        def count_active_links(site_id):
            auto_count = sum(
                1 for lnk in app_state['links']
                if lnk.get('status') == 'active' and
                (lnk['site_a'] == site_id or lnk['site_b'] == site_id)
            )
            manual_count = sum(
                1 for lnk in app_state['manual_links']
                if lnk.get('status') == 'active' and
                (lnk['site_a'] == site_id or lnk['site_b'] == site_id)
            )
            return auto_count + manual_count

        degree_a = count_active_links(site_a_id)
        degree_b = count_active_links(site_b_id)

        # Vérifier si max_links sera atteint ou dépassé
        warning = None
        error = None

        if degree_a >= site_a['max_links']:
            error = f"Le site {site_a_id} a déjà atteint son maximum de liaisons ({site_a['max_links']}/{site_a['max_links']}). Veuillez supprimer d'autres liaisons avant d'en ajouter."
        elif degree_b >= site_b['max_links']:
            error = f"Le site {site_b_id} a déjà atteint son maximum de liaisons ({site_b['max_links']}/{site_b['max_links']}). Veuillez supprimer d'autres liaisons avant d'en ajouter."
        elif degree_a == site_a['max_links'] - 1 or degree_b == site_b['max_links'] - 1:
            warning = "Attention : Cette liaison atteindra le nombre maximal de connexions pour un ou plusieurs sites. Pensez à ajuster vos contraintes si vous souhaitez générer d'autres liaisons automatiques."

        # Si erreur, bloquer la création
        if error:
            return jsonify({'error': error}), 400

        # Créer la liaison manuelle
        app_state['manual_link_counter'] += 1
        manual_link = {
            'id': f"manual_{app_state['manual_link_counter']}",
            'site_a': site_a_id,
            'site_b': site_b_id,
            'distance_km': round(distance, 3),
            'status': 'active',
            'type': 'manual'
        }

        app_state['manual_links'].append(manual_link)

        return jsonify({
            'success': True,
            'link': manual_link,
            'warning': warning,
            'message': f'Liaison manuelle créée entre {site_a_id} et {site_b_id}'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/generate', methods=['POST'])
def generate_links():
    """Génère les liaisons automatiques."""
    try:
        data = request.get_json()

        # Mettre à jour les paramètres
        algorithm = data.get('algorithm', 'mst_aug')
        distance_max_km = data.get('distance_max_km')
        favor_shortest = data.get('favor_shortest', True)

        app_state['params'] = {
            'algorithm': algorithm,
            'distance_max_km': distance_max_km,
            'favor_shortest': favor_shortest
        }

        if len(app_state['sites']) < 2:
            return jsonify({'error': 'Au moins 2 sites requis'}), 400

        # Calculer toutes les distances
        computer = GraphComputer()
        all_distances = computer.calculate_all_distances(app_state['sites'])

        # Filtrer par distance max
        if distance_max_km:
            filtered_distances = computer.filter_by_distance(
                all_distances, float(distance_max_km)
            )
        else:
            filtered_distances = all_distances

        # Exclure les paires de sites qui ont déjà une liaison manuelle ACTIVE
        manual_pairs = set()
        for link in app_state['manual_links']:
            if link.get('status') == 'active':
                manual_pairs.add(frozenset([link['site_a'], link['site_b']]))

        # Filtrer les distances pour ne pas dupliquer les liaisons manuelles
        filtered_distances = [
            d for d in filtered_distances
            if frozenset([d['site_a'], d['site_b']]) not in manual_pairs
        ]

        # Ajuster les contraintes min/max en fonction des liaisons manuelles actives
        # Créer une copie des sites avec contraintes ajustées
        adjusted_sites = []
        for site in app_state['sites']:
            # Compter les liaisons manuelles actives pour ce site
            manual_count = sum(
                1 for link in app_state['manual_links']
                if link.get('status') == 'active' and
                (link['site_a'] == site['id'] or link['site_b'] == site['id'])
            )

            # Ajuster min_links et max_links
            adjusted_site = site.copy()
            adjusted_site['min_links'] = max(0, site['min_links'] - manual_count)
            adjusted_site['max_links'] = max(0, site['max_links'] - manual_count)

            adjusted_sites.append(adjusted_site)

        # Sélectionner l'algorithme
        if algorithm == 'mst_aug':
            algo = MSTAugmentation()
        elif algorithm == 'greedy':
            algo = GreedyDegreeConstrained()
        elif algorithm == 'kconnect':
            algo = KConnectivityApproximation()
        else:
            return jsonify({'error': f'Algorithme inconnu: {algorithm}'}), 400

        # Générer les liaisons (en tenant compte des exclusions)
        links, logs, parent_child_map = algo.generate(
            adjusted_sites,  # Utiliser les sites avec contraintes ajustées
            filtered_distances,
            favor_shortest,
            app_state['excluded_links']
        )

        app_state['links'] = links
        app_state['parent_child_map'] = parent_child_map

        # Vérifier les sites avec contraintes impossibles
        for site in app_state['sites']:
            # Compter le total de liaisons (auto + manuelles actives)
            total_links = len([
                lnk for lnk in links if lnk.get('status') == 'active' and
                (lnk['site_a'] == site['id'] or lnk['site_b'] == site['id'])
            ]) + sum(
                1 for link in app_state['manual_links']
                if link.get('status') == 'active' and
                (link['site_a'] == site['id'] or link['site_b'] == site['id'])
            )

            # Vérifier si les contraintes sont satisfaites
            if total_links < site['min_links']:
                site['status'] = 'error'
                logs.append(
                    f"⚠ Site {site['id']}: min_links={site['min_links']} "
                    f"non atteint (seulement {total_links} liaisons totales)"
                )
            elif total_links > site['max_links']:
                site['status'] = 'error'
                logs.append(
                    f"⚠ Site {site['id']}: max_links={site['max_links']} "
                    f"dépassé ({total_links} liaisons totales)"
                )
            else:
                site['status'] = 'ok'

        # Compter les liaisons manuelles actives
        manual_active_count = sum(1 for lnk in app_state['manual_links'] if lnk.get('status') == 'active')

        return jsonify({
            'success': True,
            'links': links,
            'manual_links': app_state['manual_links'],
            'sites': app_state['sites'],
            'logs': logs,
            'message': f'{len(links)} liaisons auto générées, {manual_active_count} liaisons manuelles conservées'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/toggle_link', methods=['POST'])
def toggle_link():
    """Active/désactive un lien (exclut ou réactive)."""
    try:
        data = request.get_json()
        link_id = data.get('link_id')

        # Chercher dans les liens auto
        link = next((lnk for lnk in app_state['links'] if lnk['id'] == link_id), None)
        if not link:
            # Chercher dans les liens manuels
            link = next((lnk for lnk in app_state['manual_links'] if lnk['id'] == link_id), None)

        if not link:
            return jsonify({'error': 'Lien introuvable'}), 404

        # Toggle status
        if link['status'] == 'active':
            link['status'] = 'excluded'
            exc_key = f"{link['site_a']}-{link['site_b']}"
            app_state['excluded_links'].add(exc_key)
            app_state['excluded_links'].add(f"{link['site_b']}-{link['site_a']}")
            message = f'Lien {link_id} exclu'
        else:
            link['status'] = 'active'
            exc_key = f"{link['site_a']}-{link['site_b']}"
            app_state['excluded_links'].discard(exc_key)
            app_state['excluded_links'].discard(f"{link['site_b']}-{link['site_a']}")
            message = f'Lien {link_id} réactivé'

        return jsonify({
            'success': True,
            'link': link,
            'message': message
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/delete_link', methods=['POST'])
def delete_link():
    """Supprime définitivement un lien."""
    try:
        data = request.get_json()
        link_id = data.get('link_id')

        # Chercher et supprimer dans les liens auto
        app_state['links'] = [lnk for lnk in app_state['links'] if lnk['id'] != link_id]

        # Chercher et supprimer dans les liens manuels
        app_state['manual_links'] = [lnk for lnk in app_state['manual_links'] if lnk['id'] != link_id]

        # Retirer des exclusions
        app_state['excluded_links'] = {e for e in app_state['excluded_links'] if link_id not in e}

        return jsonify({
            'success': True,
            'message': f'Lien {link_id} supprimé définitivement'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/toggle_show_excluded', methods=['POST'])
def toggle_show_excluded():
    """Active/désactive l'affichage des liaisons exclues."""
    try:
        app_state['show_excluded'] = not app_state['show_excluded']

        return jsonify({
            'success': True,
            'show_excluded': app_state['show_excluded'],
            'message': f'Affichage exclusions: {"ON" if app_state["show_excluded"] else "OFF"}'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/reset_all', methods=['POST'])
def reset_all():
    """Réinitialise tous les paramètres de l'application."""
    try:
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

        return jsonify({
            'success': True,
            'message': 'Application réinitialisée'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/add_circle', methods=['POST'])
def add_circle():
    """Ajoute un cercle autour d'un site."""
    try:
        data = request.get_json()
        site_id = data.get('site_id')
        radius_km = float(data.get('radius_km', 10))

        if not site_id:
            return jsonify({'error': 'Site ID manquant'}), 400

        # Vérifier que le site existe
        site = next((s for s in app_state['sites'] if s['id'] == site_id), None)
        if not site:
            return jsonify({'error': f'Site "{site_id}" introuvable'}), 404

        # Ajouter le cercle
        circle = {
            'site_id': site_id,
            'radius_km': radius_km
        }
        app_state['circles'].append(circle)

        return jsonify({
            'success': True,
            'circle': circle,
            'message': f'Cercle ajouté autour de {site_id} (rayon: {radius_km} km)'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/clear_circles', methods=['POST'])
def clear_circles():
    """Supprime tous les cercles."""
    try:
        app_state['circles'] = []

        return jsonify({
            'success': True,
            'message': 'Tous les cercles ont été supprimés'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/export_csv', methods=['GET'])
def export_csv():
    """Exporte en CSV."""
    try:
        csv_content = storage.export_csv_extended(
            app_state['sites'],
            app_state['links'],
            app_state['manual_links']
        )

        output = BytesIO()
        output.write(csv_content.encode('utf-8'))
        output.seek(0)

        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name='geo_site_export.csv'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/export_json', methods=['GET'])
def export_json():
    """Exporte en GeoJSON."""
    try:
        json_content = storage.export_json_extended(
            app_state['sites'],
            app_state['links'],
            app_state['manual_links'],
            app_state['params'],
            list(app_state['excluded_links'])
        )

        output = BytesIO()
        output.write(json_content.encode('utf-8'))
        output.seek(0)

        return send_file(
            output,
            mimetype='application/geo+json',
            as_attachment=True,
            download_name='geo_site_save.geojson'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/export_html', methods=['GET'])
def export_html():
    """Exporte en HTML statique."""
    try:
        # Exporter seulement les liaisons actives
        active_links = get_all_active_links()
        html_content = storage.export_html(app_state['sites'], active_links)

        output = BytesIO()
        output.write(html_content.encode('utf-8'))
        output.seek(0)

        return send_file(
            output,
            mimetype='text/html',
            as_attachment=True,
            download_name='geo_site_map.html'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
