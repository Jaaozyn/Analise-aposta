import { io, Socket } from 'socket.io-client';
import toast from 'react-hot-toast';

interface PickUpdate {
  pick_id: string;
  odds_change: number;
  new_odds: number;
  old_odds: number;
  timestamp: string;
}

interface NewPick {
  pick: {
    id: string;
    homeTeam: string;
    awayTeam: string;
    sport: string;
    market: string;
    expectedValue: number;
    confidence: number;
    odds: number;
  };
  notification: boolean;
}

interface AlertNotification {
  id: string;
  type: 'ev_opportunity' | 'odds_change' | 'result_update' | 'system';
  title: string;
  message: string;
  data?: any;
  timestamp: string;
}

interface BankrollUpdate {
  user_id: string;
  new_balance: number;
  change: number;
  timestamp: string;
}

class WebSocketService {
  private socket: Socket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // 1 segundo
  private isConnected = false;
  private listeners: Map<string, Function[]> = new Map();

  constructor() {
    this.initializeConnection();
  }

  private initializeConnection() {
    const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
    const token = localStorage.getItem('auth_token');

    if (!token) {
      console.log('WebSocket: Token não encontrado, aguardando login...');
      return;
    }

    try {
      this.socket = io(WS_URL, {
        auth: {
          token: token
        },
        transports: ['websocket', 'polling'],
        upgrade: true,
        rememberUpgrade: true,
        timeout: 20000,
        forceNew: true
      });

      this.setupEventListeners();
      
    } catch (error) {
      console.error('WebSocket: Erro na conexão:', error);
      this.handleReconnection();
    }
  }

  private setupEventListeners() {
    if (!this.socket) return;

    // Eventos de conexão
    this.socket.on('connect', () => {
      console.log('WebSocket: Conectado com sucesso');
      this.isConnected = true;
      this.reconnectAttempts = 0;
      
      // Mostrar notificação de conexão apenas em desenvolvimento
      if (process.env.NODE_ENV === 'development') {
        toast.success('Conectado - Atualizações em tempo real ativas', {
          duration: 2000,
          position: 'bottom-right'
        });
      }

      this.emit('user_online', { timestamp: new Date().toISOString() });
    });

    this.socket.on('disconnect', (reason) => {
      console.log('WebSocket: Desconectado:', reason);
      this.isConnected = false;
      
      if (reason === 'io server disconnect') {
        // Server desconectou o cliente, tentar reconectar
        this.handleReconnection();
      }
    });

    this.socket.on('connect_error', (error) => {
      console.error('WebSocket: Erro de conexão:', error);
      this.isConnected = false;
      this.handleReconnection();
    });

    // Eventos de dados
    this.socket.on('pick_update', (data: PickUpdate) => {
      console.log('WebSocket: Pick atualizado:', data);
      this.notifyListeners('pick_update', data);
      
      // Notificação visual para mudanças significativas
      const oddsChangePercent = ((data.new_odds - data.old_odds) / data.old_odds) * 100;
      if (Math.abs(oddsChangePercent) >= 5) {
        toast(`📊 Odd alterada: ${oddsChangePercent > 0 ? '+' : ''}${oddsChangePercent.toFixed(1)}%`, {
          duration: 4000,
          position: 'bottom-right'
        });
      }
    });

    this.socket.on('new_pick', (data: NewPick) => {
      console.log('WebSocket: Novo pick disponível:', data);
      this.notifyListeners('new_pick', data);
      
      if (data.notification && data.pick.expectedValue > 0) {
        toast.success(`🎯 Novo pick EV+: ${data.pick.homeTeam} vs ${data.pick.awayTeam}`, {
          duration: 5000,
          position: 'bottom-right'
        });
      }
    });

    this.socket.on('alert_notification', (data: AlertNotification) => {
      console.log('WebSocket: Nova notificação:', data);
      this.notifyListeners('alert_notification', data);
      
      // Mostrar toast baseado no tipo
      switch (data.type) {
        case 'ev_opportunity':
          toast.success(`💰 ${data.title}`, {
            duration: 6000,
            position: 'bottom-right'
          });
          break;
        case 'odds_change':
          toast(`📊 ${data.title}`, {
            duration: 4000,
            position: 'bottom-right'
          });
          break;
        case 'result_update':
          toast(`📈 ${data.title}`, {
            duration: 4000,
            position: 'bottom-right'
          });
          break;
        case 'system':
          toast.loading(data.title, {
            duration: 3000,
            position: 'bottom-right'
          });
          break;
      }
    });

    this.socket.on('bankroll_update', (data: BankrollUpdate) => {
      console.log('WebSocket: Banca atualizada:', data);
      this.notifyListeners('bankroll_update', data);
      
      if (data.change !== 0) {
        const isPositive = data.change > 0;
        toast(`${isPositive ? '📈' : '📉'} Banca atualizada: ${isPositive ? '+' : ''}R$ ${data.change.toLocaleString()}`, {
          duration: 4000,
          position: 'bottom-right'
        });
      }
    });

    this.socket.on('picks_generated', (data: { count: number }) => {
      console.log('WebSocket: Novos picks gerados:', data);
      this.notifyListeners('picks_generated', data);
      
      toast.success(`🎯 ${data.count} novos picks analisados!`, {
        duration: 4000,
        position: 'bottom-right'
      });
    });

    this.socket.on('market_update', (data: any) => {
      console.log('WebSocket: Mercado atualizado:', data);
      this.notifyListeners('market_update', data);
    });

    this.socket.on('user_achievement', (data: any) => {
      console.log('WebSocket: Conquista desbloqueada:', data);
      this.notifyListeners('user_achievement', data);
      
      toast.success(`🏆 Conquista desbloqueada: ${data.title}!`, {
        duration: 6000,
        position: 'bottom-right'
      });
    });
  }

  private handleReconnection() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('WebSocket: Máximo de tentativas de reconexão atingido');
      toast.error('Conexão perdida. Verifique sua internet.', {
        duration: 5000,
        position: 'bottom-right'
      });
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1); // Backoff exponencial

    console.log(`WebSocket: Tentativa de reconexão ${this.reconnectAttempts}/${this.maxReconnectAttempts} em ${delay}ms`);
    
    setTimeout(() => {
      this.initializeConnection();
    }, delay);
  }

  // Métodos públicos
  public connect() {
    if (!this.isConnected) {
      this.initializeConnection();
    }
  }

  public disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      this.isConnected = false;
    }
  }

  public emit(event: string, data?: any) {
    if (this.socket && this.isConnected) {
      this.socket.emit(event, data);
    }
  }

  public on(event: string, callback: Function) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event)!.push(callback);
  }

  public off(event: string, callback?: Function) {
    const listeners = this.listeners.get(event);
    if (listeners) {
      if (callback) {
        const index = listeners.indexOf(callback);
        if (index > -1) {
          listeners.splice(index, 1);
        }
      } else {
        // Remove all listeners for this event
        this.listeners.set(event, []);
      }
    }
  }

  private notifyListeners(event: string, data: any) {
    const listeners = this.listeners.get(event);
    if (listeners) {
      listeners.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`WebSocket: Erro no listener ${event}:`, error);
        }
      });
    }
  }

  // Métodos utilitários
  public isConnectionActive(): boolean {
    return this.isConnected;
  }

  public getConnectionStatus() {
    return {
      connected: this.isConnected,
      reconnectAttempts: this.reconnectAttempts,
      socketId: this.socket?.id || null
    };
  }

  // Métodos específicos do negócio
  public subscribeToSport(sport: string) {
    this.emit('subscribe_sport', { sport });
  }

  public unsubscribeFromSport(sport: string) {
    this.emit('unsubscribe_sport', { sport });
  }

  public subscribeToPick(pickId: string) {
    this.emit('subscribe_pick', { pick_id: pickId });
  }

  public unsubscribeFromPick(pickId: string) {
    this.emit('unsubscribe_pick', { pick_id: pickId });
  }

  public requestPicksUpdate() {
    this.emit('request_picks_update');
  }

  public heartbeat() {
    this.emit('heartbeat', { timestamp: new Date().toISOString() });
  }
}

// Singleton instance
export const wsService = new WebSocketService();
export default wsService; 