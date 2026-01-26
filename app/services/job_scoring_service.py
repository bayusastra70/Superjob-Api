# app/services/job_scoring_service.py
from loguru import logger
from typing import Dict, List, Optional, Any
from datetime import datetime
from decimal import Decimal
from app.services.database import get_db_connection




class JobScoringService:
    def __init__(self):
        self.scoring_criteria = self._initialize_scoring_criteria()
        self.category_weights = {
            "basic_info": 0.30,      # 30%
            "job_details": 0.25,     # 25% 
            "requirements": 0.20,    # 20%
            "salary": 0.15,          # 15%
            "contact": 0.05,         # 5%
            "ai_interview": 0.05     # 5% - Bonus
        }

    def _initialize_scoring_criteria(self) -> List[Dict]:
        """Initialize scoring criteria"""
        return [
            # 1. BASIC INFORMATION (30%)
            {"category": "basic_info", "name": "Job Title", "field": "title", "weight": 0.05, "required": True},
            {"category": "basic_info", "name": "Job Code", "field": "job_code", "weight": 0.02, "required": False},
            {"category": "basic_info", "name": "Department", "field": "department", "weight": 0.04, "required": True},
            {"category": "basic_info", "name": "Location", "field": "location", "weight": 0.04, "required": True},
            {"category": "basic_info", "name": "Industry", "field": "industry", "weight": 0.04, "required": True},  # Required based on your data
            {"category": "basic_info", "name": "Employment Type", "field": "employment_type", "weight": 0.03, "required": True},
            {"category": "basic_info", "name": "Working Type", "field": "working_type", "weight": 0.03, "required": True},

            # 2. JOB DETAILS (25%)
            {"category": "job_details", "name": "Job Description", "field": "description", "weight": 0.10, "required": True},
            {"category": "job_details", "name": "Responsibilities", "field": "responsibilities", "weight": 0.07, "required": True},
            {"category": "job_details", "name": "Qualifications", "field": "qualifications", "weight": 0.05, "required": True},
            {"category": "job_details", "name": "Benefits", "field": "benefits", "weight": 0.03, "required": False},

            # 3. REQUIREMENTS (20%)
            {"category": "requirements", "name": "Experience Level", "field": "experience_level", "weight": 0.05, "required": True},
            {"category": "requirements", "name": "Education Requirement", "field": "education_requirement", "weight": 0.04, "required": True},
            {"category": "requirements", "name": "Major", "field": "major", "weight": 0.03, "required": False},
            {"category": "requirements", "name": "Gender Requirement", "field": "gender_requirement", "weight": 0.02, "required": False},
            {"category": "requirements", "name": "Age Range", "field": "age_range", "weight": 0.03, "required": False},
            {"category": "requirements", "name": "Requirements", "field": "requirements", "weight": 0.03, "required": True},

            # 4. SALARY INFORMATION (15%)
            {"category": "salary", "name": "Salary Range", "field": "salary_range", "weight": 0.04, "required": False},
            {"category": "salary", "name": "Min Salary", "field": "salary_min", "weight": 0.04, "required": True},
            {"category": "salary", "name": "Max Salary", "field": "salary_max", "weight": 0.04, "required": True},
            {"category": "salary", "name": "Salary Currency", "field": "salary_currency", "weight": 0.02, "required": False},
            {"category": "salary", "name": "Salary Interval", "field": "salary_interval", "weight": 0.01, "required": False},

            # 5. CONTACT INFORMATION (5%)
            {"category": "contact", "name": "Contact URL", "field": "contact_url", "weight": 0.03, "required": False},
            {"category": "contact", "name": "Tags", "field": "tags", "weight": 0.02, "required": False},

            # 6. AI INTERVIEW (5% - Bonus)
            {"category": "ai_interview", "name": "AI Interview Enabled", "field": "ai_interview_enabled", 
             "weight": 0.03, "required": False, "is_bonus": True, "bonus_value": 5},
            {"category": "ai_interview", "name": "AI Interview Questions", "field": "ai_interview_questions", 
             "weight": 0.02, "required": False, "is_bonus": True, "bonus_value": 5}
        ]

    def calculate_job_score(self, job_id: int) -> Dict[str, Any]:
        """Calculate job score - FINAL SIMPLE VERSION"""
        try:
            # Get job data
            job_data = self._get_complete_job_data(job_id)
            if not job_data:
                raise ValueError(f"Job with ID {job_id} not found")

            # Initialize
            criteria_details = []
            missing_fields = []
            recommendations = []
            
            # Track per category
            category_scores = {category: {"score": 0, "max": 0} for category in self.category_weights}
            
            base_criteria_count = 0
            base_criteria_met = 0
            bonuses = 0

            # Process each criteria
            for criteria in self.scoring_criteria:
                field_name = criteria["field"]
                field_value = job_data.get(field_name)
                category = criteria["category"]
                weight = criteria["weight"]
                is_bonus = criteria.get("is_bonus", False)
                required = criteria.get("required", False)
                
                # Check completeness
                is_met = self._check_field_completeness(field_name, field_value, criteria)
                
                # Add to criteria details
                criteria_details.append({
                    "category": category,
                    "criteria": criteria["name"],
                    "field_name": field_name,
                    "weight": weight,
                    "score": 100 if is_met else 0,
                    "is_met": is_met,
                    "suggestion": self._generate_suggestion(criteria, field_value) if not is_met else None,
                    "max_score": 100
                })
                
                # Track missing fields
                if not is_met and required:
                    missing_fields.append(criteria["name"])
                
                # Calculate scores
                if not is_bonus:
                    # Base criteria
                    base_criteria_count += 1
                    if is_met:
                        base_criteria_met += 1
                    
                    # Category scoring: tambah score jika terpenuhi
                    if is_met:
                        category_scores[category]["score"] += weight * 100  # Weight dalam persen
                    category_scores[category]["max"] += weight * 100  # Maximum possible
                else:
                    # Bonus
                    if is_met:
                        bonuses += criteria.get("bonus_value", 0)
            
            # 1. Calculate CATEGORY SCORES (0-100)
            final_category_scores = {}
            for category in self.category_weights:
                if category_scores[category]["max"] > 0:
                    percentage = (category_scores[category]["score"] / category_scores[category]["max"]) * 100
                    final_category_scores[category] = round(percentage, 2)
                else:
                    final_category_scores[category] = 0
            
            # 2. Calculate BASE SCORE (weighted average dari category scores kecuali ai_interview)
            base_score = 0
            total_weight_for_base = 0
            
            for category in self.category_weights:
                if category != "ai_interview":  # ai_interview adalah bonus, bukan bagian base
                    weight = self.category_weights[category]
                    base_score += final_category_scores[category] * weight  # category_score * weight
                    total_weight_for_base += weight
            
            # Normalize base_score
            if total_weight_for_base > 0:
                base_score = base_score / total_weight_for_base
            
            # 3. Calculate OVERALL SCORE dengan bonus (max 100)
            overall_score = min(base_score + bonuses, 100)
            
            # 4. Calculate COMPLETION RATE
            completion_rate = 0
            if base_criteria_count > 0:
                completion_rate = (base_criteria_met / base_criteria_count) * 100
            
            # 5. Quality label
            quality_label = self._get_quality_label(overall_score)
            
            # 6. Add recommendations
            self._add_specific_recommendations(recommendations, job_data, missing_fields)
            
            # Debug log
            logger.info(f"""
            FINAL CALCULATION for job {job_id}:
            - Category scores: {final_category_scores}
            - Base score (weighted avg): {base_score:.2f}
            - Bonuses: {bonuses}
            - Overall: {overall_score:.2f}
            - Completion: {completion_rate:.2f}
            """)
            
            return {
                "job_id": job_id,
                "job_title": job_data.get("title", "Unknown"),
                "job_code": job_data.get("job_code"),
                "score": round(overall_score, 2),
                "grade": quality_label,
                "completion_rate": round(completion_rate, 2),
                "meta": {
                    "job_status": job_data.get("status", "draft"),
                    "has_salary": bool(job_data.get("salary_min") and job_data.get("salary_max")),
                    "has_ai_interview": job_data.get("ai_interview_enabled", False),
                    "base_score": round(base_score, 2),  # HARUSNYA sekitar 70-80
                    "bonuses_applied": bonuses,
                    "total_criteria_evaluated": base_criteria_met,
                    "total_possible_criteria": base_criteria_count,
                    # "debug_info": {
                    #     "category_weights": self.category_weights,
                    #     "category_scores_calculated": final_category_scores,
                    #     "bonus_details": {
                    #         "ai_interview_enabled": job_data.get("ai_interview_enabled", False),
                    #         "bonus_value": bonuses
                    #     }
                    # }
                },
                "category_scores": final_category_scores,
                # "criteria_details": criteria_details,
                "category_weights": self.category_weights,
                "recommendations": recommendations,
                "missing_fields": missing_fields,
                "scored_at": datetime.now()
            }

        except Exception as e:
            logger.error(f"Error calculating job score for job {job_id}: {str(e)}")
            raise

    def _get_complete_job_data(self, job_id: int) -> Optional[Dict]:
        """Get complete job data"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            query = """
            SELECT 
                j.*,
                CASE 
                    WHEN j.min_age IS NOT NULL AND j.max_age IS NOT NULL 
                    THEN CONCAT(j.min_age::text, ' - ', j.max_age::text)
                    ELSE NULL 
                END as age_range,
                CASE 
                    WHEN j.salary_min IS NOT NULL AND j.salary_max IS NOT NULL 
                    THEN CONCAT(j.salary_currency, ' ', j.salary_min::text, ' - ', j.salary_currency, ' ', j.salary_max::text)
                    ELSE NULL 
                END as salary_range
            FROM jobs j
            WHERE j.id = %s
            """
            
            cursor.execute(query, (job_id,))
            result = cursor.fetchone()
            return dict(result) if result else None

        except Exception as e:
            logger.error(f"Error getting job data {job_id}: {str(e)}")
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def _check_field_completeness(self, field_name: str, value: Any, criteria: Dict) -> bool:
        """Check if field is complete"""
        if value is None:
            return False
        
        if isinstance(value, str):
            value = value.strip()
            if not value or value.lower() in ['', 'null', 'undefined', 'none']:
                return False
            
            # Check length for important fields
            if field_name in ['description', 'responsibilities', 'qualifications']:
                if len(value) < 50:  # Minimum 50 characters
                    return False
            
            if field_name == 'salary_range' and ('0' in value or 'null' in value.lower()):
                return False
        
        elif isinstance(value, (int, float, Decimal)):
            if field_name in ['salary_min', 'salary_max']:
                if value <= 0:
                    return False
            elif field_name in ['min_age', 'max_age']:
                if value <= 0:
                    return False
        
        elif isinstance(value, bool):
            return True
        
        return True

    def _generate_suggestion(self, criteria: Dict, value: Any) -> Optional[str]:
        """Generate suggestion"""
        field_name = criteria["field"]
        suggestions = {
            "title": "Tambahkan judul pekerjaan yang jelas dan spesifik",
            "description": "Perjelas deskripsi pekerjaan dengan detail tugas",
            "industry": "Sebutkan industri perusahaan",
            "salary_min": "Cantumkan gaji minimum yang kompetitif",
            "salary_max": "Tentukan gaji maksimum yang ditawarkan"
        }
        return suggestions.get(field_name)

    def _calculate_completion_rate(self, criteria_details: List[Dict]) -> float:
        """Calculate completion rate"""
        if not criteria_details:
            return 0
        
        # Only base criteria for completion rate
        base_criteria = [c for c in criteria_details if not c.get("is_bonus", False)]
        if not base_criteria:
            return 0
        
        completed = sum(1 for c in base_criteria if c["is_met"])
        total = len(base_criteria)
        
        return round((completed / total) * 100, 2) if total > 0 else 0

    def _get_quality_label(self, score: float) -> str:
        """Get quality label"""
        if score >= 85:
            return "excellent"
        elif score >= 70:
            return "good"
        elif score >= 50:
            return "fair"
        else:
            return "poor"

    def _add_specific_recommendations(self, recommendations: List[str], job_data: Dict, missing_fields: List[str]):
        """Add comprehensive recommendations"""
        
        # 1. PRIORITAS TINGGI - Field yang sangat penting
        if not job_data.get("description") or job_data.get("description", "").strip() == "":
            recommendations.append(
                "Tambahkan deskripsi pekerjaan yang jelas dan detail"
            )
        
        if not job_data.get("responsibilities") or job_data.get("responsibilities", "").strip() == "":
            recommendations.append(
                "Daftarkan tanggung jawab pekerjaan secara spesifik"
            )
        
        if not job_data.get("qualifications"):
            recommendations.append(
                "Sebutkan kualifikasi yang dibutuhkan dengan jelas"
            )
        
        # 2. PRIORITAS MENENGAH - Field penting untuk kualitas
        if not job_data.get("salary_min") or not job_data.get("salary_max"):
            recommendations.append(
                "Cantumkan rentang gaji yang kompetitif - Dapat meningkatkan pelamar hingga 30%"
            )
        
        if not job_data.get("industry"):
            recommendations.append(
                "Sebutkan industri perusahaan untuk konteks yang lebih baik"
            )
        
        # 3. FITUR PREMIUM - Optional tapi bernilai tinggi
        if not job_data.get("ai_interview_enabled"):
            recommendations.append(
                "Aktifkan AI Interview untuk proses seleksi otomatis"
            )
        
        # 4. DETAIL TAMBAHAN - Untuk kualitas maksimal
        if not job_data.get("benefits"):
            recommendations.append(
                "Sebutkan benefit dan keuntungan bekerja di perusahaan ini"
            )
        
        if not job_data.get("contact_url"):
            recommendations.append(
                "Tambahkan URL untuk informasi lebih lanjut atau proses lamaran"
            )

    def get_employer_scoring_overview(self, employer_id: int) -> Dict[str, Any]:
        """Get scoring overview for employer"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            query = """
            SELECT id, title, status, created_at
            FROM jobs 
            WHERE created_by = %s AND status IN ('published', 'draft')
            ORDER BY created_at DESC
            """
            
            cursor.execute(query, (employer_id,))
            jobs = cursor.fetchall()

            if not jobs:
                return {
                    "employer_id": employer_id,
                    "average_score": 0,
                    "total_jobs": 0,
                    "quality_distribution": {},
                    "category_averages": {},
                    "top_performers": [],
                    "needs_improvement": [],
                    "completion_stats": {},
                    "scored_jobs_count": 0
                }

            all_scores = []
            quality_distribution = {"Excellent": 0, "Good": 0, "Fair": 0, "Poor": 0}
            category_totals = {category: {"sum": 0, "count": 0} for category in self.category_weights}
            top_performers = []
            needs_improvement = []
            completion_rates = []

            for job in jobs:
                try:
                    score_data = self.calculate_job_score(job["id"])
                    all_scores.append(score_data["overall_score"])
                    completion_rates.append(score_data["completion_rate"])
                    
                    # Update distributions
                    quality_label = score_data["quality_label"]
                    if quality_label in quality_distribution:
                        quality_distribution[quality_label] += 1
                    
                    # Category averages
                    for category, score in score_data["category_scores"].items():
                        if category in category_totals:
                            category_totals[category]["sum"] += score
                            category_totals[category]["count"] += 1
                    
                    # Top/needs lists
                    job_info = {
                        "job_id": job["id"],
                        "title": job["title"],
                        "status": job["status"],
                        "score": score_data["overall_score"],
                        "quality_label": quality_label,
                        "completion_rate": score_data["completion_rate"]
                    }
                    
                    if score_data["overall_score"] >= 80:
                        top_performers.append(job_info)
                    elif score_data["overall_score"] < 60:
                        needs_improvement.append(job_info)

                except Exception as e:
                    logger.error(f"Error scoring job {job['id']}: {str(e)}")
                    continue

            # Calculate averages
            avg_score = round(sum(all_scores) / len(all_scores), 2) if all_scores else 0
            avg_completion = round(sum(completion_rates) / len(completion_rates), 2) if completion_rates else 0
            
            # Category averages
            category_averages = {}
            for category, totals in category_totals.items():
                if totals["count"] > 0:
                    category_averages[category] = round(totals["sum"] / totals["count"], 2)
                else:
                    category_averages[category] = 0
            
            # Sort lists
            top_performers.sort(key=lambda x: x["score"], reverse=True)
            needs_improvement.sort(key=lambda x: x["score"])
            
            # Completion stats
            fully_completed = sum(1 for rate in completion_rates if rate >= 90)
            partially_completed = sum(1 for rate in completion_rates if 50 <= rate < 90)

            return {
                "employer_id": employer_id,
                "average_score": avg_score,
                "total_jobs": len(jobs),
                "quality_distribution": quality_distribution,
                "category_averages": category_averages,
                "top_performers": top_performers[:5],
                "needs_improvement": needs_improvement[:5],
                "completion_stats": {
                    "average_completion": avg_completion,
                    "fully_completed": fully_completed,
                    "partially_completed": partially_completed,
                    "incomplete": len(jobs) - (fully_completed + partially_completed)
                },
                "scored_jobs_count": len(all_scores)
            }

        except Exception as e:
            logger.error(f"Error getting employer scoring overview {employer_id}: {str(e)}")
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()