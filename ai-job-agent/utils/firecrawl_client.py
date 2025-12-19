import os
import requests
import logging
from typing import List, Dict, Optional

class FirecrawlClient:
    """
    Client for interacting with firecrawl.dev to crawl and search the web.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("FirecrawlClient")
        self.api_key = os.getenv("FIRECRAWL_API_KEY")
        self.base_url = "https://api.firecrawl.dev/v0" # Verifying actual base URL might be needed

    def _get_headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def search_jobs(self, role: str, location: str, platforms: List[str]) -> List[str]:
        """
        Uses Firecrawl's search/map feature to find job URLs.
        Returns a list of URLs.
        """
        if not self.api_key:
            self.logger.error("FIRECRAWL_API_KEY not found.")
            return []

        query = f"site:({ ' OR '.join(platforms) }) {role} jobs in {location}"
        self.logger.info(f"Searching for jobs with query: {query}")

        try:
            # Firecrawl 'search' endpoint (placeholder for actual API call pattern)
            response = requests.post(
                f"{self.base_url}/search",
                headers=self._get_headers(),
                json={
                    "query": query,
                    "limit": 10
                },
                timeout=20
            )
            response.raise_for_status()
            data = response.json()
            
            # Assuming data matches Firecrawl's search result format
            return [result.get('url') for result in data.get('results', [])]
        except Exception as e:
            self.logger.error(f"Firecrawl search failed: {e}")
            return []

    def scrape_url(self, url: str) -> Optional[str]:
        """
        Scrapes a specific URL and returns the content (markdown or HTML).
        """
        if not self.api_key:
            self.logger.error("FIRECRAWL_API_KEY not found.")
            return None

        self.logger.info(f"Scraping {url} via Firecrawl...")
        try:
            response = requests.post(
                f"{self.base_url}/scrape",
                headers=self._get_headers(),
                json={
                    "url": url,
                    "formats": ["html", "markdown"]
                },
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            return data.get('data', {}).get('html') or data.get('data', {}).get('markdown')
        except Exception as e:
            self.logger.error(f"Firecrawl scrape failed for {url}: {e}")
            return None
