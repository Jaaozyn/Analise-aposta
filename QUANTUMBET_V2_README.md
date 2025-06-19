# 🚀 **QuantumBet v2.0 - A Sala de Análise Completa**

## 🎯 **Visão Geral**

**QuantumBet** é uma plataforma profissional de análise de apostas esportivas que transforma apostadores casuais em analistas sistemáticos. Com foco em **Expected Value (EV+)** e análise baseada em dados, oferecemos uma "Sala de Análise" premium onde cada decisão é fundamentada em valor matemático.

### 🏆 **Conceito: "Laboratório, Não Cassino"**
- Interface sóbria e profissional
- Foco em análise e disciplina
- EV+ como "joia" central do sistema
- Design premium "dark mode" grafite com dourado

---

## 🚀 **Versão 2.0 - Funcionalidades Implementadas**

### ✅ **1. APIs e Serviços Integrados**
- **Serviço de API centralizado** com Axios
- **Hooks customizados** com SWR para cache inteligente
- **Autenticação JWT** com refresh automático
- **Endpoints completos** para todas funcionalidades

### ✅ **2. Páginas Avançadas**
- **📊 Feed de Picks:** Filtros avançados, busca, ordenação dinâmica
- **🔬 Dossiê de Análise:** Comparação detalhada de equipes, H2H, probabilidades IA
- **💰 Gestão de Banca:** Gráficos interativos, métricas avançadas, relatórios

### ✅ **3. Sistema de Autenticação**
- **Context de autenticação** com JWT
- **Proteção de rotas** automática
- **Login/Register** com design premium
- **Auto-refresh** de tokens e logout seguro

### ✅ **4. Gráficos Interativos (Recharts)**
- **Performance Chart:** Evolução da banca com área de lucro
- **Sports Pie Chart:** Performance por esporte com alternância
- **Tooltips customizados** e visualizações responsivas

### ✅ **5. WebSocket Tempo Real**
- **Atualizações automáticas** de picks e odds
- **Notificações instantâneas** de oportunidades EV+
- **Reconexão automática** inteligente
- **Status de conexão** visual

---

## 🏗️ **Arquitetura do Sistema**

### **Backend (Python/FastAPI)**
```
backend/app/
├── services/           # 9 serviços avançados
│   ├── advanced_analytics.py
│   ├── performance_tracker.py
│   ├── educational_system.py
│   ├── alert_system.py
│   ├── subscription_tiers.py
│   └── multi_pick_generator.py
├── api/v1/endpoints/   # 7 endpoints REST
├── ml/                 # 6 módulos de ML
├── core/              # 10 módulos core
└── models/            # 4 modelos de dados
```

### **Frontend (React/Next.js)**
```
frontend/src/
├── services/          # API e WebSocket
├── hooks/             # Hooks customizados
├── contexts/          # Autenticação
├── pages/             # Páginas principais
├── components/        # Componentes reutilizáveis
└── styles/           # Design System "Sala de Análise"
```

---

## 🎨 **Design System "Sala de Análise"**

### **🎨 Paleta de Cores Premium:**
- **Fundo Principal:** Grafite escuro (#1A1D22)
- **Cards/Módulos:** Grafite claro (#252A31)
- **EV+ (A Joia):** Dourado (#FFBF00) com efeito glow
- **Informações:** Azul elétrico (#3B82F6)
- **Sucesso:** Verde (#10B981)
- **Erro:** Vermelho (#EF4444)

### **🎯 Componentes-Chave:**
- **Selo EV+:** Badge dourado animado para picks de valor
- **Cards Premium:** Bordas sutis com hover effects
- **Botões Sistema:** Hierarquia visual clara
- **Gráficos:** Cores coordenadas e interatividade

---

## 🔧 **Tecnologias Utilizadas**

### **Backend:**
- **FastAPI** - Framework web moderno
- **SQLAlchemy** - ORM para banco de dados
- **Pydantic** - Validação de dados
- **WebSocket** - Comunicação em tempo real
- **Machine Learning** - Análise preditiva
- **JWT** - Autenticação segura

### **Frontend:**
- **React 18** - Interface de usuário
- **Next.js 14** - Framework full-stack
- **TypeScript** - Tipagem estática
- **Tailwind CSS** - Estilização utilitária
- **SWR** - Cache e sincronização de dados
- **Recharts** - Gráficos interativos
- **Socket.io** - WebSocket client
- **React Hook Form** - Formulários
- **React Hot Toast** - Notificações

---

## 🚀 **Como Executar**

### **1. Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### **2. Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### **3. Acessar:**
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **Documentação:** http://localhost:8000/docs

---

## 📊 **Funcionalidades Principais**

### **🎯 Sistema de Picks:**
- **Sempre 5 picks** por partida (mesmo com EV negativo)
- **Destaque EV+** quando valor positivo é identificado
- **8 tipos de mercados** analisados
- **Confiança IA** com porcentagem
- **Unidades sugeridas** baseadas em valor

### **📈 Analytics Avançados:**
- **ROI, Sharpe Ratio, Max Drawdown**
- **Performance por esporte/mercado**
- **Insights IA personalizados**
- **Comparação com benchmarks**

### **📚 Sistema Educacional:**
- **12+ lições estruturadas**
- **Sistema XP e achievements**
- **Learning path personalizado**
- **Quizzes interativos**

### **🔔 Alertas Inteligentes:**
- **Oportunidades EV+ automáticas**
- **Mudanças significativas de odds**
- **Resumos diários personalizados**
- **Múltiplos canais de entrega**

### **💰 Tracking de Performance:**
- **Sistema manual de resultados**
- **Cálculo automático profit/loss**
- **Performance snapshots**
- **Histórico detalhado**

---

## 💎 **Modelo de Negócio**

### **Tiers de Assinatura:**
- **FREE:** R$ 0/mês - 5 picks premium, futebol apenas
- **BASIC:** R$ 49/mês - 50 picks, futebol + basquete
- **PREMIUM:** R$ 99/mês - Ilimitado, todos esportes ⭐ **Recomendado**
- **PROFESSIONAL:** R$ 149/mês - API access, consultoria
- **ENTERPRISE:** R$ 299/mês - 10 usuários, white-label

---

## 🎮 **Demo e Testes**

### **Conta Demo:**
- **Email:** demo@quantumbet.com
- **Senha:** demo123

### **Features de Desenvolvimento:**
- **Mock data** para demonstração
- **WebSocket simulado** para tempo real
- **Toast notifications** para feedback
- **Error boundaries** para estabilidade

---

## 📝 **Logs de Versão**

### **v2.0.0 (Atual)**
- ✅ Frontend completo integrado
- ✅ APIs com autenticação JWT
- ✅ WebSocket tempo real
- ✅ Gráficos avançados
- ✅ Sistema de autenticação
- ✅ Design "Sala de Análise" premium

### **v1.0.0**
- ✅ Backend com 9 serviços avançados
- ✅ Machine Learning multi-mercado
- ✅ Sistema educacional completo
- ✅ Analytics e performance tracking
- ✅ Deploy scripts automatizados

---

## 🔗 **Links Importantes**

- **🌐 Repositório:** https://github.com/Jaaozyn/Analise-aposta.git
- **📖 Documentação Backend:** `/docs` (quando rodando)
- **🎨 Design System:** `frontend/src/styles/globals.css`
- **🔧 Deploy:** Scripts em `/deploy.sh` e `/deploy.ps1`

---

## 👥 **Contribuição**

Para contribuir com o projeto:

1. **Fork** o repositório
2. **Crie** uma branch para sua feature
3. **Commit** suas mudanças
4. **Push** para a branch
5. **Abra** um Pull Request

---

## 📞 **Suporte**

Para dúvidas, sugestões ou problemas:
- **Issues:** GitHub Issues
- **Email:** suporte@quantumbet.com
- **Discord:** Comunidade QuantumBet

---

## 📄 **Licença**

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

---

**🚀 QuantumBet v2.0 - Transformando apostadores em analistas profissionais!**

*"Na QuantumBet, você não aposta por impulso, você investe com inteligência."* 