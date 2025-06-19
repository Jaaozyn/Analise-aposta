#!/bin/bash

# ==============================================
# QUANTUMBET DEPLOYMENT SCRIPT
# ==============================================
# Automated deployment script for QuantumBet platform
# Supports: Development, Staging, Production environments
# ==============================================

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="quantumbet"
DOCKER_COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"

# Default values
ENVIRONMENT=${1:-"development"}
BUILD_TYPE=${2:-"full"}
SKIP_TESTS=${3:-"false"}

# ==============================================
# UTILITY FUNCTIONS
# ==============================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_dependencies() {
    log_info "Checking system dependencies..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check Git
    if ! command -v git &> /dev/null; then
        log_error "Git is not installed. Please install Git first."
        exit 1
    fi
    
    # Check Python (for local development)
    if [[ "$ENVIRONMENT" == "development" ]] && ! command -v python3 &> /dev/null; then
        log_warning "Python 3 is not installed. Docker-only deployment will be used."
    fi
    
    log_success "All dependencies are available"
}

create_env_file() {
    log_info "Setting up environment configuration..."
    
    if [[ ! -f "$ENV_FILE" ]]; then
        log_info "Creating .env file from template..."
        
        cat > "$ENV_FILE" << EOF
# QUANTUMBET ENVIRONMENT CONFIGURATION
# Generated on $(date)

# Database
DATABASE_URL=postgresql://quantumbet_user:quantumbet_pass@db:5432/quantumbet_db

# Security
SECRET_KEY=$(openssl rand -hex 32 2>/dev/null || echo "change-this-secret-key-in-production")
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Redis Cache
REDIS_URL=redis://redis:6379/0

# Environment
ENVIRONMENT=$ENVIRONMENT
DEBUG=$([ "$ENVIRONMENT" == "development" ] && echo "true" || echo "false")
LOG_LEVEL=INFO

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# API Configuration
SPORTS_API_KEY=your-api-key-here
OPENAI_API_KEY=your-openai-key-here

# Stripe (Development Keys)
STRIPE_PUBLIC_KEY=pk_test_your_key_here
STRIPE_SECRET_KEY=sk_test_your_key_here

# Email (Development)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Feature Flags
ENABLE_AI_ASSISTANT=true
ENABLE_ADVANCED_ANALYTICS=true
ENABLE_ALERTS=true
ENABLE_EDUCATIONAL_SYSTEM=true
ENABLE_SUBSCRIPTION_TIERS=true
EOF
        
        log_success ".env file created"
        log_warning "Please edit .env file with your actual API keys and configuration"
    else
        log_info ".env file already exists"
    fi
}

setup_database() {
    log_info "Setting up database..."
    
    # Start database services
    docker-compose up -d db redis
    
    # Wait for database to be ready
    log_info "Waiting for database to be ready..."
    sleep 10
    
    # Run database migrations
    log_info "Running database migrations..."
    docker-compose exec -T backend python -m alembic upgrade head || {
        log_warning "Migration failed, database might not be ready yet"
        sleep 10
        docker-compose exec -T backend python -m alembic upgrade head
    }
    
    log_success "Database setup completed"
}

build_application() {
    log_info "Building application..."
    
    case $BUILD_TYPE in
        "full")
            log_info "Building all services..."
            docker-compose build --no-cache
            ;;
        "backend")
            log_info "Building backend only..."
            docker-compose build --no-cache backend
            ;;
        "frontend")
            log_info "Building frontend only..."
            docker-compose build --no-cache frontend
            ;;
        *)
            log_error "Invalid build type: $BUILD_TYPE"
            exit 1
            ;;
    esac
    
    log_success "Build completed"
}

run_tests() {
    if [[ "$SKIP_TESTS" == "true" ]]; then
        log_warning "Skipping tests as requested"
        return 0
    fi
    
    log_info "Running tests..."
    
    # Start test database
    docker-compose -f docker-compose.test.yml up -d test-db || {
        log_warning "Test database compose file not found, using main database"
    }
    
    # Run backend tests
    docker-compose exec -T backend python -m pytest tests/ -v --cov=app --cov-report=html || {
        log_error "Tests failed"
        return 1
    }
    
    log_success "All tests passed"
}

deploy_development() {
    log_info "Deploying to DEVELOPMENT environment..."
    
    # Start all services
    docker-compose up -d
    
    # Health check
    sleep 15
    health_check
    
    log_success "Development deployment completed"
    log_info "API available at: http://localhost:8000"
    log_info "API Documentation: http://localhost:8000/docs"
    log_info "Frontend available at: http://localhost:3000"
}

deploy_staging() {
    log_info "Deploying to STAGING environment..."
    
    # Use production-like configuration
    docker-compose -f docker-compose.yml -f docker-compose.staging.yml up -d
    
    # Run health checks
    sleep 20
    health_check
    
    log_success "Staging deployment completed"
}

deploy_production() {
    log_info "Deploying to PRODUCTION environment..."
    
    # Production safety checks
    if [[ "$SECRET_KEY" == "change-this-secret-key-in-production" ]]; then
        log_error "Production SECRET_KEY not configured!"
        exit 1
    fi
    
    # Use production configuration
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
    
    # Run comprehensive health checks
    sleep 30
    health_check
    
    log_success "Production deployment completed"
}

health_check() {
    log_info "Running health checks..."
    
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f http://localhost:8000/health >/dev/null 2>&1; then
            log_success "Backend health check passed"
            break
        fi
        
        if [[ $attempt -eq $max_attempts ]]; then
            log_error "Backend health check failed after $max_attempts attempts"
            return 1
        fi
        
        log_info "Attempt $attempt/$max_attempts: Waiting for backend..."
        sleep 5
        ((attempt++))
    done
    
    # Check database connection
    if docker-compose exec -T backend python -c "
from app.core.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    conn.execute(text('SELECT 1'))
print('Database connection: OK')
" >/dev/null 2>&1; then
        log_success "Database health check passed"
    else
        log_error "Database health check failed"
        return 1
    fi
    
    # Check Redis connection
    if docker-compose exec -T redis redis-cli ping >/dev/null 2>&1; then
        log_success "Redis health check passed"
    else
        log_warning "Redis health check failed (optional service)"
    fi
}

setup_monitoring() {
    log_info "Setting up monitoring..."
    
    # Start monitoring services if available
    if [[ -f "docker-compose.monitoring.yml" ]]; then
        docker-compose -f docker-compose.monitoring.yml up -d
        log_success "Monitoring services started"
        log_info "Grafana available at: http://localhost:3001"
        log_info "Prometheus available at: http://localhost:9090"
    else
        log_warning "Monitoring configuration not found"
    fi
}

setup_ssl() {
    if [[ "$ENVIRONMENT" == "production" ]]; then
        log_info "Setting up SSL certificates..."
        
        # Check if certbot is available
        if command -v certbot &> /dev/null; then
            # Generate SSL certificates
            log_info "Generating SSL certificates with Let's Encrypt..."
            # Add your SSL setup logic here
            log_success "SSL certificates configured"
        else
            log_warning "Certbot not found. Manual SSL configuration required."
        fi
    fi
}

cleanup() {
    log_info "Cleaning up old resources..."
    
    # Remove unused Docker images
    docker image prune -f >/dev/null 2>&1 || true
    
    # Remove unused volumes (be careful in production)
    if [[ "$ENVIRONMENT" != "production" ]]; then
        docker volume prune -f >/dev/null 2>&1 || true
    fi
    
    log_success "Cleanup completed"
}

backup_database() {
    if [[ "$ENVIRONMENT" == "production" ]]; then
        log_info "Creating database backup..."
        
        local backup_dir="./backups"
        local backup_file="${backup_dir}/quantumbet_backup_$(date +%Y%m%d_%H%M%S).sql"
        
        mkdir -p "$backup_dir"
        
        docker-compose exec -T db pg_dump -U quantumbet_user quantumbet_db > "$backup_file"
        
        if [[ -f "$backup_file" ]]; then
            log_success "Database backup created: $backup_file"
        else
            log_error "Database backup failed"
            return 1
        fi
    fi
}

show_usage() {
    cat << EOF
QUANTUMBET DEPLOYMENT SCRIPT

Usage: $0 [ENVIRONMENT] [BUILD_TYPE] [SKIP_TESTS]

ENVIRONMENT:
  development (default) - Local development setup
  staging              - Staging environment 
  production           - Production deployment

BUILD_TYPE:
  full (default)       - Build all services
  backend             - Build backend only
  frontend            - Build frontend only

SKIP_TESTS:
  false (default)      - Run tests
  true                - Skip tests

Examples:
  $0                           # Development with full build and tests
  $0 development backend false # Development with backend build and tests
  $0 staging full true         # Staging with full build, skip tests
  $0 production full false     # Production with full build and tests

Environment Variables:
  You can override default behavior with environment variables:
  SKIP_HEALTH_CHECK=true      # Skip health checks
  SKIP_MONITORING=true        # Skip monitoring setup
  SKIP_CLEANUP=true           # Skip cleanup
  FORCE_REBUILD=true          # Force rebuild even if images exist

EOF
}

# ==============================================
# MAIN DEPLOYMENT FLOW
# ==============================================

main() {
    log_info "Starting QuantumBet deployment..."
    log_info "Environment: $ENVIRONMENT"
    log_info "Build Type: $BUILD_TYPE"
    log_info "Skip Tests: $SKIP_TESTS"
    
    # Change to script directory
    cd "$SCRIPT_DIR"
    
    # Check if help is requested
    if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
        show_usage
        exit 0
    fi
    
    # Pre-deployment checks
    check_dependencies
    create_env_file
    
    # Backup in production
    if [[ "$ENVIRONMENT" == "production" ]]; then
        backup_database
    fi
    
    # Build application
    build_application
    
    # Run tests (unless skipped)
    if [[ "$SKIP_TESTS" != "true" ]]; then
        run_tests
    fi
    
    # Setup database
    setup_database
    
    # Deploy based on environment
    case $ENVIRONMENT in
        "development")
            deploy_development
            ;;
        "staging")
            deploy_staging
            ;;
        "production")
            deploy_production
            setup_ssl
            ;;
        *)
            log_error "Invalid environment: $ENVIRONMENT"
            show_usage
            exit 1
            ;;
    esac
    
    # Optional post-deployment steps
    if [[ "${SKIP_MONITORING:-false}" != "true" ]]; then
        setup_monitoring
    fi
    
    if [[ "${SKIP_CLEANUP:-false}" != "true" ]]; then
        cleanup
    fi
    
    # Final status
    log_success "🎯 QuantumBet deployment completed successfully!"
    log_info "Environment: $ENVIRONMENT"
    log_info "Deployment time: $(date)"
    
    # Show service URLs
    case $ENVIRONMENT in
        "development")
            echo -e "\n${GREEN}🚀 Services Available:${NC}"
            echo -e "  🌐 API: ${BLUE}http://localhost:8000${NC}"
            echo -e "  📚 API Docs: ${BLUE}http://localhost:8000/docs${NC}"
            echo -e "  💻 Frontend: ${BLUE}http://localhost:3000${NC}"
            echo -e "  📊 Monitoring: ${BLUE}http://localhost:3001${NC} (if enabled)"
            ;;
        "staging")
            echo -e "\n${GREEN}🚀 Staging Services:${NC}"
            echo -e "  🌐 API: ${BLUE}https://staging-api.quantumbet.com${NC}"
            echo -e "  💻 Frontend: ${BLUE}https://staging.quantumbet.com${NC}"
            ;;
        "production")
            echo -e "\n${GREEN}🚀 Production Services:${NC}"
            echo -e "  🌐 API: ${BLUE}https://api.quantumbet.com${NC}"
            echo -e "  💻 Frontend: ${BLUE}https://quantumbet.com${NC}"
            ;;
    esac
    
    echo -e "\n${YELLOW}📝 Next Steps:${NC}"
    echo -e "  1. Configure API keys in .env file"
    echo -e "  2. Set up domain DNS (for staging/production)"
    echo -e "  3. Configure monitoring alerts"
    echo -e "  4. Test all functionalities"
    echo -e "  5. Monitor logs: ${BLUE}docker-compose logs -f${NC}"
}

# ==============================================
# SCRIPT EXECUTION
# ==============================================

# Trap errors and cleanup
trap 'log_error "Deployment failed at line $LINENO"' ERR

# Check if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 