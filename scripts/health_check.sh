#!/bin/bash
# Health check script for IDP infrastructure services

set -e

echo "🔍 Checking IDP Infrastructure Services..."
echo ""

# Check MinIO
echo "📦 Checking MinIO..."
if curl -f -s http://localhost:9000/minio/health/live > /dev/null 2>&1; then
    echo "✅ MinIO is healthy"
else
    echo "❌ MinIO is not responding"
    exit 1
fi

# Check PostgreSQL
echo "🐘 Checking PostgreSQL..."
if pg_isready -h localhost -p 5432 -U idp_user > /dev/null 2>&1; then
    echo "✅ PostgreSQL is healthy"
else
    echo "❌ PostgreSQL is not responding"
    exit 1
fi

# Check Airflow
echo "🌬️  Checking Airflow..."
if curl -f -s http://localhost:8080/health > /dev/null 2>&1; then
    echo "✅ Airflow is healthy"
else
    echo "❌ Airflow is not responding"
    exit 1
fi

echo ""
echo "✅ All services are healthy!"
