import axios from "axios";

const fallbackApiUrl = "http://localhost:8000";
const configuredApiUrl = import.meta.env.VITE_API_URL || fallbackApiUrl;

export const apiClient = axios.create({
  baseURL: configuredApiUrl.replace(/\/$/, ""),
  timeout: 30000
});

