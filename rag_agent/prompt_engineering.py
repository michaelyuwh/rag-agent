"""
Advanced prompt engineering and customization system.
Provides template management, prompt optimization, and context enhancement.
"""

import json
import re
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class PromptTemplate:
    """A customizable prompt template."""
    id: str
    name: str
    description: str
    category: str  # "development", "analysis", "creative", "research"
    template: str
    variables: List[str]  # Variables that can be substituted
    parameters: Dict[str, Any]  # Default parameters (temperature, max_tokens, etc.)
    created_at: str
    modified_at: str
    usage_count: int = 0
    is_active: bool = True

@dataclass
class ContextWindow:
    """Manages context window optimization."""
    max_tokens: int
    reserved_tokens: int  # For system prompt, response, etc.
    context_ratio: float  # Ratio of context vs conversation history
    
    @property
    def available_tokens(self) -> int:
        return self.max_tokens - self.reserved_tokens
    
    @property
    def context_tokens(self) -> int:
        return int(self.available_tokens * self.context_ratio)
    
    @property
    def history_tokens(self) -> int:
        return self.available_tokens - self.context_tokens

class PromptManager:
    """Manages prompt templates and optimization."""
    
    def __init__(self, templates_dir: str = "data/prompts"):
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.templates_file = self.templates_dir / "templates.json"
        
        self.templates: Dict[str, PromptTemplate] = {}
        self.context_windows: Dict[str, ContextWindow] = {}
        
        self._load_templates()
        self._init_default_templates()
        self._init_context_windows()
    
    def _load_templates(self):
        """Load prompt templates from disk."""
        try:
            if self.templates_file.exists():
                with open(self.templates_file, 'r') as f:
                    templates_data = json.load(f)
                    self.templates = {
                        tid: PromptTemplate(**data)
                        for tid, data in templates_data.items()
                    }
                logger.info(f"Loaded {len(self.templates)} prompt templates")
        except Exception as e:
            logger.error(f"Error loading prompt templates: {e}")
            self.templates = {}
    
    def _save_templates(self):
        """Save prompt templates to disk."""
        try:
            templates_data = {
                tid: asdict(template)
                for tid, template in self.templates.items()
            }
            with open(self.templates_file, 'w') as f:
                json.dump(templates_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving prompt templates: {e}")
    
    def _init_default_templates(self):
        """Initialize default prompt templates."""
        default_templates = [
            {
                "id": "dev_assistant",
                "name": "Development Assistant",
                "description": "General purpose development assistance",
                "category": "development",
                "template": """You are an expert software developer and architect. You help with:

- Code generation and review
- Debugging and troubleshooting
- Best practices and design patterns
- Performance optimization
- Security considerations

{context_section}

User Question: {user_input}

Provide clear, practical, and actionable advice. Include code examples when helpful.""",
                "variables": ["context_section", "user_input"],
                "parameters": {"temperature": 0.3, "max_tokens": 2000}
            },
            {
                "id": "code_reviewer",
                "name": "Code Reviewer",
                "description": "Detailed code review and analysis",
                "category": "development",
                "template": """You are a senior code reviewer. Analyze the provided code for:

1. **Correctness**: Logic errors, edge cases, potential bugs
2. **Performance**: Efficiency, optimization opportunities
3. **Security**: Vulnerabilities, input validation, secure practices
4. **Maintainability**: Code clarity, documentation, structure
5. **Best Practices**: Language-specific conventions, design patterns

{context_section}

Code to Review:
```{language}
{code}
```

Provide a comprehensive review with:
- Issues found (severity: high/medium/low)
- Specific improvement suggestions
- Example fixes where applicable
- Overall assessment""",
                "variables": ["context_section", "code", "language"],
                "parameters": {"temperature": 0.2, "max_tokens": 3000}
            },
            {
                "id": "documentation_generator",
                "name": "Documentation Generator",
                "description": "Generate comprehensive documentation",
                "category": "development",
                "template": """You are a technical documentation specialist. Create clear, comprehensive documentation for:

{context_section}

Subject: {subject}
Type: {doc_type}

Requirements:
- Clear structure with headings
- Practical examples
- Prerequisites and setup instructions
- Common issues and troubleshooting
- Best practices

Generate documentation that is:
- Easy to follow for developers
- Comprehensive yet concise
- Well-organized with proper formatting
- Includes relevant code examples""",
                "variables": ["context_section", "subject", "doc_type"],
                "parameters": {"temperature": 0.4, "max_tokens": 4000}
            },
            {
                "id": "research_analyst",
                "name": "Research Analyst",
                "description": "In-depth analysis and research",
                "category": "research",
                "template": """You are a research analyst specializing in technical and business analysis. Provide thorough analysis including:

- Key findings and insights
- Data interpretation
- Trend analysis
- Recommendations
- Risk assessment

{context_section}

Research Topic: {topic}
Specific Focus: {focus_areas}

Structure your analysis with:
1. Executive Summary
2. Key Findings
3. Detailed Analysis
4. Recommendations
5. Next Steps

Be analytical, objective, and evidence-based in your response.""",
                "variables": ["context_section", "topic", "focus_areas"],
                "parameters": {"temperature": 0.5, "max_tokens": 3500}
            }
        ]
        
        # Add default templates if they don't exist
        for template_data in default_templates:
            if template_data["id"] not in self.templates:
                template = PromptTemplate(
                    created_at=datetime.now().isoformat(),
                    modified_at=datetime.now().isoformat(),
                    usage_count=0,
                    is_active=True,
                    **template_data
                )
                self.templates[template.id] = template
        
        self._save_templates()
    
    def _init_context_windows(self):
        """Initialize context window configurations for different models."""
        self.context_windows = {
            "gpt-4": ContextWindow(max_tokens=8192, reserved_tokens=1500, context_ratio=0.7),
            "gpt-3.5-turbo": ContextWindow(max_tokens=4096, reserved_tokens=1000, context_ratio=0.6),
            "claude-3": ContextWindow(max_tokens=200000, reserved_tokens=2000, context_ratio=0.8),
            "llama-7b": ContextWindow(max_tokens=4096, reserved_tokens=800, context_ratio=0.6),
            "default": ContextWindow(max_tokens=4096, reserved_tokens=1000, context_ratio=0.6),
        }
    
    def get_template(self, template_id: str) -> Optional[PromptTemplate]:
        """Get a prompt template by ID."""
        return self.templates.get(template_id)
    
    def get_templates_by_category(self, category: str) -> List[PromptTemplate]:
        """Get all templates in a category."""
        return [
            template for template in self.templates.values()
            if template.category == category and template.is_active
        ]
    
    def create_template(self, template_data: Dict[str, Any]) -> str:
        """Create a new prompt template."""
        template_id = template_data.get("id") or f"custom_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        template = PromptTemplate(
            id=template_id,
            name=template_data["name"],
            description=template_data["description"],
            category=template_data.get("category", "custom"),
            template=template_data["template"],
            variables=template_data.get("variables", []),
            parameters=template_data.get("parameters", {}),
            created_at=datetime.now().isoformat(),
            modified_at=datetime.now().isoformat(),
            usage_count=0,
            is_active=True
        )
        
        self.templates[template_id] = template
        self._save_templates()
        
        logger.info(f"Created new template: {template.name}")
        return template_id
    
    def update_template(self, template_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing template."""
        if template_id not in self.templates:
            return False
        
        template = self.templates[template_id]
        
        # Update fields
        for key, value in updates.items():
            if hasattr(template, key):
                setattr(template, key, value)
        
        template.modified_at = datetime.now().isoformat()
        self._save_templates()
        
        logger.info(f"Updated template: {template.name}")
        return True
    
    def format_prompt(self, template_id: str, variables: Dict[str, Any]) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """Format a prompt template with variables."""
        template = self.get_template(template_id)
        if not template:
            return None, None
        
        try:
            # Update usage count
            template.usage_count += 1
            self._save_templates()
            
            # Format the template
            formatted_prompt = template.template
            
            # Replace variables
            for var_name, var_value in variables.items():
                placeholder = "{" + var_name + "}"
                formatted_prompt = formatted_prompt.replace(placeholder, str(var_value))
            
            # Check for missing variables
            missing_vars = re.findall(r'\{(\w+)\}', formatted_prompt)
            if missing_vars:
                logger.warning(f"Missing variables in template {template_id}: {missing_vars}")
            
            return formatted_prompt, template.parameters
            
        except Exception as e:
            logger.error(f"Error formatting template {template_id}: {e}")
            return None, None
    
    def optimize_context(self, content: str, model_name: str = "default") -> str:
        """Optimize content for context window."""
        context_window = self.context_windows.get(model_name, self.context_windows["default"])
        
        # Estimate tokens (rough approximation: 4 chars = 1 token)
        estimated_tokens = len(content) // 4
        
        if estimated_tokens <= context_window.context_tokens:
            return content
        
        # Truncate content to fit context window
        target_chars = context_window.context_tokens * 4
        
        # Try to truncate intelligently (keep important parts)
        lines = content.split('\n')
        truncated_lines = []
        current_chars = 0
        
        # Keep first few lines (usually important context)
        for i, line in enumerate(lines[:5]):
            if current_chars + len(line) <= target_chars:
                truncated_lines.append(line)
                current_chars += len(line) + 1  # +1 for newline
        
        # Add truncation notice
        if len(lines) > len(truncated_lines):
            truncated_lines.append(f"\n[Content truncated - showing first {len(truncated_lines)} sections out of {len(lines)} total]")
        
        return '\n'.join(truncated_lines)
    
    def get_template_stats(self) -> Dict[str, Any]:
        """Get statistics about template usage."""
        active_templates = sum(1 for t in self.templates.values() if t.is_active)
        total_usage = sum(t.usage_count for t in self.templates.values())
        
        # Most used templates
        most_used = sorted(
            self.templates.values(),
            key=lambda t: t.usage_count,
            reverse=True
        )[:5]
        
        # Category breakdown
        categories = {}
        for template in self.templates.values():
            if template.is_active:
                categories[template.category] = categories.get(template.category, 0) + 1
        
        return {
            "total_templates": len(self.templates),
            "active_templates": active_templates,
            "total_usage": total_usage,
            "categories": categories,
            "most_used": [{"name": t.name, "usage": t.usage_count} for t in most_used],
        }

class PromptOptimizer:
    """Optimizes prompts for better performance."""
    
    @staticmethod
    def analyze_prompt_quality(prompt: str) -> Dict[str, Any]:
        """Analyze prompt quality and provide suggestions."""
        analysis = {
            "length": len(prompt),
            "word_count": len(prompt.split()),
            "clarity_score": 0,
            "specificity_score": 0,
            "structure_score": 0,
            "suggestions": []
        }
        
        # Clarity analysis
        if "please" in prompt.lower():
            analysis["clarity_score"] += 20
        if any(word in prompt.lower() for word in ["clear", "specific", "detailed"]):
            analysis["clarity_score"] += 20
        if prompt.count('?') > 0:
            analysis["clarity_score"] += 15
        
        # Specificity analysis
        if any(word in prompt.lower() for word in ["example", "step", "how", "what", "why"]):
            analysis["specificity_score"] += 25
        if len(prompt.split()) > 10:
            analysis["specificity_score"] += 20
        
        # Structure analysis
        if prompt.count('\n') > 1:
            analysis["structure_score"] += 30
        if any(marker in prompt for marker in ["1.", "2.", "-", "*"]):
            analysis["structure_score"] += 25
        
        # Generate suggestions
        if analysis["clarity_score"] < 40:
            analysis["suggestions"].append("Add more specific instructions or examples")
        if analysis["specificity_score"] < 30:
            analysis["suggestions"].append("Be more specific about what you want")
        if analysis["structure_score"] < 30:
            analysis["suggestions"].append("Consider structuring your prompt with bullet points or numbered lists")
        if len(prompt) < 50:
            analysis["suggestions"].append("Consider providing more context or details")
        
        return analysis

# Global prompt manager
prompt_manager = PromptManager()
prompt_optimizer = PromptOptimizer()
