"""
Grading system for email triage performance evaluation.

Provides comprehensive feedback on:
- Classification accuracy
- Priority assignment correctness
- Response quality
- Overall efficiency
"""

import logging
from typing import Dict, List, Tuple
from models import Email

logger = logging.getLogger(__name__)


class GradeMetrics:
    """Container for grading metrics"""
    def __init__(self):
        self.total_emails = 0
        self.correct_classifications = 0
        self.correct_priorities = 0
        self.responses_sent = 0
        self.good_responses = 0
        self.total_steps = 0
        self.total_reward = 0.0

    def accuracy_score(self) -> float:
        """Calculate classification accuracy (0-1)"""
        if self.total_emails == 0:
            return 0.0
        return self.correct_classifications / self.total_emails

    def priority_score(self) -> float:
        """Calculate priority accuracy (0-1)"""
        if self.total_emails == 0:
            return 0.0
        return self.correct_priorities / self.total_emails

    def response_score(self) -> float:
        """Calculate response quality score (0-1)"""
        if self.total_emails == 0:
            return 0.0
        base_rate = self.responses_sent / self.total_emails
        quality_bonus = self.good_responses / max(1, self.total_emails) * 0.5
        return min(1.0, base_rate + quality_bonus)

    def efficiency_score(self) -> float:
        """Calculate efficiency based on steps (0-1)"""
        optimal_steps = self.total_emails * 3  # 3 steps per email ideally
        if optimal_steps == 0:
            return 0.0
        return 1.0 - min(1.0, (self.total_steps - optimal_steps) / (optimal_steps * 2))

    def overall_score(self) -> float:
        """Calculate weighted overall score (0-100)"""
        weights = {
            "accuracy": 0.35,
            "priority": 0.25,
            "response": 0.20,
            "efficiency": 0.20
        }
        
        score = (
            self.accuracy_score() * weights["accuracy"] * 100 +
            self.priority_score() * weights["priority"] * 100 +
            self.response_score() * weights["response"] * 100 +
            self.efficiency_score() * weights["efficiency"] * 100
        )
        
        return score

    def to_dict(self) -> Dict:
        """Convert metrics to dictionary"""
        return {
            "total_emails": self.total_emails,
            "correct_classifications": self.correct_classifications,
            "correct_priorities": self.correct_priorities,
            "responses_sent": self.responses_sent,
            "good_responses": self.good_responses,
            "total_steps": self.total_steps,
            "total_reward": self.total_reward,
            "accuracy": round(self.accuracy_score(), 3),
            "priority_accuracy": round(self.priority_score(), 3),
            "response_score": round(self.response_score(), 3),
            "efficiency": round(self.efficiency_score(), 3),
            "overall_score": round(self.overall_score(), 2)
        }


class EmailTriageGrader:
    """Grades email triage performance"""

    def __init__(self):
        self.metrics = GradeMetrics()
        logger.info("Grader initialized")

    def grade_log(self, logs: List[Dict], emails: List[Email]) -> GradeMetrics:
        """
        Grade a batch of logs against ground truth emails.
        
        Args:
            logs: List of action logs
            emails: List of ground truth emails
            
        Returns:
            GradeMetrics object with detailed results
        """
        metrics = GradeMetrics()
        email_map = {email.id: email for email in emails}
        
        seen_emails = set()
        for log in logs:
            email_id = log.get("email_id")
            action = log.get("action", {})
            
            if email_id not in email_map:
                logger.warning(f"Email {email_id} not found in ground truth")
                continue
            
            email = email_map[email_id]
            seen_emails.add(email_id)
            
            if action.get("action_type") == "classify":
                if action.get("label") == email.true_label:
                    metrics.correct_classifications += 1
                    logger.debug(f"Email {email_id}: Classification correct")
            
            elif action.get("action_type") == "prioritize":
                if action.get("priority") == email.true_priority:
                    metrics.correct_priorities += 1
                    logger.debug(f"Email {email_id}: Priority correct")
            
            elif action.get("action_type") == "respond":
                metrics.responses_sent += 1
                logger.debug(f"Email {email_id}: Response sent")
                response_text = (action.get("response") or "").lower()
                expected_text = email.true_response.lower()
                overlap = sum(1 for word in expected_text.split() if word in response_text)
                if overlap >= 2:
                    metrics.good_responses += 1
                    logger.debug(f"Email {email_id}: Response quality good")

        metrics.total_emails = len(seen_emails)
        
        metrics.total_steps = len(logs)
        self.metrics = metrics
        
        logger.info(f"Grading complete: {metrics.overall_score():.2f}/100")
        return metrics

    def get_feedback(self, metrics: GradeMetrics) -> str:
        """
        Generate human-readable feedback.
        
        Args:
            metrics: GradeMetrics object
            
        Returns:
            Feedback string with recommendations
        """
        score = metrics.overall_score()
        feedback_parts = []
        
        # Overall assessment
        if score >= 80:
            feedback_parts.append("🌟 Excellent performance!")
        elif score >= 60:
            feedback_parts.append("👍 Good job, keep improving!")
        elif score >= 40:
            feedback_parts.append("📈 Room for improvement")
        else:
            feedback_parts.append("💡 Focus on the basics")
        
        # Detailed metrics
        feedback_parts.append(f"\n📊 Detailed Metrics:")
        feedback_parts.append(f"  • Classification Accuracy: {metrics.accuracy_score()*100:.1f}%")
        feedback_parts.append(f"  • Priority Accuracy: {metrics.priority_score()*100:.1f}%")
        feedback_parts.append(f"  • Response Rate: {metrics.response_score()*100:.1f}%")
        feedback_parts.append(f"  • Efficiency: {metrics.efficiency_score()*100:.1f}%")
        
        # Recommendations
        feedback_parts.append(f"\n💡 Recommendations:")
        
        if metrics.accuracy_score() < 0.7:
            feedback_parts.append("  • Focus on correct email classification")
        
        if metrics.priority_score() < 0.7:
            feedback_parts.append("  • Improve priority assignment accuracy")
        
        if metrics.response_score() < 0.8:
            feedback_parts.append("  • Ensure consistent customer responses")
        
        if metrics.efficiency_score() < 0.7:
            feedback_parts.append("  • Optimize workflow efficiency (reduce steps)")
        
        if metrics.accuracy_score() >= 0.8 and metrics.efficiency_score() >= 0.8:
            feedback_parts.append("  • You're doing great! Keep up the excellent work!")
        
        return "\n".join(feedback_parts)

    def rank_performance(self, score: float) -> str:
        """Get performance tier based on score"""
        if score >= 90:
            return "S Tier 🌟"
        elif score >= 80:
            return "A Tier ⭐"
        elif score >= 70:
            return "B Tier 👍"
        elif score >= 60:
            return "C Tier 📈"
        else:
            return "D Tier 💪"

    def compare_metrics(self, m1: GradeMetrics, m2: GradeMetrics) -> Dict:
        """
        Compare two metric sets.
        
        Args:
            m1: First metrics
            m2: Second metrics
            
        Returns:
            Dictionary with comparison results
        """
        return {
            "accuracy_improvement": m2.accuracy_score() - m1.accuracy_score(),
            "priority_improvement": m2.priority_score() - m1.priority_score(),
            "efficiency_improvement": m2.efficiency_score() - m1.efficiency_score(),
            "overall_improvement": m2.overall_score() - m1.overall_score(),
            "better": "Yes ✅" if m2.overall_score() > m1.overall_score() else "No ❌"
        }
