import React from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign,
  BarChart3,
  ArrowRight,
  Target
} from 'lucide-react';

interface BankrollData {
  currentBalance: number;
  initialBalance: number;
  totalProfit: number;
  roi: number;
  winRate: number;
  totalBets: number;
  chartData: { date: string; balance: number; }[];
}

interface BankrollWidgetProps {
  data: BankrollData;
  isLoading?: boolean;
}

const BankrollWidget: React.FC<BankrollWidgetProps> = ({ data, isLoading = false }) => {
  // Mock data se não houver dados
  const mockData: BankrollData = data || {
    currentBalance: 12750,
    initialBalance: 10000,
    totalProfit: 2750,
    roi: 27.5,
    winRate: 64.2,
    totalBets: 89,
    chartData: [
      { date: '2024-01-01', balance: 10000 },
      { date: '2024-01-08', balance: 10320 },
      { date: '2024-01-15', balance: 11150 },
      { date: '2024-01-22', balance: 10890 },
      { date: '2024-01-29', balance: 12100 },
      { date: '2024-02-05', balance: 12750 },
    ]
  };

  const isPositive = mockData.totalProfit > 0;
  const percentageGain = ((mockData.currentBalance - mockData.initialBalance) / mockData.initialBalance) * 100;

  // Função para criar o gráfico simples com SVG
  const createChartPath = (data: { date: string; balance: number; }[]) => {
    if (data.length < 2) return '';
    
    const width = 300;
    const height = 80;
    const padding = 10;
    
    const minBalance = Math.min(...data.map(d => d.balance));
    const maxBalance = Math.max(...data.map(d => d.balance));
    const range = maxBalance - minBalance || 1;
    
    const points = data.map((d, i) => {
      const x = padding + (i / (data.length - 1)) * (width - 2 * padding);
      const y = height - padding - ((d.balance - minBalance) / range) * (height - 2 * padding);
      return `${x},${y}`;
    });
    
    return `M ${points.join(' L ')}`;
  };

  if (isLoading) {
    return (
      <div className="card-primary p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-700 rounded-lg w-48 mb-6"></div>
          <div className="h-20 bg-gray-700 rounded-lg mb-4"></div>
          <div className="grid grid-cols-3 gap-4">
            <div className="h-12 bg-gray-700 rounded-lg"></div>
            <div className="h-12 bg-gray-700 rounded-lg"></div>
            <div className="h-12 bg-gray-700 rounded-lg"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="card-primary p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
            isPositive 
              ? 'bg-gradient-to-br from-green-400 to-green-600' 
              : 'bg-gradient-to-br from-red-400 to-red-600'
          }`}>
            <DollarSign className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-heading-3">Gestão de Banca</h2>
            <p className="text-body-small text-gray-400">
              Performance dos últimos 30 dias
            </p>
          </div>
        </div>
        
        <button className="btn-ghost text-sm">
          Detalhes
          <ArrowRight className="w-4 h-4 ml-2" />
        </button>
      </div>

      {/* Balance Display */}
      <div className="mb-6">
        <div className="flex items-baseline space-x-2 mb-2">
          <span className="text-3xl font-bold text-white">
            R$ {mockData.currentBalance.toLocaleString('pt-BR')}
          </span>
          <div className={`flex items-center space-x-1 px-2 py-1 rounded-full text-sm font-medium ${
            isPositive 
              ? 'bg-green-900/30 text-green-400' 
              : 'bg-red-900/30 text-red-400'
          }`}>
            {isPositive ? (
              <TrendingUp className="w-4 h-4" />
            ) : (
              <TrendingDown className="w-4 h-4" />
            )}
            <span>
              {isPositive ? '+' : ''}{mockData.totalProfit.toLocaleString('pt-BR')}
            </span>
          </div>
        </div>
        <p className="text-gray-400 text-sm">
          {percentageGain >= 0 ? '+' : ''}{percentageGain.toFixed(1)}% desde o início
        </p>
      </div>

      {/* Performance Chart */}
      <div className="mb-6 p-4 bg-gray-800/50 rounded-lg">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-medium text-gray-300">Evolução da Banca</h3>
          <BarChart3 className="w-4 h-4 text-gray-500" />
        </div>
        
        <div className="relative">
          <svg 
            width="100%" 
            height="80" 
            viewBox="0 0 300 80"
            className="overflow-visible"
          >
            {/* Grid lines */}
            <defs>
              <pattern id="grid" width="30" height="20" patternUnits="userSpaceOnUse">
                <path d="M 30 0 L 0 0 0 20" fill="none" stroke="#374151" strokeWidth="0.5" opacity="0.3"/>
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid)" />
            
            {/* Chart line */}
            <path
              d={createChartPath(mockData.chartData)}
              fill="none"
              stroke="url(#gradient)"
              strokeWidth="3"
              className="drop-shadow-sm"
            />
            
            {/* Gradient definition */}
            <defs>
              <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor={isPositive ? "#10B981" : "#EF4444"} />
                <stop offset="100%" stopColor={isPositive ? "#059669" : "#DC2626"} />
              </linearGradient>
            </defs>
            
            {/* Area under curve */}
            <path
              d={`${createChartPath(mockData.chartData)} L 290,70 L 10,70 Z`}
              fill="url(#areaGradient)"
              opacity="0.1"
            />
            
            <defs>
              <linearGradient id="areaGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stopColor={isPositive ? "#10B981" : "#EF4444"} opacity="0.3" />
                <stop offset="100%" stopColor={isPositive ? "#10B981" : "#EF4444"} opacity="0" />
              </linearGradient>
            </defs>
          </svg>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-3 gap-4">
        <div className="text-center p-3 bg-gray-800/30 rounded-lg">
          <div className={`text-xl font-bold ${isPositive ? 'text-green-400' : 'text-red-400'}`}>
            {mockData.roi >= 0 ? '+' : ''}{mockData.roi.toFixed(1)}%
          </div>
          <div className="text-xs text-gray-400 uppercase tracking-wider">ROI</div>
        </div>
        
        <div className="text-center p-3 bg-gray-800/30 rounded-lg">
          <div className="text-xl font-bold text-blue-400">
            {mockData.winRate.toFixed(1)}%
          </div>
          <div className="text-xs text-gray-400 uppercase tracking-wider">Win Rate</div>
        </div>
        
        <div className="text-center p-3 bg-gray-800/30 rounded-lg">
          <div className="text-xl font-bold text-gray-300">
            {mockData.totalBets}
          </div>
          <div className="text-xs text-gray-400 uppercase tracking-wider">Total Bets</div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="mt-6 pt-4 border-t border-gray-700">
        <div className="flex space-x-3">
          <button className="btn-secondary flex-1 text-sm">
            <Target className="w-4 h-4 mr-2" />
            Adicionar Resultado
          </button>
          <button className="btn-primary flex-1 text-sm">
            <BarChart3 className="w-4 h-4 mr-2" />
            Relatório Completo
          </button>
        </div>
      </div>
    </div>
  );
};

export default BankrollWidget; 