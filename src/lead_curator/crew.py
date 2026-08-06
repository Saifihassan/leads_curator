from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from lead_curator.tools.custom_tool import SearxngSearchTool, Crawl4aiSearchTool
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List, Optional, Literal

from lead_curator.schemas import (
    TaskPlan,
    TargetURLList,
    RawEntityList,
    EnrichedEntityList,
    OutreachTargetList
)

load_dotenv(override=True)

minimax = LLM(  # analyze
    model="minimax-m2.7",
    api_key=os.getenv("GENERALCOMPUTE_API_KEY"),
    base_url=os.getenv("GENERALCOMPUTE_BASE_URL"),
)
nara = LLM(  # analyze
    model="mistral-large",
    api_key=os.getenv("NARAROUTER_API_KEY"),
    base_url=os.getenv("NARAROUTER_BASE_URL"),
)
gpt = LLM(  # analyze
    model="gpt-5-mini",
    api_key=os.getenv("BLUESMIND_API_KEY"),
    base_url=os.getenv("BLUESMIND_BASE_URL"),
)


@CrewBase
class LeadCurator():
    """LeadCurator crew"""

    agents: list[BaseAgent]
    tasks: list[Task]


    @agent 
    def orchestrator(self) -> Agent:
        return Agent(
            config=self.agents_config['orchestrator'], # type: ignore[index]
            verbose=True,
            llm=minimax
        )

    @agent
    def research_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['research_agent'], # type: ignore[index]
            verbose=True,
            tools=[SearxngSearchTool()],
            llm=gpt

        )

    @agent
    def scraper_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['scraper_agent'], # type: ignore[index]
            verbose=True,
            tools=[Crawl4aiSearchTool()],
            llm=minimax
        )

    @agent
    def enricher_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['enricher_agent'], # type: ignore[index]
            verbose=True,
            tools=[SearxngSearchTool(), Crawl4aiSearchTool()],
            llm=nara
        )

    @agent
    def data_processor(self) -> Agent:
        return Agent(
            config=self.agents_config['data_processor'], # type: ignore[index]
            verbose=True,
            llm=minimax
        )

    @task
    def plan_outreach_mission(self) -> Task:
        return Task(
            config=self.tasks_config['plan_outreach_mission'], # type: ignore[index]
            output_pydantic=TaskPlan
        )

    @task
    def discover_target_urls(self) -> Task:
        return Task(
            config=self.tasks_config['discover_target_urls'], # type: ignore[index]
            output_pydantic=TargetURLList
        )

    @task
    def scrape_discovered_urls(self) -> Task:
        return Task(
            config=self.tasks_config['scrape_discovered_urls'], # type: ignore[index]
            output_pydantic=RawEntityList
        )

    @task
    def enrich_incomplete_entities(self) -> Task:
        return Task(
            config=self.tasks_config['enrich_incomplete_entities'], # type: ignore[index]
            output_pydantic=EnrichedEntityList
        )

    @task
    def refine_and_format_output(self) -> Task:
        return Task(
            config=self.tasks_config['refine_and_format_output'], # type: ignore[index]
            output_pydantic=OutreachTargetList,
            output_file="results.json"
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
