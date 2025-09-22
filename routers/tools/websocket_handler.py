"""
WebSocket handler for streaming task updates from Redis.
This module provides the infrastructure to connect WebSocket clients
to receive real-time updates from Celery tasks.
"""

import json
import uuid
import redis.asyncio as redis_async
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import os

# Store active WebSocket connections locally per container
# Global registry is now in Redis: websocket:connections:{task_id}
local_connections: Dict[str, Set[str]] = {}  # task_id -> set of connection_ids


def get_redis_client() -> redis_async.Redis:
    """Get a Redis client instance."""
    redis_host = os.getenv('REDIS_HOST', 'redis')
    redis_port = int(os.getenv('REDIS_PORT', 6379))

    return redis_async.Redis(
        host=redis_host,
        port=redis_port,
        db=0,
        decode_responses=True
    )


async def register_connection(redis_client: redis_async.Redis, task_id: str, connection_id: str) -> None:
    """Register a WebSocket connection in Redis for a specific task."""
    await redis_client.sadd(f"websocket:connections:{task_id}", connection_id)


async def unregister_connection(redis_client: redis_async.Redis, task_id: str, connection_id: str) -> None:
    """Remove a WebSocket connection from Redis for a specific task."""
    await redis_client.srem(f"websocket:connections:{task_id}", connection_id)


async def get_active_connections(redis_client: redis_async.Redis, task_id: str) -> Set[str]:
    """Get all active connection IDs for a specific task from Redis."""
    connections = await redis_client.smembers(f"websocket:connections:{task_id}")
    return set(connections) if connections else set()


async def handle_task_updates(websocket: WebSocket, task_id: str):
    """
    Handle WebSocket connections for task updates.

    Args:
        websocket: The WebSocket connection
        task_id: The task ID to listen for updates on
    """
    # Generate unique connection ID
    connection_id = str(uuid.uuid4())

    # Create a Redis connection for this WebSocket
    redis_client = get_redis_client()

    try:
        # Register this connection in Redis
        await register_connection(redis_client, task_id, connection_id)

        # Track connection locally for this container
        if task_id not in local_connections:
            local_connections[task_id] = set()
        local_connections[task_id].add(connection_id)

        # Subscribe to the task's channel
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(f"task:{task_id}")

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

    finally:
        # Clean up connection tracking
        if task_id in local_connections:
            local_connections[task_id].discard(connection_id)
            if len(local_connections[task_id]) == 0:
                del local_connections[task_id]

        # Remove connection from Redis
        await unregister_connection(redis_client, task_id, connection_id)
        await redis_client.close()


async def broadcast_task_update(task_id: str, message: str):
    """
    Broadcast a message to all WebSocket connections for a specific task.
    This function is called by all containers when they receive a task update.
    Only containers with active connections for this task will forward the message.

    Args:
        task_id: The task ID
        message: The message to broadcast
    """
    # Check if this container has any connections for this task
    if task_id not in local_connections or not local_connections[task_id]:
        return  # No connections in this container for this task

    # Get Redis client to check global connection state
    redis_client = get_redis_client()

    try:
        # Verify this task still has active connections globally
        active_connection_ids = await get_active_connections(redis_client, task_id)
        if not active_connection_ids:
            return  # No active connections for this task anywhere

        # Get the WebSocket objects for the connection IDs we have locally
        # Note: In a full implementation, you'd need to maintain a mapping
        # from connection_id to WebSocket object. For now, this is a placeholder.
        # The current implementation relies on the handle_task_updates function
        # to manage the WebSocket connections directly.

        print(f"[INFO] Broadcasting to {len(local_connections[task_id])} local connections for task {task_id}")

    except Exception as e:
        print(f"[ERROR] Error in broadcast_task_update: {e}")
    finally:
        await redis_client.close()
