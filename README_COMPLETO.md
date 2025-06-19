# QuantumBet - Plataforma de Análise Probabilística para Apostas Esportivas

## 🎯 Visão Geral

O **QuantumBet** é uma aplicação web de ponta que utiliza **Machine Learning** e análise estatística para identificar apostas esportivas com **Valor Esperado positivo (EV+)**. A plataforma transforma apostas de um "jogo de azar" em uma disciplina analítica baseada em dados.

### 🏆 Esportes Suportados
- **Futebol** - Ligas principais mundiais
- **Basquetebol** - NBA, NBB, Euroliga
- **CS2** - Torneios profissionais
- **Valorant** - Competições oficiais

## 🚀 Características Principais

### 🧠 Motor de Análise Probabilística
- Cálculo de probabilidades justas usando Machine Learning
- Identificação de discrepâncias entre modelo e odds do mercado
- Geração automática de picks com justificativa baseada em dados
- Sistema de confiança e recomendação de stake

### 📊 Dashboard "Sala de Análise"
- Interface profissional inspirada em ferramentas de análise financeira
- Visualização em tempo real das melhores oportunidades
- Gestão completa de banca com gráficos de ROI
- Histórico de performance e estatísticas detalhadas

### 💳 Sistema de Pagamentos Completo
- **Stripe** - Cartões internacionais
- **MercadoPago** - PIX, Cartões, Boleto (foco Brasil)
- **PayPal** - Carteira digital global
- **Binance Pay** - Pagamentos em criptomoedas

### 🔄 Integração de APIs
- **API-Football** - Dados de futebol em tempo real
- **PandaScore** - Estatísticas de e-sports
- **The Odds API** - Odds de múltiplas casas de apostas

## 🏗️ Arquitetura Técnica

### Backend (Python)
```
backend/
├── app/
│   ├── main.py              # FastAPI principal
│   │   ├── core/
│   │   │   ├── config.py        # Configurações
│   │   │   ├── database.py      # SQLAlchemy + PostgreSQL
│   │   │   └── cache.py         # Redis
│   │   ├── models/              # Modelos SQLAlchemy
│   │   │   ├── user.py          # Usuários e autenticação
│   │   │   ├── match.py         # Partidas esportivas
│   │   │   ├── pick.py          # Dicas/Picks gerados
│   │   │   └── subscription.py  # Assinaturas e pagamentos
│   │   ├── ml/
│   │   │   └── analyzer.py      # Motor de ML e cálculo EV
│   │   ├── services/
│   │   │   ├── sports_api.py    # Integração APIs esportivas
│   │   │   └── payments.py      # Sistema de pagamentos
│   │   └── api/v1/endpoints/    # Rotas da API
│   ├── requirements.txt
│   └── Dockerfile
```

### Frontend (React/Next.js)
```
frontend/
├── src/
│   ├── components/
│   │   ├── Dashboard.tsx    # Sala de Análise principal
│   │   ├── PickCard.tsx     # Cards de dicas
│   │   └── BankrollChart.tsx # Gráficos de banca
│   ├── pages/
│   │   ├── dashboard/       # Páginas principais
│   │   ├── picks/           # Feed de dicas
│   │   └── subscription/    # Planos e pagamentos
│   └── hooks/               # Hooks customizados
├── tailwind.config.js       # Design System
├── package.json
└── Dockerfile
```

## 🛠️ Instalação e Execução

### Pré-requisitos
- Docker e Docker Compose
- Node.js 18+ (para desenvolvimento)
- Python 3.11+ (para desenvolvimento)

### 1. Clone o Repositório
```bash
git clone https://github.com/seu-usuario/quantumbet.git
cd quantumbet
```

### 2. Configurar Variáveis de Ambiente
Crie um arquivo `.env` na raiz do projeto:

```bash
# APIs de Esportes
API_FOOTBALL_KEY=sua_chave_api_football
PANDASCORE_KEY=sua_chave_pandascore
ODDS_API_KEY=sua_chave_odds_api

# Pagamentos
STRIPE_SECRET_KEY=sk_test_sua_chave_stripe
STRIPE_PUBLISHABLE_KEY=pk_test_sua_chave_stripe
MERCADOPAGO_ACCESS_TOKEN=seu_token_mercadopago
PAYPAL_CLIENT_ID=seu_client_id_paypal
PAYPAL_CLIENT_SECRET=seu_secret_paypal

# Banco de Dados (já configurado no Docker)
DATABASE_URL=postgresql+asyncpg://quantumbet:password123@postgres:5432/quantumbet_db
REDIS_URL=redis://redis:6379

# Segurança
SECRET_KEY=sua-chave-secreta-super-segura-aqui
```

### 3. Executar com Docker Compose

```bash
# Subir todos os serviços
docker-compose up -d

# Ver logs em tempo real
docker-compose logs -f

# Parar todos os serviços
docker-compose down
```

### 4. Acessar a Aplicação

- **Frontend**: http://localhost:3000
- **API Backend**: http://localhost:8000
- **Documentação API**: http://localhost:8000/docs
- **Grafana (Monitoramento)**: http://localhost:3001 (admin/admin123)
- **Prometheus**: http://localhost:9090

## 🔧 Desenvolvimento Local

### Backend (FastAPI)
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend (Next.js)
```bash
cd frontend
npm install
npm run dev
```

## 📈 Funcionalidades Implementadas

### ✅ Módulos Completos
- [x] **Sistema de usuários** - Registro, login, perfis
- [x] **Modelos de dados** - Partidas, picks, assinaturas
- [x] **Motor de ML** - Cálculo de EV+ e probabilidades
- [x] **APIs esportivas** - Integração com provedores de dados
- [x] **Sistema de pagamentos** - Múltiplos gateways
- [x] **Cache Redis** - Performance otimizada
- [x] **Dashboard responsivo** - Interface profissional

### 🔄 Em Desenvolvimento
- [ ] **Modelos ML avançados** - Treinamento com dados históricos
- [ ] **Notificações push** - Alertas de novas oportunidades
- [ ] **App mobile** - React Native
- [ ] **API pública** - Para desenvolvedores externos

## 💡 Como Funciona o Algoritmo

### 1. Coleta de Dados
```python
# Exemplo de coleta de dados de futebol
fixtures = await football_api.get_fixtures()
team_stats = await football_api.get_team_stats(team_id)
odds = await odds_api.get_odds("soccer_epl")
```

### 2. Cálculo de Probabilidades
```python
# Análise usando ML
analyzer = FootballAnalyzer()
probabilities = analyzer.analyze_match(match_data)
# Output: {"home": 0.65, "draw": 0.20, "away": 0.15}
```

### 3. Identificação de Valor
```python
# Cálculo de Valor Esperado
ev = calculator.calculate_ev(probability=0.65, odds=1.85)
# Se EV > 5%, gerar pick
if calculator.is_value_bet(probability, odds, min_ev=5.0):
    pick = generate_pick(match, probability, odds, ev)
```

### 4. Recomendação de Stake
```python
# Kelly Criterion modificado
stake = calculator.suggest_stake(ev=12.5, confidence=0.8)
# Output: 2.5 unidades (de 10 máximo)
```

## 🎨 Design System

### Paleta de Cores
- **Fundo Principal**: `#1A1D22` (dark-900)
- **Cards/Módulos**: `#252A31` (dark-800)
- **Cor de Valor (EV+)**: `#FFBF00` (Dourado)
- **Sucesso**: `#10b981` (Verde)
- **Erro**: `#ef4444` (Vermelho)

### Componentes Principais
- **PickCard** - Exibe dicas com selo EV+
- **StatsCard** - Métricas de performance
- **BankrollChart** - Gráfico de evolução da banca
- **Dashboard** - Interface principal "Sala de Análise"

## 🔐 Segurança

- **Autenticação JWT** - Tokens seguros para APIs
- **Criptografia** - Senhas com bcrypt
- **Rate Limiting** - Proteção contra spam
- **CORS configurado** - Acesso controlado
- **Validação de dados** - Pydantic schemas
- **Logs estruturados** - Monitoramento completo

## 📊 Monitoramento

### Métricas Coletadas
- **Performance da API** - Tempo de resposta, erros
- **Acurácia do modelo** - Taxa de acerto dos picks
- **Uso de recursos** - CPU, memória, database
- **Comportamento dos usuários** - Engagement, conversão

### Dashboards Grafana
- **Visão geral da aplicação**
- **Performance do modelo ML**
- **Métricas de negócio**
- **Alertas automáticos**

## 🚀 Deploy em Produção

### Usando Docker Swarm
```bash
# Inicializar swarm
docker swarm init

# Deploy da stack
docker stack deploy -c docker-compose.prod.yml quantumbet
```

### Usando Kubernetes
```bash
# Aplicar manifests
kubectl apply -f k8s/

# Verificar status
kubectl get pods -n quantumbet
```

### Variáveis de Produção
```bash
# Usar valores reais em produção
SECRET_KEY=chave-super-segura-produção
DATABASE_URL=postgresql://usuario:senha@servidor-postgres:5432/quantumbet
REDIS_URL=redis://servidor-redis:6379

# APIs com chaves reais
API_FOOTBALL_KEY=chave-real-api-football
STRIPE_SECRET_KEY=sk_live_chave-real-stripe
```

## 🧪 Testes

### Backend
```bash
cd backend
pytest tests/ -v
pytest tests/test_ml.py -v  # Testes do modelo ML
```

### Frontend
```bash
cd frontend
npm test
npm run test:e2e  # Testes end-to-end
```

## 📚 Documentação da API

A documentação completa da API está disponível em:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Endpoints Principais

#### Picks/Dicas
- `GET /api/v1/picks/` - Listar picks com filtros
- `GET /api/v1/picks/today` - Melhores picks de hoje
- `GET /api/v1/picks/{id}` - Detalhes de um pick
- `POST /api/v1/picks/generate` - Gerar novos picks

#### Usuários
- `POST /api/v1/users/register` - Registrar usuário
- `POST /api/v1/users/login` - Fazer login
- `GET /api/v1/users/me` - Perfil do usuário

#### Pagamentos
- `POST /api/v1/payments/create` - Criar pagamento
- `GET /api/v1/payments/{id}/status` - Status do pagamento

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 🆘 Suporte

- **Email**: suporte@quantumbet.com
- **Discord**: https://discord.gg/quantumbet
- **Documentação**: https://docs.quantumbet.com

---

**QuantumBet** - Transformando apostas em análise de dados 📊⚡

> "No mundo das apostas, a informação é a única vantagem real. O QuantumBet coloca o poder da análise de dados nas suas mãos." 