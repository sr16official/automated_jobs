# How to Get LinkedIn Job RSS Feed

## Quick Guide

Since Firecrawl's search API may have limitations, using a LinkedIn RSS feed is the **most reliable way** to find jobs with the AI Job Agent.

## Step-by-Step Instructions

### 1. Go to LinkedIn Jobs
Visit [https://www.linkedin.com/jobs](https://www.linkedin.com/jobs)

### 2. Search for Your Desired Role
- Enter your job title (e.g., "Data Scientist", "Software Engineer")
- Enter your location (e.g., "New Delhi, India", "Remote")
- Apply any filters you want (experience level, job type, etc.)

### 3. Copy the URL
Once you see the search results, copy the entire URL from your browser's address bar.

**Example URL**:
```
https://www.linkedin.com/jobs/search/?keywords=data%20scientist&location=New%20Delhi%2C%20India&geoId=&trk=public_jobs_jobs-search-bar_search-submit
```

### 4. Paste into AI Job Agent
Paste this URL into the "LinkedIn RSS Feed URL" field in the dashboard.

## Why Use RSS Feeds?

✅ **Most Reliable**: Direct access to LinkedIn's job listings  
✅ **Up-to-Date**: Real-time job postings  
✅ **Customizable**: Use LinkedIn's filters to get exactly what you want  
✅ **No API Limits**: Doesn't rely on third-party search APIs  

## Alternative: Other Job Boards

You can also use RSS feeds from:
- **Indeed**: Search on Indeed and copy the URL
- **Naukri**: Search on Naukri.com and copy the URL
- **Wellfound**: Search on Wellfound (AngelList) and copy the URL

## Troubleshooting

### "No jobs found"
- Make sure you've pasted a valid job search URL
- Try searching on LinkedIn first to verify jobs exist for your criteria
- Check that your resume is uploaded (now mandatory)

### Jobs not matching your skills
- Ensure your resume has clear skill listings
- The system extracts skills automatically from your resume
- Jobs are ranked by skill similarity (60%) + profile match (40%)

## What Happens Next?

Once you provide an RSS feed:

1. **Job Discovery**: Agent fetches jobs from the feed
2. **Resume Parsing**: Your skills are extracted from the uploaded resume
3. **Skill Extraction**: Required skills are extracted from job descriptions
4. **Similarity Matching**: Jobs are ranked by how well your skills match
5. **Contact Extraction**: Recruiter emails are found (when available)
6. **Email Drafting**: Personalized emails are created in your Gmail drafts

## Need Help?

If you're still having issues finding jobs:
1. Verify your Firecrawl API key is set in `.env` (optional but helps)
2. Use the RSS feed method (most reliable)
3. Check the terminal output for detailed error messages
