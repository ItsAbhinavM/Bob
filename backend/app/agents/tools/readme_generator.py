import os
import re
import requests
from typing import Dict, List, Optional
from datetime import datetime


class ReadmeGenerator:
    def __init__(self):
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        } if self.github_token else {}
        
        # Language to badge mapping
        self.language_badges = {
            "python": "![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)",
            "javascript": "![JavaScript](https://img.shields.io/badge/javascript-%23323330.svg?style=for-the-badge&logo=javascript&logoColor=%23F7DF1E)",
            "typescript": "![TypeScript](https://img.shields.io/badge/typescript-%23007ACC.svg?style=for-the-badge&logo=typescript&logoColor=white)",
            "react": "![React](https://img.shields.io/badge/react-%2320232a.svg?style=for-the-badge&logo=react&logoColor=%2361DAFB)",
            "nextjs": "![Next JS](https://img.shields.io/badge/Next-black?style=for-the-badge&logo=next.js&logoColor=white)",
            "fastapi": "![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)",
            "nodejs": "![NodeJS](https://img.shields.io/badge/node.js-6DA55F?style=for-the-badge&logo=node.js&logoColor=white)",
            "tailwindcss": "![TailwindCSS](https://img.shields.io/badge/tailwindcss-%2338B2AC.svg?style=for-the-badge&logo=tailwind-css&logoColor=white)",
            "docker": "![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)",
        }
        
    def generate_readme(self, repo_input: str) -> str:
        """
        Main function to generate README
        repo_input can be: 'owner/repo' or 'https://github.com/owner/repo'
        """
        try:
            # Parse repository info
            owner, repo = self._parse_repo_input(repo_input)
            
            # Fetch repository data
            repo_data = self._fetch_repo_data(owner, repo)
            repo_structure = self._fetch_repo_structure(owner, repo)
            languages = self._fetch_languages(owner, repo)
            
            # Detect project type and dependencies
            project_info = self._analyze_project(repo_structure, languages)
            
            # Generate README sections
            readme = self._build_readme(repo_data, project_info, owner, repo)
            
            return readme
            
        except Exception as e:
            return f"Error generating README: {str(e)}"
    
    def _parse_repo_input(self, repo_input: str) -> tuple:
        """Parse repository input to extract owner and repo name"""
        # Remove trailing slashes and .git
        repo_input = repo_input.rstrip('/').replace('.git', '')
        
        # Handle GitHub URL
        if 'github.com' in repo_input:
            match = re.search(r'github\.com/([^/]+)/([^/]+)', repo_input)
            if match:
                return match.group(1), match.group(2)
        
        # Handle owner/repo format
        if '/' in repo_input:
            parts = repo_input.split('/')
            return parts[-2], parts[-1]
        
        raise ValueError("Invalid repository format. Use 'owner/repo' or GitHub URL")
    
    def _fetch_repo_data(self, owner: str, repo: str) -> Dict:
        """Fetch basic repository information"""
        url = f"https://api.github.com/repos/{owner}/{repo}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            raise Exception(f"Failed to fetch repo data: {response.status_code}")
        
        return response.json()
    
    def _fetch_repo_structure(self, owner: str, repo: str) -> List[Dict]:
        """Fetch repository file structure"""
        url = f"https://api.github.com/repos/{owner}/{repo}/contents"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        return []
    
    def _fetch_languages(self, owner: str, repo: str) -> Dict:
        """Fetch repository languages"""
        url = f"https://api.github.com/repos/{owner}/{repo}/languages"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        return {}
    
    def _analyze_project(self, structure: List[Dict], languages: Dict) -> Dict:
        """Analyze project type, dependencies, and structure"""
        files = {item['name']: item for item in structure if item['type'] == 'file'}
        folders = [item['name'] for item in structure if item['type'] == 'dir']
        
        info = {
            "type": "Unknown",
            "dependencies": [],
            "badges": [],
            "has_docker": False,
            "has_tests": False,
            "frontend": None,
            "backend": None,
            "database": None,
        }
        
        # Detect project type
        if "package.json" in files:
            info["type"] = "Node.js/JavaScript"
            info["dependencies"].append("package.json")
            
            # Check for React/Next.js
            if "next.config.js" in files or "next.config.ts" in files:
                info["type"] = "Next.js"
                info["frontend"] = "Next.js"
                info["badges"].append(self.language_badges.get("nextjs", ""))
            elif any("react" in folder.lower() for folder in folders):
                info["frontend"] = "React"
                info["badges"].append(self.language_badges.get("react", ""))
        
        if "requirements.txt" in files or "pyproject.toml" in files:
            if info["type"] == "Unknown":
                info["type"] = "Python"
            else:
                info["type"] = "Full-Stack"
            info["dependencies"].append("requirements.txt" if "requirements.txt" in files else "pyproject.toml")
            info["badges"].append(self.language_badges.get("python", ""))
            
            # Check for FastAPI
            if "main.py" in files or any("fastapi" in folder.lower() for folder in folders):
                info["backend"] = "FastAPI"
                info["badges"].append(self.language_badges.get("fastapi", ""))
        
        # Check for Docker
        if "Dockerfile" in files or "docker-compose.yml" in files:
            info["has_docker"] = True
            info["badges"].append(self.language_badges.get("docker", ""))
        
        # Check for tests
        test_indicators = ["test", "tests", "__tests__", "spec"]
        info["has_tests"] = any(indicator in folder.lower() for folder in folders for indicator in test_indicators)
        
        # Detect database
        if "prisma" in folders or "prisma.schema" in files:
            info["database"] = "Prisma"
        elif any("db" in folder.lower() or "database" in folder.lower() for folder in folders):
            info["database"] = "Database (detected)"
        
        # Add language badges
        for lang in languages.keys():
            lang_lower = lang.lower()
            if lang_lower in self.language_badges and self.language_badges[lang_lower] not in info["badges"]:
                info["badges"].append(self.language_badges[lang_lower])
        
        return info
    
    def _build_readme(self, repo_data: Dict, project_info: Dict, owner: str, repo: str) -> str:
        """Build the complete README.md content"""
        description = repo_data.get('description', 'No description provided')
        stars = repo_data.get('stargazers_count', 0)
        forks = repo_data.get('forks_count', 0)
        issues = repo_data.get('open_issues_count', 0)
        license_info = repo_data.get('license', {})
        license_name = license_info.get('name', 'None') if license_info else 'None'
        
        readme = f"""# {repo}

{description}

## 📊 Repository Stats

![Stars](https://img.shields.io/github/stars/{owner}/{repo}?style=social)
![Forks](https://img.shields.io/github/forks/{owner}/{repo}?style=social)
![Issues](https://img.shields.io/github/issues/{owner}/{repo})
![License](https://img.shields.io/github/license/{owner}/{repo})

## 🛠️ Tech Stack

"""
        
        # Add badges
        if project_info["badges"]:
            readme += "\n".join(project_info["badges"]) + "\n\n"
        
        # Add project type info
        readme += f"**Project Type:** {project_info['type']}\n\n"
        
        if project_info["frontend"]:
            readme += f"**Frontend:** {project_info['frontend']}\n\n"
        if project_info["backend"]:
            readme += f"**Backend:** {project_info['backend']}\n\n"
        if project_info["database"]:
            readme += f"**Database:** {project_info['database']}\n\n"
        
        # Features section
        readme += """## ✨ Features

- 🚀 Feature 1: [Add your feature description]
- 💡 Feature 2: [Add your feature description]
- ⚡ Feature 3: [Add your feature description]

"""
        
        # Installation section
        readme += """## 📦 Installation

### Prerequisites

"""
        
        if "package.json" in project_info["dependencies"]:
            readme += "- Node.js (v16 or higher)\n- npm or yarn\n"
        
        if "requirements.txt" in project_info["dependencies"] or "pyproject.toml" in project_info["dependencies"]:
            readme += "- Python 3.8+\n- pip\n"
        
        readme += """
### Setup

1. Clone the repository

```bash
git clone https://github.com/{owner}/{repo}.git
cd {repo}
```

""".format(owner=owner, repo=repo)
        
        # Add installation steps based on project type
        if "package.json" in project_info["dependencies"]:
            readme += """2. Install Node.js dependencies

```bash
npm install
# or
yarn install
```

"""
        
        if "requirements.txt" in project_info["dependencies"]:
            readme += """3. Install Python dependencies

```bash
pip install -r requirements.txt
```

"""
        elif "pyproject.toml" in project_info["dependencies"]:
            readme += """3. Install Python dependencies

```bash
pip install -e .
```

"""
        
        # Environment variables
        readme += """4. Set up environment variables

Create a `.env` file in the root directory:

```env
# Add your environment variables here
API_KEY=your_api_key
DATABASE_URL=your_database_url
```

"""
        
        # Docker setup
        if project_info["has_docker"]:
            readme += """### 🐳 Docker Setup (Optional)

```bash
docker-compose up -d
```

"""
        
        # Usage section
        readme += """## 🚀 Usage

"""
        
        if project_info["frontend"] == "Next.js":
            readme += """Start the development server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

"""
        elif "package.json" in project_info["dependencies"]:
            readme += """Start the application:

```bash
npm start
```

"""
        
        if project_info["backend"] == "FastAPI":
            readme += """Start the backend server:

```bash
uvicorn app.main:app --reload
```

API documentation available at [http://localhost:8000/docs](http://localhost:8000/docs)

"""
        
        # Testing section
        if project_info["has_tests"]:
            readme += """## 🧪 Testing

Run tests:

```bash
npm test
# or
pytest
```

"""
        
        # Project structure
        readme += """## 📁 Project Structure

```
{repo}/
├── [Add your project structure here]
```

""".format(repo=repo)
        
        # Contributing
        readme += """## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

"""
        
        # License
        readme += f"""## 📝 License

This project is licensed under the {license_name} License - see the LICENSE file for details.

"""
        
        # Footer
        readme += """## 👤 Author

**{owner}**

- GitHub: [@{owner}](https://github.com/{owner})

## ⭐ Show your support

Give a ⭐️ if this project helped you!

---

*Generated with ❤️ by Bob AI Assistant*
""".format(owner=owner)
        
        return readme


# Singleton instance
_readme_generator = None

def get_readme_generator() -> ReadmeGenerator:
    """Get or create ReadmeGenerator instance"""
    global _readme_generator
    if _readme_generator is None:
        _readme_generator = ReadmeGenerator()
    return _readme_generator

readme_generator_service = ReadmeGenerator()