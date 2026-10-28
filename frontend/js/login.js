
import { auth } from "./firebase.js";
import {
  signInWithEmailAndPassword
} from "https://www.gstatic.com/firebasejs/12.5.0/firebase-auth.js";

const form = document.getElementById("loginForm");
const message = document.getElementById("loginMessage");

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;
  const submitButton = form.querySelector('button[type="submit"]');

  message.textContent = "";
  message.className = "auth-message";
  submitButton.disabled = true;

  try {
    await signInWithEmailAndPassword(auth, email, password);

    window.location.assign("dashboard.html");
  } catch (error) {
    const messages = {
      "auth/invalid-credential":
        "Email or password is incorrect.",
      "auth/invalid-email":
        "Please enter a valid email address.",
      "auth/too-many-requests":
        "Too many attempts. Please try again later.",
      "auth/network-request-failed":
        "Network error. Check your internet connection."
    };

    message.textContent =
      messages[error.code] || "Unable to sign in. Please try again.";
  } finally {
    submitButton.disabled = false;
  }
});
