import json
import logging
import os
from utils.helpers import get_db_connection
from utils.llm_client import LLMClient
from utils.skill_matcher import SkillMatcher

class JobRankingAgent:
    """
    Agent responsible for scoring and ranking jobs based on user profile and resume skills.
    """
    
    def __init__(self, resume_skills=None):
        self.logger = logging.getLogger("JobRankingAgent")
        self.profile = self._load_profile()
        self.llm_client = LLMClient()
        self.skill_matcher = SkillMatcher()
        self.resume_skills = resume_skills or []

    def _load_profile(self):
        """Loads user profile from JSON file."""
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'user_profile.json')
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load user profile: {e}")
            return {}

    def calculate_score(self, job):
        """
        Calculates a relevance score for a job using both LLM and skill matching.
        Returns (final_score, reasons_list, skill_details).
        """
        
        # 1. Calculate skill-based score if we have resume skills and job skills
        skill_score = 0
        skill_details = {}
        skill_reasons = []
        
        if self.resume_skills:
            # Parse job required skills from database
            job_skills = []
            if job.get('required_skills'):
                try:
                    job_skills = json.loads(job['required_skills'])
                except:
                    pass
            
            if job_skills:
                skill_score, skill_details = self.skill_matcher.calculate_skill_similarity(
                    self.resume_skills, job_skills
                )
                
                # Generate skill-based reasons
                matched = skill_details.get('matched_skills', [])
                missing = skill_details.get('missing_skills', [])
                
                if matched:
                    skill_reasons.append(f"Skills match: {', '.join(matched[:3])}")
                    if len(matched) > 3:
                        skill_reasons[-1] += f" (+{len(matched)-3} more)"
                
                if missing and len(missing) <= 3:
                    skill_reasons.append(f"Missing: {', '.join(missing)}")
                elif missing:
                    skill_reasons.append(f"Missing {len(missing)} skills")
        
        # 2. Calculate LLM-based profile score
        profile_str = json.dumps(self.profile, indent=2)
        job_str = json.dumps({
            "title": job['title'],
            "location": job['location'],
        }, indent=2)
        
        system_prompt = """You are an expert Job Matching AI. Your task is to evaluate how well a job matches a candidate's profile.
        
        Output strictly in JSON format with the following keys:
        - "score": An integer from 0 to 10 (10 being a perfect match).
        - "reasons": A list of short strings explaining the score.
        
        Scoring Criteria:
        - 10: Perfect match for Role, Location, and Tech Stack/Keywords.
        - 7-9: Good match, minor differences (e.g. location slightly off but remote possible).
        - 4-6: Partial match.
        - 0-3: Poor match (wrong role, wrong location).
        """
        
        user_prompt = f"""
        Candidate Profile:
        {profile_str}
        
        Job Details:
        {job_str}
        
        Evaluate the match:
        """
        
        # Call LLM
        response_text = self.llm_client.generate_response(user_prompt, system_prompt=system_prompt)
        
        # Parse Response
        llm_score = 0
        llm_reasons = []
        
        if response_text:
            try:
                cleaned_text = response_text.replace("```json", "").replace("```", "").strip()
                data = json.loads(cleaned_text)
                llm_score = data.get("score", 0)
                llm_reasons = data.get("reasons", [])
            except json.JSONDecodeError:
                self.logger.error(f"Failed to parse LLM response JSON: {response_text}")
                llm_reasons = ["Error parsing AI analysis"]
            except Exception as e:
                self.logger.error(f"Error processing LLM response: {e}")
                llm_reasons = ["Error processing AI analysis"]
        else:
            self.logger.warning("LLM returned no response, using fallback.")
            llm_score, llm_reasons = self._fallback_score(job)

        # 3. Combine scores
        # If we have skill matching, weight it 60%, profile matching 40%
        # Otherwise, use 100% profile matching
        if self.resume_skills and skill_score > 0:
            final_score = (skill_score * 0.6) + (llm_score * 0.4)
            combined_reasons = skill_reasons + llm_reasons
        else:
            final_score = llm_score
            combined_reasons = llm_reasons
        
        final_score = round(final_score, 1)
        
        return final_score, combined_reasons, skill_details

    def _fallback_score(self, job):
        """Legacy keyword-based scoring as fallback."""
        score = 0
        reasons = []
        prefs = self.profile.get('job_preferences', {})
        target_role = prefs.get('role', '').lower()
        title = job['title'].lower()
        
        if target_role and target_role in title:
            score += 5
            reasons.append("Fallback: Title match")
            
        return score, reasons

    def rank_jobs(self):
        """Fetches new jobs, scores them, and updates the database."""
        conn = get_db_connection()
        c = conn.cursor()
        
        # Fetch jobs that haven't been ranked yet (or just re-rank 'new' ones)
        jobs = c.execute("SELECT * FROM jobs WHERE status = 'new'").fetchall()
        
        if not jobs:
            self.logger.info("No new jobs to rank.")
            conn.close()
            return
        
        self.logger.info(f"Ranking {len(jobs)} new jobs...")
        if self.resume_skills:
            self.logger.info(f"Using {len(self.resume_skills)} skills from resume for matching")
        
        updated_count = 0
        for job in jobs:
            score, reasons, skill_details = self.calculate_score(job)
            
            # Simple threshold logic
            if score >= 5:
                start_status = 'shortlisted'
            else:
                start_status = 'rejected'
            
            reasons_str = "; ".join(reasons)
            skill_match_score = skill_details.get('match_percentage', 0) if skill_details else 0
            
            c.execute('''
                UPDATE jobs 
                SET score = ?, match_reasons = ?, status = ?, skill_match_score = ?, skill_match_details = ?
                WHERE id = ?
            ''', (score, reasons_str, start_status, skill_match_score, json.dumps(skill_details), job['id']))
            updated_count += 1
            
        conn.commit()
        conn.close()
        self.logger.info(f"Ranked and updated {updated_count} jobs.")
