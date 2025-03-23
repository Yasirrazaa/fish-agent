import logging
import json
from datetime import datetime
from pathlib import Path

def setup_logger():
    """
    Setup logger with file and console handlers
    """
    # Create logs directory if it doesn't exist
    Path("logs").mkdir(exist_ok=True)
    
    # Create logger
    logger = logging.getLogger('runpod_api')
    logger.setLevel(logging.INFO)
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    
    # File handler - rotating by date
    file_handler = logging.FileHandler(
        f"logs/api_{datetime.now().strftime('%Y%m%d')}.log"
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(file_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

class LoggerMiddleware:
    """
    Middleware to log all requests and responses
    """
    def __init__(self, logger):
        self.logger = logger
        
    async def __call__(self, request, call_next):
        # Log request
        self.logger.info(f"Incoming request: {request.method} {request.url}")
        
        # Process request
        try:
            response = await call_next(request)
            # Log response
            self.logger.info(
                f"Request completed: {request.method} {request.url} - Status: {response.status_code}"
            )
            return response
        except Exception as e:
            # Log error
            self.logger.error(
                f"Error processing request: {request.method} {request.url} - Error: {str(e)}"
            )
            raise
            
def log_error(logger, error: Exception, job_id: str = None, **kwargs):
    """
    Helper function to log errors with consistent format
    """
    error_data = {
        "error_type": error.__class__.__name__,
        "error_message": str(error),
        "job_id": job_id,
        **kwargs
    }
    logger.error(json.dumps(error_data))
