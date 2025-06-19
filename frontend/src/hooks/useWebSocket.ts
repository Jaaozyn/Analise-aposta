import { useEffect, useState, useCallback, useRef } from 'react';
import { wsService } from '../services/websocket';
import { mutate } from 'swr';

// ==============================================
// HOOK PRINCIPAL DO WEBSOCKET
// ==============================================

export const useWebSocket = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState({
    connected: false,
    reconnectAttempts: 0,
    socketId: null
  });

  useEffect(() => {
    // Verificar status inicial
    setIsConnected(wsService.isConnectionActive());
    setConnectionStatus(wsService.getConnectionStatus());

    // Conectar se não estiver conectado
    wsService.connect();

    // Listeners para mudanças de status
    wsService.on('connect', () => {
      setIsConnected(true);
      setConnectionStatus(wsService.getConnectionStatus());
    });

    wsService.on('disconnect', () => {
      setIsConnected(false);
      setConnectionStatus(wsService.getConnectionStatus());
    });

    // Cleanup
    return () => {
      // Não desconectar aqui pois outros componentes podem estar usando
    };
  }, []);

  const emit = useCallback((event: string, data?: any) => {
    wsService.emit(event, data);
  }, []);

  return {
    isConnected,
    connectionStatus,
    emit,
    service: wsService
  };
};

// ==============================================
// HOOK PARA PICKS EM TEMPO REAL
// ==============================================

interface PickUpdate {
  pick_id: string;
  odds_change: number;
  new_odds: number;
  old_odds: number;
  timestamp: string;
}

interface NewPick {
  pick: any;
  notification: boolean;
}

export const useRealTimePicks = () => {
  const [recentUpdates, setRecentUpdates] = useState<PickUpdate[]>([]);
  const [newPicksCount, setNewPicksCount] = useState(0);
  const lastUpdateRef = useRef<Date>(new Date());

  useEffect(() => {
    const handlePickUpdate = (data: PickUpdate) => {
      setRecentUpdates(prev => {
        const updated = [data, ...prev.slice(0, 9)]; // Manter apenas 10 mais recentes
        return updated;
      });

      // Invalidar cache do SWR para atualizar dados
      mutate(['picks']);
    };

    const handleNewPick = (data: NewPick) => {
      setNewPicksCount(prev => prev + 1);
      
      // Invalidar cache para buscar novos picks
      mutate(['picks']);
      mutate(['picks', undefined]); // Para picks sem filtros
    };

    const handlePicksGenerated = (data: { count: number }) => {
      setNewPicksCount(prev => prev + data.count);
      
      // Invalidar todos os caches de picks
      mutate(key => Array.isArray(key) && key[0] === 'picks');
    };

    // Registrar listeners
    wsService.on('pick_update', handlePickUpdate);
    wsService.on('new_pick', handleNewPick);
    wsService.on('picks_generated', handlePicksGenerated);

    // Cleanup
    return () => {
      wsService.off('pick_update', handlePickUpdate);
      wsService.off('new_pick', handleNewPick);
      wsService.off('picks_generated', handlePicksGenerated);
    };
  }, []);

  const clearNewPicksCount = useCallback(() => {
    setNewPicksCount(0);
  }, []);

  const subscribeToSport = useCallback((sport: string) => {
    wsService.subscribeToSport(sport);
  }, []);

  const unsubscribeFromSport = useCallback((sport: string) => {
    wsService.unsubscribeFromSport(sport);
  }, []);

  const subscribeToPick = useCallback((pickId: string) => {
    wsService.subscribeToPick(pickId);
  }, []);

  const unsubscribeFromPick = useCallback((pickId: string) => {
    wsService.unsubscribeFromPick(pickId);
  }, []);

  return {
    recentUpdates,
    newPicksCount,
    clearNewPicksCount,
    subscribeToSport,
    unsubscribeFromSport,
    subscribeToPick,
    unsubscribeFromPick
  };
};

// ==============================================
// HOOK PARA BANKROLL EM TEMPO REAL
// ==============================================

interface BankrollUpdate {
  user_id: string;
  new_balance: number;
  change: number;
  timestamp: string;
}

export const useRealTimeBankroll = () => {
  const [lastUpdate, setLastUpdate] = useState<BankrollUpdate | null>(null);
  const [recentChanges, setRecentChanges] = useState<BankrollUpdate[]>([]);

  useEffect(() => {
    const handleBankrollUpdate = (data: BankrollUpdate) => {
      setLastUpdate(data);
      setRecentChanges(prev => {
        const updated = [data, ...prev.slice(0, 4)]; // Manter 5 mais recentes
        return updated;
      });

      // Invalidar caches relacionados à banca
      mutate('user-stats');
      mutate(['bankroll-history']);
      mutate('performance-metrics');
    };

    wsService.on('bankroll_update', handleBankrollUpdate);

    return () => {
      wsService.off('bankroll_update', handleBankrollUpdate);
    };
  }, []);

  return {
    lastUpdate,
    recentChanges
  };
};

// ==============================================
// HOOK PARA ALERTAS EM TEMPO REAL
// ==============================================

interface AlertNotification {
  id: string;
  type: 'ev_opportunity' | 'odds_change' | 'result_update' | 'system';
  title: string;
  message: string;
  data?: any;
  timestamp: string;
}

export const useRealTimeAlerts = () => {
  const [alerts, setAlerts] = useState<AlertNotification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    const handleAlert = (data: AlertNotification) => {
      setAlerts(prev => {
        const updated = [data, ...prev.slice(0, 19)]; // Manter 20 mais recentes
        return updated;
      });
      
      setUnreadCount(prev => prev + 1);

      // Invalidar cache de alertas
      mutate('alerts');
    };

    wsService.on('alert_notification', handleAlert);

    return () => {
      wsService.off('alert_notification', handleAlert);
    };
  }, []);

  const markAsRead = useCallback((alertId: string) => {
    setAlerts(prev => 
      prev.map(alert => 
        alert.id === alertId 
          ? { ...alert, read: true }
          : alert
      )
    );
    setUnreadCount(prev => Math.max(0, prev - 1));
  }, []);

  const markAllAsRead = useCallback(() => {
    setAlerts(prev => prev.map(alert => ({ ...alert, read: true })));
    setUnreadCount(0);
  }, []);

  return {
    alerts,
    unreadCount,
    markAsRead,
    markAllAsRead
  };
};

// ==============================================
// HOOK PARA CONQUISTAS EM TEMPO REAL
// ==============================================

interface Achievement {
  id: string;
  title: string;
  description: string;
  icon: string;
  timestamp: string;
}

export const useRealTimeAchievements = () => {
  const [recentAchievements, setRecentAchievements] = useState<Achievement[]>([]);
  const [newAchievementsCount, setNewAchievementsCount] = useState(0);

  useEffect(() => {
    const handleAchievement = (data: Achievement) => {
      setRecentAchievements(prev => {
        const updated = [data, ...prev.slice(0, 4)]; // Manter 5 mais recentes
        return updated;
      });
      
      setNewAchievementsCount(prev => prev + 1);

      // Invalidar cache de progresso do usuário
      mutate('user-progress');
    };

    wsService.on('user_achievement', handleAchievement);

    return () => {
      wsService.off('user_achievement', handleAchievement);
    };
  }, []);

  const clearNewAchievementsCount = useCallback(() => {
    setNewAchievementsCount(0);
  }, []);

  return {
    recentAchievements,
    newAchievementsCount,
    clearNewAchievementsCount
  };
};

// ==============================================
// HOOK PARA STATUS DA CONEXÃO
// ==============================================

export const useConnectionStatus = () => {
  const [status, setStatus] = useState({
    connected: false,
    reconnectAttempts: 0,
    lastConnected: null as Date | null,
    latency: 0
  });

  useEffect(() => {
    let pingInterval: NodeJS.Timeout;

    const updateStatus = () => {
      const wsStatus = wsService.getConnectionStatus();
      setStatus(prev => ({
        ...prev,
        connected: wsStatus.connected,
        reconnectAttempts: wsStatus.reconnectAttempts,
        lastConnected: wsStatus.connected ? new Date() : prev.lastConnected
      }));
    };

    const measureLatency = () => {
      const start = Date.now();
      wsService.emit('ping', { timestamp: start });
    };

    const handlePong = (data: { timestamp: number }) => {
      const latency = Date.now() - data.timestamp;
      setStatus(prev => ({ ...prev, latency }));
    };

    // Listeners para mudanças de conexão
    wsService.on('connect', updateStatus);
    wsService.on('disconnect', updateStatus);
    wsService.on('pong', handlePong);

    // Status inicial
    updateStatus();

    // Ping periódico para medir latência
    if (wsService.isConnectionActive()) {
      pingInterval = setInterval(measureLatency, 30000); // A cada 30 segundos
    }

    return () => {
      wsService.off('connect', updateStatus);
      wsService.off('disconnect', updateStatus);
      wsService.off('pong', handlePong);
      
      if (pingInterval) {
        clearInterval(pingInterval);
      }
    };
  }, []);

  return status;
};

// ==============================================
// HOOK PARA AUTO-RECONEXÃO EM BACKGROUND
// ==============================================

export const useAutoReconnect = () => {
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        // Página ficou visível, verificar conexão
        if (!wsService.isConnectionActive()) {
          console.log('WebSocket: Reconectando após página ficar visível...');
          wsService.connect();
        }
      }
    };

    const handleOnline = () => {
      console.log('WebSocket: Internet voltou, reconectando...');
      wsService.connect();
    };

    const handleOffline = () => {
      console.log('WebSocket: Internet perdida');
    };

    // Event listeners
    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);
}; 