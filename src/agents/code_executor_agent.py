import ast
import sys
import logging
from typing import Dict, Any, Optional
import traceback
from io import StringIO
import contextlib
import redis
import json
from datetime import datetime

class CodeExecutorAgent:
    def __init__(self, redis_client: redis.Redis):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.redis_client = redis_client
        self.allowed_modules = {
            'pandas', 'numpy', 'ta', 'sklearn', 
            'src.strategies', 'src.analysis', 'src.utils'
        }
        
    def validate_code(self, code: str) -> bool:
        """Validate code for security"""
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        if name.name.split('.')[0] not in self.allowed_modules:
                            return False
                elif isinstance(node, ast.ImportFrom):
                    if node.module.split('.')[0] not in self.allowed_modules:
                        return False
            return True
        except SyntaxError:
            return False

    @contextlib.contextmanager
    def capture_output(self):
        """Capture stdout and stderr"""
        new_out, new_err = StringIO(), StringIO()
        old_out, old_err = sys.stdout, sys.stderr
        try:
            sys.stdout, sys.stderr = new_out, new_err
            yield sys.stdout, sys.stderr
        finally:
            sys.stdout, sys.stderr = old_out, old_err

    def execute_code(self, code: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute code safely and return results"""
        if not self.validate_code(code):
            error_msg = "Code validation failed: Unauthorized imports or operations"
            self.publish_result(success=False, error=error_msg)
            return {"success": False, "error": error_msg}

        local_vars = context or {}
        
        try:
            with self.capture_output() as (out, err):
                exec(code, local_vars)
                
            result = {
                "success": True,
                "output": out.getvalue(),
                "error": err.getvalue(),
                "variables": {
                    k: v for k, v in local_vars.items() 
                    if not k.startswith('__') and k != 'code'
                }
            }
            
            self.publish_result(success=True, result=result)
            return result
            
        except Exception as e:
            error_msg = f"Execution error: {str(e)}\n{traceback.format_exc()}"
            self.publish_result(success=False, error=error_msg)
            return {"success": False, "error": error_msg}

    def publish_result(self, success: bool, result: Dict = None, error: str = None):
        """Publish execution results to Redis"""
        message = {
            'timestamp': datetime.now().isoformat(),
            'success': success,
            'type': 'execution_result'
        }
        
        if success and result:
            message['result'] = result
        if error:
            message['error'] = error
            
        self.redis_client.publish('code_execution', json.dumps(message))

    def run_strategy_code(self, strategy_code: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute strategy code with market data context"""
        context = {
            'market_data': market_data,
            'pd': __import__('pandas'),
            'np': __import__('numpy'),
            'ta': __import__('ta')
        }
        return self.execute_code(strategy_code, context)

    async def run_continuous(self):
        """Run continuously to execute code from Redis queue"""
        self.logger.info("Starting Code Executor Agent")
        
        while True:
            try:
                # Get code from Redis queue
                code_data = self.redis_client.brpop('code_execution_queue', timeout=1)
                
                if code_data:
                    _, code_str = code_data
                    code_info = json.loads(code_str)
                    
                    # Execute code with appropriate context
                    if code_info.get('type') == 'strategy':
                        result = self.run_strategy_code(
                            code_info['code'],
                            code_info.get('market_data', {})
                        )
                    else:
                        result = self.execute_code(code_info['code'])
                    
                    # Store result
                    result_key = f"execution_result:{code_info.get('id', datetime.now().isoformat())}"
                    self.redis_client.setex(result_key, 3600, json.dumps(result))  # Expire in 1 hour
                    
            except Exception as e:
                self.logger.error(f"Error in code execution loop: {str(e)}")
                self.publish_result(success=False, error=str(e)) 