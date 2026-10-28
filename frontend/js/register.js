
import { auth } from "./firebase.js";
import {
  createUserWithEmailAndPassword,
  updateProfile
} from "https://www.gstatic.com/firebasejs/12.5.0/firebase-auth.js";

const form = document.getElementById("registerForm");
const message = document.getElementById("registerMessage");

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const fullName = document.getElementById("fullName").value.trim();
  const email = document.getElementById("email").value.trim();
  const studentId = document.getElementById("studentId").value.trim();
  const password = document.getElementById("password").value;
  const confirmPassword =
    document.getElementById("confirmPassword").value;

  message.textContent = "";
  message.className = "auth-message";

  if (!fullName || !email || !studentId) {
    message.textContent = "Please fill in all required fields.";
    return;
  }

  if (password.length < 8) {
    message.textContent = "Password must be at least 8 characters.";
    return;
  }

  if (password !== confirmPassword) {
    message.textContent = "Passwords do not match.";
    return;
  }

  const submitButton = form.querySelector('button[type="submit"]');
  submitButton.disabled = true;

  try {
    const userCredential = await createUserWithEmailAndPassword(
      auth,
      email,
      password
    );

    await updateProfile(userCredential.user, {
      displayName: fullName
    });

    message.textContent =
      "Account created successfully. Student profile verification is still pending.";
    message.classList.add("success");

    form.reset();
  } catch (error) {
    const messages = {
      "auth/email-already-in-use":
        "This email is already registered. Please sign in.",
      "auth/invalid-email":
        "Please enter a valid email address.",
      "auth/weak-password":
        "Please choose a stronger password.",
      "auth/operation-not-allowed":
        "Email/Password sign-up is not enabled for this Firebase project.",
      "auth/network-request-failed":
        "Network error. Check your internet connection and try again."
    };

    message.textContent =
      messages[error.code] || "Registration failed. Please try again.";
  } finally {
    submitButton.disabled = false;
  }
});
