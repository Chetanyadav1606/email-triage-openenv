import random
import logging
from typing import Tuple, List, Dict, Optional
from models import Observation, Reward, Email, Action

logger = logging.getLogger(__name__)


class EmailEnv:
    """
    Email Triage Environment - Simulates real-world customer support workflows.
    
    Features:
    - Multi-email queue management
    - Customer history tracking
    - SLA-aware prioritization
    - Semantic grading with detailed feedback
    """

    MAX_STEPS = 100
    REWARD_WEIGHTS = {
        "classify_correct": 0.3,
        "classify_incorrect": -0.12,
        "prioritize_correct": 0.28,
        "prioritize_incorrect": -0.18,
        "respond_good": 0.38,
        "respond_partial": 0.16,
        "respond_bad": -0.14,
        "close_complete": 0.14,
        "close_early": -0.28,
        "step_penalty": -0.04
    }
    PRIORITY_ORDER = {"low": 1, "medium": 2, "high": 3}

    def __init__(self, emails: List[Email]):
        """
        Initialize the environment.
        
        Args:
            emails: List of Email objects to process
            
        Raises:
            ValueError: If emails list is empty
        """
        if not emails:
            raise ValueError("Emails list cannot be empty")
        
        self.initial_emails = [email.copy(deep=True) for email in emails]
        self.queue: List[Email] = []
        self.current: Optional[Email] = None
        self.history: Dict[str, List[str]] = {}
        self.logs: List[Dict] = []
        self.step_count: int = 0
        self.total_reward: float = 0.0
        self.done: bool = False
        self.email_states: Dict[str, Dict] = {}
        
        logger.info(f"Environment initialized with {len(emails)} emails")

    def reset(self) -> Observation:
        """
        Reset the environment to initial state.
        
        Returns:
            Observation: Initial environment state
        """
        self.queue = [email.copy(deep=True) for email in self.initial_emails]
        random.shuffle(self.queue)
        self.queue.sort(
            key=lambda email: (
                self.PRIORITY_ORDER.get(email.true_priority, 2),
                1 if email.customer_tier == "premium" else 0
            ),
            reverse=True
        )
        self.current = self.queue.pop(0) if self.queue else None
        self.history = {}
        self.logs = []
        self.step_count = 0
        self.total_reward = 0.0
        self.done = False
        self.email_states = {
            email.id: {
                "classified": False,
                "classified_label": None,
                "prioritized": False,
                "assigned_priority": None,
                "assigned_priority_order": None,
                "responded": False,
                "response_text": None,
                "response_quality": 0.0,
                "steps": 0
            }
            for email in self.initial_emails
        }
        
        logger.info("Environment reset")
        return self.state()

    def state(self) -> Observation:
        """Get current environment state."""
        return Observation(
            queue=self.queue.copy() if self.queue else [],
            current_email=self.current,
            history=self.history.copy(),
            step_count=self.step_count
        )

    def _sanitize_text(self, text: str) -> str:
        return " ".join(
            token for token in [
                ''.join(ch for ch in text.lower() if ch.isalnum() or ch.isspace()).strip()
            ] if token
        )

    def _evaluate_response_text(self, response: str, email: Email) -> tuple[float, str]:
        normalized_response = self._sanitize_text(response)
        if not normalized_response or len(normalized_response.split()) < 8:
            return 0.0, "Response too brief or not detailed enough"

        response_words = set(normalized_response.split())
        expected_words = set(self._sanitize_text(email.true_response).split())

        overlap = len(response_words & expected_words)
        subject_body_words = set(self._sanitize_text(email.subject + " " + email.body).split())
        intent_overlap = len(response_words & subject_body_words)

        if overlap >= 3 or (overlap >= 2 and intent_overlap >= 2):
            return 1.0, "Excellent response alignment with customer need"
        if overlap >= 1 or intent_overlap >= 2:
            return 0.6, "Good response, but it could be more specific"

        return 0.2, "Response lacks key issue details"

    def _sort_queue(self) -> None:
        self.queue.sort(
            key=lambda email: (
                self.email_states[email.id].get("assigned_priority_order")
                or self.PRIORITY_ORDER.get(email.true_priority, 2),
                1 if email.customer_tier == "premium" else 0
            ),
            reverse=True
        )

    def _advance_to_next_email(self) -> None:
        if self.queue:
            self._sort_queue()
            self.current = self.queue.pop(0)
        else:
            self.current = None
            self.done = True
            logger.info("All emails processed")

    def step(self, action: Action) -> Tuple[Observation, Reward, bool, Dict]:
        """
        Execute an action in the environment.
        
        Args:
            action: Action to perform
            
        Returns:
            Tuple of (observation, reward, done, info)
            
        Raises:
            ValueError: If action is invalid or email not found
        """
        if self.done:
            logger.warning("Attempted step after environment done")
            raise ValueError("Environment already done. Call reset() to restart.")
        
        if not self.current:
            logger.warning("No current email to process")
            raise ValueError("No current email available")

        email = self.current
        if action.email_id != email.id:
            raise ValueError(f"Action email_id {action.email_id} does not match current email {email.id}")

        reward_value = 0.0
        feedback_parts = []
        state = self.email_states[email.id]

        log_entry = {
            "email_id": email.id,
            "action": action.dict(),
            "step": self.step_count,
            "reward": 0.0
        }

        # Track memory
        if email.customer_id not in self.history:
            self.history[email.customer_id] = []
        self.history[email.customer_id].append(action.action_type)

        try:
            if action.action_type == "classify":
                state["classified"] = True
                state["classified_label"] = action.label
                if action.label == email.true_label:
                    reward_value += self.REWARD_WEIGHTS["classify_correct"]
                    feedback_parts.append("✓ Correct classification")
                    logger.debug(f"Correct classification: {action.label}")
                else:
                    reward_value += self.REWARD_WEIGHTS["classify_incorrect"]
                    feedback_parts.append(f"✗ Incorrect classification: {action.label}")
                    logger.debug(f"Incorrect classification: {action.label} vs {email.true_label}")

            elif action.action_type == "prioritize":
                state["prioritized"] = True
                state["assigned_priority"] = action.priority
                state["assigned_priority_order"] = self.PRIORITY_ORDER.get(action.priority, 1)
                if action.priority == email.true_priority:
                    reward_value += self.REWARD_WEIGHTS["prioritize_correct"]
                    feedback_parts.append("✓ Priority assigned correctly")
                    logger.debug(f"Correct priority: {action.priority}")
                else:
                    reward_value += self.REWARD_WEIGHTS["prioritize_incorrect"]
                    feedback_parts.append(f"✗ Priority mismatch: {action.priority}")
                    logger.debug(f"Priority mismatch: {action.priority} vs {email.true_priority}")
                    if email.customer_tier == "premium" and action.priority != "high":
                        reward_value += -0.08
                        feedback_parts.append("⚠ SLA warning: premium issue should be high priority")

                if not state["classified"]:
                    feedback_parts.append("Tip: classify the issue before you confirm priority.")

            elif action.action_type == "respond":
                state["responded"] = True
                state["response_text"] = action.response
                quality_score, quality_feedback = self._evaluate_response_text(action.response, email)
                state["response_quality"] = quality_score

                if quality_score >= 0.8:
                    reward_value += self.REWARD_WEIGHTS["respond_good"]
                    feedback_parts.append("✓ Strong response quality")
                elif quality_score >= 0.4:
                    reward_value += self.REWARD_WEIGHTS["respond_partial"]
                    feedback_parts.append("⚠ Response OK, could be more specific")
                else:
                    reward_value += self.REWARD_WEIGHTS["respond_bad"]
                    feedback_parts.append("✗ Response needs more detail")

                feedback_parts.append(quality_feedback)
                if not state["prioritized"]:
                    feedback_parts.append("Tip: assign priority before closing this email.")

            elif action.action_type == "close":
                if not state["responded"]:
                    reward_value += self.REWARD_WEIGHTS["close_early"]
                    feedback_parts.append("✗ Closed before sending a response")
                else:
                    reward_value += self.REWARD_WEIGHTS["close_complete"]
                    feedback_parts.append("✓ Email closed after response")

                if not state["classified"]:
                    feedback_parts.append("⚠ Classification was skipped before closing")
                if not state["prioritized"]:
                    feedback_parts.append("⚠ Priority was not assigned before closing")

                self._advance_to_next_email()

            else:
                logger.warning(f"Unknown action type: {action.action_type}")
                raise ValueError(f"Unknown action type: {action.action_type}")

        except AttributeError as e:
            logger.error(f"Invalid action format: {e}")
            raise ValueError(f"Invalid action format: {e}")

        state["steps"] += 1
        reward_value += self.REWARD_WEIGHTS["step_penalty"]

        self.step_count += 1
        if self.step_count > self.MAX_STEPS:
            self.done = True
            reward_value -= 0.5
            feedback_parts.append("⚠ Step limit exceeded")
            logger.warning("Step limit reached")

        log_entry["reward"] = reward_value
        self.total_reward += reward_value
        self.logs.append(log_entry)

        feedback = " | ".join(feedback_parts) if feedback_parts else "Action recorded"

        return (
            self.state(),
            Reward(score=reward_value, feedback=feedback),
            self.done,
            {"logs": self.logs, "total_reward": self.total_reward}
        )

    def evaluate(self) -> float:
        """
        Calculate final score based on performance.
        
        Returns:
            Final evaluation score
        """
        if not self.logs:
            return 0.0

        total_emails = len(self.initial_emails)
        if total_emails == 0:
            return 0.0

        email_map = {email.id: email for email in self.initial_emails}
        classified_correct = 0
        prioritized_correct = 0
        response_score_total = 0.0
        responded_count = 0

        for email_id, state in self.email_states.items():
            email = email_map.get(email_id)
            if not email:
                continue

            if state.get("classified") and state.get("classified_label") == email.true_label:
                classified_correct += 1
            if state.get("prioritized") and state.get("assigned_priority") == email.true_priority:
                prioritized_correct += 1
            if state.get("responded"):
                response_score_total += state.get("response_quality", 0.0)
                responded_count += 1

        classification_score = classified_correct / total_emails
        priority_score = prioritized_correct / total_emails
        response_score = response_score_total / total_emails
        efficiency_score = 1.0 - min(1.0, max(0.0, (self.step_count - total_emails * 4) / max(1, total_emails * 4)))

        final_score = (
            classification_score * 25 +
            priority_score * 25 +
            response_score * 35 +
            efficiency_score * 15
        )

        logger.info(
            f"Evaluation - Score: {final_score:.2f}, Classification: {classification_score:.2f}, "
            f"Priority: {priority_score:.2f}, Response: {response_score:.2f}, Efficiency: {efficiency_score:.2f}"
        )

        return max(0.0, min(100.0, final_score))