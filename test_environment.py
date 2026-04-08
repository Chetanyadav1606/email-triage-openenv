"""
Test suite for OpenEnv Email Triage environment.

Run with: python test_environment.py
"""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from models import Email, Action, Observation
from environment import EmailEnv
from tasks import load_tasks
from grader import EmailTriageGrader


def test_models():
    """Test Pydantic models"""
    print("\n📋 Testing Models...")
    
    try:
        # Test Email creation
        email = Email(
            id="test-1",
            subject="Test Subject",
            body="Test Body",
            customer_id="C1",
            customer_tier="premium",
            true_label="billing",
            true_priority="high",
            true_response="Test Response"
        )
        assert email.id == "test-1"
        print("  ✅ Email model works")
        
        # Test Action creation
        action = Action(
            action_type="classify",
            email_id="test-1",
            label="billing"
        )
        assert action.action_type == "classify"
        print("  ✅ Action model works")
        
    except Exception as e:
        print(f"  ❌ Model test failed: {e}")
        return False
    
    return True


def test_environment():
    """Test EmailEnv"""
    print("\n🏢 Testing Environment...")
    
    try:
        tasks = load_tasks()
        env = EmailEnv(tasks)
        print(f"  ✅ Environment initialized with {len(tasks)} emails")
        
        # Test reset
        obs = env.reset()
        assert obs.current_email is not None
        assert isinstance(obs, Observation)
        print("  ✅ Reset works")
        
        # Test step
        action = Action(
            action_type="classify",
            email_id=obs.current_email.id,
            label="billing"
        )
        next_obs, reward, done, info = env.step(action)
        assert isinstance(next_obs, Observation)
        assert reward.score != 0
        print("  ✅ Step execution works")
        
        # Test evaluate
        score = env.evaluate()
        assert isinstance(score, float)
        print("  ✅ Evaluation works")
        
    except Exception as e:
        print(f"  ❌ Environment test failed: {e}")
        return False
    
    return True


def test_grader():
    """Test EmailTriageGrader"""
    print("\n🎓 Testing Grader...")
    
    try:
        grader = EmailTriageGrader()
        print("  ✅ Grader initialized")
        
        # Run a simple session
        tasks = load_tasks()
        env = EmailEnv(tasks)
        env.reset()
        
        # Take a few actions
        for i in range(3):
            if env.current:
                action = Action(
                    action_type="classify",
                    email_id=env.current.id,
                    label=env.current.true_label
                )
                env.step(action)
            else:
                break
        
        # Grade the session
        metrics = grader.grade_log(env.logs, tasks)
        assert metrics.total_steps > 0
        print(f"  ✅ Grading works - Score: {metrics.overall_score():.2f}/100")
        
        # Test feedback
        feedback = grader.get_feedback(metrics)
        assert len(feedback) > 0
        print("  ✅ Feedback generation works")
        
    except Exception as e:
        print(f"  ❌ Grader test failed: {e}")
        return False
    
    return True


def test_tasks():
    """Test task loading"""
    print("\n📧 Testing Tasks...")
    
    try:
        tasks = load_tasks()
        assert len(tasks) > 0
        print(f"  ✅ Loaded {len(tasks)} tasks")
        
        # Verify each task
        for task in tasks:
            assert task.id
            assert task.subject
            assert task.body
            assert task.customer_id
            assert task.true_label
            assert task.true_priority
        
        print("  ✅ All tasks are valid")
        
    except Exception as e:
        print(f"  ❌ Task loading failed: {e}")
        return False
    
    return True


def test_full_workflow():
    """Test complete workflow"""
    print("\n🎮 Testing Full Workflow...")
    
    try:
        # Initialize
        tasks = load_tasks()
        env = EmailEnv(tasks)
        grader = EmailTriageGrader()
        
        # Reset
        env.reset()
        initial_queue = len(env.queue)
        print(f"  📧 Started with {initial_queue + 1} emails in queue")
        
        # Process multiple emails
        steps = 0
        max_steps = 10
        
        while not env.done and steps < max_steps:
            if env.current:
                # Choose action based on email
                if steps % 4 == 0:
                    action_type = "classify"
                    action = Action(
                        action_type=action_type,
                        email_id=env.current.id,
                        label=env.current.true_label if steps % 2 == 0 else "general"
                    )
                elif steps % 4 == 1:
                    action_type = "prioritize"
                    action = Action(
                        action_type=action_type,
                        email_id=env.current.id,
                        priority=env.current.true_priority
                    )
                elif steps % 4 == 2:
                    action_type = "respond"
                    action = Action(
                        action_type=action_type,
                        email_id=env.current.id,
                        response="Thank you for contacting us."
                    )
                else:
                    action_type = "close"
                    action = Action(
                        action_type=action_type,
                        email_id=env.current.id
                    )
                
                obs, reward, done, info = env.step(action)
                steps += 1
                print(f"  Step {steps}: {action_type:12} → Reward: {reward.score:+.2f} | {reward.feedback}")
            else:
                break
        
        print(f"  ✅ Processed {steps} actions")
        
        # Grade
        metrics = grader.grade_log(env.logs, tasks)
        print(f"  📊 Final Score: {metrics.overall_score():.2f}/100")
        print(f"  Accuracy: {metrics.accuracy_score()*100:.1f}%")
        print(f"  Efficiency: {metrics.efficiency_score()*100:.1f}%")
        
    except Exception as e:
        print(f"  ❌ Full workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("🧪 OpenEnv Email Triage Test Suite")
    print("=" * 60)
    
    tests = [
        ("Models", test_models),
        ("Tasks", test_tasks),
        ("Environment", test_environment),
        ("Grader", test_grader),
        ("Full Workflow", test_full_workflow),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} {status}")
    
    print("-" * 60)
    print(f"Total: {passed}/{total} tests passed")
    print("=" * 60)
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
