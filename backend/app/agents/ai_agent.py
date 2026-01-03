import google.generativeai as genai
import os
from datetime import datetime
from typing import Dict, Any, List, Callable, Optional
import re
import json
import asyncio
import time

from app.services.database import SessionLocal, Task
from app.services.weather_services import weather_service

class Tool:
    """A tool that the agent can use"""
    def __init__(self, name: str, description: str, func: Callable, requires_input: bool = True):
        self.name = name
        self.description = description
        self.func = func
        self.requires_input = requires_input

class AIAssistantAgent:
    """
    True AI Agent with ReAct (Reasoning + Acting) pattern
    
    The agent MUST follow this loop:
    1. Thought: Analyze what needs to be done
    2. Action: Choose and execute a tool
    3. Observation: See the result
    4. Repeat until task is complete
    5. Final Answer: Only when ALL required actions are done
    """
    
    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        # Use gemini-1.5-flash for better free tier limits (1500/day vs 20/day)
        self.model = genai.GenerativeModel('gemini-2.5-flash-lite')
        self.tools = self._initialize_tools()
        self.conversation_history = []
    
    def _initialize_tools(self) -> List[Tool]:
        """Initialize all available tools"""
        return [
            Tool(
                name="get_weather",
                description="Gets current weather for a location. Use this for ANY weather-related questions. Input: city name (e.g., 'London', 'Tokyo')",
                func=self._get_weather,
                requires_input=True
            ),
            Tool(
                name="create_task",
                description="Creates a new task or reminder. Use this when user wants to add/create/remember something. Input: task description",
                func=self._create_task,
                requires_input=True
            ),
            Tool(
                name="list_tasks",
                description="Lists all pending tasks. Use this when user asks about their tasks/todos. Input: 'all'",
                func=self._list_tasks,
                requires_input=False
            ),
            Tool(
                name="complete_task",
                description="Marks a task as completed. Use when user says they finished/completed something. Input: task title or ID",
                func=self._complete_task,
                requires_input=True
            ),
            Tool(
                name="get_current_time",
                description="Gets current date and time. Use when user asks about time/date. Input: 'now'",
                func=self._get_current_time,
                requires_input=False
            ),
        ]
    
    def _get_tools_description(self) -> str:
        """Generate description of available tools for the agent"""
        tools_desc = "Available Tools:\n"
        for tool in self.tools:
            tools_desc += f"- {tool.name}: {tool.description}\n"
        return tools_desc
    
    def _requires_tools(self, message: str) -> bool:
        """Determine if the message requires tool usage"""
        # Keywords that indicate tool usage
        tool_keywords = {
            'weather': ['weather', 'temperature', 'rain', 'sunny', 'climate', 'forecast'],
            'task': ['task', 'todo', 'remind', 'remember', 'add', 'create', 'complete', 'done', 'finish'],
            'time': ['time', 'date', 'today', 'now', 'what day'],
        }
        
        message_lower = message.lower()
        
        for category, keywords in tool_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                return True
        
        return False
    
    async def process_message(self, message: str, conversation_id: str = None) -> Dict[str, Any]:
        """
        Process user message using ReAct agent pattern
        
        ReAct Loop:
        Thought -> Action -> Observation -> Thought -> ... -> Final Answer
        """
        try:
            max_iterations = 5
            agent_scratchpad = []
            
            # Determine if tools are needed
            needs_tools = self._requires_tools(message)
            
            # Build the system prompt based on whether tools are needed
            if needs_tools:
                system_prompt = self._build_tool_required_prompt(message)
            else:
                system_prompt = self._build_general_prompt(message)
            
            # Agent ReAct loop
            for iteration in range(max_iterations):
                # Build the full prompt
                if iteration == 0:
                    full_prompt = system_prompt
                else:
                    full_prompt = system_prompt + "\n\n" + "\n".join(agent_scratchpad) + "\n\nContinue your reasoning:"
                
                # Get agent's response with retry logic
                agent_response = await self._generate_with_retry(full_prompt)
                
                if not agent_response:
                    return {
                        "response": "I'm experiencing rate limits. Please try again in a few seconds.",
                        "conversation_id": conversation_id or "new",
                        "success": False,
                        "error": "Rate limit exceeded"
                    }
                
                # Log for debugging
                print(f"\n=== Iteration {iteration + 1} ===")
                print(f"Agent Response:\n{agent_response}\n")
                
                agent_scratchpad.append(agent_response)
                
                # Check if agent is done (has Final Answer)
                if "Final Answer:" in agent_response:
                    final_answer = self._extract_final_answer(agent_response)
                    
                    return {
                        "response": final_answer,
                        "conversation_id": conversation_id or "new",
                        "success": True,
                        "iterations": iteration + 1,
                        "reasoning": agent_scratchpad
                    }
                
                # Parse and execute action
                action_result = await self._parse_and_execute_action(agent_response)
                
                if action_result:
                    agent_scratchpad.append(f"\nObservation: {action_result}\n")
                else:
                    # Agent didn't provide proper action format
                    agent_scratchpad.append("\nObservation: You must provide an Action and Action Input. Use the format:\nAction: [tool_name]\nAction Input: [input]\n")
            
            # If max iterations reached
            return {
                "response": "I've analyzed your request but need to think more. Let me summarize what I found: " + (agent_scratchpad[-1] if agent_scratchpad else "No information yet"),
                "conversation_id": conversation_id or "new",
                "success": True,
                "iterations": max_iterations,
                "reasoning": agent_scratchpad
            }
            
        except Exception as e:
            print(f"Error in agent: {str(e)}")
            import traceback
            traceback.print_exc()
            
            return {
                "response": f"I encountered an error: {str(e)}",
                "conversation_id": conversation_id or "new",
                "success": False,
                "error": str(e)
            }
    
    def _build_tool_required_prompt(self, message: str) -> str:
        """Build prompt that FORCES tool usage"""
        return f"""You are Bob, an AI agent that MUST use tools to answer user questions.

{self._get_tools_description()}

CRITICAL RULES:
1. You MUST use tools for this request - DO NOT answer without using tools first
2. Follow this EXACT format for EVERY step:

Thought: [Your reasoning about what to do next]
Action: [exact tool name]
Action Input: [the input for that tool]

3. After you see an Observation, continue with another Thought/Action cycle
4. ONLY use "Final Answer:" after you have used at least one tool and have the information
5. Your Final Answer must be natural, conversational, and based on the tool observations

User Request: {message}

Begin! Start with your first Thought:"""
    
    def _build_general_prompt(self, message: str) -> str:
        """Build prompt for general questions that don't need tools"""
        return f"""You are Bob, a helpful AI assistant.

The user asked: {message}

This appears to be a general question that doesn't require tools. Provide a helpful, concise answer.

If you realize mid-response that you DO need tools (weather, tasks, time), stop and use this format:
Thought: [reasoning]
Action: [tool_name]
Action Input: [input]

Otherwise, respond naturally with:
Final Answer: [your response]"""
    
    async def _parse_and_execute_action(self, agent_response: str) -> Optional[str]:
        """Parse the agent's response and execute the action"""
        # Extract action and input using regex
        action_match = re.search(r'Action:\s*([^\n]+)', agent_response, re.IGNORECASE)
        input_match = re.search(r'Action Input:\s*([^\n]+)', agent_response, re.IGNORECASE)
        
        if not action_match or not input_match:
            return None
        
        action_name = action_match.group(1).strip()
        action_input = input_match.group(1).strip()
        
        # Remove any quotes or extra formatting
        action_input = action_input.strip('"\'')
        
        # Find and execute the tool
        tool = next((t for t in self.tools if t.name.lower() == action_name.lower()), None)
        
        if tool:
            try:
                result = await tool.func(action_input)
                return result
            except Exception as e:
                return f"Error executing {action_name}: {str(e)}"
        else:
            available_tools = ", ".join([t.name for t in self.tools])
            return f"Error: Tool '{action_name}' not found. Available tools: {available_tools}"
    
    def _extract_final_answer(self, agent_response: str) -> str:
        """Extract the final answer from agent response"""
        if "Final Answer:" in agent_response:
            answer = agent_response.split("Final Answer:")[-1].strip()
            # Remove any remaining "Thought:" or "Action:" that might appear after
            answer = re.split(r'(Thought:|Action:)', answer)[0].strip()
            return answer
        return agent_response
    
    async def _generate_with_retry(self, prompt: str, max_retries: int = 3) -> Optional[str]:
        """Generate content with exponential backoff retry"""
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt)
                return response.text.strip()
            except Exception as e:
                error_str = str(e)
                
                # Check if it's a rate limit error
                if "quota" in error_str.lower() or "rate" in error_str.lower():
                    if attempt < max_retries - 1:
                        # Extract retry delay if available
                        wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                        
                        # Try to parse the suggested retry delay from error
                        retry_match = re.search(r'retry in ([\d.]+)s', error_str)
                        if retry_match:
                            wait_time = float(retry_match.group(1))
                        
                        print(f"Rate limit hit. Waiting {wait_time}s before retry {attempt + 1}/{max_retries}...")
                        await asyncio.sleep(wait_time)
                    else:
                        print(f"Rate limit exceeded after {max_retries} retries")
                        return None
                else:
                    # Non-rate-limit error, don't retry
                    print(f"Error generating content: {error_str}")
                    raise
        
        return None
    
    # ==================== TOOL IMPLEMENTATIONS ====================
    
    async def _get_weather(self, location: str) -> str:
        """Get weather for a location"""
        try:
            weather_data = await weather_service.get_weather(location)
            
            if "error" in weather_data:
                return f"Error: {weather_data.get('description', 'Could not fetch weather')}"
            
            return f"Weather in {weather_data['location']}: {weather_data['temperature']}°C, {weather_data['description']}. Humidity: {weather_data['humidity']}%, Wind: {weather_data['wind_speed']} m/s. Suggestion: {weather_data['suggestion']}"
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
                task_list += f"{i}. Task #{task.id}: {task.title} (created: {task.created_at.strftime('%Y-%m-%d %H:%M')})\n"
            
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