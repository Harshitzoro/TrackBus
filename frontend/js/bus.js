export function renderBuses(container, data) {
  const buses = data.buses ?? [];
  container.replaceChildren();

  if (buses.length === 0) {
    container.textContent = "No buses are currently available.";
    return;
  }

  const list = document.createElement("ul");
  for (const bus of buses) {
    const item = document.createElement("li");
    item.textContent = bus.name ?? bus.bus_id;
    list.append(item);
  }
  container.append(list);
}