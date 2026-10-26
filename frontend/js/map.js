
export function initializeMap() {
  const mapElement = document.querySelector("#map");

  if (!mapElement) {
    console.error("TrackBus map container was not found.");
    return;
  }

  mapElement.textContent = "Loading map...";

  // Load Leaflet's stylesheet without editing index.html.
  if (!document.querySelector("#leaflet-css")) {
    const leafletCss = document.createElement("link");

    leafletCss.id = "leaflet-css";
    leafletCss.rel = "stylesheet";
    leafletCss.href =
      "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";

    document.head.appendChild(leafletCss);
  }

  // Load Leaflet's JavaScript library.
  function loadLeaflet() {
    if (window.L) {
      createMap();
      return;
    }

    if (document.querySelector("#leaflet-js")) {
      return;
    }

    const leafletScript = document.createElement("script");

    leafletScript.id = "leaflet-js";
    leafletScript.src =
      "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";

    leafletScript.onload = createMap;

    leafletScript.onerror = () => {
      mapElement.textContent =
        "Map could not load. Check your internet connection.";
    };

    document.head.appendChild(leafletScript);
  }

  function createMap() {
    const L = window.L;

    // Use the sample coordinates already recorded in the project.
    const sampleLocation = [25.170469, 75.866708];

    mapElement.textContent = "";
    mapElement.style.minHeight = "18rem";

    const map = L.map(mapElement).setView(sampleLocation, 15);

    // Add a Full Screen control to the map.
    const fullscreenControl = L.control({ position: "topright" });

    fullscreenControl.onAdd = function () {
      const button = L.DomUtil.create(
        "button",
        "trackbus-fullscreen-button"
      );

      button.type = "button";
      button.textContent = "⛶";
      button.title = "Toggle map full screen";
      button.setAttribute("aria-label", "Toggle map full screen");

      // Prevent map dragging or zooming when using the button.
      L.DomEvent.disableClickPropagation(button);

      button.addEventListener("click", async () => {
        try {
          if (document.fullscreenElement === mapElement) {
            await document.exitFullscreen();
          } else {
            await mapElement.requestFullscreen();
          }
        } catch (error) {
          console.error("Unable to toggle map full screen:", error);
        }
      });

      document.addEventListener("fullscreenchange", () => {
        const isFullscreen = document.fullscreenElement === mapElement;

        button.textContent = isFullscreen
          ? "⤢ "
          : "⛶ Full Screen";

        map.invalidateSize();
      });

      return button;
    };

    fullscreenControl.addTo(map);

    // OpenStreetMap background tiles.
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    // Keep the demo marker, clearly labelled as sample data.
    L.marker(sampleLocation)
      .addTo(map)
      .bindPopup("Demo Bus - sample location (not live)");

    // Store API markers so they can be refreshed later if needed.
    const apiBusMarkers = [];

    async function loadApiBusMarkers() {
      try {
        const response = await fetch(
          "https://trackbus-api.onrender.com/api/v1/buses"
        );

        if (!response.ok) {
          throw new Error(`Bus API returned HTTP ${response.status}`);
        }

        const result = await response.json();
        const buses = Array.isArray(result.buses) ? result.buses : [];

        // Remove old API markers before drawing the latest response.
        apiBusMarkers.forEach((marker) => map.removeLayer(marker));
        apiBusMarkers.length = 0;

        buses.forEach((bus) => {
          const latitude = Number(bus.location?.latitude);
          const longitude = Number(bus.location?.longitude);

          if (
            !Number.isFinite(latitude) ||
            !Number.isFinite(longitude) ||
            latitude < -90 ||
            latitude > 90 ||
            longitude < -180 ||
            longitude > 180
          ) {
            return;
          }

          const marker = L.marker([latitude, longitude])
            .addTo(map)
            .bindPopup(
              `<strong>${String(bus.bus_id ?? "Unknown bus")}</strong><br>` +
              `API-reported location — not confirmed live<br>` +
              `Timestamp: ${String(bus.location?.timestamp ?? "Unknown")}`
            );

          apiBusMarkers.push(marker);
        });

        console.log(`Loaded ${apiBusMarkers.length} API bus markers.`);
      } catch (error) {
        console.error("Unable to load API bus markers:", error);
      }
    }

    loadApiBusMarkers();

  // Demo stop coordinates from the existing project configuration.
const stopA = [25.1386742, 75.8260137];
const stopB = [25.1421876, 75.8284360];

// Add the first stop.
L.marker(stopA)
  .addTo(map)
  .bindPopup("Stop A");

// Add the second stop.
L.marker(stopB)
  .addTo(map)
  .bindPopup("Stop B");

// Draw a straight line between the two stops.
const routeLine = L.polyline([stopA, stopB], {
  color: "blue",
  weight: 4
}).addTo(map);

// Adjust the map so both stops and the route are visible.
map.fitBounds(routeLine.getBounds(), {
  padding: [30, 30]
});

    console.log("TrackBus map initialized successfully.");
  }

  loadLeaflet();
}
