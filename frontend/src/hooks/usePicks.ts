import { useState, useEffect, useCallback } from 'react';

export interface Pick {
  id: string;
  homeTeam: string;
  awayTeam: string;
  sport: string;
  league: string;
  market: string;
  selection: string;
  odds: number;
  expectedValue: number;
  confidence: number;
  kickoffTime: string;
  units: number;
  reasoning: string;
  status: 'pending' | 'won' | 'lost' | 'void';
  createdAt: string;
}

interface UsePicksReturn {
  picks: Pick[];
  loading: boolean;
  error: string | null;
  refreshPicks: () => Promise<void>;
  generatePicks: (matchId?: string) => Promise<void>;
  getPickById: (id: string) => Pick | undefined;
}

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

export const usePicks = (): UsePicksReturn => {
  const [picks, setPicks] = useState<Pick[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Mock data para desenvolvimento - remover quando API estiver pronta
  const mockPicks: Pick[] = [
    {
      id: '1',
      homeTeam: 'Manchester City',
      awayTeam: 'Liverpool',
      sport: 'Futebol',
      league: 'Premier League',
      market: 'Over 2.5 Gols',
      selection: 'Mais de 2.5 gols',
      odds: 1.85,
      expectedValue: 12.8,
      confidence: 87,
      kickoffTime: '2024-01-15T15:30:00Z',
      units: 3,
      reasoning: 'Ambas as equipes têm médias altas de gols. Manchester City marca 2.8 gols por jogo em casa, enquanto Liverpool tem 2.4 gols por jogo. Histórico de confrontos diretos mostra 73% dos jogos com over 2.5.',
      status: 'pending',
      createdAt: '2024-01-15T10:00:00Z'
    },
    {
      id: '2',
      homeTeam: 'Lakers',
      awayTeam: 'Warriors',
      sport: 'Basquete',
      league: 'NBA',
      market: 'Total Points',
      selection: 'Over 225.5',
      odds: 1.92,
      expectedValue: 8.4,
      confidence: 74,
      kickoffTime: '2024-01-15T21:00:00Z',
      units: 2,
      reasoning: 'Lakers jogando em casa têm média de 118 pontos, Warriors 112 pontos fora. Ritmo de jogo acelerado esperado com ambas equipes no top 5 em possessões por jogo.',
      status: 'pending',
      createdAt: '2024-01-15T12:00:00Z'
    },
    {
      id: '3',
      homeTeam: 'Real Madrid',
      awayTeam: 'Barcelona',
      sport: 'Futebol',
      league: 'La Liga',
      market: 'Ambas Marcam',
      selection: 'Sim',
      odds: 1.76,
      expectedValue: 15.2,
      confidence: 91,
      kickoffTime: '2024-01-16T16:00:00Z',
      units: 4,
      reasoning: 'Clássico com histórico de muitos gols. Real Madrid não sofreu gols em apenas 2 dos últimos 10 jogos, Barcelona em apenas 1. Confrontos diretos mostram 85% com ambas marcando.',
      status: 'pending',
      createdAt: '2024-01-15T14:00:00Z'
    },
    {
      id: '4',
      homeTeam: 'Flamengo',
      awayTeam: 'Palmeiras',
      sport: 'Futebol',
      league: 'Brasileirão',
      market: 'Resultado',
      selection: 'Flamengo Vence',
      odds: 2.10,
      expectedValue: 5.7,
      confidence: 68,
      kickoffTime: '2024-01-17T19:00:00Z',
      units: 2,
      reasoning: 'Flamengo em excelente momento com 7 vitórias nos últimos 9 jogos. Jogando no Maracanã, tem 78% de aproveitamento. Palmeiras desfalcado com 3 titulares suspensos.',
      status: 'pending',
      createdAt: '2024-01-15T16:00:00Z'
    },
    {
      id: '5',
      homeTeam: 'Celtics',
      awayTeam: 'Heat',
      sport: 'Basquete',
      league: 'NBA',
      market: 'Handicap',
      selection: 'Celtics -4.5',
      odds: 1.88,
      expectedValue: 3.2,
      confidence: 65,
      kickoffTime: '2024-01-17T20:30:00Z',
      units: 1,
      reasoning: 'Celtics dominantes em casa com margem média de vitória de 8.5 pontos. Heat vem de back-to-back e viagem longa. Defesa do Celtics limita Heat a 45% de aproveitamento nos arremessos.',
      status: 'pending',
      createdAt: '2024-01-15T18:00:00Z'
    }
  ];

  const fetchPicks = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      // TODO: Substituir por chamada real à API quando estiver pronta
      // const response = await fetch(`${API_BASE_URL}/picks`, {
      //   headers: {
      //     'Authorization': `Bearer ${getAuthToken()}`,
      //     'Content-Type': 'application/json',
      //   },
      // });

      // if (!response.ok) {
      //   throw new Error(`Erro na API: ${response.status}`);
      // }

      // const data = await response.json();
      // setPicks(data.picks || []);

      // Simulando delay da API
      await new Promise(resolve => setTimeout(resolve, 1000));
      setPicks(mockPicks);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao carregar picks');
      console.error('Erro ao buscar picks:', err);
      // Em caso de erro, usar dados mock para desenvolvimento
      setPicks(mockPicks);
    } finally {
      setLoading(false);
    }
  }, []);

  const generatePicks = useCallback(async (matchId?: string) => {
    setLoading(true);
    setError(null);

    try {
      // TODO: Substituir por chamada real à API
      // const response = await fetch(`${API_BASE_URL}/picks/generate`, {
      //   method: 'POST',
      //   headers: {
      //     'Authorization': `Bearer ${getAuthToken()}`,
      //     'Content-Type': 'application/json',
      //   },
      //   body: JSON.stringify({ matchId }),
      // });

      // if (!response.ok) {
      //   throw new Error(`Erro ao gerar picks: ${response.status}`);
      // }

      // const data = await response.json();

      // Simulando geração de novos picks
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Adicionar alguns picks "novos" aos existentes
      const newPicks = mockPicks.slice(0, 2).map(pick => ({
        ...pick,
        id: `new_${Date.now()}_${Math.random()}`,
        createdAt: new Date().toISOString(),
      }));

      setPicks(prev => [...newPicks, ...prev]);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao gerar picks');
      console.error('Erro ao gerar picks:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const refreshPicks = useCallback(async () => {
    await fetchPicks();
  }, [fetchPicks]);

  const getPickById = useCallback((id: string): Pick | undefined => {
    return picks.find(pick => pick.id === id);
  }, [picks]);

  // Carregar picks iniciais
  useEffect(() => {
    fetchPicks();
  }, [fetchPicks]);

  return {
    picks,
    loading,
    error,
    refreshPicks,
    generatePicks,
    getPickById,
  };
};

// Helper function para obter token de auth (implementar quando auth estiver pronto)
const getAuthToken = (): string | null => {
  // TODO: Implementar quando sistema de auth estiver pronto
  return localStorage.getItem('auth_token');
}; 