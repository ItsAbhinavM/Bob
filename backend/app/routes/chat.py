from fastapi import APIRouter, HTTPException
from app.models.schemas import ChatMessage, ChatResponse
from app.agents.ai_agent import ai_agent
import uuid

router = APIRouter()

@router.post("/", response_model=ChatResponse)
async def process_chat(message: ChatMessage):
    """Process a chat message through the AI agent"""
    try:
        conversation_id = message.conversation_id or str(uuid.uuid4())
        
        result = await ai_agent.process_message(
            message=message.message,
            conversation_id=conversation_id
        )
        
        if not result.get("success", True):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Error processing message")
            )
        
        return ChatResponse(
            response=result["response"],
            conversation_id=result["conversation_id"],
            action_taken=None,
            data=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat message: {str(e)}"
        )