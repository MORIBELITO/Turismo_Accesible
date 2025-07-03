// firebase-configure.js
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.1/firebase-app.js";
import { getAuth, GoogleAuthProvider } from "https://www.gstatic.com/firebasejs/10.12.1/firebase-auth.js";

const firebaseConfig = {
  apiKey: "AIzaSyARMkC0EBYElA8wVOpefSgMD4oADAIqD4o",
  authDomain: "turismo-4e958.firebaseapp.com",
  projectId: "turismo-4e958",
  storageBucket: "turismo-4e958.firebasestorage.app",
  messagingSenderId: "442508451378",
  appId: "1:442508451378:web:65bed298dffe5b22e6262b",
  measurementId: "G-XSDKJ73NKW"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const googleProvider = new GoogleAuthProvider();

export { app, auth, googleProvider };
