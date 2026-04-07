"""
Gerenciador de CSV
"""

import csv
import logging
import os
import time
from typing import List, Set, Dict, Any, Optional

import requests
from bs4 import BeautifulSoup
import bibtexparser

from src.models import Article, EvaluationResult
from src.config import Config


logger = logging.getLogger(__name__)

class CSVHandler:

    FIELDNAMES = [
        "bibtex_id",
        "title",
        "abstract",
        "decision",
        "justification",
        "model_name",
        "prompt_version",
        "execution_date",
        "processing_time_seconds"
    ]

    @staticmethod
    def file_exists(csv_file: str) -> bool:
        return os.path.exists(csv_file)

    @staticmethod
    def get_processed_ids(csv_file: str) -> Set[str]:

        if not CSVHandler.file_exists(csv_file):
            return set()

        processed = set()

        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("bibtex_id"):
                    processed.add(row["bibtex_id"])

        return processed

    @staticmethod
    def write_result(csv_file: str, result: EvaluationResult) -> None:

        file_exists = CSVHandler.file_exists(csv_file)

        with open(csv_file, "a", newline="", encoding="utf-8") as f:

            writer = csv.DictWriter(f, fieldnames=CSVHandler.FIELDNAMES)

            if not file_exists:
                writer.writeheader()

            writer.writerow({
                "bibtex_id": result.bibtex_id,
                "title": result.title,
                "abstract": result.abstract,
                "decision": result.evaluation.decision,
                "justification": result.evaluation.justification,
                "model_name": result.model_name,
                "prompt_version": result.prompt_version,
                "execution_date": result.execution_date.isoformat(),
                "processing_time_seconds": result.processing_time_seconds,
            })

    @staticmethod
    def read_results(csv_file: str) -> List[Dict[str, Any]]:

        if not CSVHandler.file_exists(csv_file):
            return []

        with open(csv_file, "r", encoding="utf-8") as f:
            return list(csv.DictReader(f))