import json
import logging
from typing import Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from .models import WebSocketMessage, StreamResponse, StreamResponseType
from .analyzer import CodeForgeAnalyzer

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"WebSocket client {client_id} connected")
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"WebSocket client {client_id} disconnected")
    
    async def send_message(self, client_id: str, message: Dict[str, Any]):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send message to client {client_id}: {e}")
                self.disconnect(client_id)


manager = ConnectionManager()


@router.websocket("/ws/stream")
async def websocket_stream_endpoint(websocket: WebSocket):
    client_id = f"client_{id(websocket)}"
    analyzer = CodeForgeAnalyzer()
    
    try:
        await manager.connect(websocket, client_id)
        
        # Initialize Redis connection for this analyzer instance
        await analyzer.initialize_redis()
        
        # Send connection confirmation
        await manager.send_message(client_id, {
            "type": StreamResponseType.status,
            "message": "Connected to CodeForge AI",
            "progress": 0
        })
        
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Validate message
                try:
                    message = WebSocketMessage(**message_data)
                except ValidationError as e:
                    await manager.send_message(client_id, {
                        "type": StreamResponseType.error,
                        "message": f"Invalid request format: {str(e)}",
                        "error_code": "VALIDATION_ERROR"
                    })
                    continue
                
                if message.action == "analyze":
                    await manager.send_message(client_id, {
                        "type": StreamResponseType.status,
                        "message": f"Starting analysis: {message.problem_title}",
                        "progress": 5
                    })
                    
                    # Stream analysis
                    try:
                        async for chunk in analyzer.stream_analysis(
                            message.problem_title,
                            message.problem_description,
                            message.backend
                        ):
                            await manager.send_message(client_id, chunk)
                            
                    except Exception as e:
                        logger.error(f"Analysis error for client {client_id}: {e}")
                        await manager.send_message(client_id, {
                            "type": StreamResponseType.error,
                            "message": f"Analysis failed: {str(e)}",
                            "error_code": "ANALYSIS_ERROR"
                        })
                
                elif message.action == "ping":
                    await manager.send_message(client_id, {
                        "type": StreamResponseType.status,
                        "message": "pong",
                        "progress": 0
                    })
                
                else:
                    await manager.send_message(client_id, {
                        "type": StreamResponseType.error,
                        "message": f"Unknown action: {message.action}",
                        "error_code": "UNKNOWN_ACTION"
                    })
                    
            except json.JSONDecodeError:
                await manager.send_message(client_id, {
                    "type": StreamResponseType.error,
                    "message": "Invalid JSON format",
                    "error_code": "JSON_ERROR"
                })
            except Exception as e:
                logger.error(f"WebSocket message handling error for client {client_id}: {e}")
                await manager.send_message(client_id, {
                    "type": StreamResponseType.error,
                    "message": "Internal server error",
                    "error_code": "INTERNAL_ERROR"
                })
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket client {client_id} disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
    finally:
        manager.disconnect(client_id)