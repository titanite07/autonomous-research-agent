"""
Event Broadcaster for Real-Time Updates
Provides a non-blocking way to emit WebSocket events from any service
"""

import asyncio
from typing import Dict, Optional


class EventBroadcaster:
    """
    Singleton event broadcaster for WebSocket updates.
    Allows services to emit events without importing websocket routes.
    """
    
    _instance = None
    _active_connections: Dict[str, any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EventBroadcaster, cls).__new__(cls)
        return cls._instance
    
    def register_connection(self, job_id: str, websocket):
        """Register a WebSocket connection for a job"""
        self._active_connections[job_id] = websocket
        print(f"📡 WebSocket registered for job {job_id}")
    
    def unregister_connection(self, job_id: str):
        """Unregister a WebSocket connection"""
        if job_id in self._active_connections:
            del self._active_connections[job_id]
            print(f"📡 WebSocket unregistered for job {job_id}")
    
    async def emit(self, job_id: str, event_type: str, data: Optional[Dict] = None):
        """
        Emit an event to a specific job's WebSocket connection
        
        Args:
            job_id: Job identifier
            event_type: Type of event (e.g., "analyzing", "papers_found")
            data: Additional data to send with event
        """
        if job_id not in self._active_connections:
            # No WebSocket connected, skip silently
            return
        
        websocket = self._active_connections[job_id]
        
        try:
            message = {
                "type": event_type,
                "job_id": job_id,
                **(data or {})
            }
            
            await websocket.send_json(message)
            print(f"📡 Sent event '{event_type}' to job {job_id}")
            
        except Exception as e:
            print(f"⚠️ Failed to send event to {job_id}: {e}")
            # Remove dead connection
            self.unregister_connection(job_id)
    
    def emit_sync(self, job_id: str, event_type: str, data: Optional[Dict] = None):
        """
        Synchronous wrapper for emit() - creates new event loop if needed
        Use this from synchronous code (non-async functions)
        
        Args:
            job_id: Job identifier
            event_type: Type of event
            data: Additional data to send
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, schedule the coroutine
                asyncio.create_task(self.emit(job_id, event_type, data))
            else:
                # If no loop, run it
                loop.run_until_complete(self.emit(job_id, event_type, data))
        except RuntimeError:
            # No event loop in current thread, create one
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.emit(job_id, event_type, data))
            except Exception as e:
                print(f"⚠️ Could not emit event: {e}")
    
    def has_connection(self, job_id: str) -> bool:
        """Check if a job has an active WebSocket connection"""
        return job_id in self._active_connections


# Global broadcaster instance
broadcaster = EventBroadcaster()


def emit_event(job_id: str, event_type: str, data: Optional[Dict] = None):
    """
    Convenience function to emit events from anywhere
    Non-blocking, safe to call from sync or async code
    
    Usage:
        from api.utils.event_broadcaster import emit_event
        
        emit_event("job-123", "analyzing", {
            "message": "Starting analysis...",
            "progress": 0
        })
    """
    try:
        broadcaster.emit_sync(job_id, event_type, data)
    except Exception as e:
        print(f"⚠️ Event emission failed: {e}")
        # Don't raise - events are optional


async def emit_event_async(job_id: str, event_type: str, data: Optional[Dict] = None):
    """
    Async version of emit_event
    Use this from async functions for better performance
    
    Usage:
        from api.utils.event_broadcaster import emit_event_async
        
        await emit_event_async("job-123", "papers_found", {
            "count": 10,
            "message": "Found 10 papers"
        })
    """
    try:
        await broadcaster.emit(job_id, event_type, data)
    except Exception as e:
        print(f"⚠️ Event emission failed: {e}")
        # Don't raise - events are optional
