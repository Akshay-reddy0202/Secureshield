import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry && !originalRequest.url.includes('/auth/refresh')) {
      originalRequest._retry = true;
      const refresh_token = localStorage.getItem('ssa_refresh_token');
      if (refresh_token) {
        try {
          const res = await axios.post(`${API_BASE_URL}/auth/refresh`, { refresh_token });
          const { access_token, refresh_token: new_refresh, user: new_user } = res.data;
          
          localStorage.setItem('ssa_user', JSON.stringify(new_user));
          localStorage.setItem('ssa_access_token', access_token);
          localStorage.setItem('ssa_refresh_token', new_refresh);
          
          api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
          originalRequest.headers['Authorization'] = `Bearer ${access_token}`;
          
          return api(originalRequest);
        } catch (err) {
          localStorage.removeItem('ssa_user');
          localStorage.removeItem('ssa_access_token');
          localStorage.removeItem('ssa_refresh_token');
        }
      }
    }
    return Promise.reject(error);
  }
);

export default api;
