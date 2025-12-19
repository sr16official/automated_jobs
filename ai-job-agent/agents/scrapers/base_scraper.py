from abc import ABC, abstractmethod

class BaseScraper(ABC):
    """
    Abstract base class for all job board scrapers.
    """
    
    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """Returns True if this scraper can handle the given URL."""
        pass

    @abstractmethod
    def parse(self, html_content: str, source_url: str) -> list:
        """
        Parses HTML content and returns a list of job dictionaries.
        Each job should have: title, company, location, url.
        """
        pass
