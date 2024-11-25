import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import asyncio
import ast
import os
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr
import autogen
from src.utils.local_db import LocalDatabase

class CodeExecutorAgent:
    def __init__(self, db: LocalDatabase, trading_mode):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.db = db
        self.trading_mode = trading_mode
        self.allowed_modules = {
            'pandas', 'numpy',
            'src.strategies', 'src.analysis', 'src.utils',
            'talib', 'sklearn', 'scipy'
        }
        
        # Initialize AutoGen configuration
        self.config_list = [
            {
                'model': os.getenv('CODE_EXECUTOR_MODEL', 'gpt-4'),
                'api_key': os.getenv('OPENAI_API_KEY'),
            }
        ]
        
        # Initialize AutoGen agents
        self.assistant = autogen.AssistantAgent(
            name="Python_Coder",
            llm_config={
                "config_list": self.config_list,
                "temperature": 0.7,
                "timeout": 120,
                "seed": 42,
                "functions": [{
                    "name": "python_code_generator",
                    "description": "Generate Python code with implementation and test sections",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "implementation": {
                                "type": "string",
                                "description": "The implementation code"
                            },
                            "test": {
                                "type": "string",
                                "description": "The test code"
                            }
                        },
                        "required": ["implementation", "test"]
                    }
                }]
            },
            system_message="""You are a Python coding assistant specialized in financial analysis.
            Generate clean, efficient code with proper documentation and error handling.
            Always structure your response with IMPLEMENTATION and TEST sections.
            
            Example format:
            IMPLEMENTATION:
            import pandas as pd
            import numpy as np
            
            def function_name():
                # Implementation
                pass
                
            TEST:
            # Test code
            """
        )
        
        self.executor = autogen.UserProxyAgent(
            name="Code_Executor",
            human_input_mode="NEVER",
            code_execution_config={
                "work_dir": "coding",
                "use_docker": False,
                "last_n_messages": 3,
                "timeout": 60,
            }
        )
        
        # Other configurations
        self.max_retries = int(os.getenv('CODE_EXECUTOR_MAX_RETRIES', '3'))
        self.allow_install = os.getenv('ALLOW_PACKAGE_INSTALL', 'True').lower() == 'true'
        self.trusted_packages = {
            'pandas', 'numpy', 'ta', 'scikit-learn', 'scipy',
            'talib', 'plotly', 'matplotlib', 'seaborn'
        }
        
        # Initialize restricted builtins
        self.restricted_builtins = {
            'print': print,
            'range': range,
            'len': len,
            'int': int,
            'float': float,
            'str': str,
            'list': list,
            'dict': dict,
            'set': set,
            'tuple': tuple,
            'sum': sum,
            'min': min,
            'max': max,
            'abs': abs,
            'round': round,
            'enumerate': enumerate,
            'zip': zip,
            'bool': bool,
            '__import__': __import__,
            'isinstance': isinstance,
        }

    async def execute_with_autogen(self, prompt: str) -> Tuple[str, Dict[str, Any]]:
        """Execute code using AutoGen agents"""
        try:
            # Create a more specific prompt
            enhanced_prompt = f"""
            Task: {prompt}
            
            Requirements:
            1. Provide the code in two clear sections: IMPLEMENTATION and TEST
            2. Ensure all imports are at the top
            3. Include proper error handling
            4. Add docstrings and comments
            5. Make the code production-ready
            
            Format your response exactly like this:
            IMPLEMENTATION:
            <your implementation code>
            
            TEST:
            <your test code>
            """
            
            # Initialize chat
            chat_messages = []
            
            # Direct conversation between assistant and executor
            await asyncio.to_thread(
                self.assistant.initiate_chat,
                self.executor,
                message=enhanced_prompt
            )
            
            # Get the last assistant message from the conversation
            last_message = None
            for msg in self.assistant.chat_messages:
                if msg.get("role") == "assistant":
                    last_message = msg.get("content")
            
            if last_message:
                # Clean and extract code
                code = self.clean_code(last_message)
                
                # Execute the code
                result = self.safe_execute(code)
                
                if not result['success']:
                    # Try to fix the code if execution failed
                    fix_prompt = f"""
                    The previous code had an error: {result['error']}
                    Please fix the code and ensure it runs correctly.
                    Original code:
                    {code}
                    """
                    
                    # Try to fix the code
                    await asyncio.to_thread(
                        self.assistant.initiate_chat,
                        self.executor,
                        message=fix_prompt
                    )
                    
                    # Get the fixed code from the last message
                    for msg in reversed(self.assistant.chat_messages):
                        if msg.get("role") == "assistant":
                            code = self.clean_code(msg.get("content"))
                            result = self.safe_execute(code)
                            break
                
                return code, result
            else:
                return None, {
                    'success': False,
                    'error': "No response from assistant",
                    'stdout': '',
                    'stderr': ''
                }
            
        except Exception as e:
            self.logger.error(f"Error in AutoGen execution: {str(e)}")
            return None, {
                'success': False,
                'error': str(e),
                'stdout': '',
                'stderr': str(e)
            }

    def clean_code(self, code: str) -> str:
        """Clean and format code"""
        try:
            # Extract code from markdown if present
            if "```python" in code:
                code = code.split("```python")[1].split("```")[0]
            elif "```" in code:
                code = code.split("```")[1].split("```")[0]
            
            # Split into implementation and test sections if present
            if 'IMPLEMENTATION:' in code and 'TEST:' in code:
                impl_part = code.split('IMPLEMENTATION:')[1].split('TEST:')[0].strip()
                test_part = code.split('TEST:')[1].strip()
                code = impl_part + '\n\n' + test_part
            
            # Remove any non-code lines and clean up
            code_lines = []
            for line in code.split('\n'):
                line = line.rstrip()
                if (line.strip() and 
                    not line.strip().startswith(('>', '-', '*', '#')) or 
                    'import' in line or 
                    'def ' in line or 
                    'class ' in line or
                    '=' in line or
                    'print(' in line or
                    'return ' in line):
                    code_lines.append(line)
            
            # Join lines and ensure proper spacing
            code = '\n'.join(code_lines)
            
            # Validate the code
            ast.parse(code)
            return code
            
        except Exception as e:
            self.logger.error(f"Error cleaning code: {str(e)}")
            raise

    def execute(self, prompt: str) -> str:
        """Main execution method"""
        try:
            # Log the execution attempt
            self.db.execute_query(
                "INSERT INTO executions (prompt, response, status) VALUES (?, ?, ?)",
                (prompt, "", "STARTED")
            )
            
            # Execute with AutoGen
            code, result = asyncio.run(self.execute_with_autogen(prompt))
            
            # Format the response
            response = f"```python\n{code}\n```\n\nExecution Result:\n"
            if result['success']:
                response += f"Output:\n{result['stdout']}\n"
                if result['stderr']:
                    response += f"Warnings:\n{result['stderr']}\n"
                if result.get('locals'):
                    response += f"\nDefined Functions/Variables:\n"
                    for name, value in result['locals'].items():
                        response += f"- {name}: {type(value).__name__}\n"
            else:
                response += f"Error:\n{result.get('detailed_error', result['error'])}\n"

            # Update the execution record
            self.db.execute_query(
                "UPDATE executions SET response = ?, status = ? WHERE id = last_insert_rowid()",
                (response, "COMPLETED" if result['success'] else "FAILED")
            )

            return response

        except Exception as e:
            self.logger.error(f"Error executing prompt: {str(e)}")
            self.db.execute_query(
                "UPDATE executions SET status = ?, response = ? WHERE id = last_insert_rowid()",
                ("FAILED", self.format_error(e, ''))
            )
            raise

    def safe_execute(self, code: str) -> Dict[str, Any]:
        """Execute code in a safe environment"""
        stdout_buffer = StringIO()
        stderr_buffer = StringIO()
        
        # Create a restricted globals dictionary with proper builtins
        safe_globals = {
            '__builtins__': self.restricted_builtins,
            '__name__': '__main__',
            '__file__': None,
        }
        
        # Pre-import common modules
        try:
            import pandas as pd
            import numpy as np
            safe_globals['pd'] = pd
            safe_globals['np'] = np
            
            # Import other allowed modules
            for module_name in self.allowed_modules:
                try:
                    if '.' in module_name:
                        base_module = module_name.split('.')[0]
                        module = __import__(module_name, fromlist=[base_module])
                    else:
                        module = __import__(module_name)
                    safe_globals[module_name.split('.')[-1]] = module
                except ImportError as e:
                    self.logger.warning(f"Could not import module {module_name}: {str(e)}")
        except ImportError as e:
            self.logger.error(f"Error importing required modules: {str(e)}")
            return {
                'success': False,
                'error': f"Required module not available: {str(e)}",
                'stdout': '',
                'stderr': 'Module import failed'
            }

        try:
            # Create a local namespace for execution
            local_namespace = {}
            
            with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
                # Execute the code
                exec(code, safe_globals, local_namespace)
                
            return {
                'success': True,
                'stdout': stdout_buffer.getvalue(),
                'stderr': stderr_buffer.getvalue(),
                'locals': {k: v for k, v in local_namespace.items() 
                         if not k.startswith('_')},
                'globals': {k: v for k, v in safe_globals.items() 
                          if k not in ['__builtins__', '__name__', '__file__'] 
                          and not k.startswith('_')}
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'stdout': stdout_buffer.getvalue(),
                'stderr': stderr_buffer.getvalue()
            }

    # ... (keep other existing methods like safe_execute, etc.)
