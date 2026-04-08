"""
Task definitions with progressive difficulty levels.

Each task represents a different challenge level with:
- Clear objectives
- Deterministic graders
- Difficulties: Easy → Medium → Hard
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
from models import Email
from data_loader import DatasetLoader
import logging

logger = logging.getLogger(__name__)


@dataclass
class TaskDefinition:
    """Definition of a task with metadata"""
    name: str
    difficulty: str  # easy, medium, hard
    description: str
    num_emails: int
    expected_score: float  # Expected baseline score
    objective: str


class TaskSuite:
    """Suite of email triage tasks with varying difficulty"""

    # Task definitions
    TASKS = {
        "easy": TaskDefinition(
            name="Email Classification",
            difficulty="easy",
            description="Correctly classify emails into billing, technical, feature, or general categories",
            num_emails=20,
            expected_score=0.75,
            objective="Achieve >70% classification accuracy"
        ),
        "medium": TaskDefinition(
            name="Priority-Based Triage",
            difficulty="medium",
            description="Classify emails AND assign correct priority (low/medium/high) based on content and customer tier",
            num_emails=40,
            expected_score=0.60,
            objective="Achieve >60% combined accuracy with correct responses"
        ),
        "hard": TaskDefinition(
            name="Full Support Workflow",
            difficulty="hard",
            description="Complete workflow: classify, prioritize, send appropriate response, AND handle SLA penalties for premium customers",
            num_emails=60,
            expected_score=0.50,
            objective="Maintain >50% overall score while handling complex multi-task workflow"
        ),
    }

    def __init__(self):
        """Initialize task suite"""
        self.loader = DatasetLoader()
        self.tasks_data = {}

    def load_task_emails(self, difficulty: str, limit: Optional[int] = None) -> List[Email]:
        """
        Load emails for a specific task difficulty.
        
        Args:
            difficulty: 'easy', 'medium', or 'hard'
            limit: Override max emails
            
        Returns:
            List of Email objects for the task
        """
        if difficulty not in self.TASKS:
            raise ValueError(f"Unknown difficulty: {difficulty}")

        task_def = self.TASKS[difficulty]
        max_emails = limit or task_def.num_emails

        logger.info(f"Loading {difficulty} task with {max_emails} emails...")

        # Try to load real data first
        try:
            emails = self.loader.load_kaggle_dataset("wcukierski/enron-email-dataset", limit=max_emails * 2)
        except:
            emails = self.loader._get_fallback_emails(limit=max_emails * 2)

        # Augment with labels if needed
        emails = self.loader.augment_emails_with_labels(emails)

        # Filter by difficulty
        filtered = self._filter_by_difficulty(emails, difficulty)[:max_emails]

        if len(filtered) < max_emails:
            logger.warning(f"Only found {len(filtered)} emails, using fallback data")
            fallback = self.loader._get_fallback_emails(limit=max_emails - len(filtered))
            filtered.extend(fallback)

        logger.info(f"Loaded {len(filtered)} emails for {difficulty} task")
        return filtered

    def _filter_by_difficulty(self, emails: List[Email], difficulty: str) -> List[Email]:
        """Filter and sort emails by difficulty level"""
        
        if difficulty == "easy":
            # Easy: emails with clear, unambiguous subjects
            return [e for e in emails if len(e.subject) > 20 and len(e.subject) < 100]
        
        elif difficulty == "medium":
            # Medium: varied subjects, multiple labels
            return emails  # All emails are medium difficulty
        
        elif difficulty == "hard":
            # Hard: complex scenarios, ambiguous content
            # Prioritize emails with longer bodies (more context to parse)
            complex_emails = [e for e in emails if len(e.body) > 200]
            return sorted(complex_emails, key=lambda e: -len(e.body))[:len(emails)//2]
        
        return emails

    def get_task_definition(self, difficulty: str) -> TaskDefinition:
        """Get task metadata"""
        return self.TASKS.get(difficulty)

    def get_all_tasks(self) -> Dict[str, TaskDefinition]:
        """Get all task definitions"""
        return self.TASKS.copy()

    @staticmethod
    def create_grader_for_task(difficulty: str):
        """
        Create a grader function appropriate for the task difficulty.
        
        Args:
            difficulty: Task difficulty level
            
        Returns:
            Grader function that scores performance
        """
        if difficulty == "easy":
            return EasyTaskGrader()
        elif difficulty == "medium":
            return MediumTaskGrader()
        elif difficulty == "hard":
            return HardTaskGrader()
        else:
            raise ValueError(f"Unknown difficulty: {difficulty}")


class TaskGrader:
    """Base class for task graders"""

    def grade(self, logs: List[Dict], emails: List[Email]) -> float:
        """
        Grade performance on a task.
        
        Args:
            logs: Action logs from environment
            emails: Original emails from task
            
        Returns:
            Score from 0.0 to 1.0
        """
        raise NotImplementedError

    def get_feedback(self, score: float) -> str:
        """Get human-readable feedback"""
        raise NotImplementedError


class EasyTaskGrader(TaskGrader):
    """Grader for easy classification task"""

    def grade(self, logs: List[Dict], emails: List[Email]) -> float:
        """
        Grade classification accuracy.
        Only care about correct classifications.
        """
        if not logs:
            return 0.0

        email_map = {e.id: e for e in emails}
        classify_actions = [l for l in logs if l.get("action", {}).get("action_type") == "classify"]

        if not classify_actions:
            return 0.0

        correct = 0
        for log in classify_actions:
            email_id = log.get("email_id")
            action = log.get("action", {})
            
            if email_id in email_map:
                email = email_map[email_id]
                if action.get("label") == email.true_label:
                    correct += 1

        accuracy = correct / len(classify_actions) if classify_actions else 0.0
        # Scale: if >80% accuracy, score closer to 1.0
        return min(1.0, accuracy * 1.2)

    def get_feedback(self, score: float) -> str:
        if score >= 0.9:
            return "Excellent! Near-perfect classification accuracy."
        elif score >= 0.8:
            return "Great job! Strong classification performance."
        elif score >= 0.7:
            return "Good. Solid classification, but room to improve."
        elif score >= 0.5:
            return "Acceptable, but focus on category patterns."
        else:
            return "Poor. Review category definitions and email content more carefully."


class MediumTaskGrader(TaskGrader):
    """Grader for medium multi-task workflow"""

    def grade(self, logs: List[Dict], emails: List[Email]) -> float:
        """
        Grade multi-task performance:
        - Classification accuracy (40%)
        - Priority accuracy (30%)
        - Response rate (20%)
        - Efficiency (10%)
        """
        if not logs:
            return 0.0

        email_map = {e.id: e for e in emails}
        metrics = {
            "classify_correct": 0,
            "classify_total": 0,
            "prioritize_correct": 0,
            "prioritize_total": 0,
            "responses": 0,
            "total_steps": len(logs)
        }

        for log in logs:
            email_id = log.get("email_id")
            action = log.get("action", {})
            
            if email_id not in email_map:
                continue
            
            email = email_map[email_id]
            
            if action.get("action_type") == "classify":
                metrics["classify_total"] += 1
                if action.get("label") == email.true_label:
                    metrics["classify_correct"] += 1
            
            elif action.get("action_type") == "prioritize":
                metrics["prioritize_total"] += 1
                if action.get("priority") == email.true_priority:
                    metrics["prioritize_correct"] += 1
            
            elif action.get("action_type") == "respond":
                metrics["responses"] += 1

        # Calculate component scores
        class_score = (metrics["classify_correct"] / metrics["classify_total"]) if metrics["classify_total"] > 0 else 0
        priority_score = (metrics["prioritize_correct"] / metrics["prioritize_total"]) if metrics["prioritize_total"] > 0 else 0
        response_score = min(1.0, metrics["responses"] / len(emails)) if emails else 0
        efficiency_score = 1.0 - min(1.0, metrics["total_steps"] / (len(emails) * 4))

        # Weighted combination
        score = (
            class_score * 0.4 +
            priority_score * 0.3 +
            response_score * 0.2 +
            efficiency_score * 0.1
        )

        return min(1.0, score)

    def get_feedback(self, score: float) -> str:
        if score >= 0.8:
            return "Excellent multi-task execution! Strong accuracy across all dimensions."
        elif score >= 0.6:
            return "Good workflow execution. Consider improving priority assignment."
        elif score >= 0.4:
            return "Moderate performance. Focus on consistency and response quality."
        else:
            return "Needs improvement. Ensure you're completing all task steps."


class HardTaskGrader(TaskGrader):
    """Grader for hard full-workflow task with SLA penalties"""

    def grade(self, logs: List[Dict], emails: List[Email]) -> float:
        """
        Grade complex workflow with SLA penalties:
        - Classification (25%)
        - Priority (25%)
        - Response Rate (20%)
        - SLA Compliance (20%)
        - Efficiency (10%)
        """
        if not logs:
            return 0.0

        email_map = {e.id: e for e in emails}
        metrics = {
            "classify_correct": 0,
            "classify_total": 0,
            "prioritize_correct": 0,
            "prioritize_total": 0,
            "responses": 0,
            "sla_violations": 0,
            "total_steps": len(logs),
            "premium_missed": 0
        }

        for log in logs:
            email_id = log.get("email_id")
            action = log.get("action", {})
            
            if email_id not in email_map:
                continue
            
            email = email_map[email_id]
            
            # Check SLA: premium should be high priority
            if email.customer_tier == "premium" and email.true_priority == "high":
                if action.get("action_type") == "prioritize" and action.get("priority") != "high":
                    metrics["sla_violations"] += 1
                    metrics["premium_missed"] += 1

            if action.get("action_type") == "classify":
                metrics["classify_total"] += 1
                if action.get("label") == email.true_label:
                    metrics["classify_correct"] += 1
            
            elif action.get("action_type") == "prioritize":
                metrics["prioritize_total"] += 1
                if action.get("priority") == email.true_priority:
                    metrics["prioritize_correct"] += 1
            
            elif action.get("action_type") == "respond":
                metrics["responses"] += 1

        # Calculate component scores
        class_score = (metrics["classify_correct"] / metrics["classify_total"]) if metrics["classify_total"] > 0 else 0
        priority_score = (metrics["prioritize_correct"] / metrics["prioritize_total"]) if metrics["prioritize_total"] > 0 else 0
        response_score = min(1.0, metrics["responses"] / len(emails)) if emails else 0
        efficiency_score = 1.0 - min(1.0, metrics["total_steps"] / (len(emails) * 5))
        
        # SLA compliance: penalty for missing premium cases
        sla_score = 1.0 - (metrics["premium_missed"] / max(1, len([e for e in emails if e.customer_tier == "premium"])) * 0.5)

        # Weighted combination with SLA penalties
        score = (
            class_score * 0.25 +
            priority_score * 0.25 +
            response_score * 0.2 +
            sla_score * 0.2 +
            efficiency_score * 0.1
        )

        return min(1.0, max(0.0, score))

    def get_feedback(self, score: float) -> str:
        if score >= 0.8:
            return "Outstanding! Excellent SLA compliance and workflow execution."
        elif score >= 0.6:
            return "Good performance. Watch for premium customer SLA violations."
        elif score >= 0.4:
            return "Acceptable. Focus on SLA compliance and response consistency."
        else:
            return "Poor. Critical SLA violations. Prioritize premium customers properly."
