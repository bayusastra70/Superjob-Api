from typing import Optional, List
import json
import httpx
import re
from io import BytesIO
from loguru import logger

from mistralai import Mistral

from app.core.config import settings
from app.schemas.cv_extraction import (
    CVExtractedData,
    ProfileData,
    WorkExperience,
    Education,
    Certification,
)


# Constants for AI input validation
MAX_PROMPT_LENGTH = (
    30000  # Maximum characters for prompt (safety margin for 32k context)
)
MIN_CV_CONTENT_LENGTH = 100  # Minimum meaningful CV content
PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|above|earlier)\s+(instructions|prompts|rules)",
    r"disregard\s+(all\s+)?(previous|above|earlier)\s+(instructions|prompts|rules)",
    r"forget\s+(all\s+)?(previous|above|earlier)\s+(instructions|prompts|rules)",
    r"system\s*:\s*",
    r"you\s+are\s+now\s+",
    r"new\s+instructions\s*:",
    r"override\s+(all\s+)?(previous|above|earlier)",
]


def validate_ai_input(
    prompt: str, cv_text: str, api_key: Optional[str], model: Optional[str]
) -> None:
    """
    Validate AI input before sending to Mistral API.

    Performs 5 validations:
    1. API Configuration Check - Ensure API key and model are configured
    2. Prompt Length Validation - Ensure prompt doesn't exceed context window
    3. Content Validation - Ensure CV has minimum meaningful content
    4. Encoding Validation - Ensure valid UTF-8 and no null bytes
    5. Prompt Injection Detection - Check for common injection patterns

    Args:
        prompt: The complete prompt to be sent to AI
        cv_text: The extracted CV text
        api_key: Mistral API key
        model: Mistral model name

    Raises:
        Exception: If any validation fails with descriptive message
    """
    # 1. API Configuration Check
    if not api_key:
        raise Exception("MISTRAL_API_KEY not configured")

    if not model:
        raise Exception("MISTRAL_MODEL not configured")

    # 2. Prompt Length Validation
    prompt_length = len(prompt)
    if prompt_length > MAX_PROMPT_LENGTH:
        raise Exception(
            f"Prompt too long: {prompt_length} characters (max: {MAX_PROMPT_LENGTH}). "
            f"CV text may be too large."
        )

    # 3. Content Validation - Check CV has meaningful content
    if not cv_text or len(cv_text.strip()) == 0:
        raise Exception("CV text is empty")

    # Count alphanumeric characters
    alphanumeric_count = sum(1 for c in cv_text if c.isalnum())
    if alphanumeric_count < MIN_CV_CONTENT_LENGTH:
        raise Exception(
            f"CV content too short: {alphanumeric_count} alphanumeric characters "
            f"(min: {MIN_CV_CONTENT_LENGTH}). CV may not contain valid text."
        )

    # 4. Encoding Validation
    try:
        # Check for null bytes
        if "\x00" in prompt or "\x00" in cv_text:
            raise Exception("Input contains null bytes")

        # Validate UTF-8 encoding by encoding and decoding
        prompt.encode("utf-8").decode("utf-8")
        cv_text.encode("utf-8").decode("utf-8")

    except UnicodeError as e:
        raise Exception(f"Invalid UTF-8 encoding in input: {e}")

    # 5. Prompt Injection Detection
    combined_text = (prompt + cv_text).lower()
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, combined_text, re.IGNORECASE):
            logger.warning(f"Potential prompt injection detected: pattern '{pattern}'")
            raise Exception(
                "Potential prompt injection detected in CV content. "
                "Please ensure the CV file is valid and not malicious."
            )

    logger.debug(
        f"AI input validation passed: prompt_length={prompt_length}, cv_alphanumeric={alphanumeric_count}"
    )


class CVExtractionService:
    def __init__(self):
        self.api_key = settings.MISTRAL_API_KEY
        self.model = settings.MISTRAL_MODEL
        self.client = Mistral(api_key=self.api_key)

    def extract_text_from_pdf(self, pdf_content: bytes) -> str:
        try:
            import pdfplumber

            with pdfplumber.open(BytesIO(pdf_content)) as pdf:
                text = ""
                for page in pdf.pages:
                    extracted_text = page.extract_text()
                    if extracted_text:
                        text += extracted_text + "\n"
                logger.info(f"Extracted {len(text)} characters from PDF")
                return text.strip()
        except ImportError:
            logger.error(
                "pdfplumber not installed. Install with: pip install pdfplumber"
            )
            raise Exception("PDF extraction library not available")
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise

    def _build_extraction_prompt(self) -> str:
        return """You are a CV/resume parser. Extract structured information from the CV text below and return ONLY a valid JSON object with this exact structure:

{
    "profile": {
        "full_name": "Full name of the candidate",
        "phone": "Phone number",
        "location": "City or country",
        "summary": "Professional summary"
    },
    "experience": [
        {
            "company": "Company name",
            "position": "Job title",
            "start_month": "Start month in Indonesian (Januari, Februari, Maret, April, Mei, Juni, Juli, Agustus, September, Oktober, November, Desember)",
            "start_year": "Start year (4 digits, e.g., 2020)",
            "end_month": "End month in Indonesian (leave null if current)",
            "end_year": "End year (4 digits, leave null if current)",
            "is_current": true or false,
            "description": "Key responsibilities and achievements"
        }
    ],
    "education": [
        {
            "institution": "School/University name",
            "degree": "Degree type in Indonesian (e.g., SD, SMP, SMA, Sarjana, Magister, Doktor)",
            "field": "Field of study",
            "start_month": "Start month in Indonesian",
            "start_year": "Start year (4 digits)",
            "end_month": "End month in Indonesian (leave null if currently studying)",
            "end_year": "End year (4 digits, leave null if currently studying)",
            "is_current": true or false,
            "description": "Additional description or achievements"
        }
    ],
    "skills": ["Skill 1", "Skill 2", "Skill 3"],
    "languages": ["Language 1", "Language 2"],
    "certifications": [
        {
            "name": "Certification name",
            "issuer": "Issuing organization",
            "issue_month": "Issue month in Indonesian",
            "issue_year": "Issue year (4 digits)"
        }
    ]
}

Rules:
1. Return ONLY valid JSON, no markdown, no explanations
2. If information is not found, use null for strings, empty array [] for lists
3. For experience, list most recent first
4. Include all skills mentioned (technical and soft skills)
5. Extract languages only if explicitly mentioned with proficiency level
6. For descriptions, capture key achievements and responsibilities
7. Do NOT extract email addresses from the CV
8. Month names MUST be in Indonesian: Januari, Februari, Maret, April, Mei, Juni, Juli, Agustus, September, Oktober, November, Desember
9. Years MUST be 4 digits (e.g., 2020, 2024)
10. If a position is current (still working there), set is_current to true and leave end_month/end_year as null
11. If currently studying, set is_current to true and leave end_month/end_year as null

CV Text:
"""

    async def _call_mistral_api(self, cv_text: str) -> str:
        prompt = self._build_extraction_prompt() + cv_text[:15000]

        # Validate AI input before making API call
        validate_ai_input(prompt, cv_text, self.api_key, self.model)

        try:
            if not self.model:
                raise Exception("MISTRAL_MODEL not configured")
            response = await self.client.chat.complete_async(
                model=self.model,  # type: ignore[arg-type]
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=4000,
            )

            content = response.choices[0].message.content
            if content is None:
                raise Exception("Mistral API returned empty response")
            return str(content)

        except Exception as e:
            logger.error(f"Mistral API call failed: {e}")
            raise Exception(f"Failed to call Mistral API")

    def _parse_json_response(self, raw_response: str) -> CVExtractedData:
        try:
            json_str = raw_response.strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]
            json_str = json_str.strip()

            data = json.loads(json_str)

            profile_data = None
            if data.get("profile"):
                profile_data = ProfileData(**data["profile"])

            experience = []
            for exp in data.get("experience", []):
                experience.append(WorkExperience(**exp))

            education = []
            for edu in data.get("education", []):
                education.append(Education(**edu))

            skills = data.get("skills", [])
            languages = data.get("languages", [])

            certifications = []
            for cert in data.get("certifications", []):
                certifications.append(Certification(**cert))

            return CVExtractedData(
                profile=profile_data,
                experience=experience,
                education=education,
                skills=skills,
                languages=languages,
                certifications=certifications,
            )
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Raw response: {raw_response[:500]}")
            raise Exception(f"Failed to parse AI response as JSON: {e}")
        except Exception as e:
            logger.error(f"Error parsing CV extraction response: {e}")
            raise

    async def extract_from_pdf_content(self, pdf_content: bytes) -> CVExtractedData:
        try:
            logger.info("Starting CV extraction process")
            start_time = __import__("time").time()

            cv_text = self.extract_text_from_pdf(pdf_content)
            if not cv_text:
                raise Exception("No text extracted from PDF")

            raw_response = await self._call_mistral_api(cv_text)
            extracted_data = self._parse_json_response(raw_response)

            elapsed = __import__("time").time() - start_time
            logger.info(f"CV extraction completed in {elapsed:.2f}s")

            return extracted_data
        except Exception as e:
            logger.error(f"CV extraction failed: {e}")
            raise

    async def extract_and_save(
        self, cv_url: str, user_id: int, db_connection=None
    ) -> Optional[CVExtractedData]:
        try:
            logger.info(f"Starting background CV extraction for user {user_id}")

            import httpx

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(cv_url)
                response.raise_for_status()
                pdf_content = response.content

            extracted_data = await self.extract_from_pdf_content(pdf_content)

            self._save_to_database(db_connection, user_id, cv_url, extracted_data)

            logger.info(f"Background CV extraction completed for user {user_id}")
            return extracted_data

        except Exception as e:
            logger.error(f"Background CV extraction failed for user {user_id}: {e}")
            self._update_error_status(db_connection, user_id, str(e))
            raise

    def _save_to_database(
        self, conn, user_id: int, cv_url: str, extracted_data: CVExtractedData
    ):
        try:
            from app.services.database import get_db_connection
            from datetime import datetime

            conn = get_db_connection()
            cursor = conn.cursor()

            profile_dict = (
                extracted_data.profile.model_dump() if extracted_data.profile else None
            )

            if profile_dict:
                extracted_full_name = profile_dict.get("full_name")
                extracted_phone = profile_dict.get("phone")

                if extracted_full_name:
                    cursor.execute(
                        """
                        UPDATE users
                        SET full_name = %s
                        WHERE id = %s AND (full_name IS NULL OR full_name = '')
                        """,
                        (extracted_full_name, user_id),
                    )

                if extracted_phone:
                    cursor.execute(
                        """
                        UPDATE users
                        SET phone = %s
                        WHERE id = %s AND (phone IS NULL OR phone = '')
                        """,
                        (extracted_phone, user_id),
                    )

                new_profile_dict = {
                    "summary": profile_dict.get("summary"),
                    "location": profile_dict.get("location"),
                }
            else:
                new_profile_dict = None

            experience_dict = [exp.model_dump() for exp in extracted_data.experience]
            education_dict = [edu.model_dump() for edu in extracted_data.education]
            certifications_dict = [
                cert.model_dump() for cert in extracted_data.certifications
            ]

            cursor.execute(
                """
                UPDATE candidate_info
                SET cv_extracted_profile = %s,
                    cv_extracted_experience = %s,
                    cv_extracted_education = %s,
                    cv_extracted_skills = %s,
                    cv_extracted_languages = %s,
                    cv_extracted_certifications = %s,
                    cv_extracted_at = %s,
                    cv_extraction_status = 'completed',
                    cv_extraction_error = NULL
                WHERE user_id = %s
            """,
                (
                    json.dumps(new_profile_dict) if new_profile_dict else None,
                    json.dumps(experience_dict),
                    json.dumps(education_dict),
                    extracted_data.skills,
                    extracted_data.languages,
                    json.dumps(certifications_dict),
                    datetime.utcnow(),
                    user_id,
                ),
            )

            conn.commit()
            logger.info(f"CV extraction data saved for user {user_id}")

        except Exception as e:
            logger.error(f"Error saving CV extraction to database: {e}")
            if conn:
                conn.rollback()

    def _update_error_status(self, conn, user_id: int, error_message: str):
        try:
            from app.services.database import get_db_connection

            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE candidate_info
                SET cv_extraction_status = 'failed',
                    cv_extraction_error = %s
                WHERE user_id = %s
            """,
                (error_message[:500], user_id),
            )

            conn.commit()
            logger.info(f"Updated error status for user {user_id}")

        except Exception as e:
            logger.error(f"Error updating error status: {e}")


cv_extraction_service = CVExtractionService()
