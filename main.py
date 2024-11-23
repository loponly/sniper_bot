import asyncio
import os
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.task import Console, TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models import OpenAIChatCompletionClient
import redis
import json
from datetime import datetime
import logging
import yaml
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from typing import Dict, Any
from huggingface_hub import snapshot_download
from pathlib import Path
import shutil
from src.agents.code_executor_agent import CodeExecutorAgent

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis connection for inter-agent communication
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

async def execute_strategy(code: str) -> str:
    try:
        exec_globals = {}
        exec(code, exec_globals)
        result = "Strategy executed successfully"
        redis_client.publish('execution_results', json.dumps({
            'timestamp': datetime.now().isoformat(),
            'result': result
        }))
        return result
    except Exception as e:
        error_msg = f"Error executing strategy: {str(e)}"
        redis_client.publish('execution_errors', json.dumps({
            'timestamp': datetime.now().isoformat(),
            'error': error_msg
        }))
        return error_msg

async def analyze_market(data: dict) -> str:
    try:
        from src.analysis.market_analyzer import MarketAnalyzer
        analyzer = MarketAnalyzer()
        results = analyzer.analyze_market(
            symbol=data.get('symbol', 'BTCUSDT'),
            interval=data.get('interval', '1h'),
            start_date=data.get('start_date'),
            end_date=data.get('end_date'),
            volume_threshold=data.get('volume_threshold', 2.0),
            price_threshold=data.get('price_threshold', 0.03)
        )
        redis_client.publish('market_analysis', json.dumps({
            'timestamp': datetime.now().isoformat(),
            'results': str(results)
        }))
        return str(results)
    except Exception as e:
        error_msg = f"Error analyzing market: {str(e)}"
        redis_client.publish('analysis_errors', json.dumps({
            'timestamp': datetime.now().isoformat(),
            'error': error_msg
        }))
        return error_msg

def load_config():
    with open('config/agents_config.yaml', 'r') as file:
        return yaml.safe_load(file)

class ModelDownloader:
    def __init__(self, cache_dir: str = "/app/models"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def download_model(self, model_id: str) -> str:
        """Download model from Hugging Face and return local path"""
        try:
            logger.info(f"Downloading model: {model_id}")
            local_path = snapshot_download(
                repo_id=model_id,
                cache_dir=self.cache_dir,
                local_files_only=False  # Force download if not cached
            )
            logger.info(f"Model downloaded to: {local_path}")
            return local_path
        except Exception as e:
            logger.error(f"Error downloading model {model_id}: {e}")
            raise

class ModelManager:
    def __init__(self, model_name: str):
        self.downloader = ModelDownloader()
        self.model_path = self.downloader.download_model(model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            device_map="auto",  # Automatically handle device placement
            torch_dtype=torch.float16  # Use half precision for memory efficiency
        )
        self.model.eval()

    def generate_response(self, prompt: str, max_length: int = 512) -> str:
        try:
            inputs = self.tokenizer(prompt, return_tensors="pt", padding=True, truncation=True)
            inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs["input_ids"],
                    max_length=max_length,
                    num_return_sequences=1,
                    temperature=0.7,
                    pad_token_id=self.tokenizer.eos_token_id,
                    do_sample=True,
                    top_p=0.95
                )
            
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            return response
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return str(e)

class ContinuousAgent:
    def __init__(self, agent_type: str):
        self.agent_type = agent_type
        self.config = load_config()[agent_type]
        self.model = ModelManager(self.config['model'])
        self.agent = self._create_agent()
        
    def _create_agent(self) -> AssistantAgent:
        if self.agent_type == "strategy_finder":
            return AssistantAgent(
                name="strategy_finder",
                model_client=OpenAIChatCompletionClient(
                    model=self.config['model'],
                    api_key=os.getenv('OPENAI_API_KEY'),
                ),
                system_message=f"""You are a strategy finder. Your role is to:
                1. Analyze market conditions and requirements
                2. Select the most appropriate trading strategy from available options
                3. Provide strategy configuration parameters
                Monitor continuously and adapt strategies based on market conditions.
                
                Configuration Parameters:
                - Minimum confidence: {self.config['parameters']['min_confidence']}
                - Maximum strategies: {self.config['parameters']['max_strategies']}
                - Strategy timeout: {self.config['parameters']['strategy_timeout']} seconds"""
            )
        elif self.agent_type == "market_analyzer":
            return AssistantAgent(
                name="market_analyzer",
                model_client=OpenAIChatCompletionClient(
                    model=self.config['model'],
                    api_key=os.getenv('OPENAI_API_KEY'),
                ),
                system_message=f"""You are a market analysis specialist. Your role is to:
                1. Continuously analyze market data and patterns
                2. Identify potential opportunities and risks
                3. Provide real-time market insights
                
                Configuration Parameters:
                - Symbols: {self.config['parameters']['symbols']}
                - Timeframes: {self.config['parameters']['timeframes']}
                - Indicators: {self.config['parameters']['indicators']}""",
                tools=[analyze_market]
            )
        elif self.agent_type == "strategy_executor":
            return AssistantAgent(
                name="strategy_executor",
                model_client=OpenAIChatCompletionClient(
                    model=self.config['model'],
                    api_key=os.getenv('OPENAI_API_KEY'),
                ),
                system_message=f"""You are a strategy execution specialist. Your role is to:
                1. Execute strategies based on real-time market analysis
                2. Manage risk and position sizing
                3. Monitor and report execution results
                
                Configuration Parameters:
                - Maximum position size: {self.config['parameters']['max_position_size']}
                - Stop loss: {self.config['parameters']['stop_loss']}
                - Take profit: {self.config['parameters']['take_profit']}
                - Maximum trades per day: {self.config['parameters']['max_trades_per_day']}
                - Risk per trade: {self.config['parameters']['risk_per_trade']}""",
                tools=[execute_strategy]
            )
        elif self.agent_type == "code_executor":
            return CodeExecutorAgent(redis_client)

    async def run_continuous(self):
        while True:
            try:
                if self.agent_type == "code_executor":
                    await self.agent.run_continuous()
                elif self.agent_type == "strategy_finder":
                    await self._run_strategy_finder()
                elif self.agent_type == "market_analyzer":
                    await self._run_market_analyzer()
                elif self.agent_type == "strategy_executor":
                    await self._run_strategy_executor()
                
                await asyncio.sleep(int(os.getenv('AGENT_INTERVAL', 60)))
            except Exception as e:
                logger.error(f"Error in {self.agent_type}: {str(e)}")
                await asyncio.sleep(5)

    async def _run_strategy_finder(self):
        market_data = redis_client.get('market_analysis')
        if market_data:
            strategy = await self.agent.run(f"Analyze market data and recommend strategy: {market_data}")
            redis_client.set('selected_strategy', json.dumps(strategy))

    async def _run_market_analyzer(self):
        await self.agent.run("Analyze current market conditions")

    async def _run_strategy_executor(self):
        strategy = redis_client.get('selected_strategy')
        if strategy:
            await self.agent.run(f"Execute strategy: {strategy}")

async def main():
    agent_type = os.getenv('AGENT_TYPE')
    if not agent_type:
        raise ValueError("AGENT_TYPE environment variable must be set")

    agent = ContinuousAgent(agent_type)
    await agent.run_continuous()

if __name__ == "__main__":
    asyncio.run(main())