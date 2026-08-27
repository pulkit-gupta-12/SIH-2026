/**
 * Auth Service — login, register, refresh, me endpoints.
 */
import apiClient from './apiClient';
import type { UserRole } from '../store/authStore';

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  username: string;
  password: string;
  email?: string;
  first_name?: string;
  last_name?: string;
  phone?: string;
  role: UserRole;
  state?: string;
  organization?: string;
}

export interface AuthUser {
  id: number;
  username: string;
  email: string;
  name: string;
  roles: string[];
}

export interface LoginResponse {
  access: string;
  refresh: string;
  user: AuthUser;
}

export const authService = {
  async login(credentials: LoginCredentials): Promise<LoginResponse> {
    const { data } = await apiClient.post<LoginResponse>('/auth/login/', credentials);
    return data;
  },

  async register(registerData: RegisterData): Promise<LoginResponse> {
    const { data } = await apiClient.post<LoginResponse>('/auth/register/', registerData);
    return data;
  },

  async refreshToken(refresh: string) {
    const { data } = await apiClient.post('/auth/refresh/', { refresh });
    return data;
  },

  async getMe(): Promise<AuthUser> {
    const { data } = await apiClient.get<AuthUser>('/auth/me/');
    return data;
  },
};
