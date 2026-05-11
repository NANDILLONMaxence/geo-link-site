/**
 * Gestion de l'interface utilisateur - VERSION CORRIGÃ‰E COMPLÃˆTE
 * VERSION Ã‰TENDUE avec liaisons manuelles et exclusions avancÃ©es
 */

// Ã‰tat global
let appState = {
    sites: [],
    links: [],
    manual_links: [],
    params: {},
    show_excluded: true,
    circles: []
};

let currentLinkId = null;
let manualLinkModeActive = false;
let circleModeActive = false;
let showCircles = true;

/**
 * Initialisation au chargement de la page
 */
document.addEventListener('DOMContentLoaded', async () => {
    MapManager.init();
    await loadStatus();
    setupEventListeners();
});

/**
 * Configure tous les Ã©vÃ©nements
 */
function setupEventListeners() {
    // Import
    document.getElementById('importCsv').addEventListener('change', handleImportCSV);
    document.getElementById('importJson').addEventListener('change', handleImportJSON);
    
    // Nouveau site
    document.getElementById('btnNewSite').addEventListener('click', showNewSiteModal);
    document.getElementById('formNewSite').addEventListener('submit', handleAddSite);
    document.getElementById('btnCancelNewSite').addEventListener('click', hideNewSiteModal);
    
    // Ã‰dition site
    document.getElementById('formEditSite').addEventListener('submit', handleEditSite);
    document.getElementById('btnCancelEditSite').addEventListener('click', hideEditSiteModal);
    
    // GÃ©nÃ©ration
    document.getElementById('btnGenerate').addEventListener('click', handleGenerate);
    document.getElementById('btnRegenerate').addEventListener('click', handleGenerate);
    
    // Export
    document.getElementById('btnExportCsv').addEventListener('click', () => API.exportCSV());
    document.getElementById('btnExportJson').addEventListener('click', () => API.exportJSON());
    document.getElementById('btnExportHtml').addEventListener('click', () => API.exportHTML());
    
    // Liaison manuelle
    const btnManualLink = document.getElementById('btnManualLink');
    if (btnManualLink) {
        btnManualLink.addEventListener('click', toggleManualLinkMode);
    }
    
    // Mode cercle
    const btnCircleMode = document.getElementById('btnCircleMode');
    if (btnCircleMode) {
        btnCircleMode.addEventListener('click', toggleCircleMode);
    }
    
    const btnToggleCircles = document.getElementById('btnToggleCircles');
    if (btnToggleCircles) {
        btnToggleCircles.addEventListener('click', handleToggleCircles);
    }
    
    const btnClearCircles = document.getElementById('btnClearCircles');
    if (btnClearCircles) {
        btnClearCircles.addEventListener('click', handleClearCircles);
    }
    
    // Toggle exclusions
    const toggleExcluded = document.getElementById('toggleExcluded');
    if (toggleExcluded) {
        toggleExcluded.addEventListener('change', handleToggleShowExcluded);
    }
    
    // Reset
    const btnReset = document.getElementById('btnReset');
    if (btnReset) {
        btnReset.addEventListener('click', handleReset);
    }
    
    // DÃ©tails lien
    const btnToggleLink = document.getElementById('btnToggleLink');
    if (btnToggleLink) {
        btnToggleLink.addEventListener('click', handleToggleLink);
    }
    
    const btnDeleteLink = document.getElementById('btnDeleteLink');
    if (btnDeleteLink) {
        btnDeleteLink.addEventListener('click', handleDeleteLink);
    }
    
    const btnCloseLinkDetails = document.getElementById('btnCloseLinkDetails');
    if (btnCloseLinkDetails) {
        btnCloseLinkDetails.addEventListener('click', hideLinkDetailsModal);
    }
    
    // Confirmation liaison manuelle
    const btnConfirmManualLink = document.getElementById('btnConfirmManualLink');
    if (btnConfirmManualLink) {
        btnConfirmManualLink.addEventListener('click', handleConfirmManualLink);
    }
    
    const btnCancelManualLink = document.getElementById('btnCancelManualLink');
    if (btnCancelManualLink) {
        btnCancelManualLink.addEventListener('click', hideManualLinkConfirmModal);
    }
    
    // Fermeture des modaux
    document.querySelectorAll('.close').forEach(closeBtn => {
        closeBtn.addEventListener('click', (e) => {
            e.target.closest('.modal').style.display = 'none';
        });
    });
    
    window.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal')) {
            e.target.style.display = 'none';
        }
    });
}

/**
 * Charge l'Ã©tat depuis le serveur
 */
async function loadStatus() {
    try {
        const data = await API.getStatus();
        appState = data;
        refreshUI();
    } catch (error) {
        addLog('Erreur chargement: ' + error.message, 'error');
    }
}

/**
 * RafraÃ®chit toute l'interface
 */
function refreshUI() {
    refreshSitesList();
    refreshMap();
    updateSiteCount();
    updateToggleExcluded();
    
    // Restaurer les cercles
    if (appState.circles && appState.circles.length > 0) {
        MapManager.restoreCircles(appState.circles, appState.sites);
    }
}

/**
 * RafraÃ®chit la liste des sites
 */
function refreshSitesList() {
    const container = document.getElementById('sitesList');
    container.innerHTML = '';
    
    appState.sites.forEach(site => {
        const item = document.createElement('div');
        item.className = 'site-item' + (site.status === 'error' ? ' error' : '');
        
        const coords = site.lat_dms && site.lng_dms 
            ? `${site.lat_dms}, ${site.lng_dms}`
            : `${site.lat.toFixed(4)}Â°, ${site.lng.toFixed(4)}Â°`;
        
        // Compter les liaisons actives (auto + manuelles)
        const autoLinks = appState.links.filter(l => 
            l.status === 'active' && (l.site_a === site.id || l.site_b === site.id)
        ).length;
        
        const manualLinks = appState.manual_links.filter(l => 
            l.status === 'active' && (l.site_a === site.id || l.site_b === site.id)
        ).length;
        
        const totalLinks = autoLinks + manualLinks;
        
        item.innerHTML = `
            <div class="site-info">
                <div class="site-name">${site.id}</div>
                <div class="site-coords">${coords}</div>
                <div class="site-constraints">
                    Min/Max: ${site.min_links}/${site.max_links} | 
                    Liens: ${totalLinks} (${autoLinks}A + ${manualLinks}M)
                </div>
            </div>
            <div class="site-actions">
                <button class="btn btn-primary btn-sm" data-site-id="${site.id}" data-action="edit">Ã‰diter</button>
                <button class="btn btn-warning btn-sm" data-site-id="${site.id}" data-action="delete">Suppr.</button>
            </div>
        `;
        
        // Ajouter les Ã©vÃ©nements aux boutons
        const editBtn = item.querySelector('[data-action="edit"]');
        const deleteBtn = item.querySelector('[data-action="delete"]');
        
        editBtn.addEventListener('click', () => editSite(site.id));
        deleteBtn.addEventListener('click', () => deleteSite(site.id));
        
        container.appendChild(item);
    });
}

/**
 * RafraÃ®chit la carte
 */
function refreshMap() {
    MapManager.refresh(
        appState.sites, 
        appState.links, 
        appState.manual_links,
        appState.show_excluded
    );
}

/**
 * Met Ã  jour le compteur de sites
 */
function updateSiteCount() {
    document.getElementById('siteCount').textContent = appState.sites.length;
}

/**
 * Met Ã  jour le toggle des exclusions
 */
function updateToggleExcluded() {
    const toggle = document.getElementById('toggleExcluded');
    if (toggle) {
        toggle.checked = appState.show_excluded;
    }
}

/**
 * Ajoute un message dans les logs
 */
function addLog(message, type = 'info') {
    const logsContainer = document.getElementById('logs');
    const entry = document.createElement('div');
    entry.className = 'log-entry';
    entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    logsContainer.appendChild(entry);
    logsContainer.scrollTop = logsContainer.scrollHeight;
}

// Exposer globalement pour map.js
window.addLog = addLog;

/**
 * Gestion import CSV
 */
async function handleImportCSV(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    try {
        const result = await API.importCSV(file);
        if (result.error) {
            addLog('Erreur import CSV: ' + result.error, 'error');
            alert('Erreur: ' + result.error);
        } else {
            appState.sites = result.sites;
            appState.links = result.links;
            appState.manual_links = result.manual_links || [];
            refreshUI();
            addLog(result.message);
        }
    } catch (error) {
        addLog('Erreur import CSV: ' + error.message, 'error');
        alert('Erreur: ' + error.message);
    }
    
    e.target.value = '';
}

/**
 * Gestion import JSON
 */
async function handleImportJSON(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    try {
        const result = await API.importJSON(file);
        if (result.error) {
            addLog('Erreur import GeoJSON: ' + result.error, 'error');
            alert('Erreur: ' + result.error);
        } else {
            appState.sites = result.sites;
            appState.links = result.links;
            appState.manual_links = result.manual_links || [];
            appState.params = result.params || {};
            
            // Mettre Ã  jour les paramÃ¨tres dans l'UI
            if (appState.params.algorithm) {
                document.getElementById('algorithm').value = appState.params.algorithm;
            }
            if (appState.params.distance_max_km) {
                document.getElementById('distanceMax').value = appState.params.distance_max_km;
            }
            document.getElementById('favorShortest').checked = 
                appState.params.favor_shortest !== false;
            
            refreshUI();
            addLog(result.message);
        }
    } catch (error) {
        addLog('Erreur import GeoJSON: ' + error.message, 'error');
        alert('Erreur: ' + error.message);
    }
    
    e.target.value = '';
}

/**
 * Affiche le modal nouveau site
 */
function showNewSiteModal() {
    document.getElementById('modalNewSite').style.display = 'block';
    document.getElementById('formNewSite').reset();
}

/**
 * Cache le modal nouveau site
 */
function hideNewSiteModal() {
    document.getElementById('modalNewSite').style.display = 'none';
}

/**
 * Gestion ajout site
 */
async function handleAddSite(e) {
    e.preventDefault();
    
    const siteData = {
        id: document.getElementById('siteName').value.trim(),
        lat_dms: document.getElementById('siteLat').value.trim(),
        lng_dms: document.getElementById('siteLng').value.trim(),
        min_links: parseInt(document.getElementById('siteMinLinks').value),
        max_links: parseInt(document.getElementById('siteMaxLinks').value)
    };
    
    try {
        const result = await API.addSite(siteData);
        if (result.error) {
            alert('Erreur: ' + result.error);
        } else {
            appState.sites.push(result.site);
            refreshUI();
            addLog(result.message);
            hideNewSiteModal();
        }
    } catch (error) {
        alert('Erreur: ' + error.message);
    }
}

/**
 * Affiche le modal Ã©dition site
 */
function editSite(siteId) {
    const site = appState.sites.find(s => s.id === siteId);
    if (!site) return;
    
    document.getElementById('editSiteId').value = site.id;
    
    // Utiliser DMS si disponible, sinon convertir depuis dÃ©cimal
    if (site.lat_dms && site.lng_dms) {
        document.getElementById('editSiteLat').value = site.lat_dms;
        document.getElementById('editSiteLng').value = site.lng_dms;
    } else {
        // Conversion approximative dÃ©cimal â†’ DMS pour affichage
        document.getElementById('editSiteLat').value = decimalToDMS(site.lat, 'lat');
        document.getElementById('editSiteLng').value = decimalToDMS(site.lng, 'lng');
    }
    
    document.getElementById('editSiteMinLinks').value = site.min_links;
    document.getElementById('editSiteMaxLinks').value = site.max_links;
    
    document.getElementById('modalEditSite').style.display = 'block';
}

/**
 * Convertit dÃ©cimal en DMS (fonction helper)
 */
function decimalToDMS(decimal, type) {
    const direction = type === 'lat' 
        ? (decimal >= 0 ? 'N' : 'S')
        : (decimal >= 0 ? 'E' : 'W');
    
    decimal = Math.abs(decimal);
    const degrees = Math.floor(decimal);
    const minutesDecimal = (decimal - degrees) * 60;
    const minutes = Math.floor(minutesDecimal);
    const seconds = (minutesDecimal - minutes) * 60;
    
    return `${degrees}Â°${minutes.toString().padStart(2, '0')}'${seconds.toFixed(2).padStart(5, '0')}''${direction}`;
}

/**
 * Cache le modal Ã©dition site
 */
function hideEditSiteModal() {
    document.getElementById('modalEditSite').style.display = 'none';
}

/**
 * Gestion Ã©dition site
 */
async function handleEditSite(e) {
    e.preventDefault();
    
    const siteData = {
        id: document.getElementById('editSiteId').value,
        lat_dms: document.getElementById('editSiteLat').value.trim(),
        lng_dms: document.getElementById('editSiteLng').value.trim(),
        min_links: parseInt(document.getElementById('editSiteMinLinks').value),
        max_links: parseInt(document.getElementById('editSiteMaxLinks').value)
    };
    
    try {
        const result = await API.editSite(siteData);
        if (result.error) {
            alert('Erreur: ' + result.error);
        } else {
            const index = appState.sites.findIndex(s => s.id === siteData.id);
            if (index !== -1) {
                appState.sites[index] = result.site;
            }
            refreshUI();
            addLog(result.message);
            hideEditSiteModal();
        }
    } catch (error) {
        alert('Erreur: ' + error.message);
    }
}

/**
 * Supprime un site
 */
async function deleteSite(siteId) {
    if (!confirm(`âš ï¸ Supprimer le site "${siteId}" ?\n\nToutes les liaisons associÃ©es seront Ã©galement supprimÃ©es.`)) {
        return;
    }
    
    try {
        const result = await API.deleteSite(siteId);
        if (result.error) {
            alert('Erreur: ' + result.error);
            addLog('Erreur suppression: ' + result.error, 'error');
        } else {
            appState.sites = appState.sites.filter(s => s.id !== siteId);
            appState.links = appState.links.filter(
                l => l.site_a !== siteId && l.site_b !== siteId
            );
            appState.manual_links = appState.manual_links.filter(
                l => l.site_a !== siteId && l.site_b !== siteId
            );
            refreshUI();
            addLog(result.message);
        }
    } catch (error) {
        alert('Erreur: ' + error.message);
        addLog('Erreur: ' + error.message, 'error');
    }
}

/**
 * Active/dÃ©sactive le mode crÃ©ation liaison manuelle
 */
function toggleManualLinkMode() {
    manualLinkModeActive = !manualLinkModeActive;
    
    const btn = document.getElementById('btnManualLink');
    if (manualLinkModeActive) {
        btn.classList.add('btn-active');
        btn.textContent = 'âœ“ Mode liaison manuelle';
        addLog('Mode crÃ©ation liaison manuelle activÃ©. Cliquez sur deux sites.');
    } else {
        btn.classList.remove('btn-active');
        btn.textContent = 'CrÃ©er liaison manuelle';
        addLog('Mode crÃ©ation liaison manuelle dÃ©sactivÃ©.');
    }
    
    MapManager.toggleManualLinkMode(manualLinkModeActive);
}

/**
 * Affiche la confirmation de crÃ©ation liaison manuelle
 */
function showManualLinkConfirmation(siteA, siteB) {
    const siteAData = appState.sites.find(s => s.id === siteA);
    const siteBData = appState.sites.find(s => s.id === siteB);
    
    if (!siteAData || !siteBData) return;
    
    const latDiff = siteBData.lat - siteAData.lat;
    const lngDiff = siteBData.lng - siteAData.lng;
    const approxDist = Math.sqrt(latDiff * latDiff + lngDiff * lngDiff) * 111;
    
    document.getElementById('manualLinkSiteA').textContent = siteA;
    document.getElementById('manualLinkSiteB').textContent = siteB;
    document.getElementById('manualLinkDistance').textContent = approxDist.toFixed(1);
    
    const modal = document.getElementById('modalManualLinkConfirm');
    modal.dataset.siteA = siteA;
    modal.dataset.siteB = siteB;
    modal.style.display = 'block';
}

window.showManualLinkConfirmation = showManualLinkConfirmation;

/**
 * Cache le modal de confirmation liaison manuelle
 */
function hideManualLinkConfirmModal() {
    document.getElementById('modalManualLinkConfirm').style.display = 'none';
}

/**
 * Confirme la crÃ©ation de la liaison manuelle
 */
async function handleConfirmManualLink() {
    const modal = document.getElementById('modalManualLinkConfirm');
    const siteA = modal.dataset.siteA;
    const siteB = modal.dataset.siteB;
    
    try {
        const result = await API.createManualLink(siteA, siteB);
        
        if (result.error) {
            alert('Erreur: ' + result.error);
            addLog('Erreur crÃ©ation liaison: ' + result.error, 'error');
        } else {
            appState.manual_links.push(result.link);
            
            if (result.warning) {
                alert('âš ï¸ ' + result.warning);
                addLog('Warning: ' + result.warning, 'warning');
            }
            
            refreshUI();
            addLog(result.message);
            hideManualLinkConfirmModal();
        }
    } catch (error) {
        alert('Erreur: ' + error.message);
        addLog('Erreur: ' + error.message, 'error');
    }
}

/**
 * Gestion gÃ©nÃ©ration
 */
async function handleGenerate() {
    if (appState.sites.length < 2) {
        alert('Au moins 2 sites sont nÃ©cessaires');
        return;
    }
    
    const params = {
        algorithm: document.getElementById('algorithm').value,
        favor_shortest: document.getElementById('favorShortest').checked
    };
    
    const distanceMax = document.getElementById('distanceMax').value;
    if (distanceMax) {
        params.distance_max_km = parseFloat(distanceMax);
    }
    
    try {
        addLog('GÃ©nÃ©ration en cours...');
        const result = await API.generate(params);
        
        if (result.error) {
            addLog('Erreur: ' + result.error, 'error');
            alert('Erreur: ' + result.error);
        } else {
            appState.links = result.links;
            appState.manual_links = result.manual_links || appState.manual_links;
            appState.sites = result.sites;
            
            if (result.logs) {
                result.logs.forEach(log => addLog(log));
            }
            
            refreshUI();
            addLog(result.message);
        }
    } catch (error) {
        addLog('Erreur: ' + error.message, 'error');
        alert('Erreur: ' + error.message);
    }
}

/**
 * Toggle affichage des exclusions
 */
async function handleToggleShowExcluded() {
    try {
        const result = await API.toggleShowExcluded();
        if (result.success) {
            appState.show_excluded = result.show_excluded;
            refreshMap();
            addLog(result.message);
        }
    } catch (error) {
        addLog('Erreur: ' + error.message, 'error');
    }
}

/**
 * Reset complet de l'application
 */
async function handleReset() {
    const confirmation = confirm(
        'âš ï¸ ATTENTION âš ï¸\n\n' +
        'Cette action va SUPPRIMER DÃ‰FINITIVEMENT :\n' +
        'â€¢ Tous les sites\n' +
        'â€¢ Toutes les liaisons (auto + manuelles)\n' +
        'â€¢ Toutes les exclusions\n' +
        'â€¢ Tous les paramÃ¨tres\n\n' +
        'Cette opÃ©ration est IRRÃ‰VERSIBLE !\n\n' +
        'ÃŠtes-vous absolument certain de vouloir continuer ?'
    );
    
    if (!confirmation) {
        addLog('Reset annulÃ©');
        return;
    }
    
    try {
        addLog('Reset en cours...');
        const result = await API.resetAll();
        
        if (result.success) {
            appState.sites = [];
            appState.links = [];
            appState.manual_links = [];
            appState.show_excluded = true;
            
            document.getElementById('algorithm').value = 'mst_aug';
            document.getElementById('distanceMax').value = '';
            document.getElementById('favorShortest').checked = true;
            
            refreshUI();
            addLog(result.message);
            alert('âœ… Application rÃ©initialisÃ©e avec succÃ¨s !');
        }
    } catch (error) {
        alert('Erreur: ' + error.message);
        addLog('Erreur reset: ' + error.message, 'error');
    }
}

/**
 * Affiche les dÃ©tails d'un lien
 */
function showLinkDetails(link) {
    currentLinkId = link.id;
    
    const linkType = link.type === 'manual' ? 'Manuelle' : 'Automatique';
    const isExcluded = link.status === 'excluded';
    
    const detailsContainer = document.getElementById('linkDetails');
    detailsContainer.innerHTML = `
        <p><strong>ID:</strong> ${link.id}</p>
        <p><strong>Type:</strong> ${linkType}</p>
        <p><strong>Site A:</strong> ${link.site_a}</p>
        <p><strong>Site B:</strong> ${link.site_b}</p>
        <p><strong>Distance:</strong> ${link.distance_km.toFixed(2)} km</p>
        <p><strong>Statut:</strong> ${isExcluded ? 'Exclu' : 'Actif'}</p>
    `;
    
    const toggleBtn = document.getElementById('btnToggleLink');
    const deleteBtn = document.getElementById('btnDeleteLink');
    
    if (toggleBtn) {
        toggleBtn.textContent = isExcluded ? 'RÃ©activer' : 'Exclure';
        toggleBtn.style.display = 'inline-block';
    }
    
    if (deleteBtn) {
        deleteBtn.style.display = 'inline-block';
    }
    
    document.getElementById('modalLinkDetails').style.display = 'block';
}

window.showLinkDetails = showLinkDetails;

/**
 * Cache le modal dÃ©tails lien
 */
function hideLinkDetailsModal() {
    document.getElementById('modalLinkDetails').style.display = 'none';
    currentLinkId = null;
}

/**
 * Toggle le statut d'un lien (exclure/rÃ©activer)
 */
async function handleToggleLink() {
    if (!currentLinkId) {
        addLog('Erreur: Aucun lien sÃ©lectionnÃ©', 'error');
        return;
    }
    
    try {
        const result = await API.toggleLink(currentLinkId);
        if (result.error) {
            alert('Erreur: ' + result.error);
            addLog('Erreur toggle: ' + result.error, 'error');
        } else {
            let link = appState.links.find(l => l.id === currentLinkId);
            if (!link) {
                link = appState.manual_links.find(l => l.id === currentLinkId);
            }
            if (link) {
                link.status = result.link.status;
            }
            
            refreshMap();
            addLog(result.message);
            hideLinkDetailsModal();
        }
    } catch (error) {
        alert('Erreur: ' + error.message);
        addLog('Erreur: ' + error.message, 'error');
    }
}

/**
 * Supprime dÃ©finitivement un lien
 */
async function handleDeleteLink() {
    if (!currentLinkId) {
        addLog('Erreur: Aucun lien sÃ©lectionnÃ©', 'error');
        return;
    }
    
    const confirmation = confirm(
        'âš ï¸ SUPPRESSION DÃ‰FINITIVE âš ï¸\n\n' +
        'Cette action va supprimer dÃ©finitivement cette liaison.\n\n' +
        'Si c\'est une liaison manuelle, elle sera perdue.\n' +
        'Si c\'est une liaison automatique, elle pourra Ãªtre recrÃ©Ã©e lors d\'une prochaine gÃ©nÃ©ration.\n\n' +
        'Confirmer la suppression ?'
    );
    
    if (!confirmation) {
        addLog('Suppression annulÃ©e');
        return;
    }
    
    try {
        const result = await API.deleteLink(currentLinkId);
        if (result.error) {
            alert('Erreur: ' + result.error);
            addLog('Erreur suppression: ' + result.error, 'error');
        } else {
            appState.links = appState.links.filter(l => l.id !== currentLinkId);
            appState.manual_links = appState.manual_links.filter(l => l.id !== currentLinkId);
            
            refreshUI();
            addLog(result.message);
            hideLinkDetailsModal();
        }
    } catch (error) {
        alert('Erreur: ' + error.message);
        addLog('Erreur: ' + error.message, 'error');
    }
}

// Exposer les fonctions nÃ©cessaires
window.editSite = editSite;
window.deleteSite = deleteSite;

/**
 * Active/dÃ©sactive le mode cercle
 */
function toggleCircleMode() {
    circleModeActive = !circleModeActive;
    
    const btn = document.getElementById('btnCircleMode');
    if (circleModeActive) {
        btn.classList.add('btn-active');
        btn.textContent = 'âœ“ Mode cercle actif';
        addLog('Mode cercle activÃ©. Cliquez sur un site.');
        
        // DÃ©sactiver le mode liaison manuelle si actif
        if (manualLinkModeActive) {
            toggleManualLinkMode();
        }
    } else {
        btn.classList.remove('btn-active');
        btn.textContent = 'Mode cercle';
        addLog('Mode cercle dÃ©sactivÃ©.');
    }
    
    MapManager.toggleCircleMode(circleModeActive);
}

/**
 * GÃ¨re le clic sur un site en mode cercle
 */
async function handleSiteClickForCircle(siteId) {
    const radiusKm = parseFloat(document.getElementById('circleRadius').value) || 10;
    
    try {
        const result = await API.addCircle(siteId, radiusKm);
        
        if (result.error) {
            alert('Erreur: ' + result.error);
            addLog('Erreur crÃ©ation cercle: ' + result.error, 'error');
        } else {
            // Ajouter Ã  l'Ã©tat local
            appState.circles.push(result.circle);
            
            // Afficher sur la carte
            MapManager.addCircle(siteId, radiusKm, appState.sites);
            
            addLog(result.message);
        }
    } catch (error) {
        alert('Erreur: ' + error.message);
        addLog('Erreur: ' + error.message, 'error');
    }
}

// Exposer pour map.js
window.handleSiteClickForCircle = handleSiteClickForCircle;

/**
 * Toggle affichage des cercles
 */
function handleToggleCircles() {
    showCircles = !showCircles;
    
    const btn = document.getElementById('btnToggleCircles');
    btn.textContent = showCircles ? 'Masquer cercles' : 'Afficher cercles';
    
    MapManager.toggleCirclesVisibility(showCircles);
    addLog(showCircles ? 'Cercles affichÃ©s' : 'Cercles masquÃ©s');
}

/**
 * Efface tous les cercles
 */
async function handleClearCircles() {
    if (!confirm('Supprimer tous les cercles ?')) {
        return;
    }
    
    try {
        const result = await API.clearCircles();
        
        if (result.success) {
            appState.circles = [];
            MapManager.clearAllCircles();
            addLog(result.message);
        }
    } catch (error) {
        alert('Erreur: ' + error.message);
        addLog('Erreur: ' + error.message, 'error');
    }
}