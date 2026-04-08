"""
Email tasks and datasets for the triage environment.

Includes realistic customer support scenarios covering:
- Billing issues
- Technical problems
- Feature requests
- Account issues
"""

from models import Email


def load_tasks():
    """
    Load sample emails for training and evaluation.
    
    Returns:
        List of Email objects with realistic support scenarios
    """
    return [
        # Easy difficulty - Clear classification
        Email(
            id="1",
            subject="Payment failed - Card declined",
            body="I tried to renew my subscription but my card was declined. "
                 "Can you help me complete this transaction?",
            customer_id="C1",
            customer_tier="premium",
            true_label="billing",
            true_priority="high",
            true_response="We'll help you resolve the payment issue. "
                         "Please try a different card or contact your bank."
        ),
        Email(
            id="2",
            subject="App crashes on login screen",
            body="Every time I try to log in, the app shows a white screen "
                 "and crashes. This started happening today.",
            customer_id="C2",
            customer_tier="free",
            true_label="technical",
            true_priority="medium",
            true_response="Thank you for reporting. We're investigating this issue. "
                         "Try clearing your app cache and reinstalling if possible."
        ),
        Email(
            id="3",
            subject="Refund request for last purchase",
            body="I purchased the annual plan last week but it's not what I expected. "
                 "I'd like a refund.",
            customer_id="C1",
            customer_tier="premium",
            true_label="billing",
            true_priority="high",
            true_response="We can process a refund. Our team will contact you within 24 hours."
        ),
        
        # Medium difficulty - Context-dependent
        Email(
            id="4",
            subject="Request: Dark mode feature",
            body="The app would be so much better with a dark mode. "
                 "My eyes hurt when using it at night.",
            customer_id="C3",
            customer_tier="free",
            true_label="feature",
            true_priority="low",
            true_response="Great suggestion! We've added this to our roadmap. "
                         "We'll notify you when it's released."
        ),
        Email(
            id="5",
            subject="Account locked - suspicious activity",
            body="I can't log in to my account. It says suspicious activity was detected. "
                 "I haven't done anything unusual. How do I unlock it?",
            customer_id="C4",
            customer_tier="premium",
            true_label="technical",
            true_priority="high",
            true_response="For security reasons, we've locked your account. "
                         "Click the link in your email to verify your identity."
        ),
        
        # Hard difficulty - Complex scenarios
        Email(
            id="6",
            subject="Billing concern - Unexpected charges",
            body="I was charged twice this month. The invoice shows two separate charges "
                 "for the same date. Please explain what happened and issue a refund.",
            customer_id="C5",
            customer_tier="enterprise",
            true_label="billing",
            true_priority="high",
            true_response="We apologize for the duplicate charge. We've immediately issued "
                         "a refund. You should see it in 3-5 business days."
        ),
        Email(
            id="7",
            subject="API integration failing - urgent",
            body="We've been trying to integrate your API for 2 days. "
                 "Getting 500 errors on every request to /v2/users endpoint. "
                 "This is blocking our product launch. URGENT!",
            customer_id="C6",
            customer_tier="enterprise",
            true_label="technical",
            true_priority="high",
            true_response="We've escalated this to our engineering team immediately. "
                         "Our lead engineer will contact you in the next 30 minutes."
        ),
        Email(
            id="8",
            subject="General inquiry - How to...",
            body="How do I export my data from the platform? "
                 "I need to share my usage statistics with my team.",
            customer_id="C7",
            customer_tier="free",
            true_label="general",
            true_priority="low",
            true_response="You can export your data by going to Settings > Data Export. "
                         "We support CSV and JSON formats."
        ),
        Email(
            id="9",
            subject="Feature suggestion - Bulk operations",
            body="Would love to see bulk upload feature. Currently I have to add "
                 "100 items one by one. That's very time consuming.",
            customer_id="C3",
            customer_tier="premium",
            true_label="feature",
            true_priority="medium",
            true_response="Thank you for the suggestion. We're considering bulk operations "
                         "for our Q3 roadmap. Your feedback helps us prioritize!"
        ),
        Email(
            id="10",
            subject="Cannot reset password",
            body="I forgot my password and tried to reset it. I never get the reset email. "
                 "I've checked spam folder too.",
            customer_id="C8",
            customer_tier="free",
            true_label="technical",
            true_priority="medium",
            true_response="Let's troubleshoot this. Try requesting the reset again, "
                         "and include an alternative email if available."
        ),
    ]


def load_evaluation_tasks():
    """
    Load additional emails for comprehensive evaluation.
    
    Returns:
        List of Email objects for evaluation
    """
    return load_tasks()  # Can be extended with more tasks for evaluation


def load_demo_tasks():
    """
    Load simplified tasks for quick demonstration.
    
    Returns:
        List of 3 Email objects for quick demo
    """
    return load_tasks()[:3]