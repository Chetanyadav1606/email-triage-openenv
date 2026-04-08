"""
FastAPI application for OpenEnv Email Triage Environment.

Provides REST API endpoints for:
- Environment reset and step execution
- Real-time scoring
- Performance evaluation with detailed grading
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from environment import EmailEnv
from models import Action, Observation, Reward
from grader import EmailTriageGrader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global state
env: EmailEnv = None
grader: EmailTriageGrader = EmailTriageGrader()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    logger.info("OpenEnv Email Triage starting up...")
    yield
    logger.info("OpenEnv Email Triage shutting down...")


app = FastAPI(
    title="📧 OpenEnv Email Triage",
    description="Intelligent customer support workflow simulator with real-world challenges",
    version="2.0",
    lifespan=lifespan
)

# Add CORS middleware to allow frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except RuntimeError:
    logger.warning("Static files directory not found. Frontend UI may not be available.")


@app.get("/", tags=["Root"])
async def root():
    """Serve the frontend interface"""
    try:
        return FileResponse("static/index.html")
    except FileNotFoundError:
        return {
            "message": "Welcome to OpenEnv Email Triage",
            "version": "2.0",
            "endpoints": {
                "frontend": "/static/index.html",
                "reset": "POST /reset",
                "step": "POST /step",
                "score": "GET /score",
                "health": "GET /health"
            }
        }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment_ready": env is not None,
        "message": "Service is running"
    }


@app.post("/reset", response_model=Observation, tags=["Environment"])
async def reset(difficulty: str = "easy"):
    """
    Reset the environment to initial state.
    
    Args:
        difficulty: Task difficulty - 'easy', 'medium', or 'hard' (default: easy)
    
    Returns:
        Observation: Initial environment state with first email
        
    Raises:
        HTTPException: If reset fails
    """
    global env
    try:
        from task_suite import TaskSuite
        
        task_suite = TaskSuite()
        
        # Validate difficulty
        if difficulty not in ["easy", "medium", "hard"]:
            raise ValueError("difficulty must be 'easy', 'medium', or 'hard'")
        
        # Load emails for this task
        emails = task_suite.load_task_emails(difficulty)
        
        env = EmailEnv(emails)
        initial_state = env.reset()
        
        logger.info(f"Environment reset with {len(emails)} {difficulty} emails")
        return initial_state
    except ValueError as e:
        logger.warning(f"Invalid difficulty: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid difficulty: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Reset failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reset failed: {str(e)}"
        )


@app.post("/step", tags=["Environment"])
async def step(action: Action):
    """
    Execute an action in the environment.
    
    Args:
        action: Action to perform with type, email_id, and optional parameters
        
    Returns:
        Dictionary with observation, reward, done status, and info
        
    Raises:
        HTTPException: If environment not initialized or action invalid
    """
    if env is None:
        logger.warning("Step attempted without initializing environment")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Environment not initialized. Call /reset first."
        )
    
    try:
        obs, reward, done, info = env.step(action)
        
        logger.info(
            f"Step {env.step_count}: {action.action_type} | "
            f"Reward: {reward.score:.2f} | Done: {done}"
        )
        
        return {
            "observation": obs,
            "reward": reward,
            "done": done,
            "info": info
        }
    
    except ValueError as e:
        logger.warning(f"Invalid action: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid action: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Step execution failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Step execution failed: {str(e)}"
        )


@app.get("/score", tags=["Evaluation"])
async def score():
    """
    Get the final score and comprehensive evaluation.
    
    Returns:
        Dictionary with final score and grading metrics
        
    Raises:
        HTTPException: If environment not initialized
    """
    if env is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Environment not initialized. Call /reset first."
        )
    
    try:
        final_score = env.evaluate()
        
        # Get detailed grading using the actual emails from the environment
        metrics = grader.grade_log(env.logs, env.initial_emails)
        feedback = grader.get_feedback(metrics)
        rank = grader.rank_performance(metrics.overall_score())
        
        logger.info(f"Score evaluated: {final_score:.2f} - Rank: {rank}")
        
        return {
            "final_score": final_score,
            "evaluation_metrics": metrics.to_dict(),
            "rank": rank,
            "feedback": feedback,
            "steps_taken": env.step_count,
            "total_reward": env.total_reward
        }
    
    except Exception as e:
        logger.error(f"Score evaluation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Score evaluation failed: {str(e)}"
        )


@app.get("/status", tags=["Environment"])
async def get_status():
    """
    Get current environment status and statistics.
    
    Returns:
        Dictionary with current state and stats
    """
    if env is None:
        return {
            "status": "not_initialized",
            "message": "Call /reset to initialize"
        }
    
    return {
        "status": "active",
        "current_email": env.current.id if env.current else None,
        "queue_size": len(env.queue),
        "step_count": env.step_count,
        "total_reward": env.total_reward,
        "done": env.done,
        "max_steps": env.MAX_STEPS,
        "customer_count": len(env.history)
    }


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("FastAPI application started")
    logger.info(f"API docs available at: /docs")
    logger.info(f"ReDoc available at: /redoc")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("FastAPI application shutting down")


# Error handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle ValueError exceptions"""
    logger.error(f"ValueError: {exc}")
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(exc)
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )