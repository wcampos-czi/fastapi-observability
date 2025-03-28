#!/bin/bash

# Wait for Grafana to be ready
until curl -s http://grafana:3000/api/health; do
    echo "Waiting for Grafana to be ready..."
    sleep 2
done

# Create datasources
curl -X POST http://admin:admin@grafana:3000/api/datasources \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Prometheus",
    "type": "prometheus",
    "url": "http://prometheus:9090",
    "access": "proxy",
    "basicAuth": false,
    "isDefault": true
  }'

curl -X POST http://admin:admin@grafana:3000/api/datasources \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tempo",
    "type": "tempo",
    "url": "http://tempo:3200",
    "access": "proxy",
    "basicAuth": false
  }'

curl -X POST http://admin:admin@grafana:3000/api/datasources \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Loki",
    "type": "loki",
    "url": "http://loki:3100",
    "access": "proxy",
    "basicAuth": false
  }'

# Create dashboards
curl -X POST http://admin:admin@grafana:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d "{\"dashboard\": $(cat /var/lib/grafana/dashboards/fastapi-metrics.json)}"

curl -X POST http://admin:admin@grafana:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d "{\"dashboard\": $(cat /var/lib/grafana/dashboards/fastapi-traces.json)}"

curl -X POST http://admin:admin@grafana:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d "{\"dashboard\": $(cat /var/lib/grafana/dashboards/fastapi-logs.json)}"

echo "Grafana dashboards provisioned successfully!" 