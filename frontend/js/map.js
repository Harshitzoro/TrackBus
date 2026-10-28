import { auth } from "./firebase.js";

import { auth } from "./firebase.js";

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


    async function loadApiBusMarkers() {
      const apiUrl = "https://trackbus-api.onrender.com/api/v1/buses";

      try {
        const user = auth.currentUser;

        if (!user) {
          console.warn("Bus map waiting for Firebase sign-in.");
          return;
        }

        const idToken = await user.getIdToken();

        const response = await fetch(apiUrl, {
          cache: "no-store",
          headers: {
            Authorization: `Bearer ${idToken}`
          }
        });

        if (response.status === 401) {
          console.error(
            "Bus API authentication failed. Check the Firebase ID token."
          );
          return;
        }

        if (response.status === 403) {
          console.error(
            "Bus API access denied. Check the student's bus assignment."
          );
          return;
        }

        if (!response.ok) {
          throw new Error(`Bus API request failed: ${response.status}`);
        }

        const result = await response.json();
        const buses = Array.isArray(result)
          ? result
          : result.buses;

        if (!Array.isArray(buses)) {
          throw new Error("Unexpected bus API response format.");
        }

        // Keep the previous markers if the API temporarily returns no buses.
        if (buses.length === 0) {
          console.warn("No bus records returned by the API.");
          return;
        }

        // Remove old API markers before displaying the latest records.
        apiBusMarkers.forEach((marker) => map.removeLayer(marker));
        apiBusMarkers.length = 0;

        // Rebuild the selector without duplicate options.
        busSelector.replaceChildren();

        const defaultOption = document.createElement("option");
        defaultOption.value = "";
        defaultOption.textContent = "Find a bus...";
        busSelector.appendChild(defaultOption);

        buses.forEach((bus) => {
          const latitude = Number(
            bus.location?.latitude ?? bus.latitude
          );
          const longitude = Number(
            bus.location?.longitude ?? bus.longitude
          );

          if (
            !Number.isFinite(latitude) ||
            !Number.isFinite(longitude) ||
            latitude < -90 || latitude > 90 ||
            longitude < -180 || longitude > 180
          ) {
            console.warn("Skipping invalid bus coordinates:", bus.bus_id);
            return;
          }

          const busId = String(bus.bus_id ?? bus.busNumber ?? "Unknown bus");
          const busIcon = L.divIcon({
            html: '<span style="font-size:28px;">🚌</span>',
            className: "",
            iconSize: [36, 36],
            iconAnchor: [18, 18],
            popupAnchor: [0, -18]
          });

          const marker = L.marker([latitude, longitude], {
            icon: busIcon
          }).addTo(map);

          const timestamp = bus.location?.timestamp ?? bus.timestamp;
          const recordedTime = timestamp
            ? new Date(timestamp).toLocaleString()
            : "Unavailable";

          const speed = bus.location?.speed_kmph ?? bus.speed_kmph;
          const speedText =
            speed !== null && speed !== undefined && speed !== "" &&
            Number.isFinite(Number(speed))
              ? `${Number(speed)} km/h`
              : "Unavailable";

          const popup = document.createElement("div");
          const title = document.createElement("strong");
          title.textContent = busId;
          popup.appendChild(title);

          [
            `Mode: API record; live status unconfirmed`,
            `Latitude: ${latitude}`,
            `Longitude: ${longitude}`,
            `Recorded: ${recordedTime}`,
            `Speed: ${speedText}`
          ].forEach((line) => {
            popup.appendChild(document.createElement("br"));
            popup.appendChild(document.createTextNode(line));
          });

          marker.bindPopup(popup);
          apiBusMarkers.push(marker);

          const option = document.createElement("option");
          option.value = String(apiBusMarkers.length - 1);
          option.textContent = busId;
          busSelector.appendChild(option);
        });

        if (apiBusMarkers.length > 0) {
          const busBounds = L.featureGroup(apiBusMarkers).getBounds();

          if (busBounds.isValid()) {
            map.fitBounds(busBounds, {
              padding: [40, 40],
              maxZoom: 15
            });
          }
        }

        console.log(
          `Map refreshed: ${apiBusMarkers.length} valid bus markers.`,
          new Date().toLocaleTimeString()
        );

      } catch (error) {
        console.error("Unable to refresh bus locations:", error);
      }
    }

busSelector.addEventListener("change", () => {
  apiBusMarkers.forEach((marker) => {
    marker.setOpacity(1);
    marker.closePopup();
  });

  if (busSelector.value === "") {
    return;
  }

  const selectedIndex = Number(busSelector.value);
  const selectedMarker = apiBusMarkers[selectedIndex];

  if (!selectedMarker) {
    return;
  }

  apiBusMarkers.forEach((marker) => {
    marker.setOpacity(marker === selectedMarker ? 1 : 0);
  });

  map.setView(selectedMarker.getLatLng(), 16);
  selectedMarker.openPopup();
});
showAllBusesButton.addEventListener("click", () => {
  if (apiBusMarkers.length === 0) {
    alert("No bus locations are available yet.");
    return;
  }

  apiBusMarkers.forEach((marker) => {
    marker.setOpacity(1);
    marker.closePopup();
  });

  busSelector.value = "";

  const busBounds = L.featureGroup(apiBusMarkers).getBounds();

  if (busBounds.isValid()) {
    map.fitBounds(busBounds, {
      padding: [40, 40],
      maxZoom: 15
    });
  }
});
    // Load bus locations immediately.
    loadApiBusMarkers();

    // Refresh bus locations every 10 seconds without reloading the page.
    const busRefreshTimer = window.setInterval(() => {
      loadApiBusMarkers();
    }, 10000);

    console.log("TrackBus map initialized successfully.");
  }

  loadLeaflet();
}