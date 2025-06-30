import axios from 'axios';
import { apiClient } from './apiClient';

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  organization: {
    id: string;
    name: string;
    plan_type: string;
  };
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface RegisterData {
  email: string;
  password: string;
  full_name: string;
  organization_name: string;
}

class AuthService {
  async login(email: string, password: string): Promise<AuthResponse> {
    const response = await apiClient.post('/auth/login', {
      email,
      password,
    });
    
    if (response.data.access_token) {
      this.setAuthToken(response.data.access_token);
    }
    
    return response.data;
  }

  async register(userData: RegisterData): Promise<AuthResponse> {
    const response = await apiClient.post('/auth/register', userData);
    
    if (response.data.access_token) {
      this.setAuthToken(response.data.access_token);
    }
    
    return response.data;
  }

  async logout(): Promise<void> {
    try {
      await apiClient.post('/auth/logout');
    } catch (error) {
      // Ignore logout errors
    } finally {
      this.removeAuthToken();
    }
  }

  async refreshToken(): Promise<{ access_token: string; token_type: string; expires_in: number }> {
    const response = await apiClient.post('/auth/refresh');
    
    if (response.data.access_token) {
      this.setAuthToken(response.data.access_token);
    }
    
    return response.data;
  }

  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get('/auth/me');
    return response.data;
  }

  private setAuthToken(token: string): void {
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  }

  private removeAuthToken(): void {
    delete apiClient.defaults.headers.common['Authorization'];
  }

  // Set token for existing sessions
  setToken(token: string): void {
    this.setAuthToken(token);
  }
}

export const authService = new AuthService();