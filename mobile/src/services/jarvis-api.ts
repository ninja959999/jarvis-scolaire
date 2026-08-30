import axios, { AxiosInstance } from "axios";

const API_URL = process.env.EXPO_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export interface JarvisChatResponse {
  text: string;
  intent?: string;
  confidence?: number;
}

export interface JarvisApi {
  chat(message: string, context?: Record<string, unknown>): Promise<JarvisChatResponse>;
  getDashboard(): Promise<unknown>;
  getWeather(latitude?: number, longitude?: number): Promise<unknown>;
  getTrains(departure: string, arrival: string, date?: string): Promise<unknown>;
}

class JarvisApiClient implements JarvisApi {
  private readonly client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_URL,
      timeout: 15_000,
      headers: { "Content-Type": "application/json" },
    });
  }

  async chat(message: string, context?: Record<string, unknown>): Promise<JarvisChatResponse> {
    const { data } = await this.client.post<JarvisChatResponse>("/api/ai/chat", {
      message,
      context,
    });
    return data;
  }

  async getDashboard(): Promise<unknown> {
    const { data } = await this.client.get("/api/dashboard");
    return data;
  }

  async getWeather(latitude?: number, longitude?: number): Promise<unknown> {
    const { data } = await this.client.get("/api/weather", {
      params: { latitude, longitude },
    });
    return data;
  }

  async getTrains(departure: string, arrival: string, date?: string): Promise<unknown> {
    const { data } = await this.client.get("/api/trains", {
      params: { departure, arrival, date },
    });
    return data;
  }
}

export const jarvisApi = new JarvisApiClient();
