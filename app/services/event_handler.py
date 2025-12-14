import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class EventHandler:
    def __init__(self):
        self.scoring_engine = None
    
    def handle_new_application(self, application_id: int, job_id: int):
        """Handle new candidate application"""
        try:
            from app.services.scoring_engine import ScoringEngine
            self.scoring_engine = ScoringEngine()
            self.scoring_engine.trigger_scoring(application_id, job_id)
            logger.info(f"Scoring triggered for new application {application_id}")
        except Exception as e:
            logger.error(f"Error handling new application: {e}")
    
    def handle_cv_update(self, application_id: int, job_id: int):
        """Handle CV update event"""
        try:
            from app.services.scoring_engine import ScoringEngine
            self.scoring_engine = ScoringEngine()
            self.scoring_engine.trigger_scoring(application_id, job_id)
            logger.info(f"Scoring triggered for CV update {application_id}")
        except Exception as e:
            logger.error(f"Error handling CV update: {e}")

# Global event handler instance
event_handler = EventHandler()