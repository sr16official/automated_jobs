import logging
from typing import List, Tuple, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class SkillMatcher:
    """
    Utility to calculate similarity between resume skills and job requirements.
    Uses both exact matching and semantic similarity.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("SkillMatcher")
    
    def normalize_skill(self, skill: str) -> str:
        """Normalize skill name for better matching."""
        # Convert to lowercase and strip whitespace
        skill = skill.lower().strip()
        
        # Common normalizations
        normalizations = {
            'js': 'javascript',
            'ts': 'typescript',
            'py': 'python',
            'react.js': 'react',
            'node.js': 'node',
            'nodejs': 'node',
            'postgresql': 'postgres',
            'aws': 'amazon web services',
            'gcp': 'google cloud platform',
            'k8s': 'kubernetes',
        }
        
        return normalizations.get(skill, skill)
    
    def calculate_exact_matches(self, resume_skills: List[str], job_skills: List[str]) -> Tuple[List[str], List[str]]:
        """
        Find exact matches between resume and job skills.
        
        Args:
            resume_skills: List of skills from resume
            job_skills: List of required skills from job
            
        Returns:
            Tuple of (matched_skills, missing_skills)
        """
        # Normalize all skills
        resume_set = set([self.normalize_skill(s) for s in resume_skills])
        job_set = set([self.normalize_skill(s) for s in job_skills])
        
        # Find matches and missing skills
        matched = list(resume_set & job_set)
        missing = list(job_set - resume_set)
        
        return matched, missing
    
    def calculate_semantic_similarity(self, resume_skills: List[str], job_skills: List[str]) -> float:
        """
        Calculate semantic similarity between skill sets using TF-IDF and cosine similarity.
        
        Args:
            resume_skills: List of skills from resume
            job_skills: List of required skills from job
            
        Returns:
            Similarity score between 0 and 1
        """
        if not resume_skills or not job_skills:
            return 0.0
        
        try:
            # Create skill documents
            resume_doc = ' '.join([self.normalize_skill(s) for s in resume_skills])
            job_doc = ' '.join([self.normalize_skill(s) for s in job_skills])
            
            # Calculate TF-IDF vectors
            vectorizer = TfidfVectorizer()
            tfidf_matrix = vectorizer.fit_transform([resume_doc, job_doc])
            
            # Calculate cosine similarity
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            return float(similarity)
            
        except Exception as e:
            self.logger.error(f"Error calculating semantic similarity: {e}")
            return 0.0
    
    def calculate_skill_similarity(self, resume_skills: List[str], job_skills: List[str]) -> Tuple[float, Dict]:
        """
        Calculate overall similarity score between resume and job skills.
        
        Args:
            resume_skills: List of skills from resume
            job_skills: List of required skills from job
            
        Returns:
            Tuple of (score 0-10, details dict)
        """
        if not job_skills:
            # If no job skills specified, return neutral score
            return 5.0, {
                "matched_skills": [],
                "missing_skills": [],
                "match_percentage": 0,
                "semantic_similarity": 0
            }
        
        if not resume_skills:
            # No resume skills means no match
            return 0.0, {
                "matched_skills": [],
                "missing_skills": job_skills,
                "match_percentage": 0,
                "semantic_similarity": 0
            }
        
        # Calculate exact matches
        matched_skills, missing_skills = self.calculate_exact_matches(resume_skills, job_skills)
        match_percentage = (len(matched_skills) / len(job_skills)) * 100 if job_skills else 0
        
        # Calculate semantic similarity
        semantic_sim = self.calculate_semantic_similarity(resume_skills, job_skills)
        
        # Calculate final score (0-10 scale)
        # Weight: 70% exact matches, 30% semantic similarity
        exact_match_score = (len(matched_skills) / len(job_skills)) * 7.0 if job_skills else 0
        semantic_score = semantic_sim * 3.0
        
        final_score = min(exact_match_score + semantic_score, 10.0)
        
        details = {
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "match_percentage": round(match_percentage, 1),
            "semantic_similarity": round(semantic_sim, 2),
            "total_job_skills": len(job_skills),
            "total_resume_skills": len(resume_skills)
        }
        
        self.logger.info(f"Skill match: {len(matched_skills)}/{len(job_skills)} exact matches, "
                        f"{match_percentage:.1f}% coverage, score: {final_score:.1f}/10")
        
        return round(final_score, 1), details
    
    def get_match_explanation(self, details: Dict) -> str:
        """
        Generate human-readable explanation of skill matching.
        
        Args:
            details: Details dictionary from calculate_skill_similarity
            
        Returns:
            Explanation string
        """
        matched = details.get("matched_skills", [])
        missing = details.get("missing_skills", [])
        match_pct = details.get("match_percentage", 0)
        
        explanation_parts = []
        
        if matched:
            explanation_parts.append(f"Matched skills: {', '.join(matched[:5])}")
            if len(matched) > 5:
                explanation_parts[-1] += f" (+{len(matched)-5} more)"
        
        if missing:
            explanation_parts.append(f"Missing skills: {', '.join(missing[:3])}")
            if len(missing) > 3:
                explanation_parts[-1] += f" (+{len(missing)-3} more)"
        
        explanation_parts.append(f"Skill coverage: {match_pct:.0f}%")
        
        return "; ".join(explanation_parts)
