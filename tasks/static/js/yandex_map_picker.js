document.addEventListener("DOMContentLoaded", function () {
    const latInput = document.getElementById("id_latitude");
    const lngInput = document.getElementById("id_longitude");

    if (!latInput || !lngInput) return;

    // create map container
    const mapDiv = document.createElement("div");
    mapDiv.id = "yandex-map";
    mapDiv.style = "width: 100%; height: 400px; margin-top: 10px; border-radius: 8px;";
    latInput.parentElement.parentElement.appendChild(mapDiv);

    // load Yandex Map
    ymaps.ready(init);
    function init() {
        const defaultLat = latInput.value ? parseFloat(latInput.value) : 41.3111;
        const defaultLng = lngInput.value ? parseFloat(lngInput.value) : 69.2797;

        const map = new ymaps.Map("yandex-map", {
            center: [defaultLat, defaultLng],
            zoom: 7,
            controls: ["zoomControl", "searchControl", "geolocationControl"],
        });

        let marker;
        if (latInput.value && lngInput.value) {
            marker = new ymaps.Placemark([defaultLat, defaultLng], {}, { draggable: true });
            map.geoObjects.add(marker);
        }

        // on map click
        map.events.add("click", function (e) {
            const coords = e.get("coords");
            latInput.value = coords[0].toFixed(6);
            lngInput.value = coords[1].toFixed(6);

            if (marker) map.geoObjects.remove(marker);
            marker = new ymaps.Placemark(coords, {}, { draggable: true });
            map.geoObjects.add(marker);

            // on marker drag
            marker.events.add("dragend", function (e) {
                const newCoords = e.get("target").geometry.getCoordinates();
                latInput.value = newCoords[0].toFixed(6);
                lngInput.value = newCoords[1].toFixed(6);
            });
        });

        // if existing marker is draggable
        if (marker) {
            marker.events.add("dragend", function (e) {
                const newCoords = e.get("target").geometry.getCoordinates();
                latInput.value = newCoords[0].toFixed(6);
                lngInput.value = newCoords[1].toFixed(6);
            });
        }
    }
});
