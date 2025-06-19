import axios, { AxiosInstance, AxiosResponse } from 'axios';

// Configuração da API base
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Interceptor para adicionar token de autenticação
    this.api.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Interceptor para tratar respostas
    this.api.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          // Token expirado - redirecionar para login
          localStorage.removeItem('auth_token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // ==============================================
  // AUTHENTICATION ENDPOINTS
  // ==============================================
  
  async login(email: string, password: string) {
    const response = await this.api.post('/auth/login', { email, password });
    return response.data;
  }

  async register(userData: RegisterData) {
    const response = await this.api.post('/auth/register', userData);
    return response.data;
  }

  async logout() {
    const response = await this.api.post('/auth/logout');
    localStorage.removeItem('auth_token');
    return response.data;
  }

  async refreshToken() {
    const response = await this.api.post('/auth/refresh');
    return response.data;
  }

  async getProfile() {
    const response = await this.api.get('/auth/profile');
    return response.data;
  }

  // ==============================================
  // PICKS ENDPOINTS
  // ==============================================

  async getPicks(filters?: PickFilters) {
    const params = new URLSearchParams();
    if (filters?.sport) params.append('sport', filters.sport);
    if (filters?.min_ev) params.append('min_ev', filters.min_ev.toString());
    if (filters?.date) params.append('date', filters.date);
    if (filters?.limit) params.append('limit', filters.limit.toString());

    const response = await this.api.get(`/picks?${params.toString()}`);
    return response.data;
  }

  async generatePicks(matchId?: string) {
    const response = await this.api.post('/picks/generate', { match_id: matchId });
    return response.data;
  }

  async getPickById(pickId: string) {
    const response = await this.api.get(`/picks/${pickId}`);
    return response.data;
  }

  async getPickAnalysis(pickId: string) {
    const response = await this.api.get(`/picks/${pickId}/analysis`);
    return response.data;
  }

  // ==============================================
  // MATCHES ENDPOINTS
  // ==============================================

  async getMatches(filters?: MatchFilters) {
    const params = new URLSearchParams();
    if (filters?.sport) params.append('sport', filters.sport);
    if (filters?.date) params.append('date', filters.date);
    if (filters?.league) params.append('league', filters.league);

    const response = await this.api.get(`/matches?${params.toString()}`);
    return response.data;
  }

  async getMatchAnalysis(matchId: string) {
    const response = await this.api.get(`/matches/${matchId}/analysis`);
    return response.data;
  }

  // ==============================================
  // ANALYTICS & PERFORMANCE ENDPOINTS
  // ==============================================

  async getUserStats() {
    const response = await this.api.get('/analytics/user-stats');
    return response.data;
  }

  async getBankrollHistory(period?: string) {
    const params = period ? `?period=${period}` : '';
    const response = await this.api.get(`/analytics/bankroll${params}`);
    return response.data;
  }

  async getPerformanceMetrics() {
    const response = await this.api.get('/analytics/performance');
    return response.data;
  }

  async addBetResult(data: BetResultData) {
    const response = await this.api.post('/analytics/bet-result', data);
    return response.data;
  }

  async getInsights() {
    const response = await this.api.get('/analytics/insights');
    return response.data;
  }

  // ==============================================
  // SUBSCRIPTION & PRICING ENDPOINTS
  // ==============================================

  async getSubscriptionTiers() {
    const response = await this.api.get('/pricing/tiers');
    return response.data;
  }

  async getCurrentSubscription() {
    const response = await this.api.get('/pricing/subscription');
    return response.data;
  }

  async upgradeSubscription(tierId: string) {
    const response = await this.api.post('/pricing/upgrade', { tier_id: tierId });
    return response.data;
  }

  // ==============================================
  // ALERTS & NOTIFICATIONS ENDPOINTS
  // ==============================================

  async getAlerts() {
    const response = await this.api.get('/alerts');
    return response.data;
  }

  async markAlertAsRead(alertId: string) {
    const response = await this.api.patch(`/alerts/${alertId}/read`);
    return response.data;
  }

  async updateAlertSettings(settings: AlertSettings) {
    const response = await this.api.put('/alerts/settings', settings);
    return response.data;
  }

  // ==============================================
  // EDUCATIONAL SYSTEM ENDPOINTS
  // ==============================================

  async getLessons() {
    const response = await this.api.get('/education/lessons');
    return response.data;
  }

  async getLesson(lessonId: string) {
    const response = await this.api.get(`/education/lessons/${lessonId}`);
    return response.data;
  }

  async completeLesson(lessonId: string, score?: number) {
    const response = await this.api.post(`/education/lessons/${lessonId}/complete`, { score });
    return response.data;
  }

  async getUserProgress() {
    const response = await this.api.get('/education/progress');
    return response.data;
  }
}

// ==============================================
// TYPE DEFINITIONS
// ==============================================

export interface RegisterData {
  email: string;
  password: string;
  full_name: string;
  preferred_sports?: string[];
}

export interface PickFilters {
  sport?: string;
  min_ev?: number;
  date?: string;
  limit?: number;
}

export interface MatchFilters {
  sport?: string;
  date?: string;
  league?: string;
}

export interface BetResultData {
  pick_id: string;
  result: 'won' | 'lost' | 'void';
  stake: number;
  odds: number;
  profit_loss: number;
}

export interface AlertSettings {
  ev_threshold: number;
  sports: string[];
  notification_methods: string[];
  daily_summary: boolean;
}

// Singleton instance
export const apiService = new ApiService();
export default apiService; 