import json
import requests
from typing import Dict, Any
from loguru import logger
from app.core.config import settings
from mistralai import Mistral

class SimpleAIGenerator:
    def __init__(self):
        # Pakai API key yang sudah ada di config
        self.api_key = settings.MISTRAL_API_KEY
        self.model = settings.MISTRAL_MODEL or "mistral-small-latest"
        
        if not self.api_key:
            raise ValueError("MISTRAL_API_KEY not configured")
        
        self.client = Mistral(api_key=self.api_key)
    
    async def generate_job_descriptions(self, job_data):
        """Generate menggunakan Mistral API"""
        try:
            prompt = self._build_prompt(job_data)
            
            response = self.client.chat.complete(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1000
            )
            
            # return {
            #     "success": True,
            #     "data": self._parse_response(response.choices[0].message.content),
            #     "model": self.model,
            #     "provider": "mistral-api"
            # }
            result = self._parse_response(response.choices[0].message.content)
            return result;
            
        except Exception as e:
            logger.error(f"Mistral API error: {e}")
            return {
                "success": False,
                "data": self._get_default_templates(job_data),
                "error": str(e)
            }
    
    def _build_prompt(self, job_data):
        """Build prompt untuk Mistral"""
        title = job_data.get('title', 'Posisi')
        dept = job_data.get('department', 'IT')
        
        return f"""
        Buat deskripsi pekerjaan dalam Bahasa Indonesia untuk posisi {title} di departemen {dept}.
        
        Format output JSON:
        {{
            "description": "Deskripsi singkat tentang posisi...",
            "requirements": "Syarat dan kualifikasi...",
            "responsibilities": "Tanggung jawab pekerjaan...",
            "benefits": "Benefit yang ditawarkan..."
        }}
        
        Gunakan Bahasa Indonesia yang profesional.
        """
    
    def _parse_response(self, response_text):
        """Parse response"""
        try:
            import json
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            
            if start != -1 and end > start:
                data = json.loads(response_text[start:end])
                return {
                    "description": data.get("description", ""),
                    "requirements": data.get("requirements", ""),
                    "responsibilities": data.get("responsibilities", ""),
                    "benefits": data.get("benefits", "")
                }
        except:
            pass
        
        return {
            "description": response_text,
            "requirements": "",
            "responsibilities": "",
            "benefits": ""
        }
    
    def _get_default_templates(self, job_data):
        """Default templates"""
        title = job_data.get('title', 'Posisi')
        return {
            "description": f"Posisi {title} bertanggung jawab untuk mendukung operasional.",
            "requirements": f"Pendidikan sesuai dengan posisi {title}.",
            "responsibilities": f"Menjalankan tugas sesuai job description.",
            "benefits": "Gaji kompetitif."
        }

# Singleton
ai_generator = SimpleAIGenerator()