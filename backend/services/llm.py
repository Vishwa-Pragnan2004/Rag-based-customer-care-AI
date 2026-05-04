import os
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.model_id = "Qwen/Qwen2.5-0.5B-Instruct"
        self.pipeline = None
        self._load_pipeline()

    def _load_pipeline(self):
        try:
            import torch
            from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
            
            logger.info(f"[LLM] Loading HuggingFace model '{self.model_id}' on CPU...")
            tokenizer = AutoTokenizer.from_pretrained(self.model_id)
            model = AutoModelForCausalLM.from_pretrained(
                self.model_id
            )
            self.pipeline = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                max_new_tokens=512,
                do_sample=True,
                temperature=0.2
            )
            logger.info(f"[LLM] HuggingFace: loaded '{self.model_id}' successfully")
        except Exception as e:
            logger.error(f"Failed to load HF pipeline: {e}")
            self.pipeline = None

    def complete(self, messages: List[Dict[str, str]], **kwargs) -> str:
        if not self.pipeline:
            return "Error: LLM pipeline not initialized. Ensure you have the required dependencies."
        
        try:
            prompt = ""
            for m in messages:
                role = m.get("role", "user")
                content = m.get("content", "")
                prompt += f"<|im_start|>{role}\n{content}<|im_end|>\n"
            prompt += "<|im_start|>assistant\n"
            
            outputs = self.pipeline(prompt, max_new_tokens=kwargs.get("max_tokens", 512), temperature=kwargs.get("temperature", 0.2))
            generated_text = outputs[0]["generated_text"]
            
            if "<|im_start|>assistant\n" in generated_text:
                answer = generated_text.split("<|im_start|>assistant\n")[-1].strip()
                if answer.endswith("<|im_end|>"):
                    answer = answer[:-9].strip()
                return answer
            return generated_text.strip()
        except Exception as e:
            logger.error(f"Generation error: {e}")
            return f"Error running local LLM: {str(e)}"
