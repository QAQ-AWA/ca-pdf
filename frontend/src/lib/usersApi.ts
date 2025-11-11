import { httpClient } from "./httpClient";

export interface User {
  id: string;
  username: string;
  email: string;
  role: "user" | "admin";
  is_active: boolean;
  created_at: string;
}

export interface UserListResponse {
  items: User[];
  total_count: number;
  skip: number;
  limit: number;
}

export interface CreateUserData {
  username: string;
  email: string;
  password: string;
  role?: string;
  is_active?: boolean;
}

export interface UpdateUserData {
  email?: string;
  role?: string;
  is_active?: boolean;
}

export interface ListUsersParams {
  skip?: number;
  limit?: number;
  search?: string;
  role?: string;
  is_active?: boolean;
}

export const usersApi = {
  listUsers: async (params?: ListUsersParams) => {
    const response = await httpClient.get<UserListResponse>("/api/v1/users", { params });
    return response.data;
  },

  getUser: async (id: string) => {
    const response = await httpClient.get<User>(`/api/v1/users/${id}`);
    return response.data;
  },

  createUser: async (data: CreateUserData) => {
    const response = await httpClient.post<User>("/api/v1/users", data);
    return response.data;
  },

  updateUser: async (id: string, data: UpdateUserData) => {
    const response = await httpClient.patch<User>(`/api/v1/users/${id}`, data);
    return response.data;
  },

  deleteUser: async (id: string) => {
    await httpClient.delete(`/api/v1/users/${id}`);
  },

  resetPassword: async (id: string, new_password: string) => {
    const response = await httpClient.post(`/api/v1/users/${id}/reset-password`, { new_password });
    return response.data;
  },

  toggleActive: async (id: string) => {
    const response = await httpClient.post<User>(`/api/v1/users/${id}/toggle-active`);
    return response.data;
  },
};
