import React from 'react';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  ReferenceLine,
  Area,
  ComposedChart,
  Bar
} from 'recharts';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface PerformanceData {
  date: string;
  balance: number;
  profit: number;
  roi: number;
  bets: number;
}

interface PerformanceChartProps {
  data: PerformanceData[];
  period: string;
  showProfitArea?: boolean;
  showBetsBar?: boolean;
  height?: number;
}

const PerformanceChart: React.FC<PerformanceChartProps> = ({ 
  data, 
  period, 
  showProfitArea = false,
  showBetsBar = false,
  height = 400 
}) => {
  
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-80 bg-gray-800/50 rounded-lg">
        <div className="text-center">
          <TrendingUp className="w-12 h-12 text-gray-500 mx-auto mb-2" />
          <p className="text-gray-400">Sem dados para exibir</p>
        </div>
      </div>
    );
  }

  // Calcular estatísticas
  const latestData = data[data.length - 1];
  const firstData = data[0];
  const totalChange = latestData.balance - firstData.balance;
  const percentChange = ((totalChange / firstData.balance) * 100);
  const isPositive = totalChange >= 0;

  // Formatadores customizados
  const formatCurrency = (value: number) => {
    return `R$ ${value.toLocaleString('pt-BR')}`;
  };

  const formatPercent = (value: number) => {
    return `${value.toFixed(1)}%`;
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    switch (period) {
      case '7d':
        return date.toLocaleDateString('pt-BR', { weekday: 'short' });
      case '30d':
        return date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });
      case '90d':
      case '1y':
        return date.toLocaleDateString('pt-BR', { month: 'short' });
      default:
        return date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });
    }
  };

  // Custom Tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-gray-800 border border-gray-600 rounded-lg p-4 shadow-lg">
          <p className="text-gray-300 text-sm mb-2">{new Date(label).toLocaleDateString('pt-BR')}</p>
          <div className="space-y-1">
            <div className="flex justify-between items-center">
              <span className="text-gray-400 text-sm">Banca:</span>
              <span className="text-white font-medium">{formatCurrency(data.balance)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400 text-sm">Lucro:</span>
              <span className={`font-medium ${data.profit >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {data.profit >= 0 ? '+' : ''}{formatCurrency(data.profit)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400 text-sm">ROI:</span>
              <span className={`font-medium ${data.roi >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {data.roi >= 0 ? '+' : ''}{formatPercent(data.roi)}
              </span>
            </div>
            {showBetsBar && (
              <div className="flex justify-between items-center">
                <span className="text-gray-400 text-sm">Apostas:</span>
                <span className="text-blue-400 font-medium">{data.bets}</span>
              </div>
            )}
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-4">
      
      {/* Header com estatísticas */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-white">Performance da Banca</h3>
          <p className="text-gray-400 text-sm">Evolução nos últimos {period}</p>
        </div>
        
        <div className="text-right">
          <div className="flex items-center space-x-2">
            {isPositive ? (
              <TrendingUp className="w-5 h-5 text-green-400" />
            ) : (
              <TrendingDown className="w-5 h-5 text-red-400" />
            )}
            <span className={`text-lg font-bold ${isPositive ? 'text-green-400' : 'text-red-400'}`}>
              {isPositive ? '+' : ''}{formatCurrency(totalChange)}
            </span>
          </div>
          <div className={`text-sm ${isPositive ? 'text-green-400' : 'text-red-400'}`}>
            {isPositive ? '+' : ''}{formatPercent(percentChange)}
          </div>
        </div>
      </div>

      {/* Gráfico */}
      <div style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          {showBetsBar ? (
            <ComposedChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <defs>
                <linearGradient id="balanceGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10B981" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#10B981" stopOpacity={0}/>
                </linearGradient>
              </defs>
              
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              
              <XAxis 
                dataKey="date" 
                stroke="#9CA3AF"
                fontSize={12}
                tickFormatter={formatDate}
              />
              
              <YAxis 
                yAxisId="balance"
                stroke="#9CA3AF"
                fontSize={12}
                tickFormatter={formatCurrency}
              />
              
              <YAxis 
                yAxisId="bets"
                orientation="right"
                stroke="#3B82F6"
                fontSize={12}
              />
              
              <Tooltip content={<CustomTooltip />} />
              
              {/* Linha de referência para break-even */}
              <ReferenceLine 
                yAxisId="balance"
                y={firstData.balance} 
                stroke="#6B7280" 
                strokeDasharray="5 5"
                label={{ value: "Break Even", position: "insideTopRight" }}
              />
              
              {/* Área do lucro */}
              {showProfitArea && (
                <Area
                  yAxisId="balance"
                  type="monotone"
                  dataKey="balance"
                  stroke="#10B981"
                  fillOpacity={0.3}
                  fill="url(#balanceGradient)"
                />
              )}
              
              {/* Barras de apostas */}
              <Bar 
                yAxisId="bets"
                dataKey="bets" 
                fill="#3B82F6" 
                opacity={0.6}
                radius={[2, 2, 0, 0]}
              />
              
              {/* Linha principal da banca */}
              <Line 
                yAxisId="balance"
                type="monotone" 
                dataKey="balance" 
                stroke="#10B981" 
                strokeWidth={3}
                dot={{ fill: '#10B981', strokeWidth: 2, r: 4 }}
                activeDot={{ r: 6, stroke: '#10B981', strokeWidth: 2 }}
              />
              
            </ComposedChart>
          ) : (
            <LineChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <defs>
                <linearGradient id="balanceGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10B981" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#10B981" stopOpacity={0}/>
                </linearGradient>
              </defs>
              
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              
              <XAxis 
                dataKey="date" 
                stroke="#9CA3AF"
                fontSize={12}
                tickFormatter={formatDate}
              />
              
              <YAxis 
                stroke="#9CA3AF"
                fontSize={12}
                tickFormatter={formatCurrency}
              />
              
              <Tooltip content={<CustomTooltip />} />
              
              {/* Linha de referência para break-even */}
              <ReferenceLine 
                y={firstData.balance} 
                stroke="#6B7280" 
                strokeDasharray="5 5"
                label={{ value: "Break Even", position: "insideTopRight" }}
              />
              
              {/* Área do lucro */}
              {showProfitArea && (
                <Area
                  type="monotone"
                  dataKey="balance"
                  stroke="#10B981"
                  fillOpacity={0.3}
                  fill="url(#balanceGradient)"
                />
              )}
              
              {/* Linha principal */}
              <Line 
                type="monotone" 
                dataKey="balance" 
                stroke="#10B981" 
                strokeWidth={3}
                dot={{ fill: '#10B981', strokeWidth: 2, r: 4 }}
                activeDot={{ r: 6, stroke: '#10B981', strokeWidth: 2 }}
              />
              
            </LineChart>
          )}
        </ResponsiveContainer>
      </div>

      {/* Estatísticas adicionais */}
      <div className="grid grid-cols-3 gap-4 pt-4 border-t border-gray-700">
        <div className="text-center">
          <div className="text-sm text-gray-400">Banca Inicial</div>
          <div className="text-white font-medium">{formatCurrency(firstData.balance)}</div>
        </div>
        <div className="text-center">
          <div className="text-sm text-gray-400">Banca Atual</div>
          <div className="text-white font-medium">{formatCurrency(latestData.balance)}</div>
        </div>
        <div className="text-center">
          <div className="text-sm text-gray-400">ROI Período</div>
          <div className={`font-medium ${isPositive ? 'text-green-400' : 'text-red-400'}`}>
            {isPositive ? '+' : ''}{formatPercent(percentChange)}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PerformanceChart; 