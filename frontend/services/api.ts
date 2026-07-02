import axios from "axios";

// Detect if running in Catalyst Web Client Hosting or local development
const isCatalyst = process.env.NEXT_PUBLIC_CATALYST_ENV === "production";

// Base URL: Use relative paths for Catalyst (API Gateway handles routing)
const API_BASE_URL = isCatalyst 
  ? "/api" 
  : process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 15000, // 15 seconds timeout for Catalyst Serverless
});

// Request interceptor to automatically inject JWT token or Zoho Catalyst Auth
apiClient.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    // Check for Catalyst Auth token first
    const catalystToken = localStorage.getItem("catalyst_auth_token");
    const legacyToken = localStorage.getItem("suraksha_token");
    const token = catalystToken || legacyToken;
    
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

// Response interceptor for error handling (e.g., 401 Unauthorized)
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Handle unauthorized - redirect to Catalyst login
      console.error("Authentication required. Redirecting to login...");
      if (typeof window !== "undefined") {
        window.location.href = "/auth/login";
      }
    }
    return Promise.reject(error);
  }
);
