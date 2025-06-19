import React from 'react';
import { 
  TrendingUp, 
  Clock, 
  Target,
  ArrowRight,
  Star
} from 'lucide-react';

interface Pick {
  id: string;
  homeTeam: string;
  awayTeam: string;
  sport: string;
  market: string;
  odds: number;
  expectedValue: number;
  confidence: number;
  kickoffTime: string;
  units: number;
}

interface ValueOpportunitiesProps {
  picks: Pick[];
  isLoading?: boolean;
}

const ValueOpportunities: React.FC<ValueOpportunitiesProps> = ({ picks, isLoading = false }) => {
  // Mock data se não houver picks
  const mockPicks: Pick[] = picks?.length ? picks : [
    {
      id: '1',
      homeTeam: 'Manchester City',
      awayTeam: 'Liverpool',
      sport: 'Futebol',
      market: 'Over 2.5 Gols',
      odds: 1.85,
      expectedValue: 12.8,
      confidence: 87,
      kickoffTime: '2024-01-15T15:30:00Z',
      units: 3
    },
    {
      id: '2',
      homeTeam: 'Lakers',
      awayTeam: 'Warriors',
      sport: 'Basquete',
      market: 'Total Points Over 225.5',
      odds: 1.92,
      expectedValue: 8.4,
      confidence: 74,
      kickoffTime: '2024-01-15T21:00:00Z',
      units: 2
    },
    {
      id: '3',
      homeTeam: 'Real Madrid',
      awayTeam: 'Barcelona',
      sport: 'Futebol',
      market: 'Ambas Marcam',
      odds: 1.76,
      expectedValue: 15.2,
      confidence: 91,
      kickoffTime: '2024-01-16T16:00:00Z',
      units: 4
    }
  ];

  const displayPicks = mockPicks.slice(0, 3);

  const formatTime = (timeString: string) => {
    const date = new Date(timeString);
    return date.toLocaleTimeString('pt-BR', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const formatDate = (timeString: string) => {
    const date = new Date(timeString);
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    if (date.toDateString() === today.toDateString()) {
      return 'Hoje';
    } else if (date.toDateString() === tomorrow.toDateString()) {
      return 'Amanhã';
    }
    return date.toLocaleDateString('pt-BR', { 
      day: '2-digit', 
      month: '2-digit' 
    });
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 85) return 'text-green-400';
    if (confidence >= 70) return 'text-yellow-400';
    return 'text-gray-400';
  };

  if (isLoading) {
    return (
      <div className="card-primary p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-700 rounded-lg w-64 mb-6"></div>
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="p-4 bg-gray-800 rounded-lg">
                <div className="h-4 bg-gray-700 rounded w-48 mb-2"></div>
                <div className="h-3 bg-gray-700 rounded w-32"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="card-primary p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-yellow-400 to-yellow-600 flex items-center justify-center">
            <TrendingUp className="w-5 h-5 text-gray-900" />
          </div>
          <div>
            <h2 className="text-heading-3">Oportunidades de Valor de Hoje</h2>
            <p className="text-body-small text-gray-400">
              {displayPicks.length} picks com EV+ identificado
            </p>
          </div>
        </div>
        
        <button className="btn-ghost text-sm">
          Ver Todas
          <ArrowRight className="w-4 h-4 ml-2" />
        </button>
      </div>

      <div className="space-y-4">
        {displayPicks.map((pick) => (
          <div 
            key={pick.id}
            className="card-value p-4 hover:transform hover:scale-[1.02] transition-all cursor-pointer"
          >
            {/* EV+ Badge - A Joia do Sistema */}
            <div className="flex items-start justify-between mb-3">
              <div className="ev-badge">
                <Star className="w-3 h-3 mr-1" />
                EV+ {pick.expectedValue.toFixed(1)}%
              </div>
              <div className="text-right">
                <div className="flex items-center space-x-2 text-gray-400 text-sm">
                  <Clock className="w-4 h-4" />
                  <span>{formatDate(pick.kickoffTime)} • {formatTime(pick.kickoffTime)}</span>
                </div>
              </div>
            </div>

            {/* Match Info */}
            <div className="mb-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="text-white font-semibold">
                    {pick.homeTeam} vs {pick.awayTeam}
                  </div>
                  <span className="text-xs bg-gray-700 text-gray-300 px-2 py-1 rounded-full">
                    {pick.sport}
                  </span>
                </div>
              </div>
            </div>

            {/* Pick Details */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
              <div>
                <p className="text-gray-400 text-xs uppercase tracking-wider mb-1">Mercado</p>
                <p className="text-white font-medium">{pick.market}</p>
              </div>
              
              <div>
                <p className="text-gray-400 text-xs uppercase tracking-wider mb-1">Odd Mínima</p>
                <p className="text-white font-bold text-lg">{pick.odds.toFixed(2)}</p>
              </div>
              
              <div>
                <p className="text-gray-400 text-xs uppercase tracking-wider mb-1">Confiança</p>
                <div className="flex items-center space-x-2">
                  <div className="progress-bar h-1.5 w-12">
                    <div 
                      className="progress-info h-full"
                      style={{ width: `${pick.confidence}%` }}
                    ></div>
                  </div>
                  <span className={`font-medium ${getConfidenceColor(pick.confidence)}`}>
                    {pick.confidence}%
                  </span>
                </div>
              </div>
              
              <div>
                <p className="text-gray-400 text-xs uppercase tracking-wider mb-1">Unidades</p>
                <div className="flex items-center space-x-1">
                  <Target className="w-4 h-4 text-yellow-400" />
                  <span className="text-white font-bold">{pick.units}u</span>
                </div>
              </div>
            </div>

            {/* Action Button */}
            <div className="mt-4 pt-4 border-t border-gray-700">
              <button className="btn-value w-full text-sm">
                Ver Análise Completa
                <ArrowRight className="w-4 h-4 ml-2" />
              </button>
            </div>
          </div>
        ))}
      </div>

      {displayPicks.length === 0 && (
        <div className="text-center py-8">
          <div className="w-16 h-16 mx-auto rounded-full bg-gray-800 flex items-center justify-center mb-4">
            <TrendingUp className="w-8 h-8 text-gray-500" />
          </div>
          <h3 className="text-lg font-medium text-white mb-2">Nenhuma Oportunidade Hoje</h3>
          <p className="text-gray-400">
            Nossa IA não identificou picks com valor positivo no momento.
          </p>
        </div>
      )}
    </div>
  );
};

export default ValueOpportunities; 