document.addEventListener("DOMContentLoaded", function() {
    const latInput = document.getElementById("id_latitude");
    const lngInput = document.getElementById("id_longitude");

    if (!latInput || !lngInput) return;

    // Create map element dynamically
    const mapDiv = document.createElement("div");
    mapDiv.id = "mapid";
    mapDiv.style = "height: 400px; margin-top: 10px; border-radius: 8px;";
    latInput.parentElement.parentElement.appendChild(mapDiv);

    const defaultLat = latInput.value ? parseFloat(latInput.value) : 41.3111;
    const defaultLng = lngInput.value ? parseFloat(lngInput.value) : 69.2797;

    const map = L.map('mapid').setView([defaultLat, defaultLng], 7);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 18
    }).addTo(map);

    let marker;
    if (latInput.value && lngInput.value) {
        marker = L.marker([defaultLat, defaultLng]).addTo(map);
    }

    map.on('click', function(e) {
        const { lat, lng } = e.latlng;
        latInput.value = lat.toFixed(6);
        lngInput.value = lng.toFixed(6);

        if (marker) map.removeLayer(marker);
        marker = L.marker([lat, lng]).addTo(map);
    });
});
