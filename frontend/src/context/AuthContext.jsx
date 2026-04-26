import { createContext, useContext, useState, useEffect } from 'react';
import api from '../api/axios';

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
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }
    setLoading(false);
  }, []);

  const login = async (email, password) => {
    try {
      setError(null);
      const res = await api.post("/auth/login", { email, password });

      const { user: userData, access_token, refresh_token } = res.data;

      localStorage.setItem('ssa_user', JSON.stringify(userData));
      localStorage.setItem('ssa_access_token', access_token);
      localStorage.setItem('ssa_refresh_token', refresh_token);

      api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      setUser(userData);
    } catch (err) {
      setError(err.response?.data?.detail || "Invalid credentials");
      throw err;
    }
  };

  const register = async (email, password, name, role, department) => {
    try {
      setError(null);
      const res = await api.post("/auth/register", { email, password, name, role, department });

      const { user: userData, access_token, refresh_token } = res.data;

      localStorage.setItem('ssa_user', JSON.stringify(userData));
      localStorage.setItem('ssa_access_token', access_token);
      localStorage.setItem('ssa_refresh_token', refresh_token);

      api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
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
    delete api.defaults.headers.common['Authorization'];
  };

  if (loading) return null; // or a loading spinner

  return (
    <AuthContext.Provider value={{ user, login, register, logout, error }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
