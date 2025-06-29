"""
🌐 Flask Health Check Server
"""
import os
import threading
import logging
from datetime import datetime
from flask import Flask, jsonify

from ..config import CONFIG

logger = logging.getLogger(__name__)

class HealthServer:
    """Flask server for health checks"""
    
    def __init__(self):
        self.app = Flask(__name__)
        self.thread = None
        self.running = False
        
        # Register routes
        self._register_routes()
    
    def _register_routes(self):
        """Register Flask routes"""
        
        @self.app.route('/health')
        def health_check():
            """Health check endpoint for Railway"""
            try:
                return jsonify({
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "bot_name": CONFIG["BOT_NAME"],
                    "version": CONFIG["BOT_VERSION"],
                    "uptime": "running"
                }), 200
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                return jsonify({
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }), 500
        
        @self.app.route('/')
        def root():
            """Root endpoint"""
            return jsonify({
                "message": "Telegram University Bot is running",
                "bot_name": CONFIG["BOT_NAME"],
                "version": CONFIG["BOT_VERSION"],
                "health_check": "/health"
            }), 200
        
        @self.app.route('/status')
        def status():
            """Status endpoint"""
            return jsonify({
                "status": "running",
                "timestamp": datetime.now().isoformat(),
                "bot_name": CONFIG["BOT_NAME"],
                "version": CONFIG["BOT_VERSION"]
            }), 200
    
    async def start(self):
        """Start the Flask server in a separate thread"""
        def run_flask():
            try:
                port = int(os.getenv('PORT', 5000))
                self.app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
            except Exception as e:
                logger.error(f"Flask server error: {e}")
        
        self.thread = threading.Thread(target=run_flask, daemon=True)
        self.thread.start()
        self.running = True
        logger.info("🌐 Health check server started")
    
    async def stop(self):
        """Stop the Flask server"""
        self.running = False
        logger.info("🛑 Health check server stopped") 