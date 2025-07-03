// firebase-auth.js
import {
  GoogleAuthProvider,
  signInWithPopup,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  onAuthStateChanged
} from "https://www.gstatic.com/firebasejs/10.12.1/firebase-auth.js";

import { auth } from "./firebase-config.js";

// Google Login
export function googleLogin() {
  const provider = new GoogleAuthProvider();
  return signInWithPopup(auth, provider);
}

// Google Register
export function googleRegister() {
  const provider = new GoogleAuthProvider();
  return signInWithPopup(auth, provider);
}

// Email Login
export function emailLogin(email, password) {
  return signInWithEmailAndPassword(auth, email, password);
}

// Email Register
export function emailRegister(email, password) {
  return createUserWithEmailAndPassword(auth, email, password);
}

// Auth State Listener
export function checkAuthState(callback) {
  return onAuthStateChanged(auth, callback);
}