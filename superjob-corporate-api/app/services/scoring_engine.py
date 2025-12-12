import logging
from typing import Dict, Any, Optional
import random

logger = logging.getLogger(__name__)

class ScoringEngine:
    def __init__(self):
        self.weights = {
            'skill': 0.6,      # 60%
            'experience': 0.3,  # 30%
            'education': 0.1    # 10%
        }
    
    def calculate_fit_score(self, application_id: int, job_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate fit score for a candidate application
        MVP: Using dummy/random scoring
        Future: Integrate with ML model
        """
        try:
            # Dummy scoring logic - replace with actual algorithm
            skill_score = self._calculate_skill_match(job_requirements)
            experience_score = self._calculate_experience_match(job_requirements)
            education_score = self._calculate_education_match(job_requirements)
            
            # Calculate weighted fit score
            fit_score = (
                skill_score * self.weights['skill'] +
                experience_score * self.weights['experience'] +
                education_score * self.weights['education']
            )
            
            reasons = {
                "skill_match": f"Skill compatibility: {skill_score:.1f}%",
                "experience_match": f"Experience relevance: {experience_score:.1f}%",
                "education_match": f"Education alignment: {education_score:.1f}%",
                "summary": "Score calculated based on skill, experience, and education match"
            }
            
            return {
                "fit_score": round(fit_score, 2),
                "skill_score": round(skill_score, 2),
                "experience_score": round(experience_score, 2),
                "education_score": round(education_score, 2),
                "reasons": reasons
            }
            
        except Exception as e:
            logger.error(f"Error calculating fit score for application {application_id}: {e}")
            # Return default score in case of error
            return {
                "fit_score": 50.0,
                "skill_score": 50.0,
                "experience_score": 50.0,
                "education_score": 50.0,
                "reasons": {"error": "Scoring temporarily unavailable, using default score"}
            }
    
    def _calculate_skill_match(self, job_requirements: Dict[str, Any]) -> float:
        """Calculate skill match score (dummy implementation)"""
        # TODO: Implement actual skill matching logic
        return random.uniform(60, 95)
    
    def _calculate_experience_match(self, job_requirements: Dict[str, Any]) -> float:
        """Calculate experience match score (dummy implementation)"""
        # TODO: Implement actual experience matching logic
        return random.uniform(50, 90)
    
    def _calculate_education_match(self, job_requirements: Dict[str, Any]) -> float:
        """Calculate education match score (dummy implementation)"""
        # TODO: Implement actual education matching logic
        return random.uniform(70, 100)
    
    # def trigger_scoring(self, application_id: int, job_id: int):
    #     """
    #     Trigger scoring calculation for an application
    #     This would be called by event handlers
    #     """
    #     from app.services.candidate_service import CandidateService
    #     from app.schemas.candidate import CandidateScoreCreate
        
    #     try:
    #         # Get job requirements (dummy data for now)
    #         job_requirements = self._get_job_requirements(job_id)
            
    #         # Calculate scores
    #         scores = self.calculate_fit_score(application_id, job_requirements)
            
    #         # Save to database
    #         candidate_service = CandidateService()
    #         score_data = CandidateScoreCreate(
    #             application_id=application_id,
    #             fit_score=scores["fit_score"],
    #             skill_score=scores["skill_score"],
    #             experience_score=scores["experience_score"],
    #             education_score=scores["education_score"],
    #             reasons=scores["reasons"]
    #         )
            
    #         candidate_service.save_candidate_score(score_data)
    #         logger.info(f"Score calculated for application {application_id}")
            
    #     except Exception as e:
    #         logger.error(f"Error triggering scoring for application {application_id}: {e}")

    def trigger_scoring(self, application_id: int, job_id: int, candidate_name: str = "Test Candidate"):
        """
        Trigger scoring calculation untuk testing
        """
        from app.services.candidate_service import CandidateService
        from app.schemas.candidate import CandidateScoreCreate
        
        try:
            # Get job requirements (dummy data for testing)
            job_requirements = self._get_job_requirements(job_id)
            
            # Calculate scores
            scores = self.calculate_fit_score(application_id, job_requirements)
            
            # Save to database
            candidate_service = CandidateService()
            score_data = CandidateScoreCreate(
                application_id=application_id,
                fit_score=scores["fit_score"],
                skill_score=scores["skill_score"],
                experience_score=scores["experience_score"],
                education_score=scores["education_score"],
                reasons=scores["reasons"]
            )
            
            candidate_service.save_candidate_score(score_data, job_id, candidate_name)
            logger.info(f"Score calculated for application {application_id}")
            
        except Exception as e:
            logger.error(f"Error triggering scoring for application {application_id}: {e}")
    
    def _get_job_requirements(self, job_id: int) -> Dict[str, Any]:
        """Get job requirements from Odoo (dummy implementation)"""
        # TODO: Implement actual job requirements fetching from Odoo
        return {
            "required_skills": ["Python", "FastAPI", "PostgreSQL"],
            "min_experience": 2,
            "education_level": "Bachelor",
            "job_level": "Mid"
        }