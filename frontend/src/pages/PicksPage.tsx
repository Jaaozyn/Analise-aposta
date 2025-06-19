import React, { useState, useMemo } from 'react';
import { 
  Target, 
  Filter, 
  RefreshCw,
  Search,
  TrendingUp,
  Star,
  Clock,
  BarChart3,
  AlertCircle,
  CheckCircle2,
  Calendar
} from 'lucide-react';
import { usePicks, useGeneratePicks } from '../hooks/useApi';
import PickCard from '../components/PickCard';
import toast from 'react-hot-toast';

const PicksPage: React.FC = () => {
  const [filterSport, setFilterSport] = useState('all');
  const [filterEV, setFilterEV] = useState('all');
  const [filterDate, setFilterDate] = useState('today');
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('ev_desc');

  // Hooks para dados da API
  const { picks, isLoading, error, refreshPicks } = usePicks({
    sport: filterSport !== 'all' ? filterSport : undefined,
    min_ev: filterEV === 'positive' ? 0.1 : undefined,
    date: filterDate !== 'all' ? filterDate : undefined,
  });

  const { generatePicks } = useGeneratePicks();

  const handleRefresh = async () => {
    try {
      await refreshPicks();
      toast.success('Picks atualizados com sucesso!');
    } catch (error) {
      toast.error('Erro ao atualizar picks');
    }
  };

  const handleGeneratePicks = async () => {
    try {
      await generatePicks();
      toast.success('Novos picks gerados!');
    } catch (error) {
      toast.error('Erro ao gerar picks');
    }
  };

  // Filtros e ordenação
  const filteredAndSortedPicks = useMemo(() => {
    let filtered = picks;

    // Filtro por busca
    if (searchTerm) {
      filtered = filtered.filter(pick => 
        pick.homeTeam.toLowerCase().includes(searchTerm.toLowerCase()) ||
        pick.awayTeam.toLowerCase().includes(searchTerm.toLowerCase()) ||
        pick.league.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Ordenação
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'ev_desc':
          return b.expectedValue - a.expectedValue;
        case 'ev_asc':
          return a.expectedValue - b.expectedValue;
        case 'confidence_desc':
          return b.confidence - a.confidence;
        case 'confidence_asc':
          return a.confidence - b.confidence;
        case 'time_asc':
          return new Date(a.kickoffTime).getTime() - new Date(b.kickoffTime).getTime();
        case 'time_desc':
          return new Date(b.kickoffTime).getTime() - new Date(a.kickoffTime).getTime();
        default:
          return 0;
      }
    });

    return filtered;
  }, [picks, searchTerm, sortBy]);

  const statsData = useMemo(() => {
    const totalPicks = filteredAndSortedPicks.length;
    const positivePicks = filteredAndSortedPicks.filter(p => p.expectedValue > 0).length;
    const avgEV = totalPicks > 0 ? 
      (filteredAndSortedPicks.reduce((sum, p) => sum + p.expectedValue, 0) / totalPicks).toFixed(1) : 0;
    const avgConfidence = totalPicks > 0 ? 
      (filteredAndSortedPicks.reduce((sum, p) => sum + p.confidence, 0) / totalPicks).toFixed(1) : 0;

    return { totalPicks, positivePicks, avgEV, avgConfidence };
  }, [filteredAndSortedPicks]);

  if (error) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="w-16 h-16 mx-auto text-red-500 mb-4" />
        <h3 className="text-lg font-medium text-white mb-2">Erro ao carregar picks</h3>
        <p className="text-gray-400 mb-4">Tente novamente em alguns instantes</p>
        <button onClick={handleRefresh} className="btn-primary">
          <RefreshCw className="w-4 h-4 mr-2" />
          Tentar Novamente
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-8 fade-in">
      
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-heading-1 mb-2">Feed de Oportunidades</h1>
          <p className="text-body-large text-gray-400">
            Picks analisados pela nossa IA. Foque nos com EV+ para máximo valor.
          </p>
        </div>
        
        <div className="flex space-x-3">
          <button 
            onClick={handleGeneratePicks}
            className="btn-value"
            disabled={isLoading}
          >
            <Star className="w-4 h-4 mr-2" />
            Gerar Novos Picks
          </button>
          
          <button 
            onClick={handleRefresh}
            disabled={isLoading}
            className="btn-secondary"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            {isLoading ? 'Carregando...' : 'Atualizar'}
          </button>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card-primary p-4 text-center">
          <div className="text-2xl font-bold text-white mb-1">{statsData.totalPicks}</div>
          <div className="text-sm text-gray-400">Total de Picks</div>
        </div>
        <div className="card-primary p-4 text-center">
          <div className="text-2xl font-bold text-yellow-400 mb-1">{statsData.positivePicks}</div>
          <div className="text-sm text-gray-400">Com EV+</div>
        </div>
        <div className="card-primary p-4 text-center">
          <div className="text-2xl font-bold text-green-400 mb-1">{statsData.avgEV}%</div>
          <div className="text-sm text-gray-400">EV Médio</div>
        </div>
        <div className="card-primary p-4 text-center">
          <div className="text-2xl font-bold text-blue-400 mb-1">{statsData.avgConfidence}%</div>
          <div className="text-sm text-gray-400">Confiança Média</div>
        </div>
      </div>

      {/* Filters */}
      <div className="card-primary p-6">
        <div className="flex flex-col lg:flex-row lg:items-center space-y-4 lg:space-y-0 lg:space-x-6">
          <div className="flex items-center space-x-2">
            <Filter className="w-5 h-5 text-gray-400" />
            <span className="text-sm font-medium text-gray-300">Filtros:</span>
          </div>
          
          <div className="flex flex-wrap gap-4">
            <select 
              value={filterSport} 
              onChange={(e) => setFilterSport(e.target.value)}
              className="bg-gray-800 border border-gray-600 text-white px-3 py-2 rounded-lg text-sm min-w-[120px]"
            >
              <option value="all">Todos Esportes</option>
              <option value="futebol">Futebol</option>
              <option value="basquete">Basquete</option>
              <option value="tenis">Tênis</option>
              <option value="americano">Futebol Americano</option>
            </select>
            
            <select 
              value={filterEV} 
              onChange={(e) => setFilterEV(e.target.value)}
              className="bg-gray-800 border border-gray-600 text-white px-3 py-2 rounded-lg text-sm min-w-[120px]"
            >
              <option value="all">Todos EV</option>
              <option value="positive">Apenas EV+</option>
            </select>

            <select 
              value={filterDate} 
              onChange={(e) => setFilterDate(e.target.value)}
              className="bg-gray-800 border border-gray-600 text-white px-3 py-2 rounded-lg text-sm min-w-[120px]"
            >
              <option value="today">Hoje</option>
              <option value="tomorrow">Amanhã</option>
              <option value="week">Esta Semana</option>
              <option value="all">Todos</option>
            </select>

            <select 
              value={sortBy} 
              onChange={(e) => setSortBy(e.target.value)}
              className="bg-gray-800 border border-gray-600 text-white px-3 py-2 rounded-lg text-sm min-w-[140px]"
            >
              <option value="ev_desc">EV+ Maior</option>
              <option value="ev_asc">EV+ Menor</option>
              <option value="confidence_desc">Confiança Maior</option>
              <option value="confidence_asc">Confiança Menor</option>
              <option value="time_asc">Horário Crescente</option>
              <option value="time_desc">Horário Decrescente</option>
            </select>
          </div>
          
          <div className="flex-1 min-w-[200px]">
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input 
                type="text" 
                placeholder="Buscar times, ligas..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full bg-gray-800 border border-gray-600 text-white pl-10 pr-4 py-2 rounded-lg text-sm"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="card-primary p-6 animate-pulse">
              <div className="h-4 bg-gray-700 rounded w-3/4 mb-4"></div>
              <div className="h-3 bg-gray-700 rounded w-1/2 mb-2"></div>
              <div className="h-3 bg-gray-700 rounded w-2/3"></div>
            </div>
          ))}
        </div>
      )}

      {/* Picks Grid */}
      {!isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredAndSortedPicks.map((pick) => (
            <PickCard 
              key={pick.id} 
              pick={pick}
              onViewAnalysis={(id) => console.log('Ver análise:', id)}
            />
          ))}
        </div>
      )}

      {/* Empty State */}
      {!isLoading && filteredAndSortedPicks.length === 0 && (
        <div className="text-center py-12">
          <TrendingUp className="w-16 h-16 mx-auto text-gray-500 mb-4" />
          <h3 className="text-lg font-medium text-white mb-2">
            Nenhum pick encontrado
          </h3>
          <p className="text-gray-400 mb-4">
            Tente ajustar os filtros ou aguarde novos picks.
          </p>
          <button onClick={handleGeneratePicks} className="btn-primary">
            <Star className="w-4 h-4 mr-2" />
            Gerar Novos Picks
          </button>
        </div>
      )}

      {/* Real-time Status */}
      <div className="fixed bottom-4 right-4 bg-gray-800 border border-gray-700 rounded-lg p-3 shadow-lg">
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
          <span className="text-sm text-gray-300">
            Atualizações em tempo real
          </span>
        </div>
      </div>
    </div>
  );
};

export default PicksPage; 