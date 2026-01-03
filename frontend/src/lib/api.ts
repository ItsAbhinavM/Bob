import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface Task {
  id: string;
  title: string;
  description?: string;
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled';
  priority: 'low' | 'medium' | 'high';
  due_date?: string;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface WeatherData {
  location: string;
  temperature: number;
  condition: string;
  description: string;
  humidity: number;
  wind_speed: number;
  suggestion: string;
}

export interface ChatMessage {
  message: string;
  conversation_id?: string;
}

export interface ChatResponse {
  response: string;
  conversation_id: string;
  action_taken?: string;
  data?: any;
}

export const taskAPI = {
  create: async (task: Partial<Task>): Promise<Task> => {
    const response = await apiClient.post('/api/tasks', task);
    return response.data;
  },
  
  getAll: async (status?: string): Promise<Task[]> => {
    const params = status ? { status } : {};
    const response = await apiClient.get('/api/tasks', { params });
    return response.data;
  },
  
  getById: async (id: string): Promise<Task> => {
    const response = await apiClient.get(`/api/tasks/${id}`);
    return response.data;
  },
  
  update: async (id: string, updates: Partial<Task>): Promise<Task> => {
    const response = await apiClient.put(`/api/tasks/${id}`, updates);
    return response.data;
  },
  
  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/tasks/${id}`);
  },
};

export const weatherAPI = {
  get: async (location: string): Promise<WeatherData> => {
    const response = await apiClient.get('/api/weather', {
      params: { location },
    });
    return response.data;
  },
};

export const chatAPI = {
  send: async (message: ChatMessage): Promise<ChatResponse> => {
    const response = await apiClient.post('/api/chat', message);
    return response.data;
  },
};

export default apiClient;