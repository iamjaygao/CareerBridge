"""
Crawler service for job data collection
"""

import asyncio
from typing import List, Dict, Any, Optional
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.scrapers.indeed_scraper import IndeedScraper
from app.services.scrapers.linkedin_scraper import LinkedInScraper

logger = structlog.get_logger()

class CrawlerService:
    """Main crawler service that orchestrates job scraping"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.scrapers = {
                'indeed': IndeedScraper(),
                'linkedin': LinkedInScraper()
            }
            self._initialized = True
    
    @classmethod
    async def initialize(cls):
        """Initialize the crawler service"""
        if not cls._instance:
            cls._instance = cls()
        
        # Initialize scrapers
        for name, scraper in cls._instance.scrapers.items():
            try:
                await scraper.initialize()
                logger.info(f"Initialized {name} scraper")
            except Exception as e:
                logger.error(f"Failed to initialize {name} scraper", error=str(e))
    
    @classmethod
    async def cleanup(cls):
        """Cleanup resources"""
        if cls._instance:
            for name, scraper in cls._instance.scrapers.items():
                try:
                    await scraper.cleanup()
                    logger.info(f"Cleaned up {name} scraper")
                except Exception as e:
                    logger.error(f"Failed to cleanup {name} scraper", error=str(e))
    
    async def crawl_jobs(
        self,
        keywords: str,
        location: Optional[str] = None,
        sources: Optional[List[str]] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Crawl jobs from multiple sources"""
        if sources is None:
            sources = ['indeed', 'linkedin']
        
        all_jobs = []
        
        for source in sources:
            if source in self.scrapers:
                try:
                    jobs = await self.scrapers[source].scrape_jobs(
                        keywords=keywords,
                        location=location,
                        limit=limit // len(sources)
                    )
                    all_jobs.extend(jobs)
                    logger.info(f"Crawled {len(jobs)} jobs from {source}")
                except Exception as e:
                    logger.error(f"Failed to crawl from {source}", error=str(e))
        
        return all_jobs
    
    async def crawl_trending_jobs(self, days: int = 7) -> List[Dict[str, Any]]:
        """Crawl trending jobs from all sources"""
        trending_jobs = []
        
        for name, scraper in self.scrapers.items():
            try:
                jobs = await scraper.get_trending_jobs(days=days)
                trending_jobs.extend(jobs)
                logger.info(f"Got {len(jobs)} trending jobs from {name}")
            except Exception as e:
                logger.error(f"Failed to get trending jobs from {name}", error=str(e))
        
        return trending_jobs
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all scrapers"""
        health_status = {
            "status": "healthy",
            "scrapers": {}
        }
        
        for name, scraper in self.scrapers.items():
            try:
                scraper_health = await scraper.health_check()
                health_status["scrapers"][name] = scraper_health
                
                if scraper_health.get("status") != "healthy":
                    health_status["status"] = "unhealthy"
                    
            except Exception as e:
                health_status["scrapers"][name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                health_status["status"] = "unhealthy"
        
        return health_status 