"""
schemas.py — Pydantic models for the Freelance Outreach Agent System
Compatible with CrewAI output_json and Pydantic v2
"""

from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional, List, Dict, Literal, Any
from datetime import datetime
from enum import Enum


# ═══════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════

class EntityType(str, Enum):
    PERSON = "person"
    COMPANY = "company"
    JOB_POSTING = "job_posting"
    EVENT = "event"
    GROUP = "group"


class Platform(str, Enum):
    LINKEDIN = "linkedin"
    WEBSITE = "website"
    CLUTCH = "clutch"
    G2 = "g2"
    CRUNCHBASE = "crunchbase"
    WELLFOUND = "wellfound"


class SearchStrategy(str, Enum):
    DIRECT_SITE_SEARCH = "direct_site_search"
    DIRECTORY_SCRAPE = "directory_scrape"
    HYBRID = "hybrid"
    SOCIAL_SEARCH = "social_search"


class PageType(str, Enum):
    LINKEDIN_PROFILE = "linkedin_profile"
    LINKEDIN_COMPANY = "linkedin_company"
    DIRECTORY_LISTING = "directory_listing"
    COMPANY_WEBSITE = "company_website"
    UNKNOWN = "unknown"


class Priority(int, Enum):
    HIGH = 1
    MEDIUM = 2
    LOW = 3


# ═══════════════════════════════════════════════════════════════
# TASK PLAN — Output of Orchestrator Agent
# ═══════════════════════════════════════════════════════════════

class TaskPlan(BaseModel):
    """
    Structured plan produced by the Orchestrator Agent.
    Guides all downstream agents.
    """
    entity_type: EntityType = Field(
        description="What kind of entity the user is looking for"
    )
    platforms: List[Platform] = Field(
        default=[Platform.LINKEDIN],
        description="Which platforms to search on"
    )
    location: Optional[str] = Field(
        default=None,
        description="Geographic constraint (city, region, country)"
    )
    industry: Optional[str] = Field(
        default=None,
        description="Industry or vertical constraint"
    )
    keywords: List[str] = Field(
        default_factory=list,
        description="Additional keywords to refine search"
    )
    required_fields: List[str] = Field(
        default_factory=lambda: ["name", "platform_url"],
        description="Fields that MUST be present in final output"
    )
    search_strategy: SearchStrategy = Field(
        default=SearchStrategy.HYBRID,
        description="Approach to finding targets"
    )
    estimated_results: int = Field(
        default=20,
        ge=1,
        le=50,
        description="Target number of results to return"
    )
    special_instructions: Optional[str] = Field(
        default=None,
        description="Any extra constraints (e.g., 'only companies hiring', 'CEOs only')"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this plan was generated"
    )

    @field_validator("estimated_results")
    @classmethod
    def cap_results(cls, v: int) -> int:
        return min(v, 50)


# ═══════════════════════════════════════════════════════════════
# TARGET URL — Output of Research Agent
# ═══════════════════════════════════════════════════════════════

class TargetURL(BaseModel):
    """
    A discovered URL ready for scraping.
    Produced by the Research Agent via SearXNG.
    """
    url: str = Field(description="The discovered URL")
    source_query: str = Field(description="Which search query found this URL")
    relevance_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence that this URL matches the user's intent"
    )
    page_type: PageType = Field(
        default=PageType.UNKNOWN,
        description="Classification of the page"
    )
    priority: Priority = Field(
        default=Priority.MEDIUM,
        description="Scrape priority — 1 = highest"
    )
    title: Optional[str] = Field(
        default=None,
        description="Page title from search result"
    )
    snippet: Optional[str] = Field(
        default=None,
        description="Search result snippet"
    )
    discovered_at: datetime = Field(
        default_factory=datetime.utcnow
    )

    @field_validator("relevance_score")
    @classmethod
    def clamp_score(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class TargetURLList(BaseModel):
    """Wrapper for a list of TargetURLs."""
    urls: List[TargetURL] = Field(description="Ranked list of URLs to scrape")
    total_discovered: int = Field(description="Total URLs found before filtering")
    search_queries_used: List[str] = Field(default_factory=list)


# ═══════════════════════════════════════════════════════════════
# OUTREACH TARGET — Final Output
# ═══════════════════════════════════════════════════════════════

class OutreachTarget(BaseModel):
    """
    The output entity ready for outreach.
    Produced by the Scraper and Enricher Agents.
    """
    # ── Core Identity ──
    entity_type: EntityType = Field(description="Type of entity")
    name: str = Field(description="Entity name (person or company)")
    
    # ── Description ──
    description: Optional[str] = Field(
        default=None,
        description="Brief description of the person or company"
    )

    # ── Contact Info ──
    email: Optional[EmailStr] = Field(default=None, description="Email address")
    phone: Optional[str] = Field(default=None, description="Phone number")
    website: Optional[str] = Field(default=None, description="Website URL")
    
    # ── Social Media Handles & Links ──
    platform: Platform = Field(description="Primary platform discovered on")
    platform_url: Optional[str] = Field(
        default=None,
        description="Direct URL on the primary platform"
    )
    linkedin: Optional[str] = Field(default=None, description="LinkedIn URL or handle")
    twitter: Optional[str] = Field(default=None, description="Twitter/X URL or handle")
    instagram: Optional[str] = Field(default=None, description="Instagram URL or handle")
    other_socials: Optional[List[str]] = Field(default=None, description="Other social media URLs")

    # ── Metadata ──
    source_urls: List[str] = Field(
        default_factory=list,
        description="All URLs that contributed to this entity"
    )
    discovered_at: datetime = Field(default_factory=datetime.utcnow)


class OutreachTargetList(BaseModel):
    """Final output wrapper."""
    targets: List[OutreachTarget] = Field(description="Final outreach-ready entities")


# ═══════════════════════════════════════════════════════════════
# EXTRACTION SCHEMAS — Passed to Crawl4AI per page_type
# ═══════════════════════════════════════════════════════════════

LINKEDIN_COMPANY_SCHEMA = {
    "name": "Company name",
    "website": "Company website URL",
    "description": "About section / what the company does",
    "contact_email": "Contact email if visible",
    "phone": "Phone number if visible",
    "social_links": "Any social media handles found (Twitter, Instagram, etc)"
}

LINKEDIN_PROFILE_SCHEMA = {
    "name": "Person's full name",
    "current_company": "Current company name",
    "contact_email": "Contact email if visible",
    "phone": "Phone number if visible",
    "social_links": "Any social media handles found (Twitter, Instagram, etc)"
}

DIRECTORY_LISTING_SCHEMA = {
    "name": "Company or agency name",
    "website": "Official website",
    "contact_email": "Contact email if visible",
    "phone": "Phone number if visible",
    "description": "About the company",
    "social_links": "Any social media handles found (Twitter, Instagram, etc)"
}

TWITTER_PROFILE_SCHEMA = {
    "name": "Display name",
    "handle": "Twitter handle without @",
    "website": "Linked website if any",
    "contact_email": "Contact email if visible",
    "phone": "Phone number if visible"
}

PERSONAL_WEBSITE_SCHEMA = {
    "name": "Person or company name",
    "contact_email": "Email address",
    "phone": "Phone number if visible",
    "social_links": "Any social media handles found (Twitter, Instagram, LinkedIn, etc)"
}

EXTRACTION_SCHEMAS = {
    PageType.LINKEDIN_COMPANY: LINKEDIN_COMPANY_SCHEMA,
    PageType.LINKEDIN_PROFILE: LINKEDIN_PROFILE_SCHEMA,
    PageType.DIRECTORY_LISTING: DIRECTORY_LISTING_SCHEMA,
    PageType.COMPANY_WEBSITE: DIRECTORY_LISTING_SCHEMA,
}


def get_extraction_schema(page_type: PageType) -> dict:
    """Get the appropriate Crawl4AI extraction schema for a page type."""
    return EXTRACTION_SCHEMAS.get(page_type, {
        "name": "Entity name",
        "description": "What this entity does",
        "contact_email": "Email address",
        "phone": "Phone number",
        "social_links": "Any social media handles found (Twitter, Instagram, etc)"
    })
