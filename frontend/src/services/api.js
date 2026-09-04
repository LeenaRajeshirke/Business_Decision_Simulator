import axios from "axios";

const baseURL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

const api = axios.create({ baseURL });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("ds_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export class ApiError extends Error {
  constructor(status, detail) {
    super(detail || "Something went wrong.");
    this.status = status;
    this.detail = detail;
  }
}

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const status = err.response?.status;
    const detail = err.response?.data?.detail;
    const friendly = {
      401: "Your session has expired. Please log in again.",
      403: "You don't have permission to do that.",
      404: "We couldn't find what you were looking for.",
      422: typeof detail === "string" ? detail : "Some of the information provided isn't valid.",
      500: "Something went wrong on our end. Please try again.",
    };
    if (status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("ds_token");
    }
    return Promise.reject(
      new ApiError(status, friendly[status] || (typeof detail === "string" ? detail : "Network error — please check your connection."))
    );
  }
);

export default api;
