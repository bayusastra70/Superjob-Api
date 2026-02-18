import json
import requests
from typing import Dict, Any, List
from loguru import logger
from app.core.config import settings
from mistralai import Mistral

class SimpleAIGenerator:
    def __init__(self):
        # Pakai API key yang sudah ada di config
        self.api_key = settings.MISTRAL_API_KEY
        self.model = settings.MISTRAL_MODEL or "mistral-small-latest"
        
        if not self.api_key:
            logger.warning("MISTRAL_API_KEY not set. AI generator will return default templates.")
            self.client = None
        else:
            self.client = Mistral(api_key=self.api_key)
    
    async def generate_job_descriptions(self, job_data):
        """Generate menggunakan Mistral API"""
        if not self.client:
            return {
                "success": False,
                "data": self._get_default_templates(job_data),
                "error": "MISTRAL_API_KEY not configured"
            }
        try:
            prompt = self._build_prompt(job_data)
            
            response = self.client.chat.complete(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1000
            )
            
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
    

    async def generate_interview_questions(self, interview_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI interview questions"""
        if not self.client:
            return {
                "questions": self._get_default_questions(interview_data)
            }
        try:
            prompt = self._build_interview_prompt(interview_data)
            
            response = self.client.chat.complete(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1500
            )
            
            questions = self._parse_interview_response(response.choices[0].message.content)
            
            return {
                "questions": questions
            }
            
        except Exception as e:
            logger.error(f"Mistral API error for interview questions: {e}")
            return {
                "questions": self._get_default_questions(interview_data)
            }
    
    def _build_interview_prompt(self, interview_data: Dict[str, Any]) -> str:
        """Build prompt untuk interview questions"""
        title = interview_data.get('title', 'Posisi')
        dept = interview_data.get('department', 'IT')
        exp_level = interview_data.get('experience_level', 'Fresh Graduate')
        num_q = interview_data.get('num_questions', 5)
        q_type = interview_data.get('question_type', 'mixed')
        
        prompt = f"""
        Buat {num_q} pertanyaan interview dalam Bahasa Indonesia untuk posisi {title} 
        di departemen {dept} dengan level {exp_level}.
        
        Tipe pertanyaan: {q_type}
        
        Format output: Array JSON dengan string pertanyaan:
        [
            "Pertanyaan 1?",
            "Pertanyaan 2?",
            "Pertanyaan 3?"
        ]
        
        Aturan:
        1. Gunakan Bahasa Indonesia yang formal
        2. Pertanyaan harus relevan dengan posisi {title}
        3. Untuk technical positions, sertakan pertanyaan teknis
        4. Untuk behavioral, fokus pada soft skills
        5. Return HANYA array JSON, tidak ada penjelasan lain
        """
        
        # Customize based on question type
        if q_type == "technical":
            prompt += "\n6. Fokus pada pertanyaan teknis dan pengetahuan spesifik"
        elif q_type == "behavioral":
            prompt += "\n6. Fokus pada soft skills, teamwork, problem solving"
        
        return prompt
    
    def _parse_interview_response(self, response_text: str) -> List[str]:
        """Parse interview questions response"""
        try:
            import json
            # Cari array JSON
            start = response_text.find('[')
            end = response_text.rfind(']') + 1
            
            if start != -1 and end > start:
                json_str = response_text[start:end]
                questions = json.loads(json_str)
                
                # Validate and clean questions
                cleaned_questions = []
                for q in questions:
                    if isinstance(q, str) and len(q.strip()) > 5:
                        cleaned_questions.append(q.strip())
                
                if len(cleaned_questions) > 0:
                    return cleaned_questions
                    
        except Exception as e:
            logger.error(f"Failed to parse interview response: {e}")
        
        # Fallback
        return self._get_default_questions({})
    
    def _get_default_questions(self, interview_data: Dict[str, Any]) -> List[str]:
        """Default interview questions"""
        title = interview_data.get('title', 'Posisi')
        
        default_questions = [
            f"Ceritakan tentang pengalaman Anda terkait posisi {title}?",
            "Apa motivasi Anda melamar posisi ini?",
            "Bagaimana Anda menangani tekanan dalam pekerjaan?",
            "Ceritakan tentang pencapaian terbesar dalam karir Anda?",
            "Apa kelebihan dan kekurangan Anda?",
            "Bagaimana Anda bekerja dalam tim?",
            "Apa yang Anda ketahui tentang perusahaan kami?",
            "Di mana Anda melihat diri Anda dalam 5 tahun ke depan?",
            "Mengapa kami harus memilih Anda untuk posisi ini?",
            "Apa yang Anda harapkan dari atasan dan rekan kerja?"
        ]
        
        # Return based on requested number
        num_q = interview_data.get('num_questions', 5)
        return default_questions[:num_q]

# Singleton
ai_generator = SimpleAIGenerator()