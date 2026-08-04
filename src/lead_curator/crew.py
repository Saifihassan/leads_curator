from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from lead_curator.tools.custom_tool import SearxngSearchTool, Crawl4aiSearchTool
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List, Optional

load_dotenv(override=True)
class SearchQueryList(BaseModel):
    queries: List[str] = Field(description="List of highly specialized search queries.")

class Lead(BaseModel):
    name: str
    website: str | None
    linkedin: str | None
    email: str | None
    phone: str | None
    instagram: str | None
    location: str | None
    description: str | None
    services: list[str]
    source_url: str

class LeadExtraction(BaseModel):
    leads: list[Lead]

# gpt4 = LLM(  # analyze
#     model="gpt-5-mini",
#     api_key=os.getenv("BLUESMIND_API_KEY"),
#     base_url=os.getenv("BLUESMIND_BASE_URL"),
    
# )
gpt4 = LLM(  # analyze
    model="minimax-m2.7",
    api_key=os.getenv("GENERALCOMPUTE_API_KEY"),
    base_url=os.getenv("GENERALCOMPUTE_BASE_URL"),
)
nara = LLM(  # analyze
    model="stepfun-3.7-flash",
    api_key=os.getenv("NARAROUTER_API_KEY"),
    base_url=os.getenv("NARAROUTER_BASE_URL"),
)


@CrewBase
class LeadCurator():
    """LeadCurator crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def query_creator(self) -> Agent:
        return Agent(
            config=self.agents_config['query_creator'], # type: ignore[index]
            verbose=True,
            llm=nara
        )

    @agent
    def web_scraper(self) -> Agent:
        return Agent(
            config=self.agents_config['web_scraper'], # type: ignore[index]
            verbose=True,
            tools=[SearxngSearchTool(), Crawl4aiSearchTool()],
            llm=nara
        )

    @agent
    def lead_enricher(self) -> Agent:
        return Agent(
            config=self.agents_config['lead_enricher'], # type: ignore[index]
            verbose=True,
            tools=[SearxngSearchTool(), Crawl4aiSearchTool()],
            llm=nara
        )

    @task
    def query_creation_task(self) -> Task:
        return Task(
            config=self.tasks_config['query_creation_task'], # type: ignore[index]
            output_pydantic=SearchQueryList
        )

    @task
    def data_scraping_task(self) -> Task:
        return Task(
            config=self.tasks_config['data_scraping_task'], # type: ignore[index]
            output_pydantic=LeadExtraction,
            output_file="results.json"
        )

    @task
    def lead_enrichment_task(self) -> Task:
        return Task(
            config=self.tasks_config['lead_enrichment_task'], # type: ignore[index]
            output_pydantic=LeadExtraction,
         
        )

    @crew
    def crew(self) -> Crew:
        """Creates the LeadCurator crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
