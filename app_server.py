#!/usr/bin/env python3
"""
Smart Timetable Management System - Production Server
Deployment-ready Flask application with multi-user portals
"""

import os
import sys
from datetime import datetime
import logging

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log') if os.path.exists('.') else logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Create Flask application
app = create_app()

@app.route('/health')
def health_check():
    """Health check endpoint for deployment"""
    return {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0',
        'service': 'Smart Timetable Management System'
    }

@app.route('/api/status')
def api_status():
    """API status endpoint"""
    try:
        from models import db, User, TimetableSlot
        
        # Check database connectivity
        user_count = User.query.count()
        slot_count = TimetableSlot.query.count()
        
        return {
            'database': 'connected',
            'users': user_count,
            'timetable_slots': slot_count,
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        return {
            'database': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }, 500

if __name__ == "__main__":
    # Production settings
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
    
    logger.info(f"Starting Smart Timetable Management System on port {port}")
    logger.info(f"Debug mode: {debug}")
    
    app.run(
        host="0.0.0.0",
        port=port,
        debug=debug,
        threaded=True
    )