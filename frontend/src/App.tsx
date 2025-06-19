import React, { useState } from 'react';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, ProtectedRoute } from './contexts/AuthContext';
import Header from './components/Layout/Header';
import PicksPage from './pages/PicksPage';
import AnalysisPage from './pages/AnalysisPage';
import BankrollPage from './pages/BankrollPage';
import { useWebSocket, useAutoReconnect, useConnectionStatus } from './hooks/useWebSocket';
import './styles/globals.css';

// Componente Dashboard integrado com APIs e WebSocket
const Dashboard = () => {
  const { isConnected } = useWebSocket();
  const connectionStatus = useConnectionStatus();

  return (
    <div className="space-y-8 fade-in">
      
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Central de Comando</h1>
          <p className="text-base text-gray-400">
            Bem-vindo à sua sala de análise. Aqui você encontra as melhores oportunidades do dia.
          </p>
        </div>
        
        {/* Status da Conexão */}
        <div className="flex items-center space-x-2 text-sm">
          <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`}></div>
          <span className="text-gray-400">
            {isConnected ? 'Tempo real ativo' : 'Reconectando...'}
          </span>
          {connectionStatus.latency > 0 && (
            <span className="text-gray-500">({connectionStatus.latency}ms)</span>
          )}
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card-primary p-6 text-center">
          <div className="text-2xl font-bold text-yellow-400 mb-1">5</div>
          <div className="text-sm text-gray-400">Picks Hoje</div>
        </div>

        <div className="card-primary p-6 text-center">
          <div className="text-2xl font-bold text-green-400 mb-1">+12.5%</div>
          <div className="text-sm text-gray-400">ROI Mensal</div>
        </div>

        <div className="card-primary p-6 text-center">
          <div className="text-2xl font-bold text-blue-400 mb-1">64.2%</div>
          <div className="text-sm text-gray-400">Win Rate</div>
        </div>

        <div className="card-primary p-6 text-center">
          <div className="text-2xl font-bold text-purple-400 mb-1">R$ 2.750</div>
          <div className="text-sm text-gray-400">Lucro Total</div>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Oportunidades de Valor */}
        <div className="lg:col-span-2">
          <div className="card-primary p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-white">Oportunidades de Valor de Hoje</h2>
              {isConnected && (
                <div className="flex items-center space-x-2 text-xs text-green-400">
                  <div className="w-1 h-1 bg-green-400 rounded-full animate-pulse"></div>
                  <span>Atualizando automaticamente</span>
                </div>
              )}
            </div>
            
            <div className="space-y-4">
              <div className="card-value p-4">
                <div className="flex items-start justify-between mb-3">
                  <div className="ev-badge">⭐ EV+ 12.8%</div>
                  <div className="text-gray-400 text-sm">Hoje 15:30</div>
                </div>
                <h3 className="text-white font-semibold mb-1">Manchester City vs Liverpool</h3>
                <p className="text-gray-400 text-sm mb-3">Premier League</p>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <p className="text-gray-400 text-xs mb-1">MERCADO</p>
                    <p className="text-white">Over 2.5 Gols</p>
                  </div>
                  <div>
                    <p className="text-gray-400 text-xs mb-1">ODD</p>
                    <p className="text-white font-bold">1.85</p>
                  </div>
                  <div>
                    <p className="text-gray-400 text-xs mb-1">CONFIANÇA</p>
                    <p className="text-blue-400">87%</p>
                  </div>
                </div>
              </div>

              <div className="card-value p-4">
                <div className="flex items-start justify-between mb-3">
                  <div className="ev-badge">⭐ EV+ 8.4%</div>
                  <div className="text-gray-400 text-sm">Hoje 21:00</div>
                </div>
                <h3 className="text-white font-semibold mb-1">Lakers vs Warriors</h3>
                <p className="text-gray-400 text-sm mb-3">NBA</p>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <p className="text-gray-400 text-xs mb-1">MERCADO</p>
                    <p className="text-white">Over 225.5</p>
                  </div>
                  <div>
                    <p className="text-gray-400 text-xs mb-1">ODD</p>
                    <p className="text-white font-bold">1.92</p>
                  </div>
                  <div>
                    <p className="text-gray-400 text-xs mb-1">CONFIANÇA</p>
                    <p className="text-blue-400">74%</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Gestão de Banca */}
        <div>
          <div className="card-primary p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Gestão de Banca</h3>
            
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Banca Atual</span>
                <span className="text-white font-bold text-xl">R$ 12.750</span>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Lucro Total</span>
                <span className="text-green-400 font-bold">+R$ 2.750</span>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-gray-400">ROI</span>
                <span className="text-green-400 font-bold">+27.5%</span>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Win Rate</span>
                <span className="text-blue-400 font-bold">64.2%</span>
              </div>
            </div>
          </div>

          {/* Próximos Jogos */}
          <div className="card-primary p-6 mt-6">
            <h3 className="text-lg font-semibold text-white mb-4">Próximos Jogos</h3>
            
            <div className="space-y-3">
              <div className="flex justify-between items-center py-2">
                <div>
                  <div className="text-sm font-medium text-white">Real vs Barça</div>
                  <div className="text-xs text-gray-400">La Liga • Amanhã 16:00</div>
                </div>
                <div className="text-xs text-blue-400 font-medium">EM ANÁLISE</div>
              </div>
              
              <div className="flex justify-between items-center py-2">
                <div>
                  <div className="text-sm font-medium text-white">Flamengo vs Palmeiras</div>
                  <div className="text-xs text-gray-400">Brasileirão • Dom 19:00</div>
                </div>
                <div className="text-xs text-yellow-400 font-medium">AGUARDANDO</div>
              </div>
            </div>
          </div>

          {/* Insights IA com WebSocket */}
          <div className="card-primary p-6 mt-6">
            <h3 className="text-lg font-semibold text-white mb-4">Insights IA</h3>
            
            <div className="space-y-3">
              <div className="bg-purple-900/20 rounded-lg p-3">
                <div className="flex items-start space-x-2">
                  <div className="w-2 h-2 rounded-full bg-purple-400 mt-1.5"></div>
                  <div>
                    <p className="text-sm text-purple-300 font-medium mb-1">
                      Performance Excelente
                    </p>
                    <p className="text-xs text-gray-400">
                      Seus últimos 10 picks tiveram 70% de acerto. Continue seguindo picks com EV+ alto.
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="bg-yellow-900/20 rounded-lg p-3">
                <div className="flex items-start space-x-2">
                  <div className="w-2 h-2 rounded-full bg-yellow-400 mt-1.5"></div>
                  <div>
                    <p className="text-sm text-yellow-300 font-medium mb-1">
                      Oportunidade Hoje
                    </p>
                    <p className="text-xs text-gray-400">
                      3 jogos da Premier League com EV+ acima de 10%. Recomendamos 2-3 unidades.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Componente principal da aplicação
function MainApp() {
  const [currentPage, setCurrentPage] = useState('dashboard');
  
  // Hooks do WebSocket
  useAutoReconnect(); // Auto-reconexão em background

  const handleNavigate = (page: string) => {
    setCurrentPage(page);
  };

  const renderCurrentPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <Dashboard />;
      case 'picks':
        return <PicksPage />;
      case 'analysis':
        return <AnalysisPage />;
      case 'bankroll':
        return <BankrollPage />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-900">
      <Header 
        currentPage={currentPage} 
        onNavigate={handleNavigate} 
      />
      
      <main className="container-main py-8">
        {renderCurrentPage()}
      </main>

      {/* Toast Notifications */}
      <Toaster
        position="bottom-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#1F2937',
            color: '#FFFFFF',
            border: '1px solid #374151',
          },
          success: {
            iconTheme: {
              primary: '#10B981',
              secondary: '#FFFFFF',
            },
          },
          error: {
            iconTheme: {
              primary: '#EF4444',
              secondary: '#FFFFFF',
            },
          },
        }}
      />
    </div>
  );
}

// App com Providers
function App() {
  return (
    <AuthProvider>
      <ProtectedRoute>
        <MainApp />
      </ProtectedRoute>
    </AuthProvider>
  );
}

export default App; 