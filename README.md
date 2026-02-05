<div align="center">
<img width="220" alt="Bob-removebg-preview" src="https://github.com/user-attachments/assets/7c96b7e7-2568-4962-8261-71e03a441257" />

  <br/>

  <a href="https://nextjs.org/">
    <img src="https://img.shields.io/badge/Next.js-14-black?style=for-the-badge&logo=next.js&logoColor=white" />
  </a>
  <a href="https://fastapi.tiangolo.com/">
    <img src="https://img.shields.io/badge/FastAPI-0.104-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  </a>
  <a href="https://www.python.org/">
    <img src="https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  </a>
  <a href="https://www.typescriptlang.org/">
    <img src="https://img.shields.io/badge/TypeScript-5.0-3178C6?style=for-the-badge&logo=typescript&logoColor=white" />
  </a>
  <a href="https://www.langchain.com/">
    <img src="https://img.shields.io/badge/LangChain-0.1-121212?style=for-the-badge&logo=chainlink&logoColor=white" />
  </a>
  <br/>
  <br/>

  <p><strong>A project built during the HackFiesta Hackathon.</strong></p>

</div>

---

## What is Bob?

Bob is a **voice-first Agentic assistant** specifically designed for student developers and learners. Unlike generic AI chatbots, Bob integrates directly into your development workflow, eliminating the context-switching that kills productivity.

Think of Bob as your pair-programming buddy who:
- **Listens while you code** (hands stay on the keyboard)
- **Understands developer problems** (not just generic questions)
- **Integrates with your tools** (GitHub, Stack Overflow, YouTube, Discord)
- **Learns with you** (saves conversation history with syntax highlighting)

### Why Bob?

**Before Bob:**
- 15 browser tabs open (Stack Overflow, ChatGPT, YouTube, GitHub, Gmail)
- Constant context switching
- Lost flow state every 5 minutes

**After Bob:**
- One conversation that handles everything
- Voice-first interaction (but with beautiful formatted text responses)
- Mental load reduced by 80%

---

## Features

### **Voice-First Interaction**
- Natural speech recognition with technical vocabulary support
- Real-time audio visualization during conversation
- Speak your questions, get formatted responses
- Text input available as fallback

### **Developer Tools**

#### GitHub Integration
- **README Generator**: Analyzes your repo and creates professional documentation
- **Project Validator**: Scores your project out of 10, compares to similar repos, suggests improvements
- **Issue Management**: Create, list, and manage GitHub issues via voice/text
- **Repository Browser**: List and explore your repositories

#### Debugging Assistant
- **Stack Overflow Search**: Finds and synthesizes solutions to your errors
- **Error Analysis**: Paste error messages, get ranked solutions
- **Code Snippet Manager**: Save and search reusable code patterns

#### Learning Tools
- **YouTube Transcript Extraction**: Takes notes from coding tutorials automatically
- **Structured Note Generation**: Converts transcripts into organized markdown notes
- **Interview Practice**: Ask coding interview questions, get feedback

### **Smart Chat Interface**
- **Markdown Rendering**: Code blocks with syntax highlighting (100+ languages)
- **Copy Code Button**: One-click copy for every code snippet
- **Conversation History**: All chats saved to localStorage, searchable
- **Sliding Panel**: Chat history doesn't interrupt the voice interface

### **Integrations**
- **Discord**: Share findings and code reviews with your team
- **Email**: Send updates and summaries via SMTP
- **Weather**: Quick context checks without leaving conversation
- **Tasks**: Create reminders and to-dos

---

## Design

<div align="center">

  <img src="https://github.com/user-attachments/assets/8db4b8e5-9038-4191-96a8-b986220ab74f" width="48%" />
  <img src="https://github.com/user-attachments/assets/e3d9ce9c-b474-4bda-90e4-863e8a302d73" width="48%" />

  <img src="https://github.com/user-attachments/assets/5a343f71-b7b1-4f78-b3b7-7eef63d2b41d" width="48%" />
  <img src="https://github.com/user-attachments/assets/5267b06b-c305-4ce9-aa38-f5981f3e7da5" width="48%" />

</div>
---

## Installation

### Prerequisites

- **Node.js** (v16 or higher)
- **Python** 3.8+
- **npm** or **yarn**
- **pip**

### Installation
1. Clone the repository:

   ```bash
   git clone https://github.com/ItsAbhinavM/bob.git
   cd Bob/
   ```

2. Install front-end dependencies:

   ```bash
   cd frontend/
   npm install
   ```
3. Install back-end packages on a virtual environmen:
   ```bash
   cd ..
   cd backend/
   python -m venv venv
   source venv/bin/activate/
   pip install -r requirements.txt
   ```
3. Set up environment variables:

   Follow the [.env.sample](https://github.com/ItsAbhinavM/bob/blob/main/backend/.env.sample) template and add your own API keys.

4. Start the development server:

   ```bash
   # Run front-end
   npm run dev
   # Run back-end
   uvicorn main:app --reload
   ```


## Project Structure

```
Bob/
├── frontend/                    # Next.js Frontend
│   ├── public/
│   │   └── assets/
│   │       ├── Bob.png         # Logo
│   │       └── user.png        # Avatar
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx      # Root layout
│   │   │   ├── page.tsx        # Home page (VoiceAssistant)
│   │   │   └── globals.css     # Global styles
│   │   ├── components/
│   │   │   ├── VoiceAssistant.tsx      # Main UI component
│   │   │   ├── TextInputBar.tsx        # Text input component
│   │   │   ├── MessageContent.tsx      # Markdown renderer
│   │   │   ├── AudioVisualizer.tsx     # Voice visualizer
│   │   │   └── FloatingVideoEye.tsx    # Camera component
│   │   └── lib/
│   │       ├── api.ts          # API client
│   │       └── useVoice.ts     # Voice hooks
│   ├── .env.local
│   ├── package.json
│   └── next.config.js
│
└── backend/                     # FastAPI Backend
    ├── app/
    │   ├── main.py             # FastAPI app entry point
    │   ├── agents/
    │   │   ├── ai_agent.py     # LangChain ReAct agent (THE BRAIN)
    │   │   └── tools/
    │   │       ├── readme_generator.py      # GitHub README generator
    │   │       ├── project_validator.py     # Project scoring system
    │   │       ├── email_service.py         # Email integration
    │   │       ├── contact_service.py       # Contact management
    │   │       ├── youtube_transcript.py    # YouTube notes
    │   │       └── discord_sharing.py       # Discord webhook
    │   ├── models/
    │   │   └── schemas.py      # Pydantic models
    │   ├── routers/
    │   │   ├── chat.py         # Main chat endpoint
    │   │   ├── tasks.py        # Task management
    │   │   └── weather.py      # Weather API
    │   └── services/
    │       ├── database.py     # SQLite models
    │       └── weather_services.py
    ├── .env
    ├── requirements.txt
    └── bob_assistant.db        # SQLite database
```

---

## Tech Stack

#### Frontend
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Web Speech API** - Voice recognition
- **React Markdown** - Markdown rendering
- **React Syntax Highlighter** - Code syntax highlighting

#### Backend
- **FastAPI** - Modern Python web framework
- **LangChain** - LLM orchestration (ReAct agent)
- **Gemini API** - Language model
- **SQLite** - Database (tasks, contacts, conversations)
- **yt-dlp** - YouTube transcript extraction
- **GitHub API** - Repository analysis
- **Stack Overflow API** - Developer Q&A search

### Agent Architecture

Bob uses a **LangChain ReAct agent** with custom tools:

```
User Input (Voice/Text)
        ↓
   Speech-to-Text
        ↓
   ReAct Agent
        ↓
   Tool Selection
        ↓
   ┌─────────────────────────┐
   │  Available Tools:       │
   │  • GitHub Integration   │
   │  • Stack Overflow       │
   │  • YouTube Transcripts  │
   │  • Task Management      │
   │  • Email/Discord        │
   │  • Weather, etc.        │
   └─────────────────────────┘
        ↓
   Response Generation
        ↓
   Text-to-Speech + Markdown Display
```

## Show Your Support

If you think Bob is cool, give it a ⭐️!

Built with ❤️ for student developers everywhere.

## LICENSE
This project is licensed under [GPL v2](https://github.com/ItsAbhinavM/bob/blob/main/LICENSE).

---
