import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';
import { User } from '../types';

interface AuthContextType {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  login: () => Promise<void>;
  logout: () => void;
  refreshAccessToken: () => Promise<boolean>;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [refreshToken, setRefreshToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const API_URL = 'http://localhost:8000';

  useEffect(() => {
    // Check for existing session
    const savedToken = localStorage.getItem('codeduel_token');
    const savedRefreshToken = localStorage.getItem('codeduel_refresh_token');
    const savedUser = localStorage.getItem('codeduel_user');

    if (savedToken && savedUser) {
      setToken(savedToken);
      setRefreshToken(savedRefreshToken);
      setUser(JSON.parse(savedUser));
      
      // Set axios default header
      axios.defaults.headers.common['Authorization'] = `Bearer ${savedToken}`;
    }
    
    setIsLoading(false);
  }, []);

  const login = async () => {
    try {
      setIsLoading(true);
      const response = await axios.post(`${API_URL}/api/auth/guest`);
      const { user: newUser, token: newToken, refresh_token: newRefreshToken } = response.data;

      setUser(newUser);
      setToken(newToken);
      setRefreshToken(newRefreshToken);

      // Save to localStorage
      localStorage.setItem('codeduel_token', newToken);
      localStorage.setItem('codeduel_refresh_token', newRefreshToken);
      localStorage.setItem('codeduel_user', JSON.stringify(newUser));

      // Set axios default header
      axios.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const refreshAccessToken = async (): Promise<boolean> => {
    try {
      if (!refreshToken) {
        return false;
      }

      const response = await axios.post(`${API_URL}/api/auth/refresh`, {
        refresh_token: refreshToken
      });

      const { token: newToken } = response.data;
      setToken(newToken);
      localStorage.setItem('codeduel_token', newToken);
      axios.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
      
      return true;
    } catch (error) {
      console.error('Token refresh failed:', error);
      // If refresh fails, logout the user
      logout();
      return false;
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    setRefreshToken(null);
    
    // Clear localStorage
    localStorage.removeItem('codeduel_token');
    localStorage.removeItem('codeduel_refresh_token');
    localStorage.removeItem('codeduel_user');
    
    // Clear axios default header
    delete axios.defaults.headers.common['Authorization'];
  };

  const value = {
    user,
    token,
    refreshToken,
    login,
    logout,
    refreshAccessToken,
    isLoading,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
