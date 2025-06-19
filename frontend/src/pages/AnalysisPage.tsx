import React, { useState } from 'react';
import { 
  BarChart3, 
  TrendingUp, 
  Users, 
  Clock,
  Target,
  Zap,
  Shield,
  Award,
  AlertTriangle,
  CheckCircle,
  ArrowRight,
  Eye,
  Activity
} from 'lucide-react';
import { useMatches, useMatchAnalysis } from '../hooks/useApi';

const AnalysisPage: React.FC = () => {
  const [selectedMatchId, setSelectedMatchId] = useState<string | null>(null);
  const [selectedSport, setSelectedSport] = useState('futebol');

  const { matches, isLoading: matchesLoading } = useMatches({ 
    sport: selectedSport,
    date: 'today' 
  });

  const { analysis, isLoading: analysisLoading } = useMatchAnalysis(selectedMatchId || '');

  // Mock data para demonstração
  const mockAnalysis = {
    match: {
      id: '1',
      homeTeam: 'Manchester City',
      awayTeam: 'Liverpool',
      league: 'Premier League',
      kickoffTime: '2024-01-15T15:30:00Z',
      venue: 'Etihad Stadium'
    },
    headToHead: {
      totalGames: 10,
      homeWins: 4,
      awayWins: 3,
      draws: 3,
      avgGoalsHome: 2.1,
      avgGoalsAway: 1.8,
      bothTeamsScore: 7,
      over25: 6
    },
    form: {
      home: ['W', 'W', 'D', 'W', 'L'],
      away: ['W', 'L', 'W', 'W', 'D']
    },
    keyStats: {
      home: {
        goalsPerGame: 2.8,
        goalsConceded: 0.9,
        possession: 68,
        shotsPerGame: 18.2,
        cleanSheets: 12
      },
      away: {
        goalsPerGame: 2.4,
        goalsConceded: 1.2,
        possession: 58,
        shotsPerGame: 14.8,
        cleanSheets: 8
      }
    },
    predictions: {
      homeWin: 45,
      draw: 28,
      awayWin: 27,
      over25: 78,
      bothScore: 73,
      corners: 11.5
    },
    picks: [
      {
        market: 'Over 2.5 Gols',
        selection: 'Sim',
        odds: 1.85,
        expectedValue: 12.8,
        confidence: 87,
        reasoning: 'Ambas equipes têm médias altas de gols...'
      },
      {
        market: 'Ambas Marcam',
        selection: 'Sim',
        odds: 1.76,
        expectedValue: 8.4,
        confidence: 74,
        reasoning: 'Histórico favorável...'
      }
    ],
    injuries: [
      { player: 'Kevin De Bruyne', team: 'home', status: 'Dúvida', impact: 'Alto' },
      { player: 'Mohamed Salah', team: 'away', status: 'Confirmado', impact: 'Alto' }
    ]
  };

  const getFormIcon = (result: string) => {
    switch (result) {
      case 'W': return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'L': return <AlertTriangle className="w-4 h-4 text-red-400" />;
      case 'D': return <div className="w-4 h-4 rounded-full bg-yellow-400"></div>;
      default: return null;
    }
  };

  const renderProbabilityBar = (label: string, value: number, color: string) => (
    <div className="mb-3">
      <div className="flex justify-between text-sm mb-1">
        <span className="text-gray-300">{label}</span>
        <span className="text-white font-medium">{value}%</span>
      </div>
      <div className="progress-bar h-2">
        <div 
          className={`h-full rounded-full bg-${color}-500`}
          style={{ width: `${value}%` }}
        ></div>
      </div>
    </div>
  );

  return (
    <div className="space-y-8 fade-in">
      
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-heading-1 mb-2">Dossiê de Análise</h1>
          <p className="text-body-large text-gray-400">
            Análise completa de partidas com estatísticas detalhadas e insights da IA.
          </p>
        </div>
        
        <div className="flex items-center space-x-4">
          <select 
            value={selectedSport}
            onChange={(e) => setSelectedSport(e.target.value)}
            className="bg-gray-800 border border-gray-600 text-white px-4 py-2 rounded-lg"
          >
            <option value="futebol">Futebol</option>
            <option value="basquete">Basquete</option>
            <option value="tenis">Tênis</option>
          </select>
        </div>
      </div>

      {/* Match Selection */}
      <div className="card-primary p-6">
        <h3 className="text-heading-4 mb-4">Selecione uma Partida</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[mockAnalysis.match, 
            { id: '2', homeTeam: 'Real Madrid', awayTeam: 'Barcelona', league: 'La Liga', kickoffTime: '2024-01-16T16:00:00Z' },
            { id: '3', homeTeam: 'Lakers', awayTeam: 'Warriors', league: 'NBA', kickoffTime: '2024-01-15T21:00:00Z' }
          ].map((match) => (
            <button
              key={match.id}
              onClick={() => setSelectedMatchId(match.id)}
              className={`p-4 rounded-lg border text-left transition-all ${
                selectedMatchId === match.id
                  ? 'border-yellow-500 bg-yellow-500/10'
                  : 'border-gray-700 hover:border-gray-600'
              }`}
            >
              <div className="text-white font-semibold mb-1">
                {match.homeTeam} vs {match.awayTeam}
              </div>
              <div className="text-gray-400 text-sm mb-2">{match.league}</div>
              <div className="flex items-center text-gray-400 text-sm">
                <Clock className="w-4 h-4 mr-1" />
                {new Date(match.kickoffTime).toLocaleString('pt-BR')}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Analysis Content */}
      {selectedMatchId && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Main Analysis */}
          <div className="lg:col-span-2 space-y-6">
            
            {/* Head to Head */}
            <div className="card-primary p-6">
              <h3 className="text-heading-4 mb-4 flex items-center">
                <BarChart3 className="w-5 h-5 mr-2 text-blue-400" />
                Confronto Direto
              </h3>
              
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                <div className="text-center p-3 bg-gray-800/50 rounded-lg">
                  <div className="text-2xl font-bold text-white">{mockAnalysis.headToHead.totalGames}</div>
                  <div className="text-xs text-gray-400">Jogos</div>
                </div>
                <div className="text-center p-3 bg-gray-800/50 rounded-lg">
                  <div className="text-2xl font-bold text-green-400">{mockAnalysis.headToHead.homeWins}</div>
                  <div className="text-xs text-gray-400">Vitórias Casa</div>
                </div>
                <div className="text-center p-3 bg-gray-800/50 rounded-lg">
                  <div className="text-2xl font-bold text-red-400">{mockAnalysis.headToHead.awayWins}</div>
                  <div className="text-xs text-gray-400">Vitórias Fora</div>
                </div>
                <div className="text-center p-3 bg-gray-800/50 rounded-lg">
                  <div className="text-2xl font-bold text-yellow-400">{mockAnalysis.headToHead.draws}</div>
                  <div className="text-xs text-gray-400">Empates</div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-6">
                <div>
                  <h4 className="text-white font-medium mb-2">Média de Gols</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-gray-400">Casa:</span>
                      <span className="text-white">{mockAnalysis.headToHead.avgGoalsHome}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Fora:</span>
                      <span className="text-white">{mockAnalysis.headToHead.avgGoalsAway}</span>
                    </div>
                  </div>
                </div>
                <div>
                  <h4 className="text-white font-medium mb-2">Tendências</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-gray-400">Ambas Marcam:</span>
                      <span className="text-green-400">{mockAnalysis.headToHead.bothTeamsScore}/{mockAnalysis.headToHead.totalGames}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Over 2.5:</span>
                      <span className="text-blue-400">{mockAnalysis.headToHead.over25}/{mockAnalysis.headToHead.totalGames}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Team Comparison */}
            <div className="card-primary p-6">
              <h3 className="text-heading-4 mb-4 flex items-center">
                <Users className="w-5 h-5 mr-2 text-green-400" />
                Comparação de Equipes
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* Home Team */}
                <div>
                  <h4 className="text-white font-semibold mb-4 text-center">
                    {mockAnalysis.match.homeTeam}
                  </h4>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-gray-400">Gols por Jogo:</span>
                      <span className="text-white font-medium">{mockAnalysis.keyStats.home.goalsPerGame}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Gols Sofridos:</span>
                      <span className="text-white font-medium">{mockAnalysis.keyStats.home.goalsConceded}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Posse de Bola:</span>
                      <span className="text-white font-medium">{mockAnalysis.keyStats.home.possession}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Finalizações:</span>
                      <span className="text-white font-medium">{mockAnalysis.keyStats.home.shotsPerGame}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Clean Sheets:</span>
                      <span className="text-white font-medium">{mockAnalysis.keyStats.home.cleanSheets}</span>
                    </div>
                  </div>
                </div>

                {/* Away Team */}
                <div>
                  <h4 className="text-white font-semibold mb-4 text-center">
                    {mockAnalysis.match.awayTeam}
                  </h4>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-gray-400">Gols por Jogo:</span>
                      <span className="text-white font-medium">{mockAnalysis.keyStats.away.goalsPerGame}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Gols Sofridos:</span>
                      <span className="text-white font-medium">{mockAnalysis.keyStats.away.goalsConceded}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Posse de Bola:</span>
                      <span className="text-white font-medium">{mockAnalysis.keyStats.away.possession}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Finalizações:</span>
                      <span className="text-white font-medium">{mockAnalysis.keyStats.away.shotsPerGame}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Clean Sheets:</span>
                      <span className="text-white font-medium">{mockAnalysis.keyStats.away.cleanSheets}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Form Analysis */}
            <div className="card-primary p-6">
              <h3 className="text-heading-4 mb-4 flex items-center">
                <Activity className="w-5 h-5 mr-2 text-purple-400" />
                Forma Recente
              </h3>
              
              <div className="grid grid-cols-2 gap-8">
                <div>
                  <h4 className="text-white font-medium mb-3">{mockAnalysis.match.homeTeam}</h4>
                  <div className="flex space-x-2">
                    {mockAnalysis.form.home.map((result, index) => (
                      <div key={index} className="w-8 h-8 rounded-full flex items-center justify-center bg-gray-800">
                        {getFormIcon(result)}
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <h4 className="text-white font-medium mb-3">{mockAnalysis.match.awayTeam}</h4>
                  <div className="flex space-x-2">
                    {mockAnalysis.form.away.map((result, index) => (
                      <div key={index} className="w-8 h-8 rounded-full flex items-center justify-center bg-gray-800">
                        {getFormIcon(result)}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            
            {/* Predictions */}
            <div className="card-primary p-6">
              <h3 className="text-heading-4 mb-4 flex items-center">
                <Target className="w-5 h-5 mr-2 text-yellow-400" />
                Probabilidades IA
              </h3>
              
              <div className="space-y-3">
                {renderProbabilityBar('Vitória Casa', mockAnalysis.predictions.homeWin, 'green')}
                {renderProbabilityBar('Empate', mockAnalysis.predictions.draw, 'yellow')}
                {renderProbabilityBar('Vitória Fora', mockAnalysis.predictions.awayWin, 'red')}
                {renderProbabilityBar('Over 2.5 Gols', mockAnalysis.predictions.over25, 'blue')}
                {renderProbabilityBar('Ambas Marcam', mockAnalysis.predictions.bothScore, 'purple')}
              </div>
            </div>

            {/* Recommended Picks */}
            <div className="card-primary p-6">
              <h3 className="text-heading-4 mb-4 flex items-center">
                <TrendingUp className="w-5 h-5 mr-2 text-green-400" />
                Picks Recomendados
              </h3>
              
              <div className="space-y-4">
                {mockAnalysis.picks.map((pick, index) => (
                  <div key={index} className="card-value p-4">
                    <div className="flex justify-between items-start mb-2">
                      <div className="ev-badge-small">
                        EV+ {pick.expectedValue.toFixed(1)}%
                      </div>
                      <div className="text-white font-bold">{pick.odds.toFixed(2)}</div>
                    </div>
                    <div className="text-white font-medium mb-1">{pick.market}</div>
                    <div className="text-gray-400 text-sm mb-2">{pick.selection}</div>
                    <div className="text-blue-400 text-xs">
                      Confiança: {pick.confidence}%
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Injuries & News */}
            <div className="card-primary p-6">
              <h3 className="text-heading-4 mb-4 flex items-center">
                <AlertTriangle className="w-5 h-5 mr-2 text-red-400" />
                Lesões & Notícias
              </h3>
              
              <div className="space-y-3">
                {mockAnalysis.injuries.map((injury, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-800/50 rounded-lg">
                    <div>
                      <div className="text-white font-medium">{injury.player}</div>
                      <div className="text-gray-400 text-sm">{injury.status}</div>
                    </div>
                    <div className={`px-2 py-1 rounded text-xs font-medium ${
                      injury.impact === 'Alto' ? 'bg-red-900/30 text-red-400' :
                      injury.impact === 'Médio' ? 'bg-yellow-900/30 text-yellow-400' :
                      'bg-gray-800 text-gray-400'
                    }`}>
                      {injury.impact}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* No Selection State */}
      {!selectedMatchId && (
        <div className="text-center py-12">
          <Eye className="w-16 h-16 mx-auto text-gray-500 mb-4" />
          <h3 className="text-lg font-medium text-white mb-2">
            Selecione uma partida para análise
          </h3>
          <p className="text-gray-400">
            Escolha uma partida acima para ver a análise completa
          </p>
        </div>
      )}
    </div>
  );
};

export default AnalysisPage; 