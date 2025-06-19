# ==============================================
# QUANTUMBET DEPLOYMENT SCRIPT (PowerShell)
# ==============================================
# Automated deployment script for QuantumBet platform (Windows)
# Supports: Development, Staging, Production environments
# ==============================================

param(
    [Parameter(Position=0)]
    [ValidateSet("development", "staging", "production")]
    [string]$Environment = "development",
    
    [Parameter(Position=1)]
    [ValidateSet("full", "backend", "frontend")]
    [string]$BuildType = "full",
    
    [Parameter(Position=2)]
    [bool]$SkipTests = $false
)

# Configuration
$ProjectName = "quantumbet"
$DockerComposeFile = "docker-compose.yml"
$EnvFile = ".env"

# Colors for output
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Test-Dependencies {
    Write-Info "Checking system dependencies..."
    
    # Check Docker
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Error "Docker is not installed. Please install Docker Desktop first."
        exit 1
    }
    
    # Check Docker Compose
    if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
        Write-Error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    }
    
    # Check Git
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        Write-Error "Git is not installed. Please install Git first."
        exit 1
    }
    
    Write-Success "All dependencies are available"
}

function New-EnvFile {
    Write-Info "Setting up environment configuration..."
    
    if (-not (Test-Path $EnvFile)) {
        Write-Info "Creating .env file from template..."
        
        $envContent = @"
# QUANTUMBET ENVIRONMENT CONFIGURATION
# Generated on $(Get-Date)

# Database
DATABASE_URL=postgresql://quantumbet_user:quantumbet_pass@db:5432/quantumbet_db

# Security
SECRET_KEY=$(-join ((1..32) | ForEach-Object { '{0:X}' -f (Get-Random -Max 256) }))
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Redis Cache
REDIS_URL=redis://redis:6379/0

# Environment
ENVIRONMENT=$Environment
DEBUG=$($Environment -eq "development" ? "true" : "false")
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
"@
        
        Set-Content -Path $EnvFile -Value $envContent
        Write-Success ".env file created"
        Write-Warning "Please edit .env file with your actual API keys and configuration"
    } else {
        Write-Info ".env file already exists"
    }
}

function Initialize-Database {
    Write-Info "Setting up database..."
    
    # Start database services
    docker-compose up -d db redis
    
    # Wait for database to be ready
    Write-Info "Waiting for database to be ready..."
    Start-Sleep -Seconds 10
    
    # Run database migrations
    Write-Info "Running database migrations..."
    try {
        docker-compose exec -T backend python -m alembic upgrade head
    } catch {
        Write-Warning "Migration failed, database might not be ready yet"
        Start-Sleep -Seconds 10
        docker-compose exec -T backend python -m alembic upgrade head
    }
    
    Write-Success "Database setup completed"
}

function Build-Application {
    Write-Info "Building application..."
    
    switch ($BuildType) {
        "full" {
            Write-Info "Building all services..."
            docker-compose build --no-cache
        }
        "backend" {
            Write-Info "Building backend only..."
            docker-compose build --no-cache backend
        }
        "frontend" {
            Write-Info "Building frontend only..."
            docker-compose build --no-cache frontend
        }
        default {
            Write-Error "Invalid build type: $BuildType"
            exit 1
        }
    }
    
    Write-Success "Build completed"
}

function Invoke-Tests {
    if ($SkipTests) {
        Write-Warning "Skipping tests as requested"
        return $true
    }
    
    Write-Info "Running tests..."
    
    try {
        # Run backend tests
        docker-compose exec -T backend python -m pytest tests/ -v --cov=app --cov-report=html
        Write-Success "All tests passed"
        return $true
    } catch {
        Write-Error "Tests failed"
        return $false
    }
}

function Deploy-Development {
    Write-Info "Deploying to DEVELOPMENT environment..."
    
    # Start all services
    docker-compose up -d
    
    # Health check
    Start-Sleep -Seconds 15
    Test-HealthCheck
    
    Write-Success "Development deployment completed"
    Write-Info "API available at: http://localhost:8000"
    Write-Info "API Documentation: http://localhost:8000/docs"
    Write-Info "Frontend available at: http://localhost:3000"
}

function Deploy-Staging {
    Write-Info "Deploying to STAGING environment..."
    
    # Use production-like configuration
    docker-compose -f docker-compose.yml -f docker-compose.staging.yml up -d
    
    # Run health checks
    Start-Sleep -Seconds 20
    Test-HealthCheck
    
    Write-Success "Staging deployment completed"
}

function Deploy-Production {
    Write-Info "Deploying to PRODUCTION environment..."
    
    # Production safety checks
    $envContent = Get-Content $EnvFile -Raw
    if ($envContent -match "change-this-secret-key-in-production") {
        Write-Error "Production SECRET_KEY not configured!"
        exit 1
    }
    
    # Use production configuration
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
    
    # Run comprehensive health checks
    Start-Sleep -Seconds 30
    Test-HealthCheck
    
    Write-Success "Production deployment completed"
}

function Test-HealthCheck {
    Write-Info "Running health checks..."
    
    $maxAttempts = 30
    $attempt = 1
    
    while ($attempt -le $maxAttempts) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                Write-Success "Backend health check passed"
                break
            }
        } catch {
            if ($attempt -eq $maxAttempts) {
                Write-Error "Backend health check failed after $maxAttempts attempts"
                return $false
            }
            
            Write-Info "Attempt $attempt/$maxAttempts`: Waiting for backend..."
            Start-Sleep -Seconds 5
            $attempt++
        }
    }
    
    # Check database connection
    try {
        $dbCheck = docker-compose exec -T backend python -c @"
from app.core.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    conn.execute(text('SELECT 1'))
print('Database connection: OK')
"@
        Write-Success "Database health check passed"
    } catch {
        Write-Error "Database health check failed"
        return $false
    }
    
    # Check Redis connection
    try {
        docker-compose exec -T redis redis-cli ping | Out-Null
        Write-Success "Redis health check passed"
    } catch {
        Write-Warning "Redis health check failed (optional service)"
    }
    
    return $true
}

function Show-Usage {
    Write-Host @"
QUANTUMBET DEPLOYMENT SCRIPT (PowerShell)

Usage: .\deploy.ps1 [Environment] [BuildType] [SkipTests]

Parameters:
  Environment:
    development (default) - Local development setup
    staging              - Staging environment 
    production           - Production deployment

  BuildType:
    full (default)       - Build all services
    backend             - Build backend only
    frontend            - Build frontend only

  SkipTests:
    `$false (default)     - Run tests
    `$true               - Skip tests

Examples:
  .\deploy.ps1
  .\deploy.ps1 development backend `$false
  .\deploy.ps1 staging full `$true
  .\deploy.ps1 production full `$false

"@
}

# ==============================================
# MAIN DEPLOYMENT FLOW
# ==============================================

function Main {
    Write-Info "Starting QuantumBet deployment..."
    Write-Info "Environment: $Environment"
    Write-Info "Build Type: $BuildType"
    Write-Info "Skip Tests: $SkipTests"
    
    # Check if help is requested
    if ($args -contains "--help" -or $args -contains "-h") {
        Show-Usage
        return
    }
    
    try {
        # Pre-deployment checks
        Test-Dependencies
        New-EnvFile
        
        # Build application
        Build-Application
        
        # Run tests (unless skipped)
        if (-not $SkipTests) {
            if (-not (Invoke-Tests)) {
                Write-Error "Tests failed. Deployment aborted."
                return
            }
        }
        
        # Setup database
        Initialize-Database
        
        # Deploy based on environment
        switch ($Environment) {
            "development" { Deploy-Development }
            "staging" { Deploy-Staging }
            "production" { Deploy-Production }
            default {
                Write-Error "Invalid environment: $Environment"
                Show-Usage
                return
            }
        }
        
        # Final status
        Write-Success "🎯 QuantumBet deployment completed successfully!"
        Write-Info "Environment: $Environment"
        Write-Info "Deployment time: $(Get-Date)"
        
        # Show service URLs
        Write-Host "`n🚀 Services Available:" -ForegroundColor Green
        switch ($Environment) {
            "development" {
                Write-Host "  🌐 API: http://localhost:8000" -ForegroundColor Blue
                Write-Host "  📚 API Docs: http://localhost:8000/docs" -ForegroundColor Blue
                Write-Host "  💻 Frontend: http://localhost:3000" -ForegroundColor Blue
            }
            "staging" {
                Write-Host "  🌐 API: https://staging-api.quantumbet.com" -ForegroundColor Blue
                Write-Host "  💻 Frontend: https://staging.quantumbet.com" -ForegroundColor Blue
            }
            "production" {
                Write-Host "  🌐 API: https://api.quantumbet.com" -ForegroundColor Blue
                Write-Host "  💻 Frontend: https://quantumbet.com" -ForegroundColor Blue
            }
        }
        
        Write-Host "`n📝 Next Steps:" -ForegroundColor Yellow
        Write-Host "  1. Configure API keys in .env file"
        Write-Host "  2. Set up domain DNS (for staging/production)"
        Write-Host "  3. Test all functionalities"
        Write-Host "  4. Monitor logs: docker-compose logs -f"
        
    } catch {
        Write-Error "Deployment failed: $($_.Exception.Message)"
        Write-Error "Line: $($_.InvocationInfo.ScriptLineNumber)"
    }
}

# Run main function
Main 