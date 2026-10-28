
import { initializeApp } from "https://www.gstatic.com/firebasejs/12.5.0/firebase-app.js";
import { getAuth } from "https://www.gstatic.com/firebasejs/12.5.0/firebase-auth.js";
import { getDatabase } from "https://www.gstatic.com/firebasejs/12.5.0/firebase-database.js";

const firebaseConfig = {
  apiKey: "AIzaSyBJPV_G0ZmVp4sm8tI4-BHcj6k-B0bxol8",
  authDomain: "trackbus-255f1.firebaseapp.com",
  databaseURL: "https://trackbus-255f1-default-rtdb.asia-southeast1.firebasedatabase.app",
  projectId: "trackbus-255f1",
  storageBucket: "trackbus-255f1.firebasestorage.app",
  messagingSenderId: "55967343133",
  appId: "1:55967343133:web:fe031c6c5f605acdbb1cf4"
  
};

const app = initializeApp(firebaseConfig);

export const auth = getAuth(app);
export const database = getDatabase(app);
