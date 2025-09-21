"""
WebSocket handler for streaming task updates from Redis.
This module provides the infrastructure to connect WebSocket clients
to receive real-time updates from Celery tasks.
"""

import asyncio
import json
import redis.asyncio as redis_async
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import logging
import os

# Store active WebSocket connections
active_connections: Dict[str, Set[WebSocket]] = {}


async def handle_task_updates(websocket: WebSocket, task_id: str):
    """
    Handle WebSocket connections for task updates.
    
    Args:
        websocket: The WebSocket connection
        task_id: The task ID to listen for updates on
    """
    # Create a Redis connection for this WebSocket
    redis_host = os.getenv('REDIS_HOST', 'redis')
    redis_port = int(os.getenv('REDIS_PORT', 6379))
    
    redis_client = redis_async.Redis(
        host=redis_host,
        port=redis_port,
        db=0,
        decode_responses=True
    )
    
    # Subscribe to the task's channel
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(f"task:{task_id}")
    
    # Add this WebSocket to the set of connections for this task
    if task_id not in active_connections:
        active_connections[task_id] = set()
    active_connections[task_id].add(websocket)
    
    try:
        # Listen for updates
        async for message in pubsub.listen():
            if message['type'] == 'message':
                try:
                    # Send the message to the connected WebSocket
                    await websocket.send_text(message['data'])
                    
                    # Check if the task is finished
                    data = json.loads(message['data'])
                    if data.get('type') in ['task_end', 'task_error']:
                        break  # Exit loop to close connection
                        
                except Exception as e:
                    print(f"[ERROR] Error sending message to WebSocket: {e}")
                    break
    except WebSocketDisconnect:
        print(f"[INFO] WebSocket disconnected for task {task_id}")
    except Exception as e:
        print(f"[ERROR] Error in WebSocket handler: {e}")
    finally:
        # Clean up when connection closes
        await pubsub.unsubscribe(f"task:{task_id}")
        if task_id in active_connections:
            active_connections[task_id].discard(websocket)
            if len(active_connections[task_id]) == 0:
                del active_connections[task_id]
        await redis_client.close()


async def broadcast_task_update(task_id: str, message: str):
    """
    Broadcast a message to all WebSocket connections for a specific task.
    
    Args:
        task_id: The task ID
        message: The message to broadcast
    """
    if task_id in active_connections:
        # Create a copy of the set to avoid modification during iteration
        connections = list(active_connections[task_id])
        for connection in connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                print(f"[ERROR] Error broadcasting to WebSocket: {e}")
                # Remove broken connections
                active_connections[task_id].discard(connection)
                if len(active_connections[task_id]) == 0:
                    del active_connections[task_id]