# 🎯 QuantumBet - Plataforma de Análise Esportiva Inteligente

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)

## 📖 Sobre o Projeto

O **QuantumBet** é uma plataforma avançada de análise esportiva que utiliza Inteligência Artificial e Machine Learning para identificar oportunidades de valor em apostas esportivas. 

**⚠️ IMPORTANTE:** O QuantumBet é uma ferramenta de **análise e recomendações**, não uma casa de apostas. Focamos em educação, análise estatística e tracking de performance.

## 🚀 Funcionalidades Principais

### 🔬 **Análise IA Avançada**
- ✅ **Sempre 5 picks por partida** (mesmo quando EV for negativo)
- ✅ **Expected Value (EV+)** destacado quando identificado
- ✅ **Confidence Score** de 0-10 para cada recomendação
- ✅ **8+ mercados analisados** por partida (Over/Under, BTTS, Handicap, etc.)
- ✅ **Ensemble Models** (XGBoost + Random Forest + Neural Networks)

### 📊 **Analytics e Performance**
- ✅ **Portfolio tracking manual** - usuário reporta resultados
- ✅ **Analytics avançados** com ROI, win rate, Sharpe ratio
- ✅ **Performance por esporte** e mercado
- ✅ **Insights IA personalizados** baseados na performance

### 🎓 **Sistema Educacional**
- ✅ **12+ lições estruturadas** sobre análise esportiva
- ✅ **Learning path personalizado** por nível
- ✅ **Sistema de XP** e achievements
- ✅ **Quizzes interativos** com exemplos práticos

### 🤖 **AI Assistant**
- ✅ **ChatBot inteligente** para explicar recomendações
- ✅ **Respostas em linguagem natural** sobre análises
- ✅ **Context-aware** com sources e related topics

### 🔔 **Sistema de Alertas**
- ✅ **Alertas automáticos** para oportunidades EV+
- ✅ **Notificações** para mudanças de odds
- ✅ **Resumos diários** personalizados
- ✅ **Múltiplos canais** (Push, Email, SMS, In-app)

### 💰 **Modelo de Subscription**
- 🆓 **FREE**: 5 picks/mês, futebol apenas
- 🥉 **BASIC**: R$ 49/mês - 50 picks, futebol + basquete
- 🥈 **PREMIUM**: R$ 99/mês - Ilimitado, todos esportes ⭐
- 🥇 **PROFESSIONAL**: R$ 149/mês - API access
- 🏢 **ENTERPRISE**: R$ 299/mês - White-label

## 🏗️ Arquitetura Técnica

### **Backend (FastAPI + Python)**
```
backend/
├── app/
│   ├── main.py                 # Aplicação principal
│   ├── api/                    # Endpoints da API
│   │   └── v1/endpoints/
│   │       ├── enhanced_platform.py  # API integrada
│   │       ├── enhanced_picks.py     # Sistema de picks
│   │       ├── auth.py              # Autenticação
│   │       └── ...
│   ├── core/                   # Configurações core
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── auth.py
│   │   └── ...
│   ├── models/                 # Modelos de dados
│   │   ├── user.py
│   │   ├── pick.py
│   │   └── ...
│   ├── services/               # Lógica de negócio
│   │   ├── advanced_analytics.py    # Analytics avançados
│   │   ├── performance_tracker.py   # Tracking manual
│   │   ├── educational_system.py    # Sistema educacional
│   │   ├── alert_system.py          # Sistema de alertas
│   │   ├── subscription_tiers.py    # Tiers de assinatura
│   │   └── ...
│   └── ml/                     # Machine Learning
│       ├── enhanced_analyzer.py
│       ├── multi_market_analyzer.py
│       └── ...
└── requirements.txt
```

### **Frontend (React + TypeScript)**
```
frontend/
├── src/
│   ├── components/
│   │   └── Dashboard.tsx
│   ├── package.json
│   └── tailwind.config.js
```

## 🚀 Deploy Rápido

### **Usando Docker (Recomendado)**

1. **Clone o repositório:**
```bash
git clone https://github.com/seu-usuario/quantumbet.git
cd quantumbet
```

2. **Configure variáveis de ambiente:**
```bash
cp .env.example .env
# Edite as variáveis no arquivo .env
```

3. **Execute com Docker Compose:**
```bash
docker-compose up -d
```

4. **Acesse a aplicação:**
- API: `http://localhost:8000`
- Documentação: `http://localhost:8000/docs`
- Frontend: `http://localhost:3000`

### **Deploy Manual**

1. **Instale dependências do backend:**
```bash
cd backend
pip install -r requirements.txt
```

2. **Configure banco de dados:**
```bash
# PostgreSQL recomendado
export DATABASE_URL="postgresql://user:pass@localhost/quantumbet"
```

3. **Execute migrações:**
```bash
alembic upgrade head
```

4. **Inicie o servidor:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## ⚙️ Variáveis de Ambiente

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/quantumbet

# Security
SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Redis Cache
REDIS_URL=redis://localhost:6379

# Email (para alertas)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Sports API
SPORTS_API_KEY=your-api-key
SPORTS_API_URL=https://api.the-odds-api.com/v4

# Payment (Stripe)
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...

# OpenAI (para AI Assistant)
OPENAI_API_KEY=sk-...
```

## 📚 Documentação da API

Após iniciar o servidor, acesse:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### **Endpoints Principais:**

```bash
# Dashboard integrado
GET /api/v1/dashboard

# Performance tracking
POST /api/v1/performance/report-result
GET /api/v1/performance/analytics

# AI Assistant
POST /api/v1/ai-assistant/ask

# Sistema educacional
GET /api/v1/education/progress

# Subscription
GET /api/v1/subscription/status
```

## 🧪 Testes

```bash
# Executar testes
cd backend
pytest

# Testes com coverage
pytest --cov=app

# Testes de integração
pytest tests/integration/
```

## 🛠️ Desenvolvimento

### **Configurar ambiente de desenvolvimento:**

1. **Instale dependências:**
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

2. **Configure pre-commit hooks:**
```bash
pre-commit install
```

3. **Execute em modo desenvolvimento:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📈 Monitoramento

- **Logs**: Configurados via Python logging
- **Métricas**: Prometheus + Grafana (via Docker Compose)
- **Health Check**: `GET /health`
- **Status**: `GET /status`

## 🔒 Segurança

- ✅ **JWT Authentication** com refresh tokens
- ✅ **Rate Limiting** por endpoint
- ✅ **CORS** configurado
- ✅ **SQL Injection** protection via SQLAlchemy
- ✅ **Input Validation** via Pydantic
- ✅ **Audit Trail** para ações importantes

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 👥 Suporte

- 📧 **Email**: suporte@quantumbet.com
- 💬 **Discord**: [QuantumBet Community](https://discord.gg/quantumbet)
- 📖 **Documentação**: [docs.quantumbet.com](https://docs.quantumbet.com)

---

**🎯 QuantumBet - Transformando análise esportiva com Inteligência Artificial**

*Feito com ❤️ em Brasil 🇧🇷* 