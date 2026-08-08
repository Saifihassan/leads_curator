#!/usr/bin/env python
import sys
import warnings

from datetime import datetime

from lead_curator.crew import LeadCurator

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


def run():
    """
    Run the crew.
    """
    inputs = {
        "user_query": "Find marketing and digital marketing agencies in Mumbai, India that could potentially benefit from AI automation services. Prioritize agencies offering SEO, social media marketing, content marketing, PPC, performance marketing, branding, or web development. For each company, find and verify its official website, LinkedIn, Instagram, X/Twitter, public business email, phone number, location, services, company description, and any publicly available information that could help personalize a cold outreach message. Only return information that can be verified from reliable sources; use null when information cannot be verified."
    }

    try:
        LeadCurator().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


