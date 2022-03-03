from waitress import serve
import os
import app
serve(app.app, host='0.0.0.0', port=5000,
        #expose_tracebacks=True, 
        connection_limit=os.getenv('CONNECTION_LIMIT', '1000'), 
        threads=os.getenv('THREADS', '4'), 
        channel_timeout=os.getenv('CHANNEL_TIMEOUT', '60'), 
        cleanup_interval=os.getenv('CLEANUP_INTERVAL', '30'),
        #backlog=os.getenv('BACKLOG', '2048')
        )