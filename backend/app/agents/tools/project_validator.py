"""
Project Validator Tool
Analyzes GitHub repositories, evaluates project quality, uniqueness, and provides ratings
"""

import os
import re
import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json


class ProjectValidator:
    def __init__(self):
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        } if self.github_token else {}
        
        # Scoring weights
        self.weights = {
            "readme_quality": 2.0,
            "code_quality": 1.5,
            "documentation": 1.5,
            "activity": 1.0,
            "community": 1.0,
            "uniqueness": 2.5,
            "technical_depth": 1.5
        }
    
    def validate_project(self, repo_input: str) -> str:
        """
        Main function to validate and rate a project
        """
        try:
            # Parse repository info
            owner, repo = self._parse_repo_input(repo_input)
            
            print(f"🔍 Analyzing repository: {owner}/{repo}")
            
            # Fetch all necessary data
            repo_data = self._fetch_repo_data(owner, repo)
            readme_content = self._fetch_readme(owner, repo)
            repo_structure = self._fetch_repo_structure(owner, repo)
            languages = self._fetch_languages(owner, repo)
            commits = self._fetch_recent_commits(owner, repo)
            similar_repos = self._search_similar_projects(repo_data.get('description', ''), languages)
            
            # Perform analysis
            analysis = {
                "readme_score": self._analyze_readme(readme_content),
                "code_score": self._analyze_code_quality(repo_structure, languages),
                "documentation_score": self._analyze_documentation(repo_structure, readme_content),
                "activity_score": self._analyze_activity(repo_data, commits),
                "community_score": self._analyze_community(repo_data),
                "uniqueness_score": self._analyze_uniqueness(repo_data, similar_repos, readme_content),
                "technical_score": self._analyze_technical_depth(repo_structure, languages, readme_content)
            }
            
            # Calculate final score
            final_score = self._calculate_final_score(analysis)
            
            # Generate detailed report
            report = self._generate_report(
                owner, repo, repo_data, readme_content, 
                analysis, similar_repos, final_score
            )
            
            return report
            
        except Exception as e:
            return f"❌ Error validating project: {str(e)}"
    
    def _parse_repo_input(self, repo_input: str) -> Tuple[str, str]:
        """Parse repository input to extract owner and repo name"""
        repo_input = repo_input.rstrip('/').replace('.git', '')
        
        if 'github.com' in repo_input:
            match = re.search(r'github\.com/([^/]+)/([^/]+)', repo_input)
            if match:
                return match.group(1), match.group(2)
        
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
    
    def _fetch_readme(self, owner: str, repo: str) -> str:
        """Fetch README content"""
        readme_urls = [
            f"https://raw.githubusercontent.com/{owner}/{repo}/main/README.md",
            f"https://raw.githubusercontent.com/{owner}/{repo}/master/README.md",
            f"https://raw.githubusercontent.com/{owner}/{repo}/main/readme.md",
            f"https://raw.githubusercontent.com/{owner}/{repo}/master/readme.md"
        ]
        
        for url in readme_urls:
            response = requests.get(url)
            if response.status_code == 200:
                return response.text
        
        return ""
    
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
    
    def _fetch_recent_commits(self, owner: str, repo: str) -> List[Dict]:
        """Fetch recent commits"""
        url = f"https://api.github.com/repos/{owner}/{repo}/commits?per_page=30"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        return []
    
    def _search_similar_projects(self, description: str, languages: Dict) -> List[Dict]:
        """Search for similar projects on GitHub"""
        if not description:
            return []
        
        # Extract key terms from description
        search_terms = description.lower()[:100]  # Use first 100 chars
        primary_language = max(languages.items(), key=lambda x: x[1])[0] if languages else ""
        
        query = f"{search_terms} language:{primary_language}" if primary_language else search_terms
        url = f"https://api.github.com/search/repositories?q={query}&sort=stars&per_page=5"
        
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json().get('items', [])
        return []
    
    # ============ ANALYSIS METHODS ============
    
    def _analyze_readme(self, readme: str) -> Dict:
        """Analyze README quality (0-10)"""
        score = 0
        feedback = []
        
        if not readme:
            return {"score": 0, "feedback": ["❌ No README found"]}
        
        readme_lower = readme.lower()
        
        # Check for essential sections (2 points each, max 6)
        sections = {
            "installation": ["## installation", "## setup", "## getting started"],
            "usage": ["## usage", "## how to use", "## examples"],
            "features": ["## features", "## what it does"],
            "documentation": ["## documentation", "## api"],
            "contributing": ["## contributing", "## contribution"],
            "license": ["## license"]
        }
        
        found_sections = []
        for section, patterns in sections.items():
            if any(pattern in readme_lower for pattern in patterns):
                score += 1
                found_sections.append(section)
        
        score = min(score, 6)  # Cap at 6
        
        if len(found_sections) >= 4:
            feedback.append(f"✅ Strong README structure ({len(found_sections)} key sections)")
        else:
            feedback.append(f"⚠️ Missing important sections. Found: {', '.join(found_sections)}")
        
        # Check for visuals (1 point)
        if "![" in readme or "<img" in readme:
            score += 1
            feedback.append("✅ Contains images/diagrams")
        else:
            feedback.append("⚠️ No visual elements (screenshots, diagrams)")
        
        # Check for code examples (1 point)
        if "```" in readme:
            score += 1
            feedback.append("✅ Includes code examples")
        else:
            feedback.append("⚠️ No code examples found")
        
        # Check for badges (1 point)
        if "shields.io" in readme or "![" in readme[:500]:
            score += 0.5
            feedback.append("✅ Has status badges")
        
        # Check README length (1 point)
        if len(readme) > 1500:
            score += 0.5
            feedback.append("✅ Comprehensive documentation")
        elif len(readme) < 500:
            feedback.append("⚠️ README is too brief")
        
        return {
            "score": min(score, 10),
            "feedback": feedback,
            "length": len(readme),
            "sections_found": found_sections
        }
    
    def _analyze_code_quality(self, structure: List[Dict], languages: Dict) -> Dict:
        """Analyze code organization and structure (0-10)"""
        score = 0
        feedback = []
        
        files = {item['name']: item for item in structure if item['type'] == 'file'}
        folders = [item['name'] for item in structure if item['type'] == 'dir']
        
        # Check for organized structure (3 points)
        structure_indicators = ['src', 'lib', 'app', 'components', 'services', 'utils', 'tests']
        organized_folders = [f for f in folders if f.lower() in structure_indicators]
        
        if len(organized_folders) >= 3:
            score += 3
            feedback.append(f"✅ Well-organized structure: {', '.join(organized_folders[:3])}")
        elif len(organized_folders) >= 1:
            score += 1.5
            feedback.append(f"⚠️ Basic organization: {', '.join(organized_folders)}")
        else:
            feedback.append("⚠️ Lacks clear project structure")
        
        # Check for configuration files (2 points)
        config_files = [
            'package.json', 'requirements.txt', 'Cargo.toml', 'go.mod', 
            'Gemfile', 'composer.json', 'pyproject.toml'
        ]
        found_configs = [f for f in config_files if f in files]
        
        if found_configs:
            score += 2
            feedback.append(f"✅ Proper dependency management: {', '.join(found_configs)}")
        
        # Check for testing (2 points)
        test_indicators = ['test', 'tests', '__tests__', 'spec', 'pytest', 'jest']
        has_tests = any(indicator in folder.lower() for folder in folders for indicator in test_indicators)
        
        if has_tests:
            score += 2
            feedback.append("✅ Includes test suite")
        else:
            feedback.append("❌ No tests detected")
        
        # Check for CI/CD (1 point)
        ci_files = ['.github', '.gitlab-ci.yml', '.travis.yml', 'Jenkinsfile']
        has_ci = any(ci in files or ci in folders for ci in ci_files)
        
        if has_ci:
            score += 1
            feedback.append("✅ CI/CD configured")
        
        # Check for Docker (1 point)
        if 'Dockerfile' in files or 'docker-compose.yml' in files:
            score += 1
            feedback.append("✅ Dockerized")
        
        # Check for linting/formatting (1 point)
        lint_files = ['.eslintrc', '.prettierrc', 'pylint.rc', '.flake8', 'tslint.json']
        has_linting = any(lint in files or lint in str(files) for lint in lint_files)
        
        if has_linting:
            score += 1
            feedback.append("✅ Code quality tools configured")
        
        return {
            "score": min(score, 10),
            "feedback": feedback,
            "has_tests": has_tests,
            "has_ci": has_ci
        }
    
    def _analyze_documentation(self, structure: List[Dict], readme: str) -> Dict:
        """Analyze project documentation (0-10)"""
        score = 0
        feedback = []
        
        folders = [item['name'] for item in structure if item['type'] == 'dir']
        files = [item['name'] for item in structure if item['type'] == 'file']
        
        # Check for docs folder (3 points)
        doc_folders = ['docs', 'documentation', 'doc', 'wiki']
        has_docs_folder = any(doc in folders for doc in doc_folders)
        
        if has_docs_folder:
            score += 3
            feedback.append("✅ Dedicated documentation folder")
        
        # Check README quality (3 points)
        if len(readme) > 2000:
            score += 3
            feedback.append("✅ Comprehensive README")
        elif len(readme) > 1000:
            score += 2
            feedback.append("✅ Good README coverage")
        elif len(readme) > 500:
            score += 1
            feedback.append("⚠️ Basic README")
        
        # Check for API documentation (2 points)
        api_docs = ['swagger', 'openapi', 'api.md', 'API.md']
        has_api_docs = any(doc in str(files) or doc.lower() in readme.lower() for doc in api_docs)
        
        if has_api_docs:
            score += 2
            feedback.append("✅ API documentation present")
        
        # Check for contribution guidelines (1 point)
        if 'CONTRIBUTING.md' in files or 'contributing' in readme.lower():
            score += 1
            feedback.append("✅ Contribution guidelines")
        
        # Check for changelog (1 point)
        if 'CHANGELOG.md' in files or 'changelog' in readme.lower():
            score += 1
            feedback.append("✅ Changelog maintained")
        
        return {
            "score": min(score, 10),
            "feedback": feedback
        }
    
    def _analyze_activity(self, repo_data: Dict, commits: List[Dict]) -> Dict:
        """Analyze repository activity (0-10)"""
        score = 0
        feedback = []
        
        # Recent commits (4 points)
        if commits:
            recent_commit_date = commits[0]['commit']['author']['date']
            from datetime import datetime
            last_commit = datetime.strptime(recent_commit_date, "%Y-%m-%dT%H:%M:%SZ")
            days_since = (datetime.now() - last_commit).days
            
            if days_since < 7:
                score += 4
                feedback.append("✅ Very active (commits within last week)")
            elif days_since < 30:
                score += 3
                feedback.append("✅ Active (commits within last month)")
            elif days_since < 90:
                score += 2
                feedback.append("⚠️ Moderately active (commits within 3 months)")
            elif days_since < 180:
                score += 1
                feedback.append("⚠️ Low activity (commits within 6 months)")
            else:
                feedback.append("❌ Inactive (no recent commits)")
        
        # Commit frequency (3 points)
        if len(commits) >= 20:
            score += 3
            feedback.append(f"✅ High commit frequency ({len(commits)} recent commits)")
        elif len(commits) >= 10:
            score += 2
        elif len(commits) >= 5:
            score += 1
        
        # Open issues management (3 points)
        open_issues = repo_data.get('open_issues_count', 0)
        if open_issues == 0:
            score += 3
            feedback.append("✅ No open issues")
        elif open_issues < 5:
            score += 2
            feedback.append("✅ Few open issues")
        elif open_issues < 20:
            score += 1
            feedback.append("⚠️ Some open issues")
        else:
            feedback.append(f"⚠️ Many open issues ({open_issues})")
        
        return {
            "score": min(score, 10),
            "feedback": feedback
        }
    
    def _analyze_community(self, repo_data: Dict) -> Dict:
        """Analyze community engagement (0-10)"""
        score = 0
        feedback = []
        
        stars = repo_data.get('stargazers_count', 0)
        forks = repo_data.get('forks_count', 0)
        watchers = repo_data.get('watchers_count', 0)
        
        # Stars scoring (4 points)
        if stars >= 1000:
            score += 4
            feedback.append(f"⭐ Popular project ({stars} stars)")
        elif stars >= 100:
            score += 3
            feedback.append(f"✅ Good traction ({stars} stars)")
        elif stars >= 20:
            score += 2
            feedback.append(f"✅ Some interest ({stars} stars)")
        elif stars >= 5:
            score += 1
            feedback.append(f"⚠️ Limited attention ({stars} stars)")
        else:
            feedback.append("⚠️ New/unknown project (few stars)")
        
        # Forks scoring (3 points)
        if forks >= 100:
            score += 3
            feedback.append(f"✅ Highly forked ({forks} forks)")
        elif forks >= 20:
            score += 2
        elif forks >= 5:
            score += 1
        
        # Has license (2 points)
        if repo_data.get('license'):
            score += 2
            feedback.append(f"✅ Licensed: {repo_data['license']['name']}")
        else:
            feedback.append("⚠️ No license specified")
        
        # Community health (1 point)
        has_issues = repo_data.get('has_issues', False)
        if has_issues:
            score += 1
            feedback.append("✅ Issues enabled (community support)")
        
        return {
            "score": min(score, 10),
            "feedback": feedback
        }
    
    def _analyze_uniqueness(self, repo_data: Dict, similar_repos: List[Dict], readme: str) -> Dict:
        """Analyze project uniqueness (0-10)"""
        score = 5  # Start neutral
        feedback = []
        usp_points = []
        
        description = repo_data.get('description', '').lower()
        readme_lower = readme.lower()
        
        # Check for innovation keywords
        innovation_keywords = [
            'novel', 'first', 'new approach', 'innovative', 'unique',
            'revolutionary', 'cutting-edge', 'breakthrough', 'never before'
        ]
        
        innovation_found = sum(1 for keyword in innovation_keywords if keyword in readme_lower or keyword in description)
        
        if innovation_found >= 3:
            score += 2
            feedback.append("✅ Claims innovation/uniqueness")
        elif innovation_found >= 1:
            score += 1
        
        # Analyze similar projects
        if similar_repos:
            avg_stars = sum(repo.get('stargazers_count', 0) for repo in similar_repos) / len(similar_repos)
            current_stars = repo_data.get('stargazers_count', 0)
            
            if current_stars > avg_stars * 2:
                score += 2
                feedback.append(f"⭐ Outperforms similar projects (2x more stars)")
                usp_points.append("Market leader in category")
            elif current_stars > avg_stars:
                score += 1
                feedback.append("✅ Competitive with similar projects")
            else:
                score -= 1
                feedback.append(f"⚠️ Similar projects exist with more traction")
        else:
            score += 2
            feedback.append("✅ Few/no similar projects found (potentially unique)")
            usp_points.append("Pioneering in this space")
        
        # Check for unique tech stack combinations
        languages = repo_data.get('language', '')
        unique_combos = [
            'rust + webassembly', 'ai + blockchain', 'ml + edge computing',
            'quantum', 'web3', 'decentralized'
        ]
        
        if any(combo in readme_lower for combo in unique_combos):
            score += 1
            feedback.append("✅ Uses cutting-edge technology")
            usp_points.append("Innovative tech stack")
        
        # Extract USP from README
        usp_sections = re.findall(r'(?:why this|unique|different|usp|features).*?(?:\n\n|\Z)', readme_lower, re.DOTALL)
        
        if usp_sections:
            score += 1
            feedback.append("✅ Clearly defines unique value proposition")
        else:
            feedback.append("⚠️ USP not clearly articulated")
        
        # Detect problem-solving focus
        problem_keywords = ['solves', 'addresses', 'fixes', 'improves', 'better than']
        if sum(1 for kw in problem_keywords if kw in readme_lower) >= 2:
            score += 1
            usp_points.append("Clear problem-solution fit")
        
        return {
            "score": min(max(score, 0), 10),
            "feedback": feedback,
            "usp_points": usp_points,
            "similar_count": len(similar_repos)
        }
    
    def _analyze_technical_depth(self, structure: List[Dict], languages: Dict, readme: str) -> Dict:
        """Analyze technical complexity and depth (0-10)"""
        score = 0
        feedback = []
        
        # Multiple languages (2 points)
        if len(languages) >= 3:
            score += 2
            feedback.append(f"✅ Multi-language project ({len(languages)} languages)")
        elif len(languages) == 2:
            score += 1
        
        # Complex architecture indicators (3 points)
        architecture_keywords = [
            'microservice', 'distributed', 'scalable', 'architecture',
            'kubernetes', 'docker', 'api gateway', 'load balanc'
        ]
        
        arch_found = sum(1 for kw in architecture_keywords if kw in readme.lower())
        if arch_found >= 3:
            score += 3
            feedback.append("✅ Complex/scalable architecture")
        elif arch_found >= 1:
            score += 1.5
        
        # Advanced tech stack (2 points)
        advanced_tech = [
            'machine learning', 'ai', 'neural network', 'blockchain',
            'webassembly', 'graphql', 'grpc', 'websocket'
        ]
        
        if any(tech in readme.lower() for tech in advanced_tech):
            score += 2
            feedback.append("✅ Advanced technology implementation")
        
        # Database/data management (1 point)
        db_indicators = ['database', 'postgresql', 'mongodb', 'redis', 'sql', 'orm']
        if any(db in readme.lower() for db in db_indicators):
            score += 1
            feedback.append("✅ Data persistence layer")
        
        # Security features (1 point)
        security_keywords = ['authentication', 'authorization', 'encryption', 'jwt', 'oauth', 'security']
        if sum(1 for kw in security_keywords if kw in readme.lower()) >= 2:
            score += 1
            feedback.append("✅ Security considerations")
        
        # Performance optimization (1 point)
        perf_keywords = ['optimiz', 'performance', 'caching', 'fast', 'efficient']
        if any(kw in readme.lower() for kw in perf_keywords):
            score += 1
            feedback.append("✅ Performance-focused")
        
        return {
            "score": min(score, 10),
            "feedback": feedback
        }
    
    def _calculate_final_score(self, analysis: Dict) -> float:
        """Calculate weighted final score"""
        total_score = 0
        total_weight = sum(self.weights.values())
        
        score_mapping = {
            "readme_score": "readme_quality",
            "code_score": "code_quality",
            "documentation_score": "documentation",
            "activity_score": "activity",
            "community_score": "community",
            "uniqueness_score": "uniqueness",
            "technical_score": "technical_depth"
        }
        
        for score_key, weight_key in score_mapping.items():
            score_value = analysis[score_key].get('score', 0)
            weight = self.weights[weight_key]
            total_score += score_value * weight
        
        return round((total_score / total_weight), 1)
    
    def _generate_report(self, owner: str, repo: str, repo_data: Dict, 
                        readme: str, analysis: Dict, similar_repos: List[Dict], 
                        final_score: float) -> str:
        """Generate comprehensive validation report"""
        
        report = f"""
╔════════════════════════════════════════════════════════════════╗
║         PROJECT VALIDATION REPORT                              ║
╚════════════════════════════════════════════════════════════════╝

📦 **Project:** {owner}/{repo}
📝 **Description:** {repo_data.get('description', 'No description')}
🔗 **URL:** https://github.com/{owner}/{repo}

═══════════════════════════════════════════════════════════════

🎯 **FINAL SCORE: {final_score}/10**

"""
        
        # Rating interpretation
        if final_score >= 8.5:
            report += "⭐⭐⭐⭐⭐ **EXCELLENT** - Production-ready, well-maintained project\n\n"
        elif final_score >= 7.0:
            report += "⭐⭐⭐⭐ **VERY GOOD** - Strong project with minor improvements needed\n\n"
        elif final_score >= 5.5:
            report += "⭐⭐⭐ **GOOD** - Solid foundation, needs more polish\n\n"
        elif final_score >= 4.0:
            report += "⭐⭐ **FAIR** - Basic project, requires significant improvements\n\n"
        else:
            report += "⭐ **NEEDS WORK** - Major improvements required\n\n"
        
        report += "═══════════════════════════════════════════════════════════════\n\n"
        
        # Detailed scores
        report += "📊 **DETAILED BREAKDOWN:**\n\n"
        
        sections = [
            ("README Quality", analysis["readme_score"]),
            ("Code Organization", analysis["code_score"]),
            ("Documentation", analysis["documentation_score"]),
            ("Project Activity", analysis["activity_score"]),
            ("Community Engagement", analysis["community_score"]),
            ("Uniqueness & USP", analysis["uniqueness_score"]),
            ("Technical Depth", analysis["technical_score"])
        ]
        
        for section_name, section_data in sections:
            score = section_data.get('score', 0)
            bars = "█" * int(score) + "░" * (10 - int(score))
            report += f"**{section_name}:** {bars} {score}/10\n"
            
            for fb in section_data.get('feedback', []):
                report += f"  {fb}\n"
            report += "\n"
        
        report += "═══════════════════════════════════════════════════════════════\n\n"
        
        # Unique Selling Points
        usp_points = analysis["uniqueness_score"].get('usp_points', [])
        if usp_points:
            report += "💡 **UNIQUE SELLING POINTS:**\n\n"
            for usp in usp_points:
                report += f"  • {usp}\n"
            report += "\n"
        else:
            report += "⚠️ **UNIQUE SELLING POINTS:** Not clearly defined\n\n"
        
        # Similar projects
        if similar_repos:
            report += f"🔍 **COMPETITIVE ANALYSIS:** Found {len(similar_repos)} similar projects\n\n"
            report += "Top competitors:\n"
            for idx, sim_repo in enumerate(similar_repos[:3], 1):
                stars = sim_repo.get('stargazers_count', 0)
                report += f"  {idx}. {sim_repo['full_name']} ({stars} ⭐)\n"
            report += "\n"
        
        # Recommendations
        report += "═══════════════════════════════════════════════════════════════\n\n"
        report += "💪 **RECOMMENDATIONS FOR IMPROVEMENT:**\n\n"
        
        recommendations = self._generate_recommendations(analysis, final_score)
        for idx, rec in enumerate(recommendations, 1):
            report += f"{idx}. {rec}\n"
        
        report += "\n═══════════════════════════════════════════════════════════════\n"
        report += f"\n✨ *Analysis completed on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
        
        return report
    
    def _generate_recommendations(self, analysis: Dict, final_score: float) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # README recommendations
        if analysis["readme_score"]["score"] < 7:
            missing = set(["installation", "usage", "features", "contributing"]) - set(analysis["readme_score"].get("sections_found", []))
            if missing:
                recommendations.append(f"📝 Add missing README sections: {', '.join(missing)}")
            if analysis["readme_score"].get("length", 0) < 1000:
                recommendations.append("📝 Expand README with more detailed documentation and examples")
        
        # Code quality recommendations
        if analysis["code_score"]["score"] < 7:
            if not analysis["code_score"].get("has_tests"):
                recommendations.append("🧪 Add unit tests and integration tests")
            if not analysis["code_score"].get("has_ci"):
                recommendations.append("⚙️ Set up CI/CD pipeline (GitHub Actions, Travis, etc.)")
        
        # Documentation recommendations
        if analysis["documentation_score"]["score"] < 7:
            recommendations.append("📚 Create dedicated documentation folder with API references")
        
        # Activity recommendations
        if analysis["activity_score"]["score"] < 6:
            recommendations.append("🔄 Maintain regular commit activity and address open issues")
        
        # Community recommendations
        if analysis["community_score"]["score"] < 5:
            recommendations.append("👥 Improve community engagement: add license, enable issues, promote project")
        
        # Uniqueness recommendations
        if analysis["uniqueness_score"]["score"] < 6:
            recommendations.append("💡 Clearly articulate your unique value proposition and differentiation")
            recommendations.append("🎯 Research competitors and highlight what makes your approach better")
        
        # Technical depth recommendations
        if analysis["technical_score"]["score"] < 6:
            recommendations.append("🔧 Consider adding advanced features (auth, caching, optimization)")
        
        # General recommendations
        if final_score < 7:
            recommendations.append("🚀 Focus on the fundamentals: documentation, tests, and code organization")
        
        return recommendations[:6]  # Return top 6 recommendations


# Singleton instance
_project_validator = None

def get_project_validator() -> ProjectValidator:
    """Get or create ProjectValidator instance"""
    global _project_validator
    if _project_validator is None:
        _project_validator = ProjectValidator()
    return _project_validator