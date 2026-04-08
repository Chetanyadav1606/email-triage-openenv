"""
Validation script for OpenEnv Email Triage environment.

Checks compliance with OpenEnv spec requirements:
- Proper models (Observation, Action, Reward)
- Working reset() / step() / state()
- Task definitions with graders
- Reward function verification
- Dockerfile functionality

Run with: python validate_openenv.py
"""

import sys
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def check_imports():
    """Check all required imports"""
    logger.info("\n✓ Checking imports...")
    try:
        from models import Email, Action, Observation, Reward
        from environment import EmailEnv
        from task_suite import TaskSuite, EasyTaskGrader, MediumTaskGrader, HardTaskGrader
        from data_loader import DatasetLoader
        from inference import BaselineAgent
        logger.info("  ✅ All imports successful")
        return True
    except ImportError as e:
        logger.error(f"  ❌ Import failed: {e}")
        return False


def check_models():
    """Check Pydantic models"""
    logger.info("\n✓ Checking Pydantic models...")
    try:
        from models import Email, Action, Observation, Reward
        
        # Create instances
        email = Email(
            id="test-1",
            subject="Test",
            body="Test body",
            customer_id="C1",
            customer_tier="premium",
            true_label="billing",
            true_priority="high",
            true_response="Test response"
        )
        
        action = Action(
            action_type="classify",
            email_id="test-1",
            label="billing"
        )
        
        obs = Observation(
            queue=[email],
            current_email=email,
            history={},
            step_count=1
        )
        
        reward = Reward(score=0.5, feedback="Test")
        
        logger.info("  ✅ All models instantiate correctly")
        return True
    except Exception as e:
        logger.error(f"  ❌ Model check failed: {e}")
        return False


def check_environment():
    """Check EmailEnv API"""
    logger.info("\n✓ Checking environment API...")
    try:
        from environment import EmailEnv
        from models import Action
        from tasks import load_tasks
        
        # Create environment
        emails = load_tasks()
        env = EmailEnv(emails)
        
        # Test reset
        initial_state = env.reset()
        assert initial_state is not None
        assert initial_state.current_email is not None
        logger.info("  ✅ reset() works")
        
        # Test state
        state = env.state()
        assert state is not None
        logger.info("  ✅ state() works")
        
        # Test step
        action = Action(
            action_type="classify",
            email_id=initial_state.current_email.id,
            label="billing"
        )
        obs, reward, done, info = env.step(action)
        assert obs is not None
        assert reward is not None
        logger.info("  ✅ step() works")
        
        return True
    except Exception as e:
        logger.error(f"  ❌ Environment check failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_tasks():
    """Check task suite"""
    logger.info("\n✓ Checking task suite...")
    try:
        from task_suite import TaskSuite
        
        suite = TaskSuite()
        
        # Check all difficulties
        for difficulty in ["easy", "medium", "hard"]:
            task_def = suite.get_task_definition(difficulty)
            assert task_def is not None
            logger.info(f"  ✅ {difficulty.capitalize()} task defined")
            
            # Check grader
            grader = suite.create_grader_for_task(difficulty)
            assert grader is not None
            logger.info(f"  ✅ {difficulty.capitalize()} grader created")
        
        return True
    except Exception as e:
        logger.error(f"  ❌ Task check failed: {e}")
        return False


def check_yaml():
    """Check OpenEnv YAML"""
    logger.info("\n✓ Checking OpenEnv YAML...")
    try:
        import yaml
        
        yaml_path = Path("openenv.yaml")
        if not yaml_path.exists():
            logger.error("  ❌ openenv.yaml not found")
            return False
        
        with open(yaml_path) as f:
            spec = yaml.safe_load(f)
        
        required_fields = ["name", "version", "description", "environment_spec", "tasks"]
        for field in required_fields:
            if field not in spec:
                logger.error(f"  ❌ Missing {field}")
                return False
        
        # Check tasks
        assert "easy" in spec.get("tasks", {})
        assert "medium" in spec.get("tasks", {})
        assert "hard" in spec.get("tasks", {})
        
        logger.info("  ✅ OpenEnv YAML valid")
        return True
    except Exception as e:
        logger.error(f"  ❌ YAML check failed: {e}")
        return False


def check_graders():
    """Check grader scoring"""
    logger.info("\n✓ Checking graders...")
    try:
        from environment import EmailEnv
        from task_suite import TaskSuite
        from models import Action
        from tasks import load_tasks
        
        suite = TaskSuite()
        
        for difficulty in ["easy", "medium", "hard"]:
            emails = load_tasks()
            env = EmailEnv(emails)
            env.reset()
            
            # Take a few actions
            for _ in range(3):
                if env.current:
                    action = Action(
                        action_type="classify",
                        email_id=env.current.id,
                        label=env.current.true_label
                    )
                    env.step(action)
            
            # Grade
            grader = suite.create_grader_for_task(difficulty)
            score = grader.grade(env.logs, emails)
            
            assert 0.0 <= score <= 1.0, f"Score out of range: {score}"
            assert isinstance(score, float)
            
            logger.info(f"  ✅ {difficulty.capitalize()} grader scores: {score:.3f}")
        
        return True
    except Exception as e:
        logger.error(f"  ❌ Grader check failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_data_loader():
    """Check data loading"""
    logger.info("\n✓ Checking data loader...")
    try:
        from data_loader import DatasetLoader
        
        loader = DatasetLoader()
        
        # Test CSV loading
        emails = loader.load_local_csv("data/sample_emails.csv", limit=5)
        assert len(emails) > 0
        logger.info(f"  ✅ Loaded {len(emails)} emails from CSV")
        
        # Test augmentation
        logger.info("  ✅ Data loader working")
        return True
    except Exception as e:
        logger.error(f"  ❌ Data loader check failed: {e}")
        return False


def check_docker():
    """Check Dockerfile"""
    logger.info("\n✓ Checking Dockerfile...")
    try:
        dockerfile_path = Path("Dockerfile")
        if not dockerfile_path.exists():
            logger.error("  ❌ Dockerfile not found")
            return False
        
        content = dockerfile_path.read_text()
        
        required_commands = ["FROM", "WORKDIR", "COPY", "RUN pip", "EXPOSE", "CMD"]
        for cmd in required_commands:
            if cmd not in content:
                logger.error(f"  ❌ Missing {cmd}")
                return False
        
        logger.info("  ✅ Dockerfile valid")
        return True
    except Exception as e:
        logger.error(f"  ❌ Dockerfile check failed: {e}")
        return False


def check_reward_function():
    """Check reward function"""
    logger.info("\n✓ Checking reward function...")
    try:
        from environment import EmailEnv
        from models import Action
        from tasks import load_tasks
        
        emails = load_tasks()
        env = EmailEnv(emails)
        env.reset()
        
        rewards = []
        for _ in range(5):
            if env.current:
                action = Action(
                    action_type="classify",
                    email_id=env.current.id,
                    label=env.current.true_label
                )
                obs, reward, done, info = env.step(action)
                rewards.append(reward.score)
        
        # Check variation
        if len(set(rewards)) > 1:
            logger.info("  ✅ Reward function provides varying signal")
        else:
            logger.warning("  ⚠️  Reward function may need variation")
        
        # Check range
        for r in rewards:
            assert -1.0 <= r <= 1.0, f"Reward out of range: {r}"
        
        logger.info("  ✅ Reward function valid")
        return True
    except Exception as e:
        logger.error(f"  ❌ Reward function check failed: {e}")
        return False


def main():
    """Run all checks"""
    logger.info("="*60)
    logger.info("🚀 OpenEnv Email Triage - Specification Validation")
    logger.info("="*60)
    
    checks = [
        ("Imports", check_imports),
        ("Pydantic Models", check_models),
        ("Environment API", check_environment),
        ("Task Suite", check_tasks),
        ("Graders", check_graders),
        ("Data Loader", check_data_loader),
        ("Reward Function", check_reward_function),
        ("OpenEnv YAML", check_yaml),
        ("Dockerfile", check_docker),
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            logger.error(f"❌ {name}: {e}")
            results[name] = False
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("📊 VALIDATION SUMMARY")
    logger.info("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{name:25} {status}")
    
    logger.info("-"*60)
    logger.info(f"Total: {passed}/{total} checks passed")
    logger.info("="*60)
    
    if passed == total:
        logger.info("\n🎉 Environment is OpenEnv compliant!")
        return 0
    else:
        logger.error(f"\n⚠️  {total - passed} checks failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
