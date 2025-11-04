"""
WebSocket routes for real-time updates
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict
import asyncio
import json

router = APIRouter()

# Active WebSocket connections
active_connections: Dict[str, WebSocket] = {}

@router.websocket("/research/{job_id}")
async def research_websocket(websocket: WebSocket, job_id: str):
    """
    WebSocket endpoint for real-time research progress updates
    
    Streams events such as:
    - search_started
    - papers_found
    - agent_working (ResearchManager, DataCollector, etc.)
    - summarizing
    - synthesis_complete
    - report_ready
    
    Connect from frontend:
    const ws = new WebSocket('ws://localhost:8000/ws/research/{job_id}');
    """
    
    await websocket.accept()
    active_connections[job_id] = websocket
    
    # Register with event broadcaster
    from api.utils.event_broadcaster import broadcaster
    broadcaster.register_connection(job_id, websocket)
    
    try:
        # Send initial connection message
        await websocket.send_json({
            "type": "connected",
            "job_id": job_id,
            "message": "WebSocket connection established"
        })
        
        # Keep connection alive and listen for messages
        while True:
            # Wait for messages from client (keepalive, pings, etc.)
            data = await websocket.receive_text()
            
            # Handle client messages
            if data == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "job_id": job_id
                })
            else:
                # Echo back for debugging
                await websocket.send_json({
                    "type": "echo",
                    "message": f"Received: {data}"
                })
            
    except WebSocketDisconnect:
        # Client disconnected
        print(f"📡 Client disconnected from job {job_id}")
    
    except Exception as e:
        # Handle errors
        print(f"❌ WebSocket error for job {job_id}: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass
    
    finally:
        # Cleanup
        if job_id in active_connections:
            del active_connections[job_id]
        broadcaster.unregister_connection(job_id)

async def send_progress_update(job_id: str, event_type: str, data: dict):
    """
    Send progress update to connected client
    
    Usage:
    await send_progress_update(
        job_id="abc123",
        event_type="papers_found",
        data={"count": 10, "agent": "DataCollector"}
    )
    """
    
    if job_id in active_connections:
        websocket = active_connections[job_id]
        try:
            await websocket.send_json({
                "type": event_type,
                "job_id": job_id,
                **data
            })
        except Exception as e:
            print(f"Failed to send update to {job_id}: {e}")
            if job_id in active_connections:
                del active_connections[job_id]
