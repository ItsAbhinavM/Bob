import google.generativeai as genai
import os
from datetime import datetime
from typing import Dict, Any, List, Callable, Optional, Tuple
import re
import json
import asyncio
import time

from app.services.database import SessionLocal, Task
from app.services.weather_services import weather_service
from app.agents.tools.email_service import email_service
from app.agents.tools.contact_service import contact_service
from app.agents.tools.stack_overflow_search import stackoverflow_service
from app.agents.tools.youtube_transcript import youtube_loader
from app.agents.tools.discord_sharing import send_to_discord


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
        
        # Simple cache for common queries (saves API calls)
        self.response_cache = {}
        self.cache_enabled = True
    
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
            Tool(
                name="send_email",
                description="Sends an email via SMTP. CRITICAL: This tool ACTUALLY sends the email - you MUST use it to send emails. Input: JSON string with 'alias', 'subject', 'body'. Example: {\"alias\": \"john\", \"subject\": \"Meeting\", \"body\": \"Hi John...\"}",
                func=self._send_email,
                requires_input=True
            ),
            Tool(
                name="add_contact",
                description="Adds a new contact alias. Use when user wants to save a contact or when alias doesn't exist. Input: JSON string with 'alias', 'email', 'name' (optional)",
                func=self._add_contact,
                requires_input=True
            ),
            Tool(
                name="get_contact",
                description="Gets contact details by alias. Use this BEFORE sending email to check if alias exists. Input: alias name",
                func=self._get_contact,
                requires_input=True
            ),
            Tool(
                name="list_contacts",
                description="Lists all saved contacts. Use when user asks 'who are my contacts' or 'show contacts'. Input: 'all'",
                func=self._list_contacts,
                requires_input=False
            ),
            Tool(
                name="Get_youtube_transcript",
                func=self.get_youtube_transcript_tool,
                description="Gets notes of youtube video. Use this when user provides a YouTube link."
            ),
            Tool(
                name="Create_detailed_notes",
                func=self.create_detailed_notes_tool,
                description="Creates structured, detailed notes from a transcript. Use this after getting a YouTube transcript to format it into organized notes."
            ),
            Tool(
                name="Send through Discord",
                func=self.send_to_discord_tool,
                description="Send message through Discord"
            ),
            Tool(
                name="search_stackoverflow",
                description="Search Stack Overflow for programming questions and solutions. Use when user asks 'how to', 'error', or programming questions. Input: search query (e.g., 'CORS error FastAPI', 'async await python')",
                func=self._search_stackoverflow,
                requires_input=True
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
            'email': ['email', 'send', 'mail', 'message'],
            'contact': ['contact', 'alias', 'save contact', 'add contact'],
            'stackoverflow': ['how to', 'how do i', 'error', 'debug', 'fix', 'code', 'python', 'javascript', 'react', 'fastapi', 'api', 'function', 'syntax', 'stackoverflow'],
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
            # Check cache for non-tool queries (like "hello", "what is AI?")
            if self.cache_enabled and not self._requires_tools(message):
                cache_key = message.lower().strip()
                if cache_key in self.response_cache:
                    print(f"Cache hit for: {cache_key}")
                    cached = self.response_cache[cache_key]
                    return {
                        "response": cached,
                        "conversation_id": conversation_id or "new",
                        "success": True,
                        "iterations": 0,
                        "cached": True
                    }
            
            # Reduce iterations to save API quota (5 iterations = 5 API calls!)
            max_iterations = 5
            agent_scratchpad = []
            tools_used = []  # Track which tools were actually executed
            
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
                    
                    # CRITICAL CHECK: Verify required tools were actually used
                    message_lower = message.lower()
                    
                    # Check for email
                    if ('email' in message_lower or 'mail' in message_lower) and 'send_email' not in tools_used:
                        print("⚠️ WARNING: Email mentioned but send_email tool not used!")
                        agent_scratchpad.append("\nObservation: ERROR - You said you sent an email but you didn't use the send_email tool. You MUST call the send_email tool to actually send emails. Try again.\n")
                        continue
                    
                    # Check for weather
                    if 'weather' in message_lower and 'get_weather' not in tools_used:
                        print("⚠️ WARNING: Weather mentioned but get_weather tool not used!")
                        agent_scratchpad.append("\nObservation: ERROR - You need to use the get_weather tool to get weather information. Try again.\n")
                        continue
                    
                    # Cache the response if it's a general query
                    if self.cache_enabled and not needs_tools:
                        cache_key = message.lower().strip()
                        self.response_cache[cache_key] = final_answer
                    
                    return {
                        "response": final_answer,
                        "conversation_id": conversation_id or "new",
                        "success": True,
                        "iterations": iteration + 1,
                        "reasoning": agent_scratchpad,
                        "tools_used": tools_used
                    }
                
                # Parse and execute action
                action_result, action_name = await self._parse_and_execute_action(agent_response)
                
                if action_result:
                    if action_name:
                        tools_used.append(action_name)
                        print(f"✅ Tool executed: {action_name}")
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
                "reasoning": agent_scratchpad,
                "tools_used": tools_used
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
            2. NEVER say you did something unless you ACTUALLY used the tool
            3. Follow this EXACT format for EVERY step:

            Thought: [Your reasoning about what to do next]
            Action: [exact tool name]
            Action Input: [the input for that tool]

            4. After you see an Observation, continue with another Thought/Action cycle
            5. ONLY use "Final Answer:" after you have ACTUALLY executed the required tools
            6. Your Final Answer must be based ONLY on what the Observation shows

            IMPORTANT FOR EMAILS:
            - To send an email, you MUST call the send_email tool
            - Format: Action: send_email
                    Action Input: {{"alias": "name", "subject": "...", "body": "..."}}
            - Wait for the Observation to confirm "✅ Email sent successfully"
            - Only say "email sent" if the Observation confirms it

            User Request: {message}

            Begin! Start with your first Thought:"""
    
    def _build_general_prompt(self, message: str) -> str:
        """Build prompt for general questions that don't need tools"""
        return f"""You are Bob, a helpful AI assistant.

        The user asked: {message}

        This appears to be a general question that doesn't require tools. Provide a helpful, concise answer.

        If you realize mid-response that you DO need tools (weather, tasks, time, email), stop and use this format:
        Thought: [reasoning]
        Action: [tool_name]
        Action Input: [input]

        Otherwise, respond naturally with:
        Final Answer: [your response]"""
    
    async def _parse_and_execute_action(self, agent_response: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse the agent's response and execute the action. Returns (result, action_name)"""
        # Extract action and input using regex
        action_match = re.search(r'Action:\s*([^\n]+)', agent_response, re.IGNORECASE)
        input_match = re.search(r'Action Input:\s*([^\n]+)', agent_response, re.IGNORECASE)
        
        if not action_match or not input_match:
            return None, None
        
        action_name = action_match.group(1).strip()
        action_input = input_match.group(1).strip()
        
        # Remove any quotes or extra formatting
        action_input = action_input.strip('"\'')
        
        # Find and execute the tool
        tool = next((t for t in self.tools if t.name.lower() == action_name.lower()), None)
        
        if tool:
            try:
                result = await tool.func(action_input)
                return result, action_name
            except Exception as e:
                return f"Error executing {action_name}: {str(e)}", action_name
        else:
            available_tools = ", ".join([t.name for t in self.tools])
            return f"Error: Tool '{action_name}' not found. Available tools: {available_tools}", None
    
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
    
    async def _send_email(self, input_data: str) -> str:
        """Send email to a contact using alias"""
        
        # CRITICAL DEBUG - Shows when tool is actually called
        print("\n" + "="*60)
        print("🚨 SEND_EMAIL TOOL WAS ACTUALLY CALLED!")
        print("="*60 + "\n")
        
        try:
            print(f"📧 Email tool called with input: {input_data}")
            
            # Parse input
            try:
                data = json.loads(input_data)
                alias = data.get('alias')
                subject = data.get('subject')
                body = data.get('body')
            except:
                # Fallback parsing
                parts = {}
                for part in input_data.split(','):
                    if ':' in part:
                        key, value = part.split(':', 1)
                        parts[key.strip().lower()] = value.strip()
                
                alias = parts.get('alias')
                subject = parts.get('subject')
                body = parts.get('body')
            
            print(f"📧 Parsed - Alias: {alias}, Subject: {subject}")
            
            if not alias or not subject or not body:
                return "Error: Missing required fields. Need: alias, subject, body"
            
            # Get contact email
            contact = await contact_service.get_contact(alias)
            
            if not contact:
                return f"Contact '{alias}' not found. Please ask user to add this contact first."
            
            print(f"📧 Found contact: {contact}")
            
            # Send email
            result = await email_service.send_email(
                to_email=contact['email'],
                subject=subject,
                body=body,
                to_alias=alias
            )
            
            print(f"📧 Email result: {result}")
            
            if result['success']:
                # IMPORTANT: Return clear success message
                return f"✅ Email sent successfully to {alias} ({contact['email']}). Subject: '{subject}'"
            else:
                return f"❌ Failed to send email to {alias}: {result.get('error', 'Unknown error')}"
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"❌ Error sending email: {str(e)}"
    
    async def _add_contact(self, input_data: str) -> str:
        """Add a new contact alias"""
        try:
            import json
            
            # Parse input
            try:
                data = json.loads(input_data)
                alias = data.get('alias')
                email = data.get('email')
                name = data.get('name')
            except:
                # Fallback parsing
                parts = {}
                for part in input_data.split(','):
                    if ':' in part:
                        key, value = part.split(':', 1)
                        parts[key.strip().lower()] = value.strip()
                
                alias = parts.get('alias')
                email = parts.get('email')
                name = parts.get('name')
            
            if not alias or not email:
                return "Error: Need both alias and email. Example: alias: john, email: john@example.com"
            
            result = await contact_service.add_contact(
                alias=alias,
                email=email,
                name=name
            )
            
            if result['success']:
                return f"Contact '{alias}' added successfully for {email}"
            else:
                return f"Failed to add contact: {result.get('error', 'Unknown error')}"
                
        except Exception as e:
            return f"Error adding contact: {str(e)}"
    
    async def _get_contact(self, alias: str) -> str:
        """Get contact details by alias"""
        try:
            contact = await contact_service.get_contact(alias.strip())
            
            if not contact:
                return f"Contact '{alias}' not found. Available action: Ask user to add this contact."
            
            name_part = f" ({contact['name']})" if contact['name'] else ""
            return f"Contact '{alias}'{name_part}: {contact['email']}"
            
        except Exception as e:
            return f"Error getting contact: {str(e)}"
    
    async def _list_contacts(self, _: str = "") -> str:
        """List all contacts"""
        try:
            contacts = await contact_service.list_contacts()
            
            if not contacts:
                return "No contacts saved yet."
            
            contact_list = f"Found {len(contacts)} contacts:\n"
            for i, contact in enumerate(contacts, 1):
                name_part = f" ({contact['name']})" if contact['name'] else ""
                contact_list += f"{i}. {contact['alias']}{name_part}: {contact['email']}\n"
            
            return contact_list
            
        except Exception as e:
            return f"Error listing contacts: {str(e)}"
    
    async def _search_stackoverflow(self, query: str) -> str:
        """Search Stack Overflow and return formatted results"""
        try:
            print(f"🔍 Searching Stack Overflow for: {query}")
            
            result = await stackoverflow_service.search_question(query, num_results=2)
            
            if not result["success"]:
                return f"Stack Overflow search failed: {result.get('error', 'Unknown error')}"
            
            if result["count"] == 0:
                return f"No Stack Overflow results found for '{query}'. Try rephrasing your question."
            
            # Format results for voice readout
            response = f"Found {result['count']} Stack Overflow results for '{query}':\n\n"
            
            for i, item in enumerate(result["results"], 1):
                response += f"Result {i}: {item['title']}\n"
                response += f"Score: {item['score']} votes, {item['answer_count']} answers\n"
                
                if item["top_answer"]:
                    answer = item["top_answer"]
                    status = "Accepted answer" if answer["is_accepted"] else "Top answer"
                    response += f"{status} ({answer['score']} votes): {answer['body'][:300]}...\n"
                else:
                    response += "No answers yet.\n"
                
                response += f"Link: {item['link']}\n\n"
            
            print(f"✅ Stack Overflow search completed")
            return response
            
        except Exception as e:
            print(f"❌ Stack Overflow search error: {str(e)}")
            return f"Error searching Stack Overflow: {str(e)}"
    
    async def send_to_discord_tool(self, message: str) -> str:
        """Send a message through Discord."""
        return send_to_discord(message)
    
    async def get_youtube_transcript_tool(self, link: str) -> str:
        """
        Gets the transcript/notes from a YouTube video. 
        Provide a valid YouTube URL (e.g., https://www.youtube.com/watch?v=VIDEO_ID or https://youtu.be/VIDEO_ID).
        Returns detailed transcript with timestamps.
        """
        return youtube_loader(link)

    async def create_detailed_notes_tool(self, transcript: str) -> str:
        """
        Creates detailed and structured notes from a YouTube video transcript.
        """
        notes_prompt = f"""
            Please create detailed, well-structured notes from the following YouTube video transcript.
            Organize the content into clear sections with:
            - Main topics and subtopics
            - Key points and important information
            - Actionable insights if any
            - Summary at the end

            Transcript:
            {transcript}

            Please format the notes in a clear, readable structure with headings and bullet points.
            """
        
        try:
            # Use Gemini's generate_content method (not invoke)
            response = self.model.generate_content(notes_prompt)
            return response.text
        except Exception as e:
            return f"Error creating notes: {str(e)}"

# Create global agent instance
ai_agent = AIAssistantAgent()