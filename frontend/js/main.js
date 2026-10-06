import { getBuses } from "./api.js";
import { renderBuses } from "./bus.js";
import { initializeMap } from "./map.js";

const busList = document.querySelector("#bus-list");
initializeMap();

try {
  renderBuses(busList, await getBuses());
} catch (error) {
  document.querySelector("#service-status").textContent = "Bus service unavailable";
  console.error("Unable to load buses:", error);
}