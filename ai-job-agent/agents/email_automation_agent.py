import logging
import os
import json
from utils.helpers import get_db_connection
from utils.gmail_client import GmailClient
from utils.llm_client import LLMClient

class EmailAutomationAgent:
    """
    Agent responsible for drafting emails to recruiters.
    """
    def __init__(self):
        self.logger = logging.getLogger("EmailAutomationAgent")
        self.gmail_client = GmailClient()
        self.llm_client = LLMClient()
        self.profile = self._load_profile()
        self.resume_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'resume.pdf')

    def _load_profile(self):
        """Loads user profile from JSON file."""
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'user_profile.json')
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load user profile: {e}")
            return {}

    def generate_email_content(self, job):
        """
        Generates email subject and body using LLM.
        """
        profile_str = json.dumps(self.profile, indent=2)
        job_str = json.dumps({
            "title": job['title'],
            "company": job['company'] if job['company'] else 'the company',
            "location": job['location']
        }, indent=2)

        
        system_prompt = """You are a professional career assistant. Your goal is to write a concise, professional, and compelling email to a recruiter or hiring manager.
        
        Output strictly in JSON format with two keys:
        - "subject": The email subject line.
        - "body": The email body text (plain text, no HTML).
        
        Guidelines:
        - Keep it brief (under 150 words).
        - Mention the specific role.
        - Highlight 1-2 key strengths from the profile that match the job.
        - Polite call to action (e.g., "attached my resume", "available for a chat").
        """
        
        user_prompt = f"""
        My Profile:
        {profile_str}
        
        Job Details:
        {job_str}
        
        Write a cold email draft to the recruiter.
        """
        
        response_text = self.llm_client.generate_response(user_prompt, system_prompt=system_prompt)
        
        if response_text:
            try:
                # Clean up potential markdown formatting
                cleaned_text = response_text.replace("```json", "").replace("```", "").strip()
                return json.loads(cleaned_text)
            except Exception as e:
                self.logger.error(f"Failed to parse email content: {e}")
        
        return None

    def process_shortlisted_jobs(self):
        """
        Finds shortlisted jobs with contacts and creates draft emails.
        """
        conn = get_db_connection()
        c = conn.cursor()
        
        # Select jobs that are shortlisted, have a contact email, and haven't had a draft created yet
        # We'll use a new status or column. For now, let's assume if 'draft_created' column is NULL/0
        # First, ensure columns exist (migration step usually, but we'll do checks here or assume DB is ready)
        # For simplicity in this agent, we'll check if we can add a column or just use a flag.
        # Let's check schema first in a real app, but here we will just try to use a 'status' check or similar.
        # Since we don't have migrations, we might re-use 'contact_email' presence and check if we already did it?
        # A robust way is to add a column 'email_status'.
        
        # Let's assume we add a column 'email_status' implicitly or use a set of IDs we already processed.
        # For this MVP, we will just select all shortlisted ones with email and print for now if we can't persist state easily without schema change.
        # WAIT: 'status' column is text. We can update it to 'drafted'.
        
        jobs = c.execute("SELECT * FROM jobs WHERE status = 'shortlisted' AND contact_email IS NOT NULL AND contact_email != ''").fetchall()
        
        if not jobs:
            self.logger.info("No actionable jobs for email drafting.")
            conn.close()
            return

        self.logger.info(f"Drafting emails for {len(jobs)} jobs...")
        
        count = 0
        for job in jobs:
            # Handle multiple emails, pick first for now
            emails = job['contact_email'].split(',')
            recipient = emails[0].strip()
            
            self.logger.info(f"Generating draft for {job['title']} -> {recipient}")
            
            content = self.generate_email_content(job)
            
            if content:
                subject = content.get('subject', f"Application for {job['title']}")
                body = content.get('body', "")
                
                # Append signature
                user_name = self.profile.get('name', 'Candidate')
                body += f"\n\nBest regards,\n{user_name}"

                draft = self.gmail_client.create_draft(recipient, subject, body, attachment_path=self.resume_path)
                
                if draft:
                    c.execute("UPDATE jobs SET status = 'drafted' WHERE id = ?", (job['id'],))
                    count += 1
            else:
                self.logger.error(f"Failed to generate content for {job['id']}")

        conn.commit()
        conn.close()
        self.logger.info(f"Created {count} draft emails.")
