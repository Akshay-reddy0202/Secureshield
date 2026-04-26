import { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Restore session on mount
    const storedUser = localStorage.getItem('ssa_user');
    const token = localStorage.getItem('ssa_access_token');
    if (storedUser && token) {
      setUser(JSON.parse(storedUser));
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }
    setLoading(false);

    // Setup Axios Interceptor for 401 refresh logic
    const interceptor = axios.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;
        if (error.response?.status === 401 && !originalRequest._retry && originalRequest.url !== "http://127.0.0.1:8000/auth/refresh") {
          originalRequest._retry = true;
          const refresh_token = localStorage.getItem('ssa_refresh_token');
          if (refresh_token) {
            try {
              const res = await axios.post("http://127.0.0.1:8000/auth/refresh", { refresh_token });
              const { access_token, refresh_token: new_refresh, user: new_user } = res.data;

              localStorage.setItem('ssa_user', JSON.stringify(new_user));
              localStorage.setItem('ssa_access_token', access_token);
              localStorage.setItem('ssa_refresh_token', new_refresh);

              axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
              originalRequest.headers['Authorization'] = `Bearer ${access_token}`;
              setUser(new_user);

              return axios(originalRequest);
            } catch (err) {
              // Refresh token died or tampered, destroy session
              setUser(null);
              localStorage.removeItem('ssa_user');
              localStorage.removeItem('ssa_access_token');
              localStorage.removeItem('ssa_refresh_token');
              delete axios.defaults.headers.common['Authorization'];
            }
          } else {
            // No refresh token available, destroy session
            setUser(null);
            localStorage.removeItem('ssa_user');
            localStorage.removeItem('ssa_access_token');
            localStorage.removeItem('ssa_refresh_token');
            delete axios.defaults.headers.common['Authorization'];
          }
        }
        return Promise.reject(error);
      }
    );

    return () => axios.interceptors.response.eject(interceptor);
  }, []);

  const login = async (email, password) => {
    try {
      setError(null);
      const res = await axios.post("http://127.0.0.1:8000/auth/login", { email, password });

      const { user: userData, access_token, refresh_token } = res.data;

      localStorage.setItem('ssa_user', JSON.stringify(userData));
      localStorage.setItem('ssa_access_token', access_token);
      localStorage.setItem('ssa_refresh_token', refresh_token);

      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      setUser(userData);
    } catch (err) {
      setError(err.response?.data?.detail || "Invalid credentials");
      throw err;
    }
  };

  const register = async (email, password, name, role, department) => {
    try {
      setError(null);
      const res = await axios.post("http://127.0.0.1:8000/auth/register", { email, password, name, role, department });

      const { user: userData, access_token, refresh_token } = res.data;

      localStorage.setItem('ssa_user', JSON.stringify(userData));
      localStorage.setItem('ssa_access_token', access_token);
      localStorage.setItem('ssa_refresh_token', refresh_token);

      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      setUser(userData);
    } catch (err) {
      setError(err.response?.data?.detail || "Registration failed");
      throw err;
    }
  }

  const logout = () => {
    setUser(null);
    localStorage.removeItem('ssa_user');
    localStorage.removeItem('ssa_access_token');
    localStorage.removeItem('ssa_refresh_token');
    delete axios.defaults.headers.common['Authorization'];
  };

  if (loading) return null; // or a loading spinner

  return (
    <AuthContext.Provider value={{ user, login, register, logout, error }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
