/**
 * API client pour communiquer avec le backend Flask
 */

const API = {
    /**
     * Récupère l'état actuel
     */
    async getStatus() {
        const response = await fetch('/status');
        return await response.json();
    },

    /**
     * Importe un fichier CSV
     */
    async importCSV(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch('/import_csv', {
            method: 'POST',
            body: formData
        });
        
        return await response.json();
    },

    /**
     * Importe un fichier JSON
     */
    async importJSON(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch('/import_json', {
            method: 'POST',
            body: formData
        });
        
        return await response.json();
    },

    /**
     * Ajoute un nouveau site
     */
    async addSite(siteData) {
        const response = await fetch('/add_site', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(siteData)
        });
        
        return await response.json();
    },

    /**
     * Édite un site existant
     */
    async editSite(siteData) {
        const response = await fetch('/edit_site', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(siteData)
        });
        
        return await response.json();
    },

    /**
     * Supprime un site
     */
    async deleteSite(siteId) {
        const response = await fetch('/delete_site', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ id: siteId })
        });
        
        return await response.json();
    },

    /**
     * Crée une liaison manuelle
     */
    async createManualLink(siteA, siteB) {
        const response = await fetch('/create_manual_link', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ site_a: siteA, site_b: siteB })
        });
        
        return await response.json();
    },

    /**
     * Génère les liaisons
     */
    async generate(params) {
        const response = await fetch('/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(params)
        });
        
        return await response.json();
    },

    /**
     * Toggle le statut d'un lien (exclut/réactive)
     */
    async toggleLink(linkId) {
        const response = await fetch('/toggle_link', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ link_id: linkId })
        });
        
        return await response.json();
    },

    /**
     * Supprime définitivement un lien
     */
    async deleteLink(linkId) {
        const response = await fetch('/delete_link', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ link_id: linkId })
        });
        
        return await response.json();
    },

    /**
     * Toggle l'affichage des liaisons exclues
     */
    async toggleShowExcluded() {
        const response = await fetch('/toggle_show_excluded', {
            method: 'POST'
        });
        
        return await response.json();
    },

    /**
     * Réinitialise toute l'application
     */
    async resetAll() {
        const response = await fetch('/reset_all', {
            method: 'POST'
        });
        
        return await response.json();
    },

    /**
     * Exporte en CSV
     */
    exportCSV() {
        window.location.href = '/export_csv';
    },

    /**
     * Exporte en JSON
     */
    exportJSON() {
        window.location.href = '/export_json';
    },

    /**
     * Exporte en HTML
     */
    exportHTML() {
        window.location.href = '/export_html';
    },

    /**
     * Ajoute un cercle autour d'un site
     */
    async addCircle(siteId, radiusKm) {
        const response = await fetch('/add_circle', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ site_id: siteId, radius_km: radiusKm })
        });
        
        return await response.json();
    },

    /**
     * Supprime tous les cercles
     */
    async clearCircles() {
        const response = await fetch('/clear_circles', {
            method: 'POST'
        });
        
        return await response.json();
    }
};