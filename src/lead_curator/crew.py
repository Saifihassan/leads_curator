from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from lead_curator.tools.custom_tool import SearxngSearchTool, Crawl4aiSearchTool
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List, Optional

class SearchQueryList(BaseModel):
    queries: List[str] = Field(description="List of highly specialized search queries.")

class LeadProfile(BaseModel):
    name: Optional[str] = Field(description="Name of the person")
    linkedin: Optional[str] = Field(description="LinkedIn profile URL")
    email: Optional[str] = Field(description="Email address")
    instagram: Optional[str] = Field(description="Instagram profile URL")
    x_account: Optional[str] = Field(description="X (Twitter) profile URL")
    other_info: Optional[str] = Field(description="Any other relevant extracted info")

class LeadReport(BaseModel):
    leads: List[LeadProfile] = Field(description="List of scraped leads")

load_dotenv(override=True)

gpt4 = LLM(  # analyze
    model="minimax-m2.7",
    api_key=os.getenv("GENERALCOMPUTE_API_KEY"),
    base_url=os.getenv("GENERALCOMPUTE_BASE_URL"),
    
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
            llm=gpt4
        )

    @agent
    def web_scraper(self) -> Agent:
        return Agent(
            config=self.agents_config['web_scraper'], # type: ignore[index]
            verbose=True,
            tools=[SearxngSearchTool(), Crawl4aiSearchTool()],
            llm=gpt4
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
            output_file='report.json',
            output_pydantic=LeadReport
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
