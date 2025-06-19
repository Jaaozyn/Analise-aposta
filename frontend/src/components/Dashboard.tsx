'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { 
  TrendingUp, 
  Calendar, 
  Trophy, 
  DollarSign, 
  BarChart3,
  Target,
  Clock,
  Star
} from 'lucide-react';
import { PickCard } from './PickCard';
import { BankrollChart } from './BankrollChart';
import { StatsCard } from './StatsCard';
import { usePicks } from '../hooks/usePicks';
import { useUserStats } from '../hooks/useUserStats';

interface DashboardProps {
  className?: string;
}

export const Dashboard: React.FC<DashboardProps> = ({ className }) => {
  // Hooks para dados
  const { picks: todaysPicks, isLoading: picksLoading } = usePicks({ 
    endpoint: '/picks/today',
    params: { min_ev: 5.0 }
  });
  
  const { stats, isLoading: statsLoading } = useUserStats();

  return (
    <div className={`min-h-screen bg-dark-900 text-white ${className}`}>
      {/* Header */}
      <div className="border-b border-dark-800 bg-dark-900/95 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white">
                Sala de Análise
              </h1>
              <p className="text-dark-400 text-sm mt-1">
                Suas oportunidades de valor para hoje
              </p>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="bg-dark-800 rounded-lg px-4 py-2">
                <div className="flex items-center space-x-2">
                  <Clock className="h-4 w-4 text-dark-400" />
                  <span className="text-sm text-dark-300">
                    Atualizado agora
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatsCard
            title="ROI Mensal"
            value={`${stats?.monthly_roi || 0}%`}
            icon={TrendingUp}
            trend={stats?.roi_trend}
            color="primary"
          />
          
          <StatsCard
            title="Taxa de Acerto"
            value={`${stats?.win_rate || 0}%`}
            icon={Target}
            trend={stats?.winrate_trend}
            color="success"
          />
          
          <StatsCard
            title="Lucro Total"
            value={`R$ ${stats?.total_profit || 0}`}
            icon={DollarSign}
            trend={stats?.profit_trend}
            color="info"
          />
          
          <StatsCard
            title="Picks Ativos"
            value={`${todaysPicks?.length || 0}`}
            icon={Star}
            color="warning"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Coluna Principal - Oportunidades de Valor */}
          <div className="lg:col-span-2">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-dark-800 rounded-2xl p-6 border border-dark-700"
            >
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-xl font-semibold text-white flex items-center">
                    <Trophy className="h-5 w-5 text-primary-500 mr-2" />
                    Oportunidades de Valor de Hoje
                  </h2>
                  <p className="text-dark-400 text-sm mt-1">
                    Picks com maior EV+ identificados pelo modelo
                  </p>
                </div>
                
                <div className="bg-primary-500/20 text-primary-400 px-3 py-1 rounded-full text-sm font-medium">
                  {todaysPicks?.length || 0} picks
                </div>
              </div>

              {/* Lista de Picks */}
              <div className="space-y-4">
                {picksLoading ? (
                  // Loading skeleton
                  Array.from({ length: 3 }).map((_, i) => (
                    <div key={i} className="animate-pulse">
                      <div className="bg-dark-700 rounded-lg p-4">
                        <div className="h-4 bg-dark-600 rounded w-1/3 mb-3"></div>
                        <div className="h-3 bg-dark-600 rounded w-2/3 mb-2"></div>
                        <div className="h-3 bg-dark-600 rounded w-1/2"></div>
                      </div>
                    </div>
                  ))
                ) : todaysPicks && todaysPicks.length > 0 ? (
                  todaysPicks.slice(0, 5).map((pick) => (
                    <PickCard
                      key={pick.id}
                      pick={pick}
                      showAnalysis={false}
                      className="hover:bg-dark-700 transition-colors"
                    />
                  ))
                ) : (
                  <div className="text-center py-12">
                    <Calendar className="h-12 w-12 text-dark-600 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-dark-300 mb-2">
                      Nenhuma oportunidade encontrada
                    </h3>
                    <p className="text-dark-500 text-sm">
                      Nosso modelo está analisando as partidas de hoje.
                    </p>
                  </div>
                )}
              </div>

              {/* Ver Mais */}
              {todaysPicks && todaysPicks.length > 5 && (
                <div className="mt-6 pt-6 border-t border-dark-700">
                  <button className="w-full bg-dark-700 hover:bg-dark-600 text-white py-3 rounded-lg transition-colors font-medium">
                    Ver Todas as Oportunidades ({todaysPicks.length})
                  </button>
                </div>
              )}
            </motion.div>
          </div>

          {/* Sidebar - Gestão de Banca e Próximos Jogos */}
          <div className="space-y-6">
            {/* Gestão de Banca */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="bg-dark-800 rounded-2xl p-6 border border-dark-700"
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white flex items-center">
                  <BarChart3 className="h-5 w-5 text-success-500 mr-2" />
                  Gestão de Banca
                </h3>
              </div>

              {/* Gráfico de Performance */}
              <div className="mb-6">
                <BankrollChart data={stats?.bankroll_history} />
              </div>

              {/* Métricas Principais */}
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-dark-400 text-sm">Banca Atual</span>
                  <span className="text-white font-semibold">
                    R$ {stats?.current_bankroll || 0}
                  </span>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-dark-400 text-sm">Lucro/Prejuízo</span>
                  <span className={`font-semibold ${
                    (stats?.total_profit || 0) >= 0 ? 'text-success-500' : 'text-error-500'
                  }`}>
                    {(stats?.total_profit || 0) >= 0 ? '+' : ''}R$ {stats?.total_profit || 0}
                  </span>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-dark-400 text-sm">ROI</span>
                  <span className={`font-semibold ${
                    (stats?.roi || 0) >= 0 ? 'text-success-500' : 'text-error-500'
                  }`}>
                    {(stats?.roi || 0) >= 0 ? '+' : ''}{stats?.roi || 0}%
                  </span>
                </div>
              </div>
            </motion.div>

            {/* Próximos Jogos */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="bg-dark-800 rounded-2xl p-6 border border-dark-700"
            >
              <h3 className="text-lg font-semibold text-white flex items-center mb-4">
                <Calendar className="h-5 w-5 text-info-500 mr-2" />
                Próximos Jogos
              </h3>

              <div className="space-y-3">
                {Array.from({ length: 3 }).map((_, i) => (
                  <div key={i} className="flex items-center justify-between py-2">
                    <div>
                      <div className="text-sm font-medium text-white">
                        Team A vs Team B
                      </div>
                      <div className="text-xs text-dark-400">
                        Premier League • 15:30
                      </div>
                    </div>
                    <div className="text-xs text-primary-400 font-medium">
                      EM ANÁLISE
                    </div>
                  </div>
                ))}
              </div>

              <button className="w-full mt-4 text-dark-400 hover:text-white text-sm transition-colors">
                Ver calendário completo
              </button>
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  );
}; 