import React from 'react';
import { 
  Star, 
  Clock, 
  Target, 
  TrendingUp,
  ArrowRight,
  BarChart3
} from 'lucide-react';

interface Pick {
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
}

interface PickCardProps {
  pick: Pick;
  onViewAnalysis?: (pickId: string) => void;
}

const PickCard: React.FC<PickCardProps> = ({ pick, onViewAnalysis }) => {
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

  const getConfidenceLabel = (confidence: number) => {
    if (confidence >= 85) return 'Alta Confiança';
    if (confidence >= 70) return 'Confiança Moderada';
    return 'Baixa Confiança';
  };

  const getSportIcon = (sport: string) => {
    switch (sport.toLowerCase()) {
      case 'futebol':
        return '⚽';
      case 'basquete':
        return '🏀';
      case 'tenis':
        return '🎾';
      case 'americano':
        return '🏈';
      default:
        return '🏟️';
    }
  };

  const hasPositiveEV = pick.expectedValue > 0;

  return (
    <div className={`${hasPositiveEV ? 'card-value' : 'card-primary'} p-6 hover:transform hover:scale-[1.02] transition-all cursor-pointer fade-in`}>
      
      {/* Header com EV+ Badge */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <span className="text-2xl">{getSportIcon(pick.sport)}</span>
          <div>
            <h3 className="text-heading-4 mb-1">
              {pick.homeTeam} vs {pick.awayTeam}
            </h3>
            <p className="text-body-small text-gray-400">
              {pick.league} • {pick.sport}
            </p>
          </div>
        </div>
        
        {hasPositiveEV && (
          <div className="ev-badge">
            <Star className="w-3 h-3 mr-1" />
            EV+ {pick.expectedValue.toFixed(1)}%
          </div>
        )}
      </div>

      {/* Timing */}
      <div className="flex items-center space-x-2 text-gray-400 text-sm mb-4">
        <Clock className="w-4 h-4" />
        <span>{formatDate(pick.kickoffTime)} • {formatTime(pick.kickoffTime)}</span>
      </div>

      {/* Pick Details */}
      <div className="bg-gray-800/50 rounded-lg p-4 mb-4">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div>
            <p className="text-caption mb-1">Mercado</p>
            <p className="text-white font-semibold">{pick.market}</p>
          </div>
          <div>
            <p className="text-caption mb-1">Seleção</p>
            <p className="text-white font-semibold">{pick.selection}</p>
          </div>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
        <div className="text-center">
          <p className="text-caption mb-1">Odd Mínima</p>
          <p className="text-2xl font-bold text-white">{pick.odds.toFixed(2)}</p>
        </div>
        
        <div className="text-center">
          <p className="text-caption mb-1">Confiança</p>
          <div className="flex flex-col items-center space-y-1">
            <div className="progress-bar h-2 w-16">
              <div 
                className="progress-info h-full"
                style={{ width: `${pick.confidence}%` }}
              ></div>
            </div>
            <span className={`text-sm font-medium ${getConfidenceColor(pick.confidence)}`}>
              {pick.confidence}%
            </span>
          </div>
        </div>
        
        <div className="text-center">
          <p className="text-caption mb-1">Unidades</p>
          <div className="flex items-center justify-center space-x-1">
            <Target className="w-4 h-4 text-yellow-400" />
            <span className="text-xl font-bold text-white">{pick.units}u</span>
          </div>
        </div>
        
        <div className="text-center">
          <p className="text-caption mb-1">Status</p>
          <span className={hasPositiveEV ? 'status-positive' : 'status-neutral'}>
            {hasPositiveEV ? 'Valor+' : 'Padrão'}
          </span>
        </div>
      </div>

      {/* Reasoning */}
      <div className="bg-gray-800/30 rounded-lg p-4 mb-4">
        <div className="flex items-center space-x-2 mb-2">
          <BarChart3 className="w-4 h-4 text-blue-400" />
          <span className="text-sm font-medium text-blue-400">Análise IA</span>
        </div>
        <p className="text-body text-gray-300 leading-relaxed">
          {pick.reasoning}
        </p>
      </div>

      {/* Confidence Indicator */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <div className={`w-2 h-2 rounded-full ${
            pick.confidence >= 85 ? 'bg-green-400' :
            pick.confidence >= 70 ? 'bg-yellow-400' : 'bg-gray-400'
          }`}></div>
          <span className={`text-sm font-medium ${getConfidenceColor(pick.confidence)}`}>
            {getConfidenceLabel(pick.confidence)}
          </span>
        </div>
        
        <div className="flex items-center space-x-1 text-gray-400 text-sm">
          <TrendingUp className="w-4 h-4" />
          <span>ID: {pick.id}</span>
        </div>
      </div>

      {/* Actions */}
      <div className="flex space-x-3">
        <button 
          onClick={() => onViewAnalysis?.(pick.id)}
          className="btn-primary flex-1 text-sm"
        >
          <BarChart3 className="w-4 h-4 mr-2" />
          Ver Análise Completa
        </button>
        
        {hasPositiveEV && (
          <button className="btn-value flex-1 text-sm">
            <Star className="w-4 h-4 mr-2" />
            Seguir Pick
            <ArrowRight className="w-4 h-4 ml-2" />
          </button>
        )}
      </div>
    </div>
  );
};

export default PickCard; 