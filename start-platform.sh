#!/bin/bash

# SEO Platform Startup Script
# This script sets up and starts the complete SEO platform

set -e

echo "🚀 Starting SEO Intelligence Platform..."
echo "================================================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created. Please update it with your API keys."
fi

# Create necessary directories
echo "📁 Creating required directories..."
mkdir -p backend/uploads
mkdir -p database/data
mkdir -p monitoring/data

# Set permissions
chmod +x claude-flow
chmod +x start-platform.sh

# Start the platform
echo "🐳 Starting Docker containers..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 30

# Check service health
echo "🔍 Checking service health..."

# Check if backend is running
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend API is running"
else
    echo "⚠️  Backend API may still be starting up"
fi

# Check if frontend is running
if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend is running"
else
    echo "⚠️  Frontend may still be starting up"
fi

# Check databases
if docker-compose exec -T postgres pg_isready -U seo_user -d seo_platform > /dev/null 2>&1; then
    echo "✅ PostgreSQL is running"
else
    echo "⚠️  PostgreSQL may still be starting up"
fi

if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is running"
else
    echo "⚠️  Redis may still be starting up"
fi

echo ""
echo "🎉 SEO Platform Setup Complete!"
echo "================================================"
echo ""
echo "📱 Application URLs:"
echo "   Frontend:     http://localhost:3000"
echo "   Backend API:  http://localhost:8000"
echo "   API Docs:     http://localhost:8000/docs"
echo "   Grafana:      http://localhost:3001 (admin/admin)"
echo "   Prometheus:   http://localhost:9090"
echo "   MinIO:        http://localhost:9011 (minio_user/minio_password)"
echo ""
echo "🔑 Demo Login Credentials:"
echo "   Email:        admin@seoplatform.com"
echo "   Password:     admin123"
echo ""
echo "📋 Next Steps:"
echo "   1. Open http://localhost:3000 in your browser"
echo "   2. Login with the demo credentials above"
echo "   3. Update .env file with your API keys for full functionality:"
echo "      - OPENAI_API_KEY (for AI features)"
echo "      - DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD (for SEO data)"
echo "   4. Restart services after updating API keys: docker-compose restart"
echo ""
echo "🛠️  Management Commands:"
echo "   Stop platform:     docker-compose down"
echo "   View logs:          docker-compose logs -f"
echo "   Restart services:   docker-compose restart"
echo "   Update containers:  docker-compose pull && docker-compose up -d"
echo ""
echo "📚 Documentation:"
echo "   - See README.md for detailed setup instructions"
echo "   - API documentation available at http://localhost:8000/docs"
echo "   - Check CLAUDE.md for development commands"
echo ""

# Check if everything is running
sleep 10
echo "🔄 Final status check..."

SERVICES=(
    "postgres:5432"
    "redis:6379"
    "backend:8000"
    "frontend:3000"
)

for service in "${SERVICES[@]}"; do
    IFS=':' read -r name port <<< "$service"
    if nc -z localhost "$port" 2>/dev/null; then
        echo "✅ $name is ready on port $port"
    else
        echo "⚠️  $name may still be starting on port $port"
    fi
done

echo ""
echo "🎯 Platform is ready! Open http://localhost:3000 to get started."
echo "================================================"