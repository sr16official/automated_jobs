from utils.helpers import init_db, get_db_connection
from agents.job_search_agent import JobSearchAgent
from agents.job_ranking_agent import JobRankingAgent
from agents.contact_extraction_agent import ContactExtractionAgent
from agents.email_automation_agent import EmailAutomationAgent

def main():
    print("Initializing system...")
    init_db()

    # User Input (could be moved to interactive or profile-based later)
    role = "Software Engineer"
    location = "Bangalore"
    
    agent = JobSearchAgent()
    ranker = JobRankingAgent()
    extractor = ContactExtractionAgent()
    email_bot = EmailAutomationAgent()
    
    print(f"\n--- Starting Job Search for '{role}' in '{location}' ---")
    agent.search_and_scrape(role, location)
    
    # Check if jobs were found
    conn = get_db_connection()
    new_jobs_count = conn.execute("SELECT COUNT(*) FROM jobs WHERE status = 'new'").fetchone()[0]
    conn.close()

    if new_jobs_count > 0:
        # Ranking Phase
        print("\n--- Ranking Jobs ---")
        ranker.rank_jobs()
        
        # Contact Extraction Phase
        print("\n--- Extracting Contacts ---")
        extractor.extract_contacts()
        
        # Email Drafting Phase
        print("\n--- Drafting Emails (Google Auth) ---")
        email_bot.process_shortlisted_jobs()
        
        # Verify DB content
        print("\n--- Verifying Database Storage (Drafted & Enriched) ---")
        conn = get_db_connection()
        # Show drafted jobs
        rows = conn.execute("SELECT * FROM jobs WHERE status = 'drafted' ORDER BY score DESC LIMIT 10").fetchall()
        
        if rows:
            print(f"Top 10 Drafted Jobs:")
            for row in rows:
                print(f"- [Score: {row['score']}] {row['title']} @ {row['location']} | Email: {row['contact_email']}")
        else:
            print("No jobs drafted (either no contacts found or no shortlisted jobs).")
            
        conn.close()
    else:
        print("No new jobs found or search failed.")

if __name__ == "__main__":
    main()
