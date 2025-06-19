import React, { useState } from 'react';
import { 
  PieChart, 
  Pie, 
  Cell, 
  ResponsiveContainer, 
  Tooltip, 
  Legend,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid
} from 'recharts';
import { TrendingUp, TrendingDown, BarChart3 } from 'lucide-react';

interface SportData {
  name: string;
  bets: number;
  profit: number;
  roi: number;
  winRate: number;
  avgOdds: number;
  color: string;
}

interface SportsPieChartProps {
  data: SportData[];
  showDetails?: boolean;
}

const SportsPieChart: React.FC<SportsPieChartProps> = ({ data, showDetails = true }) => {
  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  const [viewMode, setViewMode] = useState<'pie' | 'bar'>('pie');

  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-800/50 rounded-lg">
        <div className="text-center">
          <BarChart3 className="w-12 h-12 text-gray-500 mx-auto mb-2" />
          <p className="text-gray-400">Sem dados de esportes</p>
        </div>
      </div>
    );
  }

  // Calcular totais
  const totalBets = data.reduce((sum, sport) => sum + sport.bets, 0);
  const totalProfit = data.reduce((sum, sport) => sum + sport.profit, 0);
  const avgROI = totalProfit / data.reduce((sum, sport) => sum + Math.abs(sport.profit), 0) * 100;

  // Preparar dados para gráfico de barras
  const barData = data.map(sport => ({
    ...sport,
    percentage: (sport.bets / totalBets) * 100
  })).sort((a, b) => b.profit - a.profit);

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-gray-800 border border-gray-600 rounded-lg p-4 shadow-lg">
          <h4 className="text-white font-medium mb-2">{data.name}</h4>
          <div className="space-y-1 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-400">Apostas:</span>
              <span className="text-white">{data.bets}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Lucro:</span>
              <span className={data.profit >= 0 ? 'text-green-400' : 'text-red-400'}>
                {data.profit >= 0 ? '+' : ''}R$ {data.profit.toLocaleString()}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">ROI:</span>
              <span className={data.roi >= 0 ? 'text-green-400' : 'text-red-400'}>
                {data.roi >= 0 ? '+' : ''}{data.roi.toFixed(1)}%
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Win Rate:</span>
              <span className="text-blue-400">{data.winRate.toFixed(1)}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Odd Média:</span>
              <span className="text-white">{data.avgOdds.toFixed(2)}</span>
            </div>
          </div>
        </div>
      );
    }
    return null;
  };

  // Custom label para o gráfico de pizza
  const renderLabel = ({ name, value, percent }: any) => {
    return `${name}: ${(percent * 100).toFixed(0)}%`;
  };

  return (
    <div className="space-y-6">
      
      {/* Header com controles */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-white">Performance por Esporte</h3>
          <p className="text-gray-400 text-sm">Distribuição de apostas e resultados</p>
        </div>
        
        <div className="flex bg-gray-800 rounded-lg p-1">
          <button
            onClick={() => setViewMode('pie')}
            className={`px-3 py-1 text-sm font-medium rounded transition-colors ${
              viewMode === 'pie' ? 'bg-yellow-500 text-gray-900' : 'text-gray-400'
            }`}
          >
            Pizza
          </button>
          <button
            onClick={() => setViewMode('bar')}
            className={`px-3 py-1 text-sm font-medium rounded transition-colors ${
              viewMode === 'bar' ? 'bg-yellow-500 text-gray-900' : 'text-gray-400'
            }`}
          >
            Barras
          </button>
        </div>
      </div>

      {/* Estatísticas resumo */}
      <div className="grid grid-cols-3 gap-4 p-4 bg-gray-800/30 rounded-lg">
        <div className="text-center">
          <div className="text-sm text-gray-400">Total de Apostas</div>
          <div className="text-xl font-bold text-white">{totalBets}</div>
        </div>
        <div className="text-center">
          <div className="text-sm text-gray-400">Lucro Total</div>
          <div className={`text-xl font-bold ${totalProfit >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {totalProfit >= 0 ? '+' : ''}R$ {totalProfit.toLocaleString()}
          </div>
        </div>
        <div className="text-center">
          <div className="text-sm text-gray-400">ROI Médio</div>
          <div className={`text-xl font-bold ${avgROI >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {avgROI >= 0 ? '+' : ''}{avgROI.toFixed(1)}%
          </div>
        </div>
      </div>

      {/* Gráfico */}
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          {viewMode === 'pie' ? (
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={renderLabel}
                outerRadius={120}
                fill="#8884d8"
                dataKey="bets"
                onMouseEnter={(_, index) => setActiveIndex(index)}
                onMouseLeave={() => setActiveIndex(null)}
              >
                {data.map((entry, index) => (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={entry.color}
                    stroke={activeIndex === index ? '#FFFFFF' : 'none'}
                    strokeWidth={activeIndex === index ? 2 : 0}
                    style={{
                      filter: activeIndex === index ? 'brightness(1.1)' : 'none',
                      transform: activeIndex === index ? 'scale(1.05)' : 'scale(1)',
                      transformOrigin: 'center'
                    }}
                  />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
          ) : (
            <BarChart data={barData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis 
                dataKey="name" 
                stroke="#9CA3AF"
                fontSize={12}
              />
              <YAxis 
                stroke="#9CA3AF"
                fontSize={12}
                tickFormatter={(value) => `R$ ${value}`}
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar 
                dataKey="profit" 
                radius={[4, 4, 0, 0]}
              >
                {barData.map((entry, index) => (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={entry.profit >= 0 ? '#10B981' : '#EF4444'}
                  />
                ))}
              </Bar>
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>

      {/* Detalhes por esporte */}
      {showDetails && (
        <div className="space-y-3">
          <h4 className="text-white font-medium">Detalhes por Esporte</h4>
          
          <div className="grid gap-3">
            {data.map((sport, index) => (
              <div 
                key={sport.name}
                className={`p-4 rounded-lg border transition-all cursor-pointer ${
                  activeIndex === index 
                    ? 'border-yellow-500 bg-yellow-500/10' 
                    : 'border-gray-700 hover:border-gray-600'
                }`}
                onClick={() => setActiveIndex(activeIndex === index ? null : index)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div 
                      className="w-4 h-4 rounded-full"
                      style={{ backgroundColor: sport.color }}
                    ></div>
                    <h5 className="text-white font-medium">{sport.name}</h5>
                  </div>
                  
                  <div className="flex items-center space-x-4 text-sm">
                    <div className="text-center">
                      <div className="text-gray-400">Apostas</div>
                      <div className="text-white font-medium">{sport.bets}</div>
                    </div>
                    
                    <div className="text-center">
                      <div className="text-gray-400">Lucro</div>
                      <div className={`font-medium ${sport.profit >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {sport.profit >= 0 ? '+' : ''}R$ {sport.profit.toLocaleString()}
                      </div>
                    </div>
                    
                    <div className="text-center">
                      <div className="text-gray-400">ROI</div>
                      <div className={`font-medium ${sport.roi >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {sport.roi >= 0 ? '+' : ''}{sport.roi.toFixed(1)}%
                      </div>
                    </div>
                    
                    <div className="text-center">
                      <div className="text-gray-400">Win Rate</div>
                      <div className="text-blue-400 font-medium">{sport.winRate.toFixed(1)}%</div>
                    </div>
                    
                    <div className="flex items-center">
                      {sport.profit >= 0 ? (
                        <TrendingUp className="w-4 h-4 text-green-400" />
                      ) : (
                        <TrendingDown className="w-4 h-4 text-red-400" />
                      )}
                    </div>
                  </div>
                </div>
                
                {/* Barra de progresso para % de apostas */}
                <div className="mt-3">
                  <div className="flex justify-between text-xs text-gray-400 mb-1">
                    <span>Distribuição de apostas</span>
                    <span>{((sport.bets / totalBets) * 100).toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div 
                      className="h-2 rounded-full transition-all duration-500"
                      style={{ 
                        width: `${(sport.bets / totalBets) * 100}%`,
                        backgroundColor: sport.color 
                      }}
                    ></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default SportsPieChart; 