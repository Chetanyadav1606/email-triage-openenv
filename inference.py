#!/usr/bin/env python3
"""
Baseline inference script for OpenEnv Email Triage.

Uses Hugging Face OpenAI-compatible API to generate a baseline score on all 3 task difficulties.
Records reproducible scores for model evaluation.

Usage:
    python baseline_inference.py
    
Environment variables required:
    - HF_TOKEN: Your Hugging Face API token
      (PowerShell: $env:HF_TOKEN = "hf_...")
      (CMD: set HF_TOKEN=hf_...)
      (Linux/macOS: export HF_TOKEN="hf_...")

Optional:
    - DIFFICULTY: 'easy', 'medium', 'hard', or 'all' (default: all)
    - TEMPERATURE: Model temperature (default: 0.7)
    - MODEL: Model name (default: gpt-4o-mini)
"""

import os
import sys
import json
import logging
import random
from datetime import datetime
from typing import Dict, List, Tuple
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Check Hugging Face API token
api_key = os.getenv("HF_TOKEN")
if not api_key:
    logger.error("❌ HF_TOKEN environment variable not set")
    logger.error("Set HF_TOKEN for Hugging Face API access")
    sys.exit(1)

try:
    import openai
    from environment import EmailEnv
    from task_suite import TaskSuite
    from models import Action
except ImportError as e:
    logger.error(f"❌ Missing dependency: {e}")
    logger.error("Install with: pip install openai")
    sys.exit(1)

# Use Hugging Face OpenAI-compatible API base endpoint
openai.api_base = "https://api.openai.huggingface.co/v1"
openai.api_key = api_key


class BaselineAgent:
    """AI agent using Hugging Face OpenAI-compatible inference for email triage"""

    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 0.7):
        """
        Initialize the agent.
        
        Args:
            model: OpenAI-compatible model name
            temperature: Sampling temperature (0.0-1.0)
        """
        openai.api_key = api_key
        self.client = openai
        self.model = model
        self.temperature = temperature
        self.logs = []
        logger.info(f"Initialized {model} agent with temperature={temperature}")

    def run_task(self, difficulty: str, max_steps: int = 100) -> Tuple[float, Dict]:
        """
        Run agent on a task difficulty.
        
        Args:
            difficulty: 'easy', 'medium', or 'hard'
            max_steps: Maximum steps to allow
            
        Returns:
            Tuple of (final_score, results_dict)
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"🎯 Starting {difficulty.upper()} Task")
        logger.info(f"{'='*60}")

        # Load task
        task_suite = TaskSuite()
        task_def = task_suite.get_task_definition(difficulty)
        emails = task_suite.load_task_emails(difficulty)

        logger.info(f"📧 Task: {task_def.name}")
        logger.info(f"📝 Description: {task_def.description}")
        logger.info(f"📊 Total emails: {len(emails)}")

        # Initialize environment
        random.seed(0)
        env = EmailEnv(emails)
        initial_state = env.reset()

        step_count = 0
        total_reward = 0.0
        actions_taken = []

        # Process emails
        while not env.done and step_count < max_steps:
            if not env.current:
                break

            step_count += 1
            
            # Get suggestion from LLM
            action = self._get_action_from_llm(env.current, difficulty)
            
            if not action:
                logger.warning(f"Failed to get action from LLM, skipping step")
                continue
            
            actions_taken.append({
                "step": step_count,
                "type": action.action_type,
                "email": env.current.subject[:50]
            })

            # Execute action
            obs, reward, done, info = env.step(action)
            total_reward += reward.score

            # Log
            logger.info(
                f"Step {step_count:2d}: {action.action_type:12} | "
                f"Email: {env.current.subject[:40]:40} | "
                f"Reward: {reward.score:+.2f} | {reward.feedback}"
            )

            env.done = done

        # Grade
        logger.info(f"\n📊 Evaluation...")
        
        grader = task_suite.create_grader_for_task(difficulty)
        final_score = grader.grade(env.logs, emails)
        feedback = grader.get_feedback(final_score)

        results = {
            "difficulty": difficulty,
            "task": task_def.name,
            "model": self.model,
            "temperature": self.temperature,
            "total_steps": step_count,
            "emails_processed": len([a for a in actions_taken if a["type"] in ["classify", "prioritize", "respond"]]),
            "total_reward": total_reward,
            "final_score": final_score,
            "expected_score": task_def.expected_score,
            "score_vs_expected": final_score / task_def.expected_score if task_def.expected_score > 0 else 0,
            "feedback": feedback,
            "actions": actions_taken
        }

        logger.info(f"✅ Final Score: {final_score:.3f}/1.0")
        logger.info(f"📈 Expected:   {task_def.expected_score:.3f}/1.0")
        logger.info(f"📊 Feedback:   {feedback}")

        self.logs.append(results)
        return final_score, results

    def _get_action_from_llm(self, email, difficulty: str) -> Action:
        """
        Ask LLM for the next action to take.
        
        Args:
            email: Current email to process
            difficulty: Task difficulty for context
            
        Returns:
            Action object
        """
        # Build prompt
        prompt = self._build_prompt(email, difficulty)

        try:
            response = self.client.ChatCompletion.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert customer support email triage agent. "
                            "Analyze emails and respond with JSON-formatted actions. "
                            "Be accurate and efficient."
                        )
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0,
                max_tokens=500
            )

            response_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            try:
                # Try to extract JSON from response
                if "{" in response_text:
                    json_str = response_text[response_text.index("{"):response_text.rindex("}") + 1]
                    action_dict = json.loads(json_str)
                else:
                    logger.warning(f"No JSON in response: {response_text}")
                    return None

                # Create Action
                action = Action(
                    action_type=action_dict.get("action_type", "classify"),
                    email_id=email.id,
                    label=action_dict.get("label"),
                    priority=action_dict.get("priority"),
                    response=action_dict.get("response")
                )

                return action

            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON: {response_text[:100]}")
                return None

        except Exception as e:
            logger.error(f"Hugging Face API error: {e}")
            return None

    def _build_prompt(self, email, difficulty: str) -> str:
        """Build prompt for the LLM"""
        
        if difficulty == "easy":
            return f"""Classify this email into one of: billing, technical, feature, general.
            
Subject: {email.subject}
Body: {email.body}

Respond with JSON:
{{"action_type": "classify", "label": "<category>"}}
            """

        elif difficulty == "medium":
            return f"""Analyze this email. First classify it, then prioritize it.

Subject: {email.subject}
Body: {email.body}
Customer Tier: {email.customer_tier}

Respond with prioritized JSON:
{{"action_type": "prioritize", "priority": "<low|medium|high>"}}

Or for classification first:
{{"action_type": "classify", "label": "<billing|technical|feature|general>"}}
            """

        else:  # hard
            return f"""Complete triage workflow for this email:
1. Classify into: billing, technical, feature, general
2. Prioritize: low, medium, high
3. Draft response appropriate for {email.customer_tier} customer

Subject: {email.subject}
Body: {email.body}
Customer ID: {email.customer_id}
Tier: {email.customer_tier}

Choose next action and respond with JSON:
{{"action_type": "<classify|prioritize|respond>", "label": "...", "priority": "...", "response": "..."}}
            """

    def save_results(self, output_file: str = "baseline_results.json"):
        """Save results to JSON file"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "model": self.model,
            "temperature": self.temperature,
            "tasks": self.logs,
            "summary": {
                "total_tasks": len(self.logs),
                "average_score": sum(l["final_score"] for l in self.logs) / len(self.logs) if self.logs else 0,
                "all_difficulties": [l["difficulty"] for l in self.logs]
            }
        }

        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"\n✅ Results saved to {output_file}")


def main():
    """Run baseline inference on all difficulties"""
    
    # Configuration from environment
    model = os.getenv("MODEL", "gpt-4o-mini")
    temperature = float(os.getenv("TEMPERATURE", "0.0"))
    difficulty = os.getenv("DIFFICULTY", "all")
    
    logger.info("🚀 OpenEnv Email Triage - Baseline Inference")
    logger.info(f"Model: {model}")
    logger.info(f"Temperature: {temperature}")
    logger.info("")

    # Initialize agent
    agent = BaselineAgent(model=model, temperature=temperature)

    # Determine tasks
    if difficulty == "all":
        tasks = ["easy", "medium", "hard"]
    else:
        tasks = [difficulty]

    all_scores = {}

    # Run each task
    for task_difficulty in tasks:
        try:
            score, results = agent.run_task(task_difficulty)
            all_scores[task_difficulty] = score
        except Exception as e:
            logger.error(f"Error running {task_difficulty} task: {e}")
            import traceback
            traceback.print_exc()

    # Summary
    logger.info(f"\n\n{'='*60}")
    logger.info("📊 BASELINE RESULTS SUMMARY")
    logger.info(f"{'='*60}")
    
    for difficulty, score in all_scores.items():
        logger.info(f"{difficulty.upper():10} → Score: {score:.3f}/1.0")
    
    if all_scores:
        avg_score = sum(all_scores.values()) / len(all_scores)
        logger.info(f"{'AVERAGE':10} → Score: {avg_score:.3f}/1.0")
    
    logger.info(f"{'='*60}\n")

    # Save results
    agent.save_results()


if __name__ == "__main__":
    main()
