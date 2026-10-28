
import { auth } from "./firebase.js";

const API_BASE_URL = "http://localhost:8000/api/v1";

export async function getBuses() {
  const user = auth.currentUser;

  if (!user) {
    throw new Error("Please sign in before requesting bus data.");
  }

  const idToken = await user.getIdToken();

  const response = await fetch(`${API_BASE_URL}/buses`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${idToken}`,
      Accept: "application/json"
    }
  });

  if (!response.ok) {
    throw new Error(`Bus request failed (${response.status})`);
  }

  return response.json();
}
