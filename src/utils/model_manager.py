import os
from typing import Dict, Any, Optional
import openai
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

class ModelManager:
    def __init__(self, model_config: Optional[Dict[str, Any]] = None):
        self.config = model_config or self._load_default_config()
        self.provider = self.config.get('LLM_PROVIDER', 'openai')
        self.model_name = self.config.get('LLM_MODEL', 'gpt-4')
        
        if self.provider == 'openai':
            openai.api_key = self.config.get('OPENAI_API_KEY')
            if org_id := self.config.get('OPENAI_ORG_ID'):
                openai.organization = org_id

    def _load_default_config(self) -> Dict[str, Any]:
        return {
            'LLM_PROVIDER': os.getenv('LLM_PROVIDER', 'openai'),
            'LLM_MODEL': os.getenv('LLM_MODEL', 'gpt-4'),
            'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
            'OPENAI_ORG_ID': os.getenv('OPENAI_ORG_ID'),
            'MODEL_MAX_TOKENS': int(os.getenv('MODEL_MAX_TOKENS', 8000)),
            'MODEL_TEMPERATURE': float(os.getenv('MODEL_TEMPERATURE', 0.7)),
            'MODEL_TOP_P': float(os.getenv('MODEL_TOP_P', 0.95)),
        }

    async def generate_response(self, 
                              prompt: str, 
                              max_tokens: Optional[int] = None,
                              temperature: Optional[float] = None) -> str:
        """Generate response using configured model"""
        if self.provider == 'openai':
            return await self._generate_openai(prompt, max_tokens, temperature)
        elif self.provider == 'huggingface':
            return await self._generate_huggingface(prompt, max_tokens, temperature)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    async def _generate_openai(self, 
                             prompt: str,
                             max_tokens: Optional[int] = None,
                             temperature: Optional[float] = None) -> str:
        """Generate response using OpenAI API"""
        try:
            response = await openai.ChatCompletion.acreate(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens or self.config.get('MODEL_MAX_TOKENS'),
                temperature=temperature or self.config.get('MODEL_TEMPERATURE'),
                top_p=self.config.get('MODEL_TOP_P'),
                frequency_penalty=self.config.get('MODEL_FREQUENCY_PENALTY', 0),
                presence_penalty=self.config.get('MODEL_PRESENCE_PENALTY', 0)
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")

    async def _generate_huggingface(self, 
                                  prompt: str,
                                  max_tokens: Optional[int] = None,
                                  temperature: Optional[float] = None) -> str:
        """Generate response using HuggingFace model"""
        try:
            tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            model = AutoModelForCausalLM.from_pretrained(self.model_name)
            
            inputs = tokenizer(prompt, return_tensors="pt", padding=True, truncation=True)
            
            outputs = model.generate(
                inputs["input_ids"],
                max_length=max_tokens or self.config.get('MODEL_MAX_TOKENS'),
                temperature=temperature or self.config.get('MODEL_TEMPERATURE'),
                top_p=self.config.get('MODEL_TOP_P'),
                do_sample=True
            )
            
            return tokenizer.decode(outputs[0], skip_special_tokens=True)
        except Exception as e:
            raise Exception(f"HuggingFace error: {str(e)}") 