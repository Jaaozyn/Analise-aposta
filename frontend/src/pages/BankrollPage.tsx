import React, { useState } from 'react';
import { 
  DollarSign, 
  TrendingUp, 
  TrendingDown,
  BarChart3,
  Calendar,
  Target,
  Award,
  AlertCircle,
  Plus,
  Download,
  Filter,
  Activity
} from 'lucide-react';
import { useBankrollHistory, usePerformanceMetrics, useAddBetResult, useUserStats } from '../hooks/useApi';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';
import toast from 'react-hot-toast';

const BankrollPage: React.FC = () => {
  const [selectedPeriod, setSelectedPeriod] = useState('30d');
  const [showAddResult, setShowAddResult] = useState(false);
  const [betResult, setBetResult] = useState({
    pick_id: '',
    result: 'won' as 'won' | 'lost' | 'void',
    stake: 0,
    odds: 0,
    profit_loss: 0
  });

  // Hooks para dados da API
  const { history, isLoading: historyLoading } = useBankrollHistory(selectedPeriod);
  const { metrics, isLoading: metricsLoading } = usePerformanceMetrics();
  const { stats, isLoading: statsLoading } = useUserStats();
  const { addBetResult } = useAddBetResult();

  // Mock data para demonstração
  const mockHistory = [
    { date: '2024-01-01', balance: 10000, profit: 0 },
    { date: '2024-01-05', balance: 10250, profit: 250 },
    { date: '2024-01-10', balance: 10150, profit: 150 },
    { date: '2024-01-15', balance: 10680, profit: 680 },
    { date: '2024-01-20', balance: 10520, profit: 520 },
    { date: '2024-01-25', balance: 11200, profit: 1200 },
    { date: '2024-01-30', balance: 12750, profit: 2750 },
  ];

  const mockMetrics = {
    totalBets: 89,
    wonBets: 57,
    lostBets: 28,
    voidBets: 4,
    winRate: 64.2,
    roi: 27.5,
    avgOdds: 1.82,
    profitLoss: 2750,
    maxWinStreak: 7,
    maxLoseStreak: 3,
    bestMonth: 'Janeiro',
    worstMonth: 'Dezembro',
    sharpeRatio: 1.34,
    maxDrawdown: -580
  };

  const mockStats = {
    currentBankroll: 12750,
    initialBankroll: 10000,
    totalProfit: 2750,
    roi: 27.5,
    winRate: 64.2
  };

  // Data para gráficos
  const performanceData = mockHistory.map(item => ({
    date: new Date(item.date).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' }),
    balance: item.balance,
    profit: item.profit
  }));

  const sportsData = [
    { name: 'Futebol', value: 45, profit: 1200, color: '#10B981' },
    { name: 'Basquete', value: 30, profit: 850, color: '#3B82F6' },
    { name: 'Tênis', value: 15, profit: 450, color: '#8B5CF6' },
    { name: 'Outros', value: 10, profit: 250, color: '#F59E0B' },
  ];

  const monthlyData = [
    { month: 'Set', profit: 150, bets: 12 },
    { month: 'Out', profit: 320, bets: 18 },
    { month: 'Nov', profit: -180, bets: 15 },
    { month: 'Dez', profit: 890, bets: 22 },
    { month: 'Jan', profit: 1570, bets: 22 },
  ];

  const handleAddBetResult = async () => {
    try {
      await addBetResult(betResult);
      toast.success('Resultado adicionado com sucesso!');
      setShowAddResult(false);
      setBetResult({
        pick_id: '',
        result: 'won',
        stake: 0,
        odds: 0,
        profit_loss: 0
      });
    } catch (error) {
      toast.error('Erro ao adicionar resultado');
    }
  };

  const calculateProfitLoss = () => {
    if (betResult.result === 'won') {
      setBetResult(prev => ({
        ...prev,
        profit_loss: prev.stake * (prev.odds - 1)
      }));
    } else if (betResult.result === 'lost') {
      setBetResult(prev => ({
        ...prev,
        profit_loss: -prev.stake
      }));
    } else {
      setBetResult(prev => ({
        ...prev,
        profit_loss: 0
      }));
    }
  };

  React.useEffect(() => {
    if (betResult.stake && betResult.odds) {
      calculateProfitLoss();
    }
  }, [betResult.stake, betResult.odds, betResult.result]);

  return (
    <div className="space-y-8 fade-in">
      
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-heading-1 mb-2">Gestão de Banca</h1>
          <p className="text-body-large text-gray-400">
            Controle completo da sua performance e evolução financeira.
          </p>
        </div>
        
        <div className="flex space-x-3">
          <button 
            onClick={() => setShowAddResult(true)}
            className="btn-value"
          >
            <Plus className="w-4 h-4 mr-2" />
            Adicionar Resultado
          </button>
          
          <button className="btn-secondary">
            <Download className="w-4 h-4 mr-2" />
            Exportar Relatório
          </button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="card-primary p-6 text-center">
          <div className="w-12 h-12 mx-auto rounded-lg bg-green-900/20 flex items-center justify-center mb-3">
            <DollarSign className="w-6 h-6 text-green-400" />
          </div>
          <div className="text-2xl font-bold text-green-400 mb-1">
            R$ {mockStats.currentBankroll.toLocaleString()}
          </div>
          <div className="text-sm text-gray-400">Banca Atual</div>
        </div>

        <div className="card-primary p-6 text-center">
          <div className="w-12 h-12 mx-auto rounded-lg bg-blue-900/20 flex items-center justify-center mb-3">
            <TrendingUp className="w-6 h-6 text-blue-400" />
          </div>
          <div className="text-2xl font-bold text-blue-400 mb-1">
            +{mockStats.roi}%
          </div>
          <div className="text-sm text-gray-400">ROI Total</div>
        </div>

        <div className="card-primary p-6 text-center">
          <div className="w-12 h-12 mx-auto rounded-lg bg-purple-900/20 flex items-center justify-center mb-3">
            <Target className="w-6 h-6 text-purple-400" />
          </div>
          <div className="text-2xl font-bold text-purple-400 mb-1">
            {mockMetrics.winRate}%
          </div>
          <div className="text-sm text-gray-400">Win Rate</div>
        </div>

        <div className="card-primary p-6 text-center">
          <div className="w-12 h-12 mx-auto rounded-lg bg-yellow-900/20 flex items-center justify-center mb-3">
            <Award className="w-6 h-6 text-yellow-400" />
          </div>
          <div className="text-2xl font-bold text-yellow-400 mb-1">
            {mockMetrics.totalBets}
          </div>
          <div className="text-sm text-gray-400">Total Apostas</div>
        </div>

        <div className="card-primary p-6 text-center">
          <div className="w-12 h-12 mx-auto rounded-lg bg-red-900/20 flex items-center justify-center mb-3">
            <Activity className="w-6 h-6 text-red-400" />
          </div>
          <div className="text-2xl font-bold text-red-400 mb-1">
            {mockMetrics.sharpeRatio.toFixed(2)}
          </div>
          <div className="text-sm text-gray-400">Sharpe Ratio</div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Main Performance Chart */}
        <div className="lg:col-span-2 card-primary p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-heading-4">Evolução da Banca</h3>
            
            <select 
              value={selectedPeriod}
              onChange={(e) => setSelectedPeriod(e.target.value)}
              className="bg-gray-800 border border-gray-600 text-white px-3 py-2 rounded-lg text-sm"
            >
              <option value="7d">7 dias</option>
              <option value="30d">30 dias</option>
              <option value="90d">90 dias</option>
              <option value="1y">1 ano</option>
            </select>
          </div>
          
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis 
                  dataKey="date" 
                  stroke="#9CA3AF"
                  fontSize={12}
                />
                <YAxis 
                  stroke="#9CA3AF"
                  fontSize={12}
                  tickFormatter={(value) => `R$ ${value.toLocaleString()}`}
                />
                <Tooltip 
                  contentStyle={{
                    backgroundColor: '#1F2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                    color: '#FFFFFF'
                  }}
                  formatter={(value: any) => [`R$ ${value.toLocaleString()}`, 'Banca']}
                />
                <Line 
                  type="monotone" 
                  dataKey="balance" 
                  stroke="#10B981" 
                  strokeWidth={3}
                  dot={{ fill: '#10B981', strokeWidth: 2, r: 4 }}
                  activeDot={{ r: 6, stroke: '#10B981', strokeWidth: 2 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Performance por Esporte */}
        <div className="card-primary p-6">
          <h3 className="text-heading-4 mb-6">Performance por Esporte</h3>
          
          <div className="h-64 mb-4">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={sportsData}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  dataKey="value"
                  label={({ name, value }) => `${name}: ${value}%`}
                  labelLine={false}
                  fontSize={12}
                  fill="#8884d8"
                >
                  {sportsData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{
                    backgroundColor: '#1F2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                    color: '#FFFFFF'
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          
          <div className="space-y-2">
            {sportsData.map((sport, index) => (
              <div key={index} className="flex justify-between items-center">
                <div className="flex items-center space-x-2">
                  <div 
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: sport.color }}
                  ></div>
                  <span className="text-gray-300 text-sm">{sport.name}</span>
                </div>
                <span className={`text-sm font-medium ${
                  sport.profit > 0 ? 'text-green-400' : 'text-red-400'
                }`}>
                  {sport.profit > 0 ? '+' : ''}R$ {sport.profit}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Performance Mensal */}
        <div className="lg:col-span-3 card-primary p-6">
          <h3 className="text-heading-4 mb-6">Performance Mensal</h3>
          
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={monthlyData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis 
                  dataKey="month" 
                  stroke="#9CA3AF"
                  fontSize={12}
                />
                <YAxis 
                  stroke="#9CA3AF"
                  fontSize={12}
                  tickFormatter={(value) => `R$ ${value}`}
                />
                <Tooltip 
                  contentStyle={{
                    backgroundColor: '#1F2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                    color: '#FFFFFF'
                  }}
                  formatter={(value: any, name: string) => [
                    name === 'profit' ? `R$ ${value}` : value,
                    name === 'profit' ? 'Lucro' : 'Apostas'
                  ]}
                />
                <Bar 
                  dataKey="profit" 
                  fill="#10B981"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Detailed Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Statistics */}
        <div className="card-primary p-6">
          <h3 className="text-heading-4 mb-6">Estatísticas Detalhadas</h3>
          
          <div className="grid grid-cols-2 gap-6">
            <div className="space-y-4">
              <div className="flex justify-between">
                <span className="text-gray-400">Apostas Ganhas:</span>
                <span className="text-green-400 font-medium">{mockMetrics.wonBets}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Apostas Perdidas:</span>
                <span className="text-red-400 font-medium">{mockMetrics.lostBets}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Apostas Anuladas:</span>
                <span className="text-gray-400 font-medium">{mockMetrics.voidBets}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Odd Média:</span>
                <span className="text-white font-medium">{mockMetrics.avgOdds.toFixed(2)}</span>
              </div>
            </div>
            
            <div className="space-y-4">
              <div className="flex justify-between">
                <span className="text-gray-400">Maior Sequência Positiva:</span>
                <span className="text-green-400 font-medium">{mockMetrics.maxWinStreak}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Maior Sequência Negativa:</span>
                <span className="text-red-400 font-medium">{mockMetrics.maxLoseStreak}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Max Drawdown:</span>
                <span className="text-red-400 font-medium">R$ {mockMetrics.maxDrawdown}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Melhor Mês:</span>
                <span className="text-green-400 font-medium">{mockMetrics.bestMonth}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="card-primary p-6">
          <h3 className="text-heading-4 mb-6">Atividade Recente</h3>
          
          <div className="space-y-4">
            {[
              { date: '15/01', pick: 'Man City vs Liverpool', result: 'won', profit: 185 },
              { date: '14/01', pick: 'Lakers vs Warriors', result: 'lost', profit: -100 },
              { date: '13/01', pick: 'Real vs Barça', result: 'won', profit: 150 },
              { date: '12/01', pick: 'Flamengo vs Palmeiras', result: 'void', profit: 0 },
              { date: '11/01', pick: 'Celtics vs Heat', result: 'won', profit: 120 },
            ].map((activity, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-800/50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className="text-gray-400 text-sm">{activity.date}</div>
                  <div className="text-white font-medium">{activity.pick}</div>
                </div>
                <div className="flex items-center space-x-3">
                  <div className={`px-2 py-1 rounded text-xs font-medium ${
                    activity.result === 'won' ? 'bg-green-900/30 text-green-400' :
                    activity.result === 'lost' ? 'bg-red-900/30 text-red-400' :
                    'bg-gray-800 text-gray-400'
                  }`}>
                    {activity.result.toUpperCase()}
                  </div>
                  <div className={`font-medium ${
                    activity.profit > 0 ? 'text-green-400' :
                    activity.profit < 0 ? 'text-red-400' : 'text-gray-400'
                  }`}>
                    {activity.profit > 0 ? '+' : ''}R$ {activity.profit}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Add Result Modal */}
      {showAddResult && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="card-primary p-6 m-4 w-full max-w-md">
            <h3 className="text-heading-4 mb-4">Adicionar Resultado</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  ID do Pick
                </label>
                <input 
                  type="text"
                  value={betResult.pick_id}
                  onChange={(e) => setBetResult(prev => ({ ...prev, pick_id: e.target.value }))}
                  className="w-full bg-gray-800 border border-gray-600 text-white px-3 py-2 rounded-lg"
                  placeholder="Digite o ID do pick"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Resultado
                </label>
                <select 
                  value={betResult.result}
                  onChange={(e) => setBetResult(prev => ({ ...prev, result: e.target.value as 'won' | 'lost' | 'void' }))}
                  className="w-full bg-gray-800 border border-gray-600 text-white px-3 py-2 rounded-lg"
                >
                  <option value="won">Ganhou</option>
                  <option value="lost">Perdeu</option>
                  <option value="void">Anulada</option>
                </select>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Stake (R$)
                  </label>
                  <input 
                    type="number"
                    value={betResult.stake}
                    onChange={(e) => setBetResult(prev => ({ ...prev, stake: Number(e.target.value) }))}
                    className="w-full bg-gray-800 border border-gray-600 text-white px-3 py-2 rounded-lg"
                    placeholder="100"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Odd
                  </label>
                  <input 
                    type="number"
                    step="0.01"
                    value={betResult.odds}
                    onChange={(e) => setBetResult(prev => ({ ...prev, odds: Number(e.target.value) }))}
                    className="w-full bg-gray-800 border border-gray-600 text-white px-3 py-2 rounded-lg"
                    placeholder="1.85"
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Lucro/Prejuízo (R$)
                </label>
                <input 
                  type="number"
                  value={betResult.profit_loss}
                  onChange={(e) => setBetResult(prev => ({ ...prev, profit_loss: Number(e.target.value) }))}
                  className="w-full bg-gray-800 border border-gray-600 text-white px-3 py-2 rounded-lg"
                  placeholder="Calculado automaticamente"
                  readOnly
                />
              </div>
            </div>
            
            <div className="flex space-x-3 mt-6">
              <button 
                onClick={() => setShowAddResult(false)}
                className="btn-secondary flex-1"
              >
                Cancelar
              </button>
              <button 
                onClick={handleAddBetResult}
                className="btn-primary flex-1"
              >
                Adicionar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default BankrollPage; 