from bs4 import BeautifulSoup
import logging
from .base_scraper import BaseScraper

class GreenhouseScraper(BaseScraper):
    """
    Scraper specialized for Greenhouse.io job boards.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("GreenhouseScraper")

    def can_handle(self, url: str) -> bool:
        return "greenhouse.io" in url

    def parse(self, html_content: str, source_url: str) -> list:
        if not html_content:
            return []

        soup = BeautifulSoup(html_content, 'html.parser')
        jobs = []

        # Try searching for standard "div.opening" (older/standard layouts)
        job_posts = soup.find_all('div', class_='opening')
        
        # If not found, try "tr.job-post" (newer layout like Gusto)
        if not job_posts:
            job_posts = soup.find_all('tr', class_='job-post')

        for post in job_posts:
            try:
                if post.name == 'tr':
                    link_tag = post.find('a')
                    if link_tag:
                        link = link_tag.get('href')
                        if link and not link.startswith('http'):
                             link = f"https://boards.greenhouse.io{link}"
                        
                        title_tag = link_tag.find('p', class_='body--medium') or link_tag.find('p')
                        title = title_tag.text.strip() if title_tag else "Unknown Title"

                        loc_tag = link_tag.find('p', class_='body--metadata')
                        location = loc_tag.text.strip() if loc_tag else "Unknown Location"

                        jobs.append({
                            "title": title,
                            "company": "Target Company", # Often needs to be inferred from URL or metadata
                            "location": location,
                            "url": link
                        })
                else:
                    title_tag = post.find('a')
                    location_tag = post.find('span', class_='location')

                    if title_tag:
                        title = title_tag.text.strip()
                        link = title_tag.get('href')
                        if link and not link.startswith('http'):
                            link = f"https://boards.greenhouse.io{link}"
                        
                        location = location_tag.text.strip() if location_tag else "Unknown"

                        jobs.append({
                            "title": title,
                            "company": "Target Company",
                            "location": location,
                            "url": link
                        })

            except Exception as e:
                self.logger.warning(f"Failed to parse a job post: {e}")

        return jobs
