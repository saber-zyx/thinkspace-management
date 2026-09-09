#!/bin/bash
echo "========================================================"
echo "Khởi động Hệ thống Quản lý ThinkSpace (Docker Compose)"
echo "========================================================"
echo ""
echo "Đang build và khởi động PostgreSQL cùng với FastAPI..."
docker-compose up --build
