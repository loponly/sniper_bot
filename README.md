# Crypto Trading Multi-Agent System

## Quick Start

1. One-line deployment:
```bash
./deploy.sh
```

2. Monitor all agents:
```bash
./monitor.sh
```

## Deployment Options

### 1. Docker Compose Deployment (Recommended)
```bash
# Start all services
docker-compose up -d

# Check deployment status
docker-compose ps

# View logs of all agents
docker-compose logs -f
```

### 2. Individual Service Deployment
```bash
# Start specific services
docker-compose up -d redis
docker-compose up -d strategy_finder
docker-compose up -d market_analyzer
docker-compose up -d strategy_executor
docker-compose up -d dashboard
```

## Monitoring Tools

### 1. Web Dashboard
Access at http://localhost:5000
- Real-time agent status
- Live strategy updates
- Market analysis feed
- Performance metrics

### 2. CLI Monitoring
```bash
# Monitor all agents
./scripts/monitor_agents.py

# Monitor specific agent
./scripts/monitor_agents.py --agent strategy_finder
```

### 3. Docker Logs
```bash
# All agents
docker-compose logs -f

# Specific agent
docker-compose logs -f strategy_finder
```

### 4. Redis Monitor
```bash
# Monitor all Redis events
docker-compose exec redis redis-cli monitor

# Monitor specific channels
docker-compose exec redis redis-cli psubscribe "*"
```

## Health Checks

### 1. API Endpoint
```bash
curl http://localhost:5000/health
```

### 2. Container Status
```bash
docker-compose ps
```

### 3. Resource Usage
```bash
docker stats
```

## Features

- Three-agent collaboration system
- Multiple trading strategies:
  - SMA (Simple Moving Average)
  - MACD + RSI + Bollinger Bands
  - Pump Detection
  - Dump Detection
- Real-time market analysis
- Automated strategy selection
- Risk management integration
- Built on AutoGen 0.4 framework
- Real-time console output of agent interactions

## Prerequisites

- Python 3.8+
- OpenAI API key
- Access to crypto market data

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Install the required packages:
```bash
pip install -r requirements.txt
```

3. Set up your OpenAI API key:
   - Open `main.py`
   - Replace `YOUR_API_KEY` with your actual OpenAI API key

## Docker Deployment

1. Set your OpenAI API key in your environment:
```bash
export OPENAI_API_KEY=your_api_key_here
```

2. Build and start the containers:
```bash
docker-compose up -d
```

3. Monitor the agents:
```bash
# View all container logs
docker-compose logs -f

# View specific agent logs
docker-compose logs -f strategy_finder
docker-compose logs -f market_analyzer
docker-compose logs -f strategy_executor
```

## System Architecture

### Container Architecture
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Strategy Finder │     │ Market Analyzer │     │Strategy Executor│
│    Container    │     │    Container    │     │    Container    │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                        │
         │                       │                        │
         └───────────┬──────────┴────────────┬──────────┘
                     │                       │
              ┌──────┴───────┐       ┌──────┴───────┐
              │    Redis     │       │    Shared    │
              │  Container   │       │    Volume    │
              └──────────────┘       └──────────────┘
```

### Inter-Agent Communication
- Redis pub/sub for real-time updates
- Shared state management
- Event-driven architecture

### Monitoring and Maintenance

1. Check agent status:
```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.State}}"
```

2. Redis CLI access:
```bash
docker-compose exec redis redis-cli
```

3. View agent messages:
```bash
# In Redis CLI
SUBSCRIBE market_analysis execution_results execution_errors
```

4. Container Management:
```bash
# Restart specific agent
docker-compose restart strategy_finder

# Stop all containers
docker-compose down

# Remove all containers and volumes
docker-compose down -v
```

## Configuration

### Environment Variables
- `AGENT_INTERVAL`: Time between agent runs (seconds)
- `REDIS_HOST`: Redis connection host
- `REDIS_PORT`: Redis connection port
- `OPENAI_API_KEY`: Your OpenAI API key

### Agent-Specific Settings
Each agent can be configured in docker-compose.yml:
```yaml
strategy_finder:
  environment:
    - AGENT_INTERVAL=60  # Check market every minute
```

## Troubleshooting

1. Container Issues:
```bash
# Check container logs
docker-compose logs --tail=100 [service_name]

# Restart all services
docker-compose restart
```

2. Redis Connection Issues:
```bash
# Check Redis connectivity
docker-compose exec redis redis-cli ping
```

3. Agent Communication Issues:
```bash
# Monitor Redis events
docker-compose exec redis redis-cli monitor
```

## Usage

Run the trading system:
```bash
python main.py
```

The agents will collaborate to:
1. Analyze market conditions (Market Analyzer)
2. Select appropriate trading strategy (Strategy Finder)
3. Execute and monitor the strategy (Strategy Executor)

## Architecture

### Strategy Finder Agent
- Analyzes market conditions and requirements
- Selects optimal trading strategy from available options
- Provides strategy configuration parameters
- Makes data-driven strategy recommendations

### Market Analyzer Agent
- Processes market data using technical indicators
- Identifies trading opportunities and risks
- Provides real-time market insights
- Monitors market conditions continuously

### Strategy Executor Agent
- Implements selected trading strategies
- Manages strategy configuration and initialization
- Executes trades with risk management
- Monitors and reports performance

## Available Trading Strategies

1. SMA Strategy
   - Uses Simple Moving Average crossovers
   - Configurable time windows
   - Trend following approach

2. MACD + RSI + Bollinger Bands
   - Combined technical indicator strategy
   - Multiple confirmation signals
   - Advanced market trend analysis

3. Pump Detection Strategy
   - Identifies potential market pumps
   - Volume and price spike analysis
   - Quick response to market movements

4. Dump Detection Strategy
   - Monitors for market dumps
   - Risk management focus
   - Recovery opportunity identification

## Monitoring Dashboard

The system includes a real-time web-based monitoring dashboard accessible at http://localhost:5000

### Dashboard Features
- Real-time agent status monitoring
- Live log streaming for each agent
- Error tracking and visualization
- Strategy execution results
- Market analysis updates

### Starting the Dashboard
```bash
# Start with other services
docker-compose up -d

# Start dashboard separately
docker-compose up -d dashboard
```

### Dashboard Sections

1. Strategy Finder Panel
   - Current strategy recommendations
   - Strategy selection reasoning
   - Market condition assessments

2. Market Analyzer Panel
   - Live market analysis results
   - Technical indicator readings
   - Market opportunity signals

3. Strategy Executor Panel
   - Active strategy status
   - Execution results
   - Performance metrics
   - Error logs

## Contributing

Contributions are welcome! Please feel free to submit issues and enhancement requests.

## License

[MIT License](LICENSE)

## Disclaimer

This software is for educational purposes only. Cryptocurrency trading carries significant risks. Always conduct your own research and risk assessment before trading.