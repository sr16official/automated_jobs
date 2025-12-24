import os
import logging
import json
from typing import List, Dict, Optional
import PyPDF2
import docx
from utils.llm_client import LLMClient


class ResumeParser:
    """
    Utility to parse resumes and extract skills using LLM.
    Supports PDF and DOCX formats.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("ResumeParser")
        self.llm_client = LLMClient()
        self.cache = {}  # Cache parsed results
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text content from PDF file."""
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            self.logger.error(f"Error extracting text from PDF {file_path}: {e}")
            return ""
    
    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text content from DOCX file."""
        try:
            doc = docx.Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text.strip()
        except Exception as e:
            self.logger.error(f"Error extracting text from DOCX {file_path}: {e}")
            return ""
    
    def extract_text_from_resume(self, file_path: str) -> str:
        """
        Extract text from resume file (PDF or DOCX).
        
        Args:
            file_path: Path to the resume file
            
        Returns:
            Extracted text content
        """
        if not os.path.exists(file_path):
            self.logger.error(f"Resume file not found: {file_path}")
            return ""
        
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.pdf':
            return self.extract_text_from_pdf(file_path)
        elif file_ext in ['.docx', '.doc']:
            return self.extract_text_from_docx(file_path)
        else:
            self.logger.error(f"Unsupported file format: {file_ext}")
            return ""
    
    def parse_skills_with_llm(self, resume_text: str) -> List[str]:
        """
        Use LLM to extract skills from resume text.
        
        Args:
            resume_text: Raw text extracted from resume
            
        Returns:
            List of extracted skills
        """
        if not resume_text:
            return []
        
        system_prompt = """You are an expert resume parser. Extract all technical skills, tools, technologies, frameworks, and programming languages from the resume.

Output strictly in JSON format with the following structure:
{
    "skills": ["skill1", "skill2", "skill3", ...]
}

Include:
- Programming languages (Python, Java, JavaScript, etc.)
- Frameworks and libraries (React, Django, TensorFlow, etc.)
- Tools and platforms (Docker, AWS, Git, etc.)
- Databases (PostgreSQL, MongoDB, etc.)
- Methodologies (Agile, CI/CD, etc.)

Be comprehensive but avoid duplicates. Normalize skill names (e.g., "JS" -> "JavaScript")."""

        user_prompt = f"""Extract all skills from this resume:

{resume_text[:4000]}  # Limit to avoid token limits

Return the skills in JSON format."""

        try:
            response_text = self.llm_client.generate_response(user_prompt, system_prompt=system_prompt)
            
            if response_text:
                # Clean up markdown formatting
                cleaned_text = response_text.replace("```json", "").replace("```", "").strip()
                data = json.loads(cleaned_text)
                skills = data.get("skills", [])
                
                # Normalize skills to lowercase for better matching
                skills = [skill.strip().lower() for skill in skills if skill.strip()]
                
                self.logger.info(f"Extracted {len(skills)} skills from resume")
                return skills
            else:
                self.logger.warning("LLM returned no response for skill extraction")
                return []
                
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse LLM response JSON: {e}")
            self.logger.error(f"Response was: {response_text}")
            return []
        except Exception as e:
            self.logger.error(f"Error parsing skills with LLM: {e}")
            return []
    
    def get_resume_skills(self, file_path: str) -> List[str]:
        """
        Main function to extract skills from a resume file.
        Uses caching to avoid re-parsing the same file.
        
        Args:
            file_path: Path to the resume file
            
        Returns:
            List of extracted skills
        """
        # Check cache first
        if file_path in self.cache:
            self.logger.info(f"Using cached skills for {file_path}")
            return self.cache[file_path]
        
        # Extract text from resume
        self.logger.info(f"Parsing resume: {file_path}")
        resume_text = self.extract_text_from_resume(file_path)
        
        if not resume_text:
            self.logger.error("No text extracted from resume")
            return []
        
        # Parse skills using LLM
        skills = self.parse_skills_with_llm(resume_text)
        
        # Cache the result
        self.cache[file_path] = skills
        
        return skills
    
    def get_resume_summary(self, file_path: str) -> Dict[str, any]:
        """
        Get a comprehensive summary of the resume including skills, experience, etc.
        
        Args:
            file_path: Path to the resume file
            
        Returns:
            Dictionary with resume summary
        """
        skills = self.get_resume_skills(file_path)
        
        return {
            "file_path": file_path,
            "skills": skills,
            "skill_count": len(skills)
        }
