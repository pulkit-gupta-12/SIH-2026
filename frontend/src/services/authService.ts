/**
 * Auth Service — login, refresh, me endpoints.
 */
import apiClient from './apiClient';

export interface LoginCredentials {
  username: string;
  password: string;
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

  async refreshToken(refresh: string) {
    const { data } = await apiClient.post('/auth/refresh/', { refresh });
    return data;
  },

  async getMe(): Promise<AuthUser> {
    const { data } = await apiClient.get<AuthUser>('/auth/me/');
    return data;
  },
};
