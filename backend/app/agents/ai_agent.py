import google.generativeai as genai
import os
from datetime import datetime
from typing import Dict, Any, List, Callable
import re

from app.services.database import SessionLocal, Task
from app.services.weather_services import weather_service

class Tool:
    """A tool that the agent can use"""
    def __init__(self, name: str, description: str, func: Callable):
        self.name = name
        self.description = description
        self.func = func

class AIAssistantAgent:
    """
    Proper AI Agent with ReAct (Reasoning + Acting) pattern
    
    The agent follows this loop:
    1. Thought: Analyze what needs to be done
    2. Action: Choose and execute a tool
    3. Observation: See the result
    4. Repeat until answer is found
    """
    
    def __init__(self):
        # Configure Gemini with correct model
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel('gemini-2.5-flash')  # Updated model name
        
        # Initialize tools
        self.tools = self._initialize_tools()
        
        # Agent memory for conversation
        self.conversation_history = []
    
    def _initialize_tools(self) -> List[Tool]:
        """Initialize all available tools"""
        return [
            Tool(
                name="get_weather",
                description="Gets current weather for a location. Input: city name (e.g., 'London', 'Tokyo')",
                func=self._get_weather
            ),
            Tool(
                name="create_task",
                description="Creates a new task or reminder. Input: task description",
                func=self._create_task
            ),
            Tool(
                name="list_tasks",
                description="Lists all pending tasks. Input: none (use empty string)",
                func=self._list_tasks
            ),
            Tool(
                name="complete_task",
                description="Marks a task as completed. Input: task title or keywords",
                func=self._complete_task
            ),
            Tool(
                name="get_current_time",
                description="Gets current date and time. Input: none (use empty string)",
                func=self._get_current_time
            ),
        ]
    
    def _get_tools_description(self) -> str:
        """Generate description of available tools for the agent"""
        tools_desc = "Available Tools:\n"
        for tool in self.tools:
            tools_desc += f"- {tool.name}: {tool.description}\n"
        return tools_desc
    
    async def process_message(self, message: str, conversation_id: str = None) -> Dict[str, Any]:
        """
        Process user message using ReAct agent pattern
        
        ReAct Loop:
        Thought -> Action -> Observation -> Thought -> ... -> Final Answer
        """
        try:
            max_iterations = 5  # Prevent infinite loops
            agent_scratchpad = []
            
            # Build the agent prompt
            system_prompt = f"""You are Bob, an AI agent that helps users by thinking step-by-step and using tools.

{self._get_tools_description()}

Follow this exact format for EVERY response:

Thought: [Analyze what the user wants and decide what to do]
Action: [tool_name]
Action Input: [input for the tool]

After you see the Observation, continue with:
Thought: [Analyze the observation]
Action: [next tool if needed, or "none" if done]
Action Input: [input or "none"]

When you have enough information, end with:
Thought: I now have all the information needed
Final Answer: [Your complete natural response to the user]

IMPORTANT RULES:
1. Always start with "Thought:"
2. Always use "Action:" and "Action Input:" when using a tool
3. Only use "Final Answer:" when you're completely done
4. If it's a general question (like "what is AI?"), skip tools and go straight to Final Answer

User: {message}

Begin!
"""

            # Agent ReAct loop
            for iteration in range(max_iterations):
                # Get agent's response
                if iteration == 0:
                    prompt = system_prompt
                else:
                    prompt = system_prompt + "\n\n" + "\n".join(agent_scratchpad)
                
                response = self.model.generate_content(prompt)
                agent_response = response.text.strip()
                
                agent_scratchpad.append(f"\n{agent_response}")
                
                # Check if agent is done
                if "Final Answer:" in agent_response:
                    # Extract final answer
                    final_answer = agent_response.split("Final Answer:")[-1].strip()
                    
                    return {
                        "response": final_answer,
                        "conversation_id": conversation_id or "new",
                        "success": True,
                        "iterations": iteration + 1,
                        "reasoning": agent_scratchpad
                    }
                
                # Extract action and input
                action_match = re.search(r'Action:\s*(\w+)', agent_response)
                input_match = re.search(r'Action Input:\s*(.+?)(?:\n|$)', agent_response, re.DOTALL)
                
                if action_match and input_match:
                    action_name = action_match.group(1).strip()
                    action_input = input_match.group(1).strip()
                    
                    # Execute the tool
                    tool = next((t for t in self.tools if t.name == action_name), None)
                    
                    if tool:
                        observation = await tool.func(action_input)
                        agent_scratchpad.append(f"Observation: {observation}\n")
                    else:
                        agent_scratchpad.append(f"Observation: Error - Tool '{action_name}' not found\n")
                else:
                    # If agent doesn't follow format, try to recover
                    agent_scratchpad.append("Observation: Please use the correct format (Thought/Action/Action Input)\n")
            
            # If max iterations reached, return what we have
            return {
                "response": "I processed your request but reached my thinking limit. Let me give you what I found: " + agent_scratchpad[-1],
                "conversation_id": conversation_id or "new",
                "success": True,
                "iterations": max_iterations
            }
            
        except Exception as e:
            print(f"Error in agent: {str(e)}")
            import traceback
            traceback.print_exc()
            
            return {
                "response": f"I encountered an error while processing your request: {str(e)}",
                "conversation_id": conversation_id or "new",
                "success": False,
                "error": str(e)
            }
    
    # Tool implementations
    
    async def _get_weather(self, location: str) -> str:
        """Get weather for a location"""
        try:
            weather_data = await weather_service.get_weather(location)
            
            if "error" in weather_data:
                return f"Error: {weather_data.get('description', 'Could not fetch weather')}"
            
            return f"Weather in {weather_data['location']}: {weather_data['temperature']}°C, {weather_data['description']}. Humidity: {weather_data['humidity']}%, Wind: {weather_data['wind_speed']} m/s. {weather_data['suggestion']}"
        except Exception as e:
            return f"Error fetching weather: {str(e)}"
    
    async def _create_task(self, task_description: str) -> str:
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
            task_id = task.id
            db.close()
            return f"Successfully created task #{task_id}: '{task_description}'"
        except Exception as e:
            return f"Error creating task: {str(e)}"
    
    async def _list_tasks(self, _: str = "") -> str:
        """List all pending tasks"""
        try:
            db = SessionLocal()
            tasks = db.query(Task).filter(Task.status == "pending").order_by(Task.created_at.desc()).limit(10).all()
            db.close()
            
            if not tasks:
                return "No pending tasks found."
            
            task_list = f"Found {len(tasks)} pending tasks:\n"
            for i, task in enumerate(tasks, 1):
                task_list += f"{i}. {task.title} (created: {task.created_at.strftime('%Y-%m-%d')})\n"
            
            return task_list
        except Exception as e:
            return f"Error retrieving tasks: {str(e)}"
    
    async def _complete_task(self, task_identifier: str) -> str:
        """Mark a task as completed"""
        try:
            db = SessionLocal()
            
            # Try to find by ID first, then by title
            task = None
            if task_identifier.isdigit():
                task = db.query(Task).filter(Task.id == int(task_identifier), Task.status == "pending").first()
            
            if not task:
                task = db.query(Task).filter(
                    Task.title.ilike(f"%{task_identifier}%"),
                    Task.status == "pending"
                ).first()
            
            if task:
                task.status = "completed"
                task.updated_at = datetime.utcnow()
                db.commit()
                title = task.title
                db.close()
                return f"Successfully completed task: '{title}'"
            else:
                db.close()
                return f"No pending task found matching '{task_identifier}'"
        except Exception as e:
            return f"Error completing task: {str(e)}"
    
    async def _get_current_time(self, _: str = "") -> str:
        """Get current date and time"""
        now = datetime.now()
        return f"Current date and time: {now.strftime('%A, %B %d, %Y at %I:%M %p')}"

# Create global agent instance
ai_agent = AIAssistantAgent()