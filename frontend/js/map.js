
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

const showAllBusesButton = document.createElement("button");
showAllBusesButton.type = "button";
showAllBusesButton.textContent = "Show All Buses";
showAllBusesButton.style.display = "block";
showAllBusesButton.style.marginBottom = "10px";
showAllBusesButton.style.padding = "8px 12px";

mapElement.parentElement.insertBefore(
  showAllBusesButton,
  mapElement
);

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
  const busSelector = document.createElement("select");
busSelector.id = "bus-selector";
busSelector.setAttribute("aria-label", "Select a bus to locate");

const defaultOption = document.createElement("option");
defaultOption.value = "";
defaultOption.textContent = "Find a bus...";
busSelector.appendChild(defaultOption);

busSelector.style.display = "block";
busSelector.style.width = "100%";
busSelector.style.maxWidth = "320px";
busSelector.style.padding = "8px";
busSelector.style.marginBottom = "10px";

mapElement.parentElement.insertBefore(busSelector, mapElement);


    function loadApiBusMarkers() {
      // Historical API records for map testing only.
      // These coordinates are not live bus positions.
      const testBuses = [
        {
          bus_id: "BUS-001",
          latitude: 25.011964,
          longitude: 75.914284,
          timestamp: "2026-10-15T10:25:00+00:00"
        },
        {
          bus_id: "BUS-FIREBASE-TEST",
          latitude: 25.132318,
          longitude: 75.836061,
          timestamp: "2026-10-22T11:45:48+00:00"
        },
        {
          bus_id: "BUS-TEST-001",
          latitude: 26.9124,
          longitude: 75.7873,
          timestamp: "2026-10-12T05:00:00+00:00"
        },
        {
          bus_id: "BUS_001",
          latitude: 25.138317,
          longitude: 75.827298,
          timestamp: "2026-10-24T12:16:36+00:00",
          status: "inactive"
        },
        {
          bus_id: "TRACKBUS-TEST-001",
          latitude: 25.132318,
          longitude: 75.836061,
          timestamp: "2026-10-23T10:31:25.922403+00:00"
        }
      ];

      testBuses.forEach((bus) => {
        const marker = L.marker([
  bus.latitude,
  bus.longitude
]).addTo(map);

        const recordedTime = new Date(bus.timestamp).toLocaleString();

        marker.bindPopup(`
          <strong>${bus.bus_id}</strong><br>
          <strong>Mode:</strong> Historical test data<br>
          <strong>Latitude:</strong> ${bus.latitude}<br>
          <strong>Longitude:</strong> ${bus.longitude}<br>
          <strong>Recorded:</strong> ${recordedTime}<br>
          <strong>Status:</strong> ${bus.status ?? "Unknown"}
        `);

        apiBusMarkers.push(marker);
const option = document.createElement("option");
option.value = String(apiBusMarkers.length - 1);
option.textContent = bus.bus_id;
busSelector.appendChild(option);

      });

      console.log(`Loaded ${apiBusMarkers.length} historical test bus markers.`);
    }

busSelector.addEventListener("change", () => {
  // Hide all historical bus markers first.
  apiBusMarkers.forEach((marker) => {
    marker.setOpacity(0);
    marker.closePopup();
  });

  if (busSelector.value === "") {
    return;
  }

  const selectedIndex = Number(busSelector.value);
  const marker = apiBusMarkers[selectedIndex];

  if (marker) {
    marker.setOpacity(1);
    map.setView(marker.getLatLng(), 16);
    marker.openPopup();
  }
});
showAllBusesButton.addEventListener("click", () => {
  if (apiBusMarkers.length === 0) {
    alert("No bus locations are available yet.");
    return;
  }

  const busBounds = L.featureGroup(apiBusMarkers).getBounds();

  map.fitBounds(busBounds, {
    padding: [40, 40],
    maxZoom: 15
  });
});

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
