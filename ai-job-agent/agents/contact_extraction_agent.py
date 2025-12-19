import re
import requests
import logging
from bs4 import BeautifulSoup
from utils.helpers import get_db_connection

class ContactExtractionAgent:
    """
    Agent responsible for extracting contact information (emails) from job descriptions.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("ContactExtractionAgent")
    
        self.email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

    def extract_from_text(self, text):
        """Extracts emails from text using regex."""
        if not text:
            return []
        # Find all matches
        emails = re.findall(self.email_pattern, text)
        # Filter out common false positives or image files if regex catches them (unlikely with this regex but possible)
        # Also filter out generic ignore emails if needed (e.g. valid-email@example.com)
        unique_emails = list(set(emails))
        return unique_emails

    def extract_contacts(self):
        """Iterates through shortlisted jobs and attempts to find contact info."""
        conn = get_db_connection()
        c = conn.cursor()
        
        # Select shortlisted jobs that haven't been processed for contacts yet (or just all shortlisted)
        # In this simple version, we'll process all 'shortlisted' jobs.
        jobs = c.execute("SELECT * FROM jobs WHERE status = 'shortlisted'").fetchall()
        
        if not jobs:
            self.logger.info("No shortlisted jobs to process.")
            conn.close()
            return

        self.logger.info(f"Extracting contacts for {len(jobs)} jobs...")
        
        updated_count = 0
        for job in jobs:
            url = job['url']
            self.logger.info(f"Visiting {url}...")
            
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    # Clean HTML to text to make regex easier and safer
                    soup = BeautifulSoup(response.text, 'html.parser')
                    text_content = soup.get_text(separator=' ', strip=True)
                    
                    emails = self.extract_from_text(text_content)
                    
                    # Store found emails (comma separated if multiple)
                    if emails:
                        email_str = ", ".join(emails)
                        self.logger.info(f"Found contacts for {job['title']}: {email_str}")
                    else:
                        email_str = None
                        # self.logger.info(f"No contacts found for {job['title']}")
                    
                    c.execute('''
                        UPDATE jobs 
                        SET contact_email = ?
                        WHERE id = ?
                    ''', (email_str, job['id']))
                    updated_count += 1
                else:
                    self.logger.warning(f"Failed to fetch job page: {response.status_code}")
            except Exception as e:
                self.logger.error(f"Error processing {url}: {e}")

        conn.commit()
        conn.close()
        self.logger.info(f"Finished extracting contacts. Updated {updated_count} jobs.")
