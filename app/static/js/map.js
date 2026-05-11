/**
 * Gestion de la carte Leaflet
 */

const MapManager = {
    map: null,
    markers: {},
    links: {},
    circles: {},
    manualLinkMode: false,
    circleMode: false,
    selectedSiteForLink: null,
    showCircles: true,
    
    /**
     * Initialise la carte
     */
    init() {
        this.map = L.map('map').setView([46.5, 2.5], 6);
        
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19
        }).addTo(this.map);
    },
    
    /**
     * Active/désactive le mode création liaison manuelle
     */
    toggleManualLinkMode(enabled) {
        this.manualLinkMode = enabled;
        this.selectedSiteForLink = null;
        
        // Changer le curseur
        if (enabled) {
            document.getElementById('map').style.cursor = 'crosshair';
        } else {
            document.getElementById('map').style.cursor = '';
        }
        
        // Mettre à jour les marqueurs
        Object.keys(this.markers).forEach(siteId => {
            const marker = this.markers[siteId];
            if (enabled) {
                marker.setStyle({ fillColor: '#ffcc00', weight: 2 });
            } else {
                marker.setStyle({ fillColor: '#e74c3c', weight: 1 });
            }
        });
    },
    
    /**
     * Efface tous les éléments de la carte
     */
    clear() {
        Object.values(this.markers).forEach(marker => {
            this.map.removeLayer(marker);
        });
        this.markers = {};
        
        Object.values(this.links).forEach(link => {
            if (link.line) this.map.removeLayer(link.line);
            if (link.label) this.map.removeLayer(link.label);
        });
        this.links = {};
        
        Object.values(this.circles).forEach(circle => {
            if (circle) this.map.removeLayer(circle);
        });
        this.circles = {};
    },
    
    /**
     * Affiche les sites sur la carte
     */
    displaySites(sites) {
        sites.forEach(site => {
            const isError = site.status === 'error';
            const fillColor = this.manualLinkMode ? '#ffcc00' : (isError ? '#c0392b' : '#e74c3c');
            
            const marker = L.circleMarker([site.lat, site.lng], {
                radius: 6,
                fillColor: fillColor,
                color: '#000',
                weight: this.manualLinkMode ? 2 : 1,
                opacity: 1,
                fillOpacity: 0.8,
                siteId: site.id
            });
            
            marker.bindTooltip(site.id, {
                permanent: true,
                direction: 'right',
                className: 'site-label',
                offset: [8, 0]
            });
            
            const popupContent = `
                <strong>${site.id}</strong><br>
                Lat: ${site.lat.toFixed(6)}<br>
                Lng: ${site.lng.toFixed(6)}<br>
                Min/Max liens: ${site.min_links}/${site.max_links}<br>
                Liaisons actives: ${site.link_ids ? site.link_ids.length : 0}
            `;
            marker.bindPopup(popupContent);
            
            // Gérer le clic pour liaison manuelle
            marker.on('click', (e) => {
                if (this.manualLinkMode) {
                    this.handleSiteClickForManualLink(site.id);
                    L.DomEvent.stopPropagation(e);
                } else if (this.circleMode) {
                    window.handleSiteClickForCircle(site.id);
                    L.DomEvent.stopPropagation(e);
                }
            });
            
            marker.addTo(this.map);
            this.markers[site.id] = marker;
        });
    },
    
    /**
     * Gère le clic sur un site en mode création liaison manuelle
     */
    handleSiteClickForManualLink(siteId) {
        if (!this.selectedSiteForLink) {
            // Premier site sélectionné
            this.selectedSiteForLink = siteId;
            this.markers[siteId].setStyle({ fillColor: '#00cc00', weight: 3 });
            window.addLog(`Premier site sélectionné: ${siteId}`);
        } else {
            // Second site sélectionné
            if (this.selectedSiteForLink === siteId) {
                window.addLog('Vous devez sélectionner deux sites différents');
                return;
            }
            
            const siteA = this.selectedSiteForLink;
            const siteB = siteId;
            
            // Réinitialiser la sélection
            this.markers[this.selectedSiteForLink].setStyle({ fillColor: '#ffcc00', weight: 2 });
            this.selectedSiteForLink = null;
            
            // Demander confirmation
            window.showManualLinkConfirmation(siteA, siteB);
        }
    },
    
    /**
     * Affiche les liaisons sur la carte
     */
    displayLinks(autoLinks, manualLinks, showExcluded, sites) {
        const sitesDict = {};
        sites.forEach(site => {
            sitesDict[site.id] = site;
        });
        
        // Afficher les liaisons auto
        autoLinks.forEach(link => {
            this._displayLink(link, sitesDict, 'auto', showExcluded);
        });
        
        // Afficher les liaisons manuelles
        manualLinks.forEach(link => {
            this._displayLink(link, sitesDict, 'manual', showExcluded);
        });
    },
    
    /**
     * Affiche une liaison individuelle
     */
    _displayLink(link, sitesDict, type, showExcluded) {
        const siteA = sitesDict[link.site_a];
        const siteB = sitesDict[link.site_b];
        
        if (!siteA || !siteB) return;
        
        const isActive = link.status === 'active';
        const isExcluded = link.status === 'excluded';
        
        // Ne pas afficher si exclu et toggle OFF
        if (isExcluded && !showExcluded) return;
        
        // Couleurs selon le type et le statut
        let color, opacity, weight, dashArray;
        
        if (isExcluded) {
            // Liaison exclue : rouge transparent
            color = '#ff0000';
            opacity = 0.3;
            weight = 2;
            dashArray = '5, 5';
        } else if (type === 'manual') {
            // Liaison manuelle active : bleu
            color = '#0066cc';
            opacity = 0.8;
            weight = 3;
            dashArray = null;
        } else {
            // Liaison auto active : noir
            color = '#000';
            opacity = 0.7;
            weight = 2;
            dashArray = null;
        }
        
        const lineStyle = {
            color: color,
            weight: weight,
            opacity: opacity,
            dashArray: dashArray
        };
        
        const line = L.polyline(
            [[siteA.lat, siteA.lng], [siteB.lat, siteB.lng]],
            lineStyle
        );
        
        // Ajouter un événement de clic
        line.on('click', () => {
            window.showLinkDetails(link);
        });
        
        line.addTo(this.map);
        
        // Calculer le point milieu pour l'étiquette
        const midLat = (siteA.lat + siteB.lat) / 2;
        const midLng = (siteA.lng + siteB.lng) / 2;
        
        // Label de distance
        let labelText = `${link.distance_km.toFixed(1)} km`;
        if (type === 'manual') {
            labelText += ' (M)';
        }
        if (isExcluded) {
            labelText += ' [EXCLUE]';
        }
        
        const labelColor = isExcluded ? '#ff0000' : '#666';
        const labelBg = isExcluded ? '#ffe6e6' : 'white';
        
        const distanceLabel = L.marker([midLat, midLng], {
            icon: L.divIcon({
                className: 'distance-label',
                html: `<div style="background:${labelBg};padding:2px 4px;border:1px solid ${labelColor};border-radius:3px;font-size:10px;font-weight:${isExcluded ? 'bold' : 'normal'}">
                       ${labelText}
                       </div>`,
                iconSize: [80, 20]
            }),
            interactive: false
        });
        
        distanceLabel.addTo(this.map);
        
        // Stocker les références
        this.links[link.id] = {
            line: line,
            label: distanceLabel
        };
    },
    
    /**
     * Ajuste la vue pour afficher tous les sites
     */
    fitBounds(sites) {
        if (sites.length === 0) return;
        
        const bounds = L.latLngBounds(
            sites.map(site => [site.lat, site.lng])
        );
        
        this.map.fitBounds(bounds, {
            padding: [50, 50]
        });
    },
    
    /**
     * Rafraîchit la carte complète
     */
    refresh(sites, autoLinks, manualLinks, showExcluded) {
        this.clear();
        this.displaySites(sites);
        this.displayLinks(autoLinks, manualLinks, showExcluded, sites);
        this.fitBounds(sites);
    },
    
    /**
     * Active/désactive le mode cercle
     */
    toggleCircleMode(enabled) {
        this.circleMode = enabled;
        
        if (enabled) {
            document.getElementById('map').style.cursor = 'cell';
            // Désactiver le mode liaison manuelle si actif
            if (this.manualLinkMode) {
                this.toggleManualLinkMode(false);
            }
        } else {
            document.getElementById('map').style.cursor = '';
        }
    },
    
    /**
     * Ajoute un cercle autour d'un site
     */
    addCircle(siteId, radiusKm, sites) {
        const site = sites.find(s => s.id === siteId);
        if (!site) return;
        
        // Rayon en mètres
        const radiusM = radiusKm * 1000;
        
        // Créer le cercle
        const circle = L.circle([site.lat, site.lng], {
            color: '#8B4513',  // Marron
            fillColor: '#8B4513',
            fillOpacity: 0.2,
            opacity: 0.8,
            weight: 2,
            radius: radiusM
        });
        
        circle.addTo(this.map);
        
        // Stocker
        const circleKey = `${siteId}_${Date.now()}`;
        this.circles[circleKey] = circle;
        
        return circleKey;
    },
    
    /**
     * Affiche/Masque tous les cercles
     */
    toggleCirclesVisibility(show) {
        this.showCircles = show;
        
        Object.values(this.circles).forEach(circle => {
            if (show) {
                if (!this.map.hasLayer(circle)) {
                    circle.addTo(this.map);
                }
            } else {
                if (this.map.hasLayer(circle)) {
                    this.map.removeLayer(circle);
                }
            }
        });
    },
    
    /**
     * Supprime tous les cercles
     */
    clearAllCircles() {
        Object.values(this.circles).forEach(circle => {
            if (this.map.hasLayer(circle)) {
                this.map.removeLayer(circle);
            }
        });
        this.circles = {};
    },
    
    /**
     * Restaure les cercles depuis l'état
     */
    restoreCircles(circlesData, sites) {
        this.clearAllCircles();
        circlesData.forEach(circleData => {
            this.addCircle(circleData.site_id, circleData.radius_km, sites);
        });
    }
};