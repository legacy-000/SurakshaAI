import axios from "axios";

const API_BASE_URL = "https://surakshaai-60076341598.development.catalystserverless.in/server/suraksha-api/api";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 15000,
});

apiClient.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const catalystToken = localStorage.getItem("catalyst_auth_token");
    const legacyToken = localStorage.getItem("suraksha_token");
    const token = catalystToken || legacyToken;
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
}, (error) => Promise.reject(error));

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      console.error("Authentication required. Redirecting to login...");
      if (typeof window !== "undefined") {
        window.location.href = "/auth/login";
      }
    }
    return Promise.reject(error);
  }
);
