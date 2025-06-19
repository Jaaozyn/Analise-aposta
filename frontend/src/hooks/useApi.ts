import useSWR, { mutate } from 'swr';
import { apiService, PickFilters, MatchFilters } from '../services/api';

// ==============================================
// PICKS HOOKS
// ==============================================

export const usePicks = (filters?: PickFilters) => {
  const key = ['picks', filters];
  
  const { data, error, isLoading } = useSWR(
    key,
    () => apiService.getPicks(filters),
    {
      refreshInterval: 30000, // Refresh a cada 30s
      revalidateOnFocus: true,
      dedupingInterval: 5000,
    }
  );

  const refreshPicks = () => mutate(key);

  return {
    picks: data?.picks || [],
    error,
    isLoading,
    refreshPicks,
  };
};

export const usePickById = (pickId: string) => {
  const { data, error, isLoading } = useSWR(
    pickId ? ['pick', pickId] : null,
    () => apiService.getPickById(pickId),
    {
      revalidateOnFocus: false,
    }
  );

  return {
    pick: data?.pick,
    error,
    isLoading,
  };
};

export const usePickAnalysis = (pickId: string) => {
  const { data, error, isLoading } = useSWR(
    pickId ? ['pick-analysis', pickId] : null,
    () => apiService.getPickAnalysis(pickId),
    {
      revalidateOnFocus: false,
    }
  );

  return {
    analysis: data?.analysis,
    error,
    isLoading,
  };
};

// ==============================================
// MATCHES HOOKS
// ==============================================

export const useMatches = (filters?: MatchFilters) => {
  const { data, error, isLoading } = useSWR(
    ['matches', filters],
    () => apiService.getMatches(filters),
    {
      refreshInterval: 60000, // Refresh a cada 1 minuto
    }
  );

  return {
    matches: data?.matches || [],
    error,
    isLoading,
  };
};

export const useMatchAnalysis = (matchId: string) => {
  const { data, error, isLoading } = useSWR(
    matchId ? ['match-analysis', matchId] : null,
    () => apiService.getMatchAnalysis(matchId)
  );

  return {
    analysis: data?.analysis,
    error,
    isLoading,
  };
};

// ==============================================
// USER & ANALYTICS HOOKS
// ==============================================

export const useUserStats = () => {
  const { data, error, isLoading } = useSWR(
    'user-stats',
    () => apiService.getUserStats(),
    {
      refreshInterval: 300000, // Refresh a cada 5 minutos
    }
  );

  return {
    stats: data?.stats,
    error,
    isLoading,
  };
};

export const useBankrollHistory = (period?: string) => {
  const { data, error, isLoading } = useSWR(
    ['bankroll-history', period],
    () => apiService.getBankrollHistory(period),
    {
      refreshInterval: 300000, // Refresh a cada 5 minutos
    }
  );

  return {
    history: data?.history || [],
    error,
    isLoading,
  };
};

export const usePerformanceMetrics = () => {
  const { data, error, isLoading } = useSWR(
    'performance-metrics',
    () => apiService.getPerformanceMetrics(),
    {
      refreshInterval: 300000, // Refresh a cada 5 minutos
    }
  );

  return {
    metrics: data?.metrics,
    error,
    isLoading,
  };
};

export const useInsights = () => {
  const { data, error, isLoading } = useSWR(
    'insights',
    () => apiService.getInsights(),
    {
      refreshInterval: 3600000, // Refresh a cada 1 hora
    }
  );

  return {
    insights: data?.insights || [],
    error,
    isLoading,
  };
};

// ==============================================
// SUBSCRIPTION HOOKS
// ==============================================

export const useSubscriptionTiers = () => {
  const { data, error, isLoading } = useSWR(
    'subscription-tiers',
    () => apiService.getSubscriptionTiers(),
    {
      revalidateOnFocus: false,
      revalidateOnMount: true,
    }
  );

  return {
    tiers: data?.tiers || [],
    error,
    isLoading,
  };
};

export const useCurrentSubscription = () => {
  const { data, error, isLoading } = useSWR(
    'current-subscription',
    () => apiService.getCurrentSubscription(),
    {
      refreshInterval: 3600000, // Refresh a cada 1 hora
    }
  );

  return {
    subscription: data?.subscription,
    error,
    isLoading,
  };
};

// ==============================================
// ALERTS HOOKS
// ==============================================

export const useAlerts = () => {
  const { data, error, isLoading } = useSWR(
    'alerts',
    () => apiService.getAlerts(),
    {
      refreshInterval: 60000, // Refresh a cada 1 minuto
    }
  );

  const markAsRead = async (alertId: string) => {
    await apiService.markAlertAsRead(alertId);
    mutate('alerts');
  };

  return {
    alerts: data?.alerts || [],
    unreadCount: data?.unread_count || 0,
    error,
    isLoading,
    markAsRead,
  };
};

// ==============================================
// EDUCATION HOOKS
// ==============================================

export const useLessons = () => {
  const { data, error, isLoading } = useSWR(
    'lessons',
    () => apiService.getLessons(),
    {
      revalidateOnFocus: false,
    }
  );

  return {
    lessons: data?.lessons || [],
    error,
    isLoading,
  };
};

export const useLesson = (lessonId: string) => {
  const { data, error, isLoading } = useSWR(
    lessonId ? ['lesson', lessonId] : null,
    () => apiService.getLesson(lessonId),
    {
      revalidateOnFocus: false,
    }
  );

  return {
    lesson: data?.lesson,
    error,
    isLoading,
  };
};

export const useUserProgress = () => {
  const { data, error, isLoading } = useSWR(
    'user-progress',
    () => apiService.getUserProgress(),
    {
      refreshInterval: 300000, // Refresh a cada 5 minutos
    }
  );

  return {
    progress: data?.progress,
    error,
    isLoading,
  };
};

// ==============================================
// MUTATION HOOKS (para ações que modificam dados)
// ==============================================

export const useGeneratePicks = () => {
  const generatePicks = async (matchId?: string) => {
    try {
      const result = await apiService.generatePicks(matchId);
      // Invalidar cache dos picks para buscar novos dados
      mutate(['picks']);
      return result;
    } catch (error) {
      throw error;
    }
  };

  return { generatePicks };
};

export const useAddBetResult = () => {
  const addBetResult = async (data: any) => {
    try {
      const result = await apiService.addBetResult(data);
      // Invalidar cache relacionado
      mutate('user-stats');
      mutate(['bankroll-history']);
      mutate('performance-metrics');
      return result;
    } catch (error) {
      throw error;
    }
  };

  return { addBetResult };
};

export const useCompleteLesson = () => {
  const completeLesson = async (lessonId: string, score?: number) => {
    try {
      const result = await apiService.completeLesson(lessonId, score);
      // Invalidar cache do progresso
      mutate('user-progress');
      mutate('lessons');
      return result;
    } catch (error) {
      throw error;
    }
  };

  return { completeLesson };
}; 