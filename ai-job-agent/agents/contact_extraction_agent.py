import re
import logging
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from utils.helpers import get_db_connection
from utils.firecrawl_client import FirecrawlClient

class ContactExtractionAgent:
    """
    Agent responsible for extracting contact information (emails) from job descriptions.
    Uses Firecrawl to bypass anti-bot measures and implements fallback email generation.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("ContactExtractionAgent")
        self.firecrawl = FirecrawlClient()
        self.email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

    def extract_from_text(self, text):
        """Extracts emails from text using regex."""
        if not text:
            return []
        
        # Find all matches
        emails = re.findall(self.email_pattern, text)
        
        # Filter out common false positives
        filtered_emails = []
        for email in emails:
            email_lower = email.lower()
            # Skip image files and common placeholders
            if not any(ext in email_lower for ext in ['.png', '.jpg', '.gif', '.svg', 'example.com', 'test.com']):
                filtered_emails.append(email)
        
        return list(set(filtered_emails))

    def extract_company_domain(self, url: str, company_name: str = None) -> str:
        """
        Extracts company domain from job URL or company name.
        
        Args:
            url: Job posting URL
            company_name: Company name (optional)
        
        Returns:
            Company domain (e.g., 'company.com')
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            
            # Remove common job board domains
            job_boards = ['greenhouse.io', 'lever.co', 'workable.com', 'linkedin.com', 
                         'naukri.com', 'indeed.com', 'wellfound.com', 'angellist.com']
            
            # Check if it's a job board URL
            is_job_board = any(board in domain for board in job_boards)
            
            if is_job_board:
                # For job boards, we can't extract domain from URL
                # Use company name instead
                if company_name:
                    # Clean company name and create domain
                    # Remove common suffixes and special characters
                    clean_name = company_name.lower()
                    clean_name = clean_name.replace(' hiring', '').replace('hiring ', '')
                    clean_name = clean_name.replace(' inc.', '').replace(' ltd.', '').replace(' llc', '')
                    clean_name = clean_name.replace(',', '').replace('.', '').replace('&', 'and')
                    clean_name = clean_name.replace(' ', '').replace('-', '')
                    
                    # Handle common company name patterns
                    if '(' in clean_name:
                        clean_name = clean_name.split('(')[0].strip()
                    
                    return f"{clean_name}.com"
                else:
                    return None
            else:
                # If not a job board, use the main domain
                return domain
            
        except Exception as e:
            self.logger.warning(f"Failed to extract domain: {e}")
            return None

    def generate_fallback_emails(self, company_name: str, job_url: str) -> list:
        """
        Generates likely email addresses when no contact is found.
        
        Args:
            company_name: Name of the company
            job_url: URL of the job posting
        
        Returns:
            List of potential email addresses
        """
        domain = self.extract_company_domain(job_url, company_name)
        
        if not domain:
            return []
        
        # Common email patterns for recruiting/HR
        prefixes = ['careers', 'jobs', 'hr', 'recruiting', 'talent', 'hiring']
        fallback_emails = [f"{prefix}@{domain}" for prefix in prefixes]
        
        self.logger.info(f"Generated {len(fallback_emails)} fallback emails for {company_name}")
        return fallback_emails

    def validate_email_format(self, email: str) -> bool:
        """
        Validates email format.
        
        Args:
            email: Email address to validate
        
        Returns:
            True if valid format, False otherwise
        """
        if not email:
            return False
        
        # Basic validation
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def extract_contacts(self, max_jobs: int = 50):
        """
        Iterates through jobs and attempts to find contact info.
        Uses Firecrawl for robust scraping with anti-bot bypass.
        
        Args:
            max_jobs: Maximum number of jobs to process (default: 50)
        """
        conn = get_db_connection()
        c = conn.cursor()
        
        # Select jobs that haven't been processed for contacts yet, ordered by score
        # Process all jobs, not just shortlisted, to maximize contact extraction
        jobs = c.execute("""
            SELECT * FROM jobs 
            WHERE contact_email IS NULL 
            ORDER BY score DESC 
            LIMIT ?
        """, (max_jobs,)).fetchall()
        
        if not jobs:
            self.logger.info("No jobs to process for contact extraction.")
            conn.close()
            return

        self.logger.info(f"Extracting contacts for {len(jobs)} jobs...")
        
        updated_count = 0
        for job in jobs:
            url = job['url']
            company = job['company'] or "Unknown Company"
            self.logger.info(f"Processing {job['title']} at {company}...")
            
            try:
                # Use Firecrawl to scrape the job page (bypasses anti-bot measures)
                html_content = self.firecrawl.scrape_url(url)
                
                if html_content:
                    # Parse HTML to extract text
                    soup = BeautifulSoup(html_content, 'html.parser')
                    text_content = soup.get_text(separator=' ', strip=True)
                    
                    # Extract emails from content
                    emails = self.extract_from_text(text_content)
                    
                    if emails:
                        # Validate and filter emails
                        valid_emails = [e for e in emails if self.validate_email_format(e)]
                        
                        if valid_emails:
                            email_str = ", ".join(valid_emails[:3])  # Limit to top 3
                            extraction_method = "scraped"
                            confidence = 0.8
                            self.logger.info(f"✓ Found contacts for {job['title']}: {email_str}")
                        else:
                            # No valid emails found, generate fallbacks
                            fallback_emails = self.generate_fallback_emails(company, url)
                            email_str = ", ".join(fallback_emails[:2]) if fallback_emails else None
                            extraction_method = "generated"
                            confidence = 0.3
                            if email_str:
                                self.logger.info(f"⚠ Generated fallback emails for {job['title']}: {email_str}")
                    else:
                        # No emails found, generate fallbacks
                        fallback_emails = self.generate_fallback_emails(company, url)
                        email_str = ", ".join(fallback_emails[:2]) if fallback_emails else None
                        extraction_method = "generated"
                        confidence = 0.3
                        if email_str:
                            self.logger.info(f"⚠ Generated fallback emails for {job['title']}: {email_str}")
                        else:
                            email_str = None
                            extraction_method = "none"
                            confidence = 0.0
                            self.logger.warning(f"✗ No contacts found for {job['title']}")
                else:
                    # Firecrawl failed, generate fallbacks
                    self.logger.warning(f"Failed to scrape {url}, generating fallbacks...")
                    fallback_emails = self.generate_fallback_emails(company, url)
                    email_str = ", ".join(fallback_emails[:2]) if fallback_emails else None
                    extraction_method = "generated"
                    confidence = 0.3
                
                # Update database with contact info and metadata
                c.execute('''
                    UPDATE jobs 
                    SET contact_email = ?
                    WHERE id = ?
                ''', (email_str, job['id']))
                
                updated_count += 1
                
            except Exception as e:
                self.logger.error(f"Error processing {url}: {e}")

        conn.commit()
        conn.close()
        self.logger.info(f"✓ Finished extracting contacts. Updated {updated_count} jobs.")
