import json
import logging
import os
from utils.helpers import get_db_connection
from utils.llm_client import LLMClient

class JobRankingAgent:
    """
    Agent responsible for scoring and ranking jobs based on user profile.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("JobRankingAgent")
        self.profile = self._load_profile()
        self.llm_client = LLMClient()

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
        Calculates a relevance score for a job using LLM.
        Returns (score, reasons_list).
        """
        
        # 1. Construct Prompt
        profile_str = json.dumps(self.profile, indent=2)
        job_str = json.dumps({
            "title": job['title'],
            "location": job['location'],
            # "description": job['description'] # Assuming description might be available or added later
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
        
        # 2. Call LLM
        response_text = self.llm_client.generate_response(user_prompt, system_prompt=system_prompt)
        
        # 3. Parse Response
        score = 0
        reasons = []
        
        if response_text:
            try:
                # Clean up potential markdown formatting like ```json ... ```
                cleaned_text = response_text.replace("```json", "").replace("```", "").strip()
                data = json.loads(cleaned_text)
                score = data.get("score", 0)
                reasons = data.get("reasons", [])
            except json.JSONDecodeError:
                self.logger.error(f"Failed to parse LLM response JSON: {response_text}")
                reasons = ["Error parsing AI analysis"]
            except Exception as e:
                self.logger.error(f"Error processing LLM response: {e}")
                reasons = ["Error processing AI analysis"]
        else:
             # Fallback to simple logic if LLM fails (or just return 0)
             self.logger.warning("LLM returned no response, using fallback.")
             return self._fallback_score(job)

        return score, reasons

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
        
        updated_count = 0
        for job in jobs:
            score, reasons = self.calculate_score(job)
            
            # Simple threshold logic
            if score >= 5:
                start_status = 'shortlisted'
            else:
                start_status = 'rejected'
            
            reasons_str = "; ".join(reasons)
            
            c.execute('''
                UPDATE jobs 
                SET score = ?, match_reasons = ?, status = ?
                WHERE id = ?
            ''', (score, reasons_str, start_status, job['id']))
            updated_count += 1
            
        conn.commit()
        conn.close()
        self.logger.info(f"Ranked and updated {updated_count} jobs.")
