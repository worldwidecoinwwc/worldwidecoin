@echo off
REM WorldWideCoin Docker Deployment Script (Windows)

echo 🚀 Starting WorldWideCoin Docker Deployment

REM Create necessary directories
echo 📁 Creating data and config directories...
if not exist "data" mkdir data
if not exist "data\node1" mkdir data\node1
if not exist "data\node2" mkdir data\node2
if not exist "data\node3" mkdir data\node3
if not exist "data\miner" mkdir data\miner
if not exist "config" mkdir config
if not exist "config\node1" mkdir config\node1
if not exist "config\node2" mkdir config\node2
if not exist "config\node3" mkdir config\node3
if not exist "config\miner" mkdir config\miner

REM Build and start the services
echo 🐳 Building Docker images...
docker-compose build

echo 🌐 Starting WorldWideCoin network...
docker-compose up -d node1 api1 node2 api2 node3 api3

echo ⏳ Waiting for nodes to initialize...
timeout /t 10 /nobreak > nul

echo ✅ WorldWideCoin network is running!
echo.
echo 📊 Access points:
echo   Node 1 API: http://localhost:8001
echo   Node 2 API: http://localhost:8002
echo   Node 3 API: http://localhost:8003
echo.
echo 🔗 P2P Ports:
echo   Node 1: localhost:5001
echo   Node 2: localhost:5002
echo   Node 3: localhost:5003
echo.
echo 💡 To start mining: docker-compose --profile miner up -d miner
echo 💡 To view logs: docker-compose logs -f [service_name]
echo 💡 To stop: docker-compose down

pause