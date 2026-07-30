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
        "user_query": "linkedin profiles of marketing agencies situated in delhi,agra,mumbai"
    }

    try:
        LeadCurator().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


