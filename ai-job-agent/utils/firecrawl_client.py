import os
import logging
from typing import List, Dict, Optional
from firecrawl import FirecrawlApp

class FirecrawlClient:
    """
    Client for interacting with Firecrawl API v1 using the official SDK.
    Provides web scraping and job discovery capabilities with anti-bot bypass.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("FirecrawlClient")
        self.api_key = os.getenv("FIRECRAWL_API_KEY")
        
        if not self.api_key:
            self.logger.warning("FIRECRAWL_API_KEY not found. Firecrawl features will be disabled.")
            self.app = None
        else:
            try:
                self.app = FirecrawlApp(api_key=self.api_key)
                self.logger.info("Firecrawl client initialized successfully with v1 API")
            except Exception as e:
                self.logger.error(f"Failed to initialize Firecrawl: {e}")
                self.app = None

    def search_jobs(self, role: str, location: str, platforms: List[str]) -> List[str]:
        """
        Uses Firecrawl's search feature to find job URLs.
        Returns a list of URLs.
        """
        if not self.app:
            self.logger.error("Firecrawl not initialized. Cannot search jobs.")
            return []

        query = f"{role} jobs in {location} site:({' OR '.join(platforms)})"
        self.logger.info(f"Searching for jobs with query: {query}")

        try:
            # Use Firecrawl's search endpoint
            # Note: Search functionality may vary based on your Firecrawl plan
            response = self.app.search(query, limit=10)
            
            if response and 'data' in response:
                urls = [result.get('url') for result in response['data'] if result.get('url')]
                self.logger.info(f"Found {len(urls)} job URLs via Firecrawl search")
                return urls
            else:
                self.logger.warning("No results from Firecrawl search")
                return []
                
        except Exception as e:
            self.logger.error(f"Firecrawl search failed: {e}")
            return []

    def scrape_url(self, url: str, formats: List[str] = None) -> Optional[str]:
        """
        Scrapes a specific URL and returns the content.
        
        Args:
            url: URL to scrape
            formats: List of formats to return (html, markdown, etc.)
        
        Returns:
            HTML or markdown content, or None if scraping fails
        """
        if not self.app:
            self.logger.error("Firecrawl not initialized. Cannot scrape URL.")
            return None

        if formats is None:
            formats = ['html', 'markdown']

        self.logger.info(f"Scraping {url} via Firecrawl...")
        
        try:
            # Use Firecrawl v1 scrape endpoint
            response = self.app.scrape_url(
                url,
                params={
                    'formats': formats,
                    'onlyMainContent': True  # Focus on main content, ignore ads/navigation
                }
            )
            
            if response and 'data' in response:
                data = response['data']
                # Return HTML if available, otherwise markdown
                content = data.get('html') or data.get('markdown')
                
                if content:
                    self.logger.info(f"Successfully scraped {url} ({len(content)} chars)")
                    return content
                else:
                    self.logger.warning(f"No content returned from {url}")
                    return None
            else:
                self.logger.warning(f"Invalid response from Firecrawl for {url}")
                return None
                
        except Exception as e:
            self.logger.error(f"Firecrawl scrape failed for {url}: {e}")
            return None

    def scrape_with_extraction(self, url: str, schema: Dict = None) -> Optional[Dict]:
        """
        Scrapes a URL and extracts structured data using Firecrawl's extraction features.
        Useful for extracting specific patterns like emails, phone numbers, etc.
        
        Args:
            url: URL to scrape
            schema: Optional schema for structured extraction
        
        Returns:
            Extracted data dictionary or None
        """
        if not self.app:
            self.logger.error("Firecrawl not initialized. Cannot extract data.")
            return None

        self.logger.info(f"Scraping {url} with extraction...")
        
        try:
            params = {
                'formats': ['html', 'markdown'],
                'onlyMainContent': True
            }
            
            if schema:
                params['extract'] = schema
            
            response = self.app.scrape_url(url, params=params)
            
            if response and 'data' in response:
                return response['data']
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Firecrawl extraction failed for {url}: {e}")
            return None

    def batch_scrape(self, urls: List[str]) -> List[Dict]:
        """
        Scrapes multiple URLs efficiently using Firecrawl's batch capabilities.
        
        Args:
            urls: List of URLs to scrape
        
        Returns:
            List of scraped data dictionaries
        """
        if not self.app:
            self.logger.error("Firecrawl not initialized. Cannot batch scrape.")
            return []

        self.logger.info(f"Batch scraping {len(urls)} URLs...")
        
        results = []
        for url in urls:
            content = self.scrape_url(url)
            if content:
                results.append({
                    'url': url,
                    'content': content
                })
        
        self.logger.info(f"Successfully scraped {len(results)}/{len(urls)} URLs")
        return results
