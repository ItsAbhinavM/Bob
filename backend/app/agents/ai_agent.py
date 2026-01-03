from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_structured_chat_agent
from langchain.tools import Tool
from langchain.prompts import PromptTemplate
import os
from datetime import datetime
from typing import Dict, List, Any

from app.services.database import SessionLocal, Task
from app.services.weather_service import weather_service

class AIAssistantAgent:
    """LangChain-based AI agent with multiple tools"""
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-pro",
            google_api_key=os.getenv("GEMINI_API_KEY"),
            temperature=0.7,
            convert_system_message_to_human=True
        )
        
        self.tools = self._create_tools()
        self.agent = self._create_agent()
    
    def _create_tools(self) -> List[Tool]:
        """Create tools that the agent can use"""
        
        tools = [
            Tool(
                name="get_weather",
                func=self._get_weather_sync,
                description="Get current weather information for a location. Input should be a city name."
            ),
            Tool(
                name="create_task",
                func=self._create_task,
                description="Create a new task or reminder. Input should be the task description."
            ),
            Tool(
                name="list_tasks",
                func=self._list_tasks,
                description="Get list of all pending tasks. No input needed."
            ),
            Tool(
                name="complete_task",
                func=self._complete_task,
                description="Mark a task as completed. Input should be the task title or ID."
            ),
            Tool(
                name="get_current_time",
                func=self._get_current_time,
                description="Get current date and time. No input needed."
            )
        ]
        
        return tools
    
    def _create_agent(self) -> AgentExecutor:
        """Create the LangChain agent with tools"""
        
        prompt_template = """You are Bob, a helpful AI assistant that can help users with various tasks.

You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought: {agent_scratchpad}"""

        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["input", "agent_scratchpad", "tools", "tool_names"]
        )
        
        agent = create_structured_chat_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        agent_executor = AgentExecutor.from_agent_and_tools(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=3
        )
        
        return agent_executor
    
    async def process_message(self, message: str, conversation_id: str = None) -> Dict[str, Any]:
        """Process user message through the AI agent"""
        try:
            result = self.agent.invoke({"input": message})
            response_text = result.get("output", "I'm not sure how to help with that.")
            
            return {
                "response": response_text,
                "conversation_id": conversation_id or "new",
                "success": True
            }
            
        except Exception as e:
            print(f"Error processing message: {str(e)}")
            return {
                "response": "I encountered an error processing your request. Please try again.",
                "conversation_id": conversation_id or "new",
                "success": False,
                "error": str(e)
            }
    
    def _get_weather_sync(self, location: str) -> str:
        """Synchronous wrapper for weather service"""
        import asyncio
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            weather_data = loop.run_until_complete(weather_service.get_weather(location))
            loop.close()
            
            if "error" in weather_data:
                return f"Unable to get weather for {location}: {weather_data.get('description', 'Unknown error')}"
            
            return f"Weather in {weather_data['location']}: {weather_data['temperature']}°C, {weather_data['description']}. {weather_data['suggestion']}"
        except Exception as e:
            return f"Error fetching weather: {str(e)}"
    
    def _create_task(self, task_description: str) -> str:
        """Create a new task"""
        try:
            db = SessionLocal()
            task = Task(
                title=task_description[:100],
                description=task_description,
                status="pending",
                priority="medium",
                tags=[]
            )
            db.add(task)
            db.commit()
            db.close()
            return f"Task created successfully: '{task_description}'"
        except Exception as e:
            return f"Error creating task: {str(e)}"
    
    def _list_tasks(self, _: str = "") -> str:
        """List all pending tasks"""
        try:
            db = SessionLocal()
            tasks = db.query(Task).filter(Task.status == "pending").limit(10).all()
            db.close()
            
            if not tasks:
                return "You have no pending tasks."
            
            task_list = "Your pending tasks:\n"
            for i, task in enumerate(tasks, 1):
                task_list += f"{i}. {task.title}\n"
            
            return task_list
        except Exception as e:
            return f"Error retrieving tasks: {str(e)}"
    
    def _complete_task(self, task_identifier: str) -> str:
        """Mark a task as completed"""
        try:
            db = SessionLocal()
            task = db.query(Task).filter(
                Task.title.ilike(f"%{task_identifier}%"),
                Task.status == "pending"
            ).first()
            
            if task:
                task.status = "completed"
                task.updated_at = datetime.utcnow()
                db.commit()
                db.close()
                return f"Task completed: '{task.title}'"
            else:
                db.close()
                return f"No pending task found matching '{task_identifier}'"
        except Exception as e:
            return f"Error completing task: {str(e)}"
    
    def _get_current_time(self, _: str = "") -> str:
        """Get current date and time"""
        now = datetime.now()
        return f"Current date and time: {now.strftime('%A, %B %d, %Y at %I:%M %p')}"

ai_agent = AIAssistantAgent()