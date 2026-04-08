from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict
from enum import Enum


class TierType(str, Enum):
    """Customer tier levels"""
    FREE = "free"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class LabelType(str, Enum):
    """Email classification categories"""
    BILLING = "billing"
    TECHNICAL = "technical"
    GENERAL = "general"
    FEATURE = "feature"


class PriorityType(str, Enum):
    """Priority levels for emails"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ActionType(str, Enum):
    """Types of actions available"""
    CLASSIFY = "classify"
    PRIORITIZE = "prioritize"
    RESPOND = "respond"
    CLOSE = "close"


class Email(BaseModel):
    """Represents a customer support email"""
    id: str = Field(..., description="Unique email identifier")
    subject: str = Field(..., min_length=1, description="Email subject line")
    body: str = Field(..., min_length=1, description="Email body content")
    customer_id: str = Field(..., description="Customer identifier")
    customer_tier: str = Field(..., description="Customer subscription tier")
    true_label: str = Field(..., description="Ground truth classification")
    true_priority: str = Field(..., description="Ground truth priority")
    true_response: str = Field(..., min_length=1, description="Expected response text")

    class Config:
        schema_extra = {
            "example": {
                "id": "1",
                "subject": "Payment failed",
                "body": "Card declined",
                "customer_id": "C1",
                "customer_tier": "premium",
                "true_label": "billing",
                "true_priority": "high",
                "true_response": "Retry payment or contact bank"
            }
        }


class Observation(BaseModel):
    """Current state of the environment"""
    queue: List[Email] = Field(default_factory=list, description="Remaining emails in queue")
    current_email: Optional[Email] = Field(None, description="Currently active email")
    history: Dict[str, List[str]] = Field(default_factory=dict, description="Action history per customer")
    step_count: int = Field(default=0, description="Total steps taken")

    class Config:
        schema_extra = {"description": "Complete environment state snapshot"}


class Action(BaseModel):
    """Action to take on an email"""
    action_type: str = Field(..., description="Type of action to perform")
    email_id: str = Field(..., description="Target email ID")
    label: Optional[str] = Field(None, description="Category for classify action")
    priority: Optional[str] = Field(None, description="Priority for prioritize action")
    response: Optional[str] = Field(None, description="Response text for respond action")

    @validator("label")
    def validate_label(cls, v, values):
        """Validate label is provided for classify actions"""
        if values.get("action_type") == "classify" and v is None:
            raise ValueError("label required for classify action")
        return v

    @validator("priority")
    def validate_priority(cls, v, values):
        """Validate priority is provided for prioritize actions"""
        if values.get("action_type") == "prioritize" and v is None:
            raise ValueError("priority required for prioritize action")
        return v

    @validator("response")
    def validate_response(cls, v, values):
        """Validate response is provided for respond actions"""
        if values.get("action_type") == "respond" and v is None:
            raise ValueError("response required for respond action")
        return v

    class Config:
        schema_extra = {
            "examples": [
                {
                    "action_type": "classify",
                    "email_id": "1",
                    "label": "billing"
                },
                {
                    "action_type": "respond",
                    "email_id": "1",
                    "response": "We'll help you with your issue"
                }
            ]
        }


class Reward(BaseModel):
    """Feedback on action performance"""
    score: float = Field(..., description="Reward score for action")
    feedback: str = Field(default="", description="Human-readable feedback")

    class Config:
        schema_extra = {"description": "Reward and feedback for action taken"}
