import React, { useState } from 'react';
import { 
  Target, 
  Filter, 
  RefreshCw,
  Search,
  TrendingUp,
  Star
} from 'lucide-react';

const PicksPage: React.FC = () => {
  const [filterSport, setFilterSport] = useState('all');
  const [filterEV, setFilterEV] = useState('all');
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Mock picks data
  const mockPicks = [
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
      reasoning: 'Ambas as equipes têm médias altas de gols...'
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
      reasoning: 'Lakers jogando em casa têm média de 118 pontos...'
    }
  ];

  const handleRefresh = async () => {
    setIsRefreshing(true);
    // Simular refresh
    await new Promise(resolve => setTimeout(resolve, 2000));
    setIsRefreshing(false);
  };

  const filteredPicks = mockPicks.filter(pick => {
    if (filterSport !== 'all' && pick.sport.toLowerCase() !== filterSport) return false;
    if (filterEV === 'positive' && pick.expectedValue <= 0) return false;
    return true;
  });

  return (
    <div className="space-y-8 fade-in">
      
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-heading-1 mb-2">Oportunidades de Hoje</h1>
          <p className="text-body-large text-gray-400">
            Picks analisados pela nossa IA. Foque nos com EV+ para máximo valor.
          </p>
        </div>
        
        <button 
          onClick={handleRefresh}
          disabled={isRefreshing}
          className="btn-value"
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
          {isRefreshing ? 'Atualizando...' : 'Atualizar Picks'}
        </button>
      </div>

      {/* Filters */}
      <div className="card-primary p-6">
        <div className="flex items-center space-x-6">
          <div className="flex items-center space-x-2">
            <Filter className="w-5 h-5 text-gray-400" />
            <span className="text-sm font-medium text-gray-300">Filtros:</span>
          </div>
          
          <select 
            value={filterSport} 
            onChange={(e) => setFilterSport(e.target.value)}
            className="bg-gray-800 border border-gray-600 text-white px-3 py-2 rounded-lg text-sm"
          >
            <option value="all">Todos Esportes</option>
            <option value="futebol">Futebol</option>
            <option value="basquete">Basquete</option>
            <option value="tenis">Tênis</option>
          </select>
          
          <select 
            value={filterEV} 
            onChange={(e) => setFilterEV(e.target.value)}
            className="bg-gray-800 border border-gray-600 text-white px-3 py-2 rounded-lg text-sm"
          >
            <option value="all">Todos EV</option>
            <option value="positive">Apenas EV+</option>
          </select>
          
          <div className="flex-1">
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input 
                type="text" 
                placeholder="Buscar times, ligas..."
                className="w-full bg-gray-800 border border-gray-600 text-white pl-10 pr-4 py-2 rounded-lg text-sm"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Picks Grid */}
      <div className="grid-cards">
        {filteredPicks.map((pick) => (
          <div key={pick.id} className="card-value p-6">
            
            {/* EV+ Badge */}
            <div className="flex justify-between items-start mb-4">
              <div className="ev-badge">
                <Star className="w-3 h-3 mr-1" />
                EV+ {pick.expectedValue.toFixed(1)}%
              </div>
              <span className="text-xs bg-gray-700 text-gray-300 px-2 py-1 rounded-full">
                {pick.sport}
              </span>
            </div>
            
            {/* Match */}
            <h3 className="text-heading-4 mb-2">
              {pick.homeTeam} vs {pick.awayTeam}
            </h3>
            <p className="text-body-small text-gray-400 mb-4">
              {pick.league}
            </p>
            
            {/* Pick Details */}
            <div className="bg-gray-800/50 rounded-lg p-4 mb-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-gray-400 text-xs mb-1">MERCADO</p>
                  <p className="text-white font-medium">{pick.market}</p>
                </div>
                <div>
                  <p className="text-gray-400 text-xs mb-1">ODD MÍNIMA</p>
                  <p className="text-white font-bold text-lg">{pick.odds.toFixed(2)}</p>
                </div>
              </div>
            </div>
            
            {/* Metrics */}
            <div className="grid grid-cols-2 gap-4 mb-4 text-center">
              <div>
                <p className="text-gray-400 text-xs mb-1">CONFIANÇA</p>
                <p className="text-blue-400 font-bold">{pick.confidence}%</p>
              </div>
              <div>
                <p className="text-gray-400 text-xs mb-1">UNIDADES</p>
                <p className="text-yellow-400 font-bold">{pick.units}u</p>
              </div>
            </div>
            
            {/* Actions */}
            <button className="btn-primary w-full text-sm">
              <Target className="w-4 h-4 mr-2" />
              Ver Análise Completa
            </button>
          </div>
        ))}
      </div>

      {filteredPicks.length === 0 && (
        <div className="text-center py-12">
          <TrendingUp className="w-16 h-16 mx-auto text-gray-500 mb-4" />
          <h3 className="text-lg font-medium text-white mb-2">
            Nenhum pick encontrado
          </h3>
          <p className="text-gray-400">
            Tente ajustar os filtros ou aguarde novos picks.
          </p>
        </div>
      )}
    </div>
  );
};

export default PicksPage; 