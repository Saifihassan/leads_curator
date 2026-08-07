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
        "user_query": "need linkedin,twitter/x,instagram handles of digital marketing agencies situated in bangalore"
    }

    try:
        LeadCurator().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


