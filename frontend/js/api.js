const API_BASE_URL = "http://localhost:8000/api/v1";

export async function getBuses() {
  const response = await fetch(`${API_BASE_URL}/buses`);
  if (!response.ok) {
    throw new Error(`Bus request failed (${response.status})`);
  }
  return response.json();
}