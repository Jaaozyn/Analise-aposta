#!/bin/bash

# ========================================
# QUANTUMBET - SCRIPT DE INICIALIZAÇÃO
# ========================================

echo "🚀 Iniciando setup do QuantumBet..."

# Verificar se Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não encontrado. Instale o Docker primeiro."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose não encontrado. Instale o Docker Compose primeiro."
    exit 1
fi

echo "✅ Docker e Docker Compose encontrados"

# Criar arquivo .env se não existir
if [ ! -f .env ]; then
    echo "📝 Criando arquivo .env..."
    cat > .env << EOF
# QUANTUMBET - CONFIGURAÇÕES DE AMBIENTE
PROJECT_NAME=QuantumBet
VERSION=1.0.0
SECRET_KEY=quantumbet-secret-key-$(openssl rand -hex 32)
FRONTEND_URL=http://localhost:3000

# BANCO DE DADOS
DATABASE_URL=postgresql+asyncpg://quantumbet:password123@postgres:5432/quantumbet_db

# CACHE REDIS
REDIS_URL=redis://redis:6379

# APIs DE ESPORTES (configurar depois)
API_FOOTBALL_KEY=configure_sua_chave_aqui
PANDASCORE_KEY=configure_sua_chave_aqui
ODDS_API_KEY=configure_sua_chave_aqui

# PAGAMENTOS (configurar depois)
STRIPE_SECRET_KEY=sk_test_configure_sua_chave
STRIPE_PUBLISHABLE_KEY=pk_test_configure_sua_chave
MERCADOPAGO_ACCESS_TOKEN=TEST-configure_seu_token
PAYPAL_CLIENT_ID=configure_seu_client_id
PAYPAL_CLIENT_SECRET=configure_seu_secret
PAYPAL_MODE=sandbox

# CELERY
CELERY_BROKER_URL=redis://redis:6379
CELERY_RESULT_BACKEND=redis://redis:6379

# DESENVOLVIMENTO
LOG_LEVEL=INFO
DEBUG=true
EOF
    echo "✅ Arquivo .env criado"
else
    echo "✅ Arquivo .env já existe"
fi

# Criar diretórios necessários
echo "📁 Criando diretórios..."
mkdir -p models data logs nginx/ssl monitoring/grafana monitoring/prometheus

# Criar Dockerfile para backend se não existir
if [ ! -f backend/Dockerfile ]; then
    echo "🐳 Criando Dockerfile do backend..."
    cat > backend/Dockerfile << EOF
FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \\
    gcc \\
    postgresql-client \\
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Expor porta
EXPOSE 8000

# Comando de inicialização
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
EOF
    echo "✅ Dockerfile do backend criado"
fi

# Criar Dockerfile para frontend se não existir
if [ ! -f frontend/Dockerfile ]; then
    echo "🐳 Criando Dockerfile do frontend..."
    cat > frontend/Dockerfile << EOF
FROM node:18-alpine

WORKDIR /app

# Copiar package.json
COPY package*.json ./
RUN npm ci --only=production

# Copiar código
COPY . .

# Build da aplicação
RUN npm run build

# Expor porta
EXPOSE 3000

# Comando de inicialização
CMD ["npm", "start"]
EOF
    echo "✅ Dockerfile do frontend criado"
fi

# Baixar imagens Docker
echo "📦 Baixando imagens Docker..."
docker-compose pull

# Subir serviços
echo "🚀 Iniciando serviços..."
docker-compose up -d postgres redis

# Aguardar banco de dados
echo "⏳ Aguardando banco de dados..."
sleep 10

# Subir aplicação
echo "🚀 Iniciando aplicação..."
docker-compose up -d

# Verificar status
echo "🔍 Verificando status dos serviços..."
docker-compose ps

echo ""
echo "🎉 QuantumBet iniciado com sucesso!"
echo ""
echo "📋 URLs de Acesso:"
echo "   Frontend:          http://localhost:3000"
echo "   API Backend:       http://localhost:8000"
echo "   Documentação API:  http://localhost:8000/docs"
echo "   Grafana:          http://localhost:3001 (admin/admin123)"
echo ""
echo "⚙️  Próximos passos:"
echo "   1. Configure as chaves das APIs no arquivo .env"
echo "   2. Reinicie os serviços: docker-compose restart"
echo "   3. Acesse http://localhost:3000 para começar"
echo ""
echo "📚 Documentação completa: README_COMPLETO.md"
echo ""
echo "🔧 Comandos úteis:"
echo "   Ver logs:     docker-compose logs -f"
echo "   Parar tudo:   docker-compose down"
 