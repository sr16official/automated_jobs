from fastapi import FastAPI, BackgroundTasks, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import shutil
import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path to import agents and utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from agents.job_search_agent import JobSearchAgent
from agents.job_ranking_agent import JobRankingAgent
from agents.contact_extraction_agent import ContactExtractionAgent
from agents.email_automation_agent import EmailAutomationAgent
from utils.helpers import init_db, get_db_connection

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI(title="AI Job Agent API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'frontend')
app.mount("/static", StaticFiles(directory=frontend_path), name="static")

@app.get("/")
def read_root():
    return FileResponse(os.path.join(frontend_path, 'index.html'))

@app.get("/app.js")
def get_js():
    return FileResponse(os.path.join(frontend_path, 'app.js'))
agent_status = {
    "is_running": False,
    "last_run": None,
    "current_step": "Idle",
    "progress": 0
}

# Store uploaded resume path and parsed skills
resume_path = None
resume_skills = []

def run_agent_task(role: str, location: str, rss_url: Optional[str] = None):
    global agent_status, resume_skills
    try:
        agent_status["is_running"] = True
        agent_status["progress"] = 0
        
        # Step 1: Initialize and Clear Old Jobs
        agent_status["current_step"] = "Initializing Database"
        init_db()
        
        # Clear previous jobs to show only current search results
        conn = get_db_connection()
        conn.execute("DELETE FROM jobs")
        conn.commit()
        conn.close()
        
        agent_status["progress"] = 10
        
        # Step 1.5: Parse resume if available
        if resume_path and resume_skills:
            agent_status["current_step"] = f"Using {len(resume_skills)} skills from resume"
            agent_status["progress"] = 15
        
        # Initialize agents
        search_agent = JobSearchAgent()
        ranker = JobRankingAgent(resume_skills=resume_skills)  # Pass resume skills
        extractor = ContactExtractionAgent()
        email_bot = EmailAutomationAgent()
        
        # Step 2: Search
        search_msg = f"Searching for {role}"
        if rss_url: search_msg += " (via RSS)"
        agent_status["current_step"] = search_msg
        
        search_agent.search_and_scrape(role, location, rss_url)
        agent_status["progress"] = 40
        
        # Step 3: Rank
        agent_status["current_step"] = "Ranking Jobs with Skill Matching"
        ranker.rank_jobs()
        agent_status["progress"] = 60
        
        # Step 4: Extract
        agent_status["current_step"] = "Extracting Contacts"
        extractor.extract_contacts()
        agent_status["progress"] = 80
        
        # Step 5: Draft
        agent_status["current_step"] = "Drafting Emails"
        email_bot.process_shortlisted_jobs()
        agent_status["progress"] = 100
        
        agent_status["current_step"] = "Completed"
    except Exception as e:
        agent_status["current_step"] = f"Error: {str(e)}"
    finally:
        agent_status["is_running"] = False

@app.get("/")
def read_root():
    return {"message": "AI Job Agent API is running"}

@app.post("/run")
async def run_agent(
    background_tasks: BackgroundTasks,
    role: str = Form(...),
    location: str = Form(...),
    rss_url: str = Form(""),
    resume: Optional[UploadFile] = File(None)
):
    global resume_path, resume_skills
    try:
        print(f"Received: role={role}, location={location}, rss_url={rss_url}, resume={resume}")
        
        if agent_status["is_running"]:
            return {"message": "Agent is already running", "status": agent_status}
        
        # Save resume if uploaded
        if resume and resume.filename:
            resume_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads')
            os.makedirs(resume_dir, exist_ok=True)
            resume_path = os.path.join(resume_dir, resume.filename)
            with open(resume_path, "wb") as buffer:
                shutil.copyfileobj(resume.file, buffer)
            print(f"Resume saved to: {resume_path}")
            
            # Parse resume skills
            try:
                from utils.resume_parser import ResumeParser
                parser = ResumeParser()
                resume_skills = parser.get_resume_skills(resume_path)
                print(f"Extracted {len(resume_skills)} skills from resume: {resume_skills[:10]}")
            except Exception as e:
                print(f"Error parsing resume: {e}")
                import traceback
                traceback.print_exc()
                resume_skills = []
        
        background_tasks.add_task(run_agent_task, role, location, rss_url if rss_url else None)
        return {"message": "Agent started in background", "status": agent_status}
    except Exception as e:
        print(f"Error in run_agent: {e}")
        import traceback
        traceback.print_exc()
        return {"message": f"Error: {str(e)}", "status": agent_status}

@app.get("/status")
def get_status():
    return agent_status

@app.get("/jobs")
def get_jobs(status: Optional[str] = None):
    conn = get_db_connection()
    query = "SELECT * FROM jobs"
    if status:
        query += f" WHERE status = '{status}'"
    query += " ORDER BY score DESC"
    
    rows = conn.execute(query).fetchall()
    jobs = [dict(row) for row in rows]
    conn.close()
    return jobs

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
