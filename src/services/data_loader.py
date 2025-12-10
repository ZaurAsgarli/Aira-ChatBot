import json
import logging
from typing import List, Dict, Any
from pathlib import Path

from src.config import settings
from src.models.db_schema import Course, Mentor, Learner

# Configure logging
logger = logging.getLogger(__name__)


class DataLoader:
    """
    Responsible for loading raw JSON data and converting it
    into strict Pydantic models.
    """

    def __init__(self, data_dir: str = "data/raw"):
        # Converts string path to a real Path object
        self.data_dir = Path(data_dir)

    def _load_json_file(self, filename: str) -> List[Dict[str, Any]]:
        """Helper to read a JSON file safely."""
        file_path = self.data_dir / filename
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                logger.info(f"Successfully loaded {len(data)} items from {filename}")
                return data
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON in {filename}: {e}")
            return []

    def load_courses(self) -> List[Course]:
        """Loads courses.json and validates against Course model."""
        raw_data = self._load_json_file("courses.json")
        courses = []
        for item in raw_data:
            try:
                course = Course(**item)
                courses.append(course)
            except Exception as e:
                logger.warning(f"Skipping invalid course ID {item.get('id')}: {e}")

        logger.info(f"Validated {len(courses)}/{len(raw_data)} courses.")
        return courses

    def load_mentors(self) -> List[Mentor]:
        """Loads mentors.json and validates against Mentor model."""
        raw_data = self._load_json_file("mentors.json")
        mentors = []
        for item in raw_data:
            try:
                # Validates fields like 'ad', 'soyad', 'bacariqlar'
                mentor = Mentor(**item)
                mentors.append(mentor)
            except Exception as e:
                logger.warning(f"Skipping invalid mentor ID {item.get('id')}: {e}")

        logger.info(f"Validated {len(mentors)}/{len(raw_data)} mentors.")
        return mentors

    def load_learners(self) -> List[Learner]:
        """Loads learners.json and validates against Learner model."""
        raw_data = self._load_json_file("learners.json")
        learners = []
        for item in raw_data:
            try:
                learner = Learner(**item)
                learners.append(learner)
            except Exception as e:
                logger.warning(f"Skipping invalid learner ID {item.get('id')}: {e}")

        logger.info(f"Validated {len(learners)}/{len(raw_data)} learners.")
        return learners


# Singleton instance to be used elsewhere
data_loader = DataLoader()
