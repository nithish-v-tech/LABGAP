import React, { createContext, useContext, useState, useEffect } from 'react';
import { UserProfile, UserRole } from '../types';
import { api } from '../services/api';

interface AuthContextType {
  user: UserProfile | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password?: string) => Promise<boolean>;
  logout: () => void;
  switchDemoRole: (role: UserRole) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const DEMO_CREDENTIALS: Record<UserRole, { email: string; pass: string; title: string }> = {
  admin: { email: 'admin@labgap.demo', pass: 'AdminPassword123!', title: 'Laboratory Administrator' },
  faculty: { email: 'faculty@labgap.demo', pass: 'FacultyPassword123!', title: 'Faculty / Lab Instructor' },
  student: { email: 'student@labgap.demo', pass: 'StudentPassword123!', title: 'Student Portal' },
  hod: { email: 'hod@labgap.demo', pass: 'HodPassword123!', title: 'Head of Department (HOD)' },
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('labgap_token'));
  const [loading, setLoading] = useState<boolean>(true);

  const fetchProfile = async () => {
    try {
      const res = await api.get('/auth/me');
      setUser(res.data);
      localStorage.setItem('labgap_user', JSON.stringify(res.data));
    } catch (err) {
      console.error('Failed to fetch user profile', err);
      logout();
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      fetchProfile();
    } else {
      setLoading(false);
    }
  }, [token]);

  const login = async (email: string, password = 'AdminPassword123!'): Promise<boolean> => {
    setLoading(true);
    try {
      const res = await api.post('/auth/login', { email, password });
      const newToken = res.data.access_token;
      localStorage.setItem('labgap_token', newToken);
      setToken(newToken);
      // Fetch full profile immediately
      const profileRes = await api.get('/auth/me', {
        headers: { Authorization: `Bearer ${newToken}` }
      });
      setUser(profileRes.data);
      localStorage.setItem('labgap_user', JSON.stringify(profileRes.data));
      setLoading(false);
      return true;
    } catch (err) {
      console.error('Login error', err);
      setLoading(false);
      return false;
    }
  };

  const logout = () => {
    localStorage.removeItem('labgap_token');
    localStorage.removeItem('labgap_user');
    setToken(null);
    setUser(null);
  };

  const switchDemoRole = async (targetRole: UserRole) => {
    const cred = DEMO_CREDENTIALS[targetRole];
    if (cred) {
      await login(cred.email, cred.pass);
    }
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout, switchDemoRole }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
