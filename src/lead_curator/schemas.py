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
    TWITTER = "twitter"
    INSTAGRAM = "instagram"
    WEBSITE = "website"
    CLUTCH = "clutch"
    G2 = "g2"
    CRUNCHBASE = "crunchbase"
    OTHER = "other"


class SearchStrategy(str, Enum):
    DIRECT_SITE_SEARCH = "direct_site_search"
    DIRECTORY_SCRAPE = "directory_scrape"
    HYBRID = "hybrid"
    SOCIAL_SEARCH = "social_search"


class PageType(str, Enum):
    LINKEDIN_PROFILE = "linkedin_profile"
    LINKEDIN_COMPANY = "linkedin_company"
    TWITTER_PROFILE = "twitter_profile"
    INSTAGRAM_PROFILE = "instagram_profile"
    DIRECTORY_LISTING = "directory_listing"
    PERSONAL_WEBSITE = "personal_website"
    COMPANY_WEBSITE = "company_website"
    JOB_POSTING = "job_posting"
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
# RAW ENTITY — Output of Scraper Agent
# ═══════════════════════════════════════════════════════════════

class RawEntity(BaseModel):
    """
    Unprocessed data extracted from a single URL by Crawl4AI.
    Produced by the Scraper Agent.
    """
    source_url: str = Field(description="URL this data was scraped from")
    page_type: PageType = Field(description="Classification of the source page")
    extracted_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Key-value pairs extracted from the page"
    )
    extraction_confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Overall confidence in the extraction"
    )
    field_confidences: Dict[str, float] = Field(
        default_factory=dict,
        description="Per-field confidence scores"
    )
    errors: List[str] = Field(
        default_factory=list,
        description="Any extraction errors or missing fields"
    )
    html_snapshot_path: Optional[str] = Field(
        default=None,
        description="Path to saved raw HTML (if stored)"
    )
    scraped_at: datetime = Field(default_factory=datetime.utcnow)


class RawEntityList(BaseModel):
    """Wrapper for a list of RawEntities."""
    entities: List[RawEntity]
    successful_scrapes: int
    failed_scrapes: int
    total_urls_attempted: int


# ═══════════════════════════════════════════════════════════════
# ENRICHED ENTITY — Output of Enricher Agent
# ═══════════════════════════════════════════════════════════════

class EnrichmentSource(BaseModel):
    """Documents a single enrichment action."""
    field_added: str = Field(description="Which field was enriched")
    value: Any = Field(description="The enriched value")
    source_url: str = Field(description="URL where the data was found")
    source_query: str = Field(description="Search query used to find it")
    confidence: float = Field(ge=0.0, le=1.0)
    enriched_at: datetime = Field(default_factory=datetime.utcnow)


class EnrichedEntity(BaseModel):
    """
    A RawEntity with missing fields filled in by the Enricher Agent.
    """
    # Carry forward all raw data
    source_url: str
    page_type: PageType
    extracted_data: Dict[str, Any]
    extraction_confidence: float
    field_confidences: Dict[str, float]
    errors: List[str]
    html_snapshot_path: Optional[str] = None
    scraped_at: datetime

    # Enrichment additions
    enriched_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Fields added during enrichment"
    )
    enrichment_sources: List[EnrichmentSource] = Field(
        default_factory=list,
        description="Audit trail of all enrichments"
    )
    enrichment_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence in the enrichment layer"
    )
    fields_missing: List[str] = Field(
        default_factory=list,
        description="Fields still missing after enrichment"
    )
    overall_confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Combined extraction + enrichment confidence"
    )


class EnrichedEntityList(BaseModel):
    """Wrapper for a list of EnrichedEntities."""
    entities: List[EnrichedEntity]
    total_enriched: int
    total_unenriched: int
    average_confidence: float


# ═══════════════════════════════════════════════════════════════
# DECISION MAKER — Nested in OutreachTarget
# ═══════════════════════════════════════════════════════════════

class DecisionMaker(BaseModel):
    """
    A key contact person within a company.
    """
    name: str = Field(description="Full name")
    title: str = Field(description="Job title")
    linkedin_url: Optional[str] = Field(default=None)
    email: Optional[EmailStr] = Field(default=None)
    twitter_url: Optional[str] = Field(default=None)
    is_primary_contact: bool = Field(
        default=False,
        description="Is this the best person to reach out to?"
    )
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)


# ═══════════════════════════════════════════════════════════════
# OUTREACH TARGET — Final Output
# ═══════════════════════════════════════════════════════════════

class OutreachTarget(BaseModel):
    """
    The final, refined output entity ready for outreach.
    Produced by the Data Processor Agent.
    """
    # ── Core Identity ──
    entity_type: EntityType = Field(description="Type of entity")
    name: str = Field(description="Entity name (person or company)")
    platform: Platform = Field(description="Primary platform discovered on")
    platform_url: Optional[str] = Field(
        default=None,
        description="Direct URL on the primary platform"
    )

    # ── Location & Industry ──
    location: Optional[str] = Field(default=None)
    headquarters: Optional[str] = Field(
        default=None,
        description="The main headquarters location (distinct from general office locations)"
    )
    location_relevance_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Score of how well the location matches requested (HQ=1.0, office=0.6, mention=0.2)"
    )
    industry: Optional[str] = Field(default=None)
    company_size: Optional[str] = Field(
        default=None,
        description="e.g., '11-50', '201-500'"
    )

    # ── Contact & Links ──
    website: Optional[str] = Field(default=None)
    email: Optional[EmailStr] = Field(default=None)
    phone: Optional[str] = Field(default=None)
    social_links: Dict[str, str] = Field(
        default_factory=dict,
        description="Other platform URLs: {'twitter': '...', 'github': '...'}"
    )

    # ── Company-Specific ──
    description: Optional[str] = Field(
        default=None,
        description="What the company does / person's headline"
    )
    services: Optional[List[str]] = Field(
        default=None,
        description="Services offered (for companies)"
    )
    decision_makers: Optional[List[DecisionMaker]] = Field(
        default=None,
        description="Key contacts (for companies)"
    )
    employee_count: Optional[str] = Field(default=None)
    specialties: Optional[List[str]] = Field(default=None)

    # ── Person-Specific ──
    current_company: Optional[str] = Field(default=None)
    headline: Optional[str] = Field(default=None)
    experience_summary: Optional[str] = Field(default=None)
    education: Optional[str] = Field(default=None)

    # ── Context for Outreach ──
    recent_activity: Optional[str] = Field(
        default=None,
        description="Recent post, hiring announcement, funding news"
    )
    pain_points: Optional[List[str]] = Field(
        default=None,
        description="AI-inferred outreach angles"
    )
    outreach_angle: Optional[str] = Field(
        default=None,
        description="Suggested angle for the freelancer's pitch"
    )

    # ── Metadata ──
    source_urls: List[str] = Field(
        default_factory=list,
        description="All URLs that contributed to this entity"
    )
    confidence_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Overall data quality score"
    )
    completeness_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Percentage of required fields present"
    )
    discovered_at: datetime = Field(default_factory=datetime.utcnow)
    search_query: str = Field(description="Original user query")
    task_plan_id: Optional[str] = Field(
        default=None,
        description="Reference to the TaskPlan that generated this"
    )


class OutreachTargetList(BaseModel):
    """Final output wrapper."""
    targets: List[OutreachTarget] = Field(description="Final outreach-ready entities")
    total_returned: int
    total_deduplicated: int = Field(description="How many duplicates were removed")
    average_confidence: float
    query: str = Field(description="Original user query")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# ═══════════════════════════════════════════════════════════════
# EXTRACTION SCHEMAS — Passed to Crawl4AI per page_type
# ═══════════════════════════════════════════════════════════════

LINKEDIN_COMPANY_SCHEMA = {
    "name": "Company name",
    "industry": "Industry category",
    "location": "Company office branches/locations",
    "headquarters": "Company headquarters location",
    "employee_count": "Number of employees or range",
    "website": "Company website URL",
    "description": "About section / what the company does",
    "specialties": "List of specialties or services",
    "company_size": "Size category like 11-50 employees"
}

LINKEDIN_PROFILE_SCHEMA = {
    "name": "Person's full name",
    "headline": "Professional headline",
    "location": "Person's location",
    "current_company": "Current company name",
    "current_title": "Current job title",
    "experience_summary": "Brief summary of experience",
    "education": "Education background",
    "skills": "List of skills"
}

DIRECTORY_LISTING_SCHEMA = {
    "name": "Company or agency name",
    "location": "Office location",
    "headquarters": "Headquarters location",
    "website": "Official website",
    "services": "Services offered",
    "contact_email": "Contact email if visible",
    "phone": "Phone number if visible",
    "rating": "Rating or review score",
    "review_count": "Number of reviews",
    "description": "About the company"
}

TWITTER_PROFILE_SCHEMA = {
    "name": "Display name",
    "handle": "Twitter handle without @",
    "bio": "Profile bio",
    "location": "Location from profile",
    "follower_count": "Number of followers",
    "following_count": "Number following",
    "recent_tweets_summary": "Summary of recent tweet topics",
    "website": "Linked website if any"
}

PERSONAL_WEBSITE_SCHEMA = {
    "name": "Person or company name",
    "title": "Job title or role",
    "services": "Services or offerings",
    "contact_email": "Email address",
    "about": "About section",
    "location": "Location if mentioned"
}

EXTRACTION_SCHEMAS = {
    PageType.LINKEDIN_COMPANY: LINKEDIN_COMPANY_SCHEMA,
    PageType.LINKEDIN_PROFILE: LINKEDIN_PROFILE_SCHEMA,
    PageType.DIRECTORY_LISTING: DIRECTORY_LISTING_SCHEMA,
    PageType.TWITTER_PROFILE: TWITTER_PROFILE_SCHEMA,
    PageType.PERSONAL_WEBSITE: PERSONAL_WEBSITE_SCHEMA,
    PageType.COMPANY_WEBSITE: DIRECTORY_LISTING_SCHEMA,
}


def get_extraction_schema(page_type: PageType) -> dict:
    """Get the appropriate Crawl4AI extraction schema for a page type."""
    return EXTRACTION_SCHEMAS.get(page_type, {
        "name": "Entity name",
        "description": "What this entity does",
        "location": "Location if mentioned",
        "contact_info": "Any contact information found"
    })
