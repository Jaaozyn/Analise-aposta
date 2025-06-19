import React from 'react';

const SimpleDashboard: React.FC = () => {
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
            <h2 className="text-xl font-semibold text-white mb-6">Oportunidades de Valor de Hoje</h2>
            
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
              
              <div className="flex justify-between items-center py-2">
                <div>
                  <div className="text-sm font-medium text-white">Celtics vs Heat</div>
                  <div className="text-xs text-gray-400">NBA • Seg 20:30</div>
                </div>
                <div className="text-xs text-gray-400 font-medium">PROGRAMADO</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SimpleDashboard; 