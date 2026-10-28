
import { auth } from "./firebase.js";
import { onAuthStateChanged, signOut } from
  "https://www.gstatic.com/firebasejs/12.5.0/firebase-auth.js";
import { getBuses } from "./api.js";
import { initializeMap } from "./map.js";



const $ = (id) => document.getElementById(id);

const greeting = $("studentGreeting");
const logoutButton = $("logoutButton");
const refreshButton = $("refreshButton");
const message = $("dashboardMessage");
const busName = $("busName");
const busId = $("busId");
const busStatus = $("busStatus");

let currentUser = null;
let requestInProgress = false;



function setMessage(text) {
  message.textContent = text;
}

function formatTimestamp(value) {
  if (!value) return "Not reported";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return String(value);
  }

  return date.toLocaleString();
}


function showNoLocation() {
  $("latitude").textContent = "—";
  $("longitude").textContent = "—";
  $("lastUpdated").textContent = "Not reported";
  $("busSpeed").textContent = "—";
  $("mapMessage").textContent =
    "Waiting for valid bus coordinates from the API.";
  $("mapLink").hidden = true;

  if (busMarker && busMap) {
    busMap.removeLayer(busMarker);
    busMarker = null;
  }

  if (busAccuracyCircle && busMap) {
    busMap.removeLayer(busAccuracyCircle);
    busAccuracyCircle = null;
  }

  if (busMap) {
    busMap.setView([22.9734, 78.6569], 5);
  }
}


function showLocation(location) {
  if (!location || typeof location !== "object") {
    showNoLocation();
    return false;
  }

  const lat = Number(location.latitude);
  const lng = Number(location.longitude);

  if (
    location.latitude === undefined ||
    location.longitude === undefined ||
    !Number.isFinite(lat) ||
    !Number.isFinite(lng) ||
    lat < -90 || lat > 90 ||
    lng < -180 || lng > 180
  ) {
    showNoLocation();
    return false;
  }

  $("latitude").textContent = lat.toFixed(6);
  $("longitude").textContent = lng.toFixed(6);
  $("lastUpdated").textContent = formatTimestamp(location.timestamp);
  $("busSpeed").textContent =
    location.speed_kmph == null
      ? "Not reported"
      : `${location.speed_kmph} km/h`;

  $("mapMessage").textContent = "Latest reported coordinates available";

  const mapLink = $("mapLink");
  mapLink.href =
    `https://www.google.com/maps?q=${encodeURIComponent(`${lat},${lng}`)}`;
  mapLink.hidden = false;

  return true;
}

async function loadBus() {
  if (!currentUser || requestInProgress) return;

  requestInProgress = true;
  refreshButton.disabled = true;
  setMessage("Fetching the latest bus information…");

  try {
    const data = await getBuses();
    const buses = Array.isArray(data.buses) ? data.buses : [];

    if (buses.length === 0) {
      busName.textContent = "No bus available";
      busId.textContent = "No bus records returned by the API";
      busStatus.textContent = "Unavailable";
      showNoLocation();
      setMessage("The API did not return any bus records.");
      return;
    }

    // TrackBus currently has one bus. Use the first record returned by the API.
    const bus = buses[0];

    busName.textContent = bus.name || `Bus ${bus.bus_id || ""}`;
    busId.textContent = bus.bus_id
      ? `Bus ID: ${bus.bus_id}`
      : "Bus ID not provided";

    busStatus.textContent = "Record available";

    const hasLocation = showLocation(bus.location);

    setMessage(
      hasLocation
        ? "Bus information loaded. Check the timestamp to see when the location was reported."
        : "Bus record loaded, but valid location coordinates are not available."
    );
  } catch (error) {
    console.error("Unable to load bus data:", error);
    busName.textContent = "Bus data unavailable";
    busId.textContent = "Could not reach the bus API";
    busStatus.textContent = "Connection issue";
    showNoLocation();
    setMessage(
      "Unable to load bus data. Check that the FastAPI backend is running and try again."
    );
  } finally {
    requestInProgress = false;
    refreshButton.disabled = false;
  }
}


onAuthStateChanged(auth, (user) => {
  if (!user) {
    window.location.replace("login.html");
    return;
  }

  currentUser = user;
  greeting.textContent = user.displayName || user.email || "Student";

  initializeMap();
  loadBus();
});


refreshButton.addEventListener("click", loadBus);

logoutButton.addEventListener("click", async () => {
  logoutButton.disabled = true;

  try {
    await signOut(auth);
    window.location.replace("login.html");
  } catch (error) {
    console.error("Logout failed:", error);
    setMessage("Logout failed. Please try again.");
    logoutButton.disabled = false;
  }
});
