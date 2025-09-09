"""
Agent logic: ReAct framework, tool belt, and prompt engineering.
Handles interaction with AI models and provides development tools.
"""

import json
import logging
import asyncio
import re
import math
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime

try:
    import requests
    from langchain_ollama import ChatOllama
    from langchain_openai import ChatOpenAI
    from langchain_anthropic import ChatAnthropic
except ImportError:
    # Will be handled gracefully
    pass

from .config import config_manager, ModelConfig
from .retrieval import DocumentRetrieval

logger = logging.getLogger(__name__)

class CalculatorTool:
    """Simple calculator tool for mathematical operations."""
    
    @staticmethod
    def calculate(expression: str) -> str:
        """Safely evaluate mathematical expressions."""
        try:
            # Remove any non-mathematical characters for safety
            safe_expr = re.sub(r'[^0-9+\-*/().\s]', '', expression)
            
            # Replace common math functions
            safe_expr = safe_expr.replace('sqrt', 'math.sqrt')
            safe_expr = safe_expr.replace('sin', 'math.sin')
            safe_expr = safe_expr.replace('cos', 'math.cos')
            safe_expr = safe_expr.replace('tan', 'math.tan')
            safe_expr = safe_expr.replace('log', 'math.log')
            safe_expr = safe_expr.replace('pi', 'math.pi')
            safe_expr = safe_expr.replace('e', 'math.e')
            
            # Evaluate the expression
            result = eval(safe_expr, {"__builtins__": {}, "math": math})
            return f"Result: {result}"
        except Exception as e:
            return f"Error calculating '{expression}': {str(e)}"

class WebSearchTool:
    """Web search tool (simulated - in production would use real search API)."""
    
    @staticmethod
    def search(query: str) -> str:
        """Simulate web search (placeholder for real implementation)."""
        # In a real implementation, this would use APIs like:
        # - DuckDuckGo Search API
        # - Google Custom Search API
        # - Bing Search API
        
        return f"""Web search results for "{query}":

[This is a simulated search result. In production, this would return real web search results.]

To implement real web search, you could integrate:
1. DuckDuckGo Instant Answer API (free)
2. Google Custom Search JSON API
3. Bing Web Search API
4. SerpAPI for Google results

Example result: Based on current knowledge, {query} relates to programming, development, 
or technical topics that would benefit from real-time web search capabilities."""

class CodeAnalysisTool:
    """Tool for analyzing code snippets."""
    
    @staticmethod
    def analyze_code(code: str, language: str = "python") -> str:
        """Analyze code for potential issues, improvements, or explanations."""
        analysis = []
        
        # Basic code analysis
        lines = code.split('\n')
        analysis.append(f"Code Analysis for {language.title()}:")
        analysis.append(f"- Total lines: {len(lines)}")
        analysis.append(f"- Non-empty lines: {len([l for l in lines if l.strip()])}")
        
        if language.lower() == "python":
            # Python-specific analysis
            if "import " in code:
                imports = [l.strip() for l in lines if l.strip().startswith('import ') or l.strip().startswith('from ')]
                analysis.append(f"- Imports found: {len(imports)}")
            
            if "def " in code:
                functions = [l.strip() for l in lines if l.strip().startswith('def ')]
                analysis.append(f"- Functions defined: {len(functions)}")
            
            if "class " in code:
                classes = [l.strip() for l in lines if l.strip().startswith('class ')]
                analysis.append(f"- Classes defined: {len(classes)}")
            
            # Check for common patterns
            if "print(" in code:
                analysis.append("- Contains print statements (consider using logging)")
            
            if "TODO" in code or "FIXME" in code:
                analysis.append("- Contains TODO/FIXME comments")
        
        return "\n".join(analysis)

@dataclass
class ChatMessage:
    """Represents a chat message."""
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class ChatSession:
    """Represents a chat session."""
    id: str
    title: str
    messages: List[ChatMessage]
    created_at: datetime
    updated_at: datetime
    model_used: Optional[str] = None

class ModelInterface:
    """Interface for different AI model types."""
    
    def __init__(self, model_config: ModelConfig):
        self.config = model_config
        self.client = None
        self._initialize_client()
        
    def _initialize_client(self):
        """Initialize the appropriate client based on model type."""
        try:
            if self.config.type == "ollama":
                self.client = ChatOllama(
                    base_url=self.config.endpoint,
                    model=self.config.model_id or self.config.name
                )
            elif self.config.type == "openai":
                self.client = ChatOpenAI(
                    api_key=self.config.api_key,
                    base_url=self.config.endpoint,
                    model=self.config.model_id
                )
            elif self.config.type == "anthropic":
                self.client = ChatAnthropic(
                    api_key=self.config.api_key,
                    model=self.config.model_id
                )
            elif self.config.type == "lm_studio":
                self.client = ChatOpenAI(
                    api_key="lm-studio",  # LM Studio doesn't require real API key
                    base_url=self.config.endpoint,
                    model=self.config.model_id or "local-model"
                )
            else:
                logger.error(f"Unsupported model type: {self.config.type}")
                
        except Exception as e:
            logger.error(f"Error initializing {self.config.type} client: {e}")
            self.client = None
            
    def is_available(self) -> bool:
        """Check if the model is available."""
        if not self.client:
            return False
            
        try:
            if self.config.type in ["ollama", "lm_studio"]:
                # Check if local server is running
                response = requests.get(
                    self.config.endpoint.replace("/v1", "") + "/api/tags" if "ollama" in self.config.endpoint 
                    else self.config.endpoint + "/models",
                    timeout=5
                )
                return response.status_code == 200
            else:
                # For cloud models, assume available if API key is provided
                return bool(self.config.api_key)
                
        except Exception as e:
            logger.error(f"Error checking availability for {self.config.name}: {e}")
            return False
            
    def generate_response(self, messages: List[ChatMessage], **kwargs) -> Optional[str]:
        """Generate response from the model."""
        if not self.client:
            raise RuntimeError(f"Client not initialized for {self.config.name}")
            
        try:
            # Convert ChatMessage objects to format expected by LangChain
            formatted_messages = []
            for msg in messages:
                formatted_messages.append((msg.role, msg.content))
                
            # Generate response
            response = self.client.invoke(formatted_messages)
            
            if hasattr(response, 'content'):
                return response.content
            else:
                return str(response)
                
        except Exception as e:
            logger.error(f"Error generating response with {self.config.name}: {e}")
            raise

class RAGAgent:
    """Main RAG Agent that combines retrieval and generation."""
    
    def __init__(self):
        self.config = config_manager.config
        self.retrieval = DocumentRetrieval(
            vector_store_path=self.config.vector_store_path,
            embedding_model=self.config.embedding_model
        )
        self.current_model: Optional[ModelInterface] = None
        self.chat_sessions: Dict[str, ChatSession] = {}
        self.current_session_id: Optional[str] = None
        
        # Initialize tools
        self.tools = {
            "calculator": CalculatorTool(),
            "web_search": WebSearchTool(),
            "code_analysis": CodeAnalysisTool()
        }
        
        # Load chat history
        self._load_chat_sessions()
        
        # Initialize with selected model
        if self.config.selected_model:
            self.switch_model(self.config.selected_model)
            
    def _load_chat_sessions(self):
        """Load chat sessions from disk."""
        try:
            import os
            history_dir = self.config.chat_history_path
            os.makedirs(history_dir, exist_ok=True)
            
            history_file = os.path.join(history_dir, "sessions.json")
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    sessions_data = json.load(f)
                    
                # Handle both dictionary and array formats
                if isinstance(sessions_data, dict):
                    # Convert dict format to list of sessions
                    sessions_list = list(sessions_data.values())
                elif isinstance(sessions_data, list):
                    sessions_list = sessions_data
                else:
                    logger.warning(f"Unknown sessions data format: {type(sessions_data)}")
                    return
                    
                for session_data in sessions_list:
                    # Convert message timestamps back to datetime
                    messages = []
                    for msg_data in session_data['messages']:
                        msg = ChatMessage(
                            role=msg_data['role'],
                            content=msg_data['content'],
                            timestamp=datetime.fromisoformat(msg_data['timestamp']),
                            metadata=msg_data.get('metadata')
                        )
                        messages.append(msg)
                        
                    session = ChatSession(
                        id=session_data['id'],
                        title=session_data['title'],
                        messages=messages,
                        created_at=datetime.fromisoformat(session_data['created_at']),
                        updated_at=datetime.fromisoformat(session_data['updated_at']),
                        model_used=session_data.get('model_used')
                    )
                    self.chat_sessions[session.id] = session
                    
        except Exception as e:
            logger.error(f"Error loading chat sessions: {e}")
            
    def _save_chat_sessions(self):
        """Save chat sessions to disk."""
        try:
            import os
            history_dir = self.config.chat_history_path
            os.makedirs(history_dir, exist_ok=True)
            
            # Convert sessions to JSON-serializable format
            sessions_data = []
            for session in self.chat_sessions.values():
                messages_data = []
                for msg in session.messages:
                    msg_data = {
                        'role': msg.role,
                        'content': msg.content,
                        'timestamp': msg.timestamp.isoformat(),
                        'metadata': msg.metadata
                    }
                    messages_data.append(msg_data)
                    
                session_data = {
                    'id': session.id,
                    'title': session.title,
                    'messages': messages_data,
                    'created_at': session.created_at.isoformat(),
                    'updated_at': session.updated_at.isoformat(),
                    'model_used': session.model_used
                }
                sessions_data.append(session_data)
                
            history_file = os.path.join(history_dir, "sessions.json")
            with open(history_file, 'w') as f:
                json.dump(sessions_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving chat sessions: {e}")
            
    def get_available_models(self) -> List[ModelConfig]:
        """Get list of available models."""
        available = []
        for model_config in self.config.models.values():
            interface = ModelInterface(model_config)
            if interface.is_available():
                model_config.is_available = True
                available.append(model_config)
            else:
                model_config.is_available = False
                
        return available
        
    def switch_model(self, model_key: str) -> bool:
        """Switch to a different model."""
        if model_key not in self.config.models:
            logger.error(f"Model {model_key} not found in configuration")
            return False
            
        model_config = self.config.models[model_key]
        
        try:
            new_interface = ModelInterface(model_config)
            if new_interface.is_available():
                self.current_model = new_interface
                self.config.selected_model = model_key
                config_manager.save_config()
                logger.info(f"Switched to model: {model_config.name}")
                return True
            else:
                logger.error(f"Model {model_config.name} is not available")
                return False
                
        except Exception as e:
            logger.error(f"Error switching to model {model_config.name}: {e}")
            return False
            
    def create_new_session(self, title: str = None) -> str:
        """Create a new chat session."""
        import uuid
        
        session_id = str(uuid.uuid4())
        now = datetime.now()
        
        if not title:
            title = f"Chat Session - {now.strftime('%b %d, %Y %H:%M')}"
            
        session = ChatSession(
            id=session_id,
            title=title,
            messages=[],
            created_at=now,
            updated_at=now,
            model_used=self.config.selected_model
        )
        
        self.chat_sessions[session_id] = session
        self.current_session_id = session_id
        self._save_chat_sessions()
        
        logger.info(f"Created new session: {title}")
        return session_id
        
    def switch_session(self, session_id: str) -> bool:
        """Switch to an existing session."""
        if session_id in self.chat_sessions:
            self.current_session_id = session_id
            logger.info(f"Switched to session: {self.chat_sessions[session_id].title}")
            return True
        else:
            logger.error(f"Session {session_id} not found")
            return False
            
    def delete_session(self, session_id: str) -> bool:
        """Delete a chat session."""
        if session_id in self.chat_sessions:
            title = self.chat_sessions[session_id].title
            del self.chat_sessions[session_id]
            
            if self.current_session_id == session_id:
                self.current_session_id = None
                
            self._save_chat_sessions()
            logger.info(f"Deleted session: {title}")
            return True
        else:
            return False
            
    def get_current_session(self) -> Optional[ChatSession]:
        """Get the current chat session."""
        if self.current_session_id:
            return self.chat_sessions.get(self.current_session_id)
        return None
        
    def generate_session_title(self, messages: List[ChatMessage]) -> str:
        """Generate a title for a session based on its messages."""
        if not messages:
            return "Empty Session"
            
        # Use first user message as basis for title
        first_user_msg = next((msg for msg in messages if msg.role == "user"), None)
        
        if not first_user_msg:
            return "Chat Session"
            
        # Extract key topics (simple approach)
        content = first_user_msg.content[:100]  # First 100 chars
        
        # Try to generate with AI if available
        if self.current_model:
            try:
                prompt_msgs = [
                    ChatMessage(
                        role="system",
                        content="Generate a short 4-6 word title for this conversation topic. Be specific and descriptive.",
                        timestamp=datetime.now()
                    ),
                    ChatMessage(
                        role="user", 
                        content=f"Topic: {content}",
                        timestamp=datetime.now()
                    )
                ]
                
                title = self.current_model.generate_response(prompt_msgs)
                if title and len(title) < 60:
                    return title.strip().strip('"')
                    
            except Exception as e:
                logger.error(f"Error generating title: {e}")
                
        # Fallback: extract key words
        words = content.split()[:4]
        return " ".join(words) + ("..." if len(content) > 100 else "")
        
    def _process_tool_calls(self, text: str) -> str:
        """Process any tool calls in the text and execute them."""
        import re
        
        # Look for tool call patterns like [TOOL:calculator:2+2] or [TOOL:web_search:python tutorial]
        tool_pattern = r'\[TOOL:(\w+):([^\]]+)\]'
        
        def execute_tool(match):
            tool_name = match.group(1)
            tool_input = match.group(2).strip()
            
            try:
                if tool_name == "calculator":
                    result = self.tools["calculator"].calculate(tool_input)
                    return f"🧮 {result}"
                elif tool_name == "web_search":
                    result = self.tools["web_search"].search(tool_input)
                    return f"🔍 {result}"
                elif tool_name == "code_analysis":
                    # Extract language if provided, default to python
                    if ":" in tool_input:
                        lang, code = tool_input.split(":", 1)
                        result = self.tools["code_analysis"].analyze_code(code.strip(), lang.strip())
                    else:
                        result = self.tools["code_analysis"].analyze_code(tool_input, "python")
                    return f"🔧 {result}"
                else:
                    return f"❌ Unknown tool: {tool_name}"
            except Exception as e:
                return f"❌ Tool error: {str(e)}"
        
        # Replace all tool calls with their results
        processed_text = re.sub(tool_pattern, execute_tool, text)
        return processed_text

    def chat(self, user_input: str, use_rag: bool = True) -> str:
        """
        Main chat function that processes user input and generates response.
        
        Args:
            user_input: User's message
            use_rag: Whether to use RAG (retrieval) for context
            
        Returns:
            Assistant's response
        """
        if not self.current_model:
            return "No AI model selected. Please configure a model first."
            
        # Ensure we have a current session
        if not self.current_session_id:
            self.create_new_session()
            
        current_session = self.get_current_session()
        if not current_session:
            return "Error: Could not create or access chat session."
            
        try:
            # Add user message to session
            user_msg = ChatMessage(
                role="user",
                content=user_input,
                timestamp=datetime.now()
            )
            current_session.messages.append(user_msg)
            
            # Prepare messages for the model
            messages_for_model = []
            
            # System prompt
            system_prompt = self._create_system_prompt(use_rag, user_input if use_rag else None)
            if system_prompt:
                messages_for_model.append(ChatMessage(
                    role="system",
                    content=system_prompt,
                    timestamp=datetime.now()
                ))
            
            # Add recent conversation history (last 10 messages)
            recent_messages = current_session.messages[-10:]
            messages_for_model.extend(recent_messages)
            
            # Generate response
            response = self.current_model.generate_response(messages_for_model)
            
            if response:
                # Process any tool calls in the response
                processed_response = self._process_tool_calls(response)
                
                # Add assistant response to session
                assistant_msg = ChatMessage(
                    role="assistant",
                    content=processed_response,
                    timestamp=datetime.now(),
                    metadata={"model_used": self.config.selected_model}
                )
                current_session.messages.append(assistant_msg)
                
                # Update session title if this is the first exchange
                if len(current_session.messages) <= 2:
                    current_session.title = self.generate_session_title(current_session.messages)
                    
                # Update timestamps
                current_session.updated_at = datetime.now()
                current_session.model_used = self.config.selected_model
                
                # Save session
                self._save_chat_sessions()
                
                return processed_response
            else:
                return "Sorry, I couldn't generate a response. Please try again."
                
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return f"Error generating response: {str(e)}"
            
    def _create_system_prompt(self, use_rag: bool, query: str = None) -> str:
        """Create system prompt with optional RAG context."""
        base_prompt = """You are a helpful AI assistant specialized in development tasks. You can help with:
- Code generation and review
- Debugging and troubleshooting  
- Explaining technical concepts
- Document analysis and summarization
- Architecture and design guidance

You have access to the following tools that you can use by including tool calls in your response:

🧮 **Calculator**: Use [TOOL:calculator:expression] for mathematical calculations
   Example: [TOOL:calculator:2+2*3] or [TOOL:calculator:sqrt(16)]

🔍 **Web Search**: Use [TOOL:web_search:query] to search for current information
   Example: [TOOL:web_search:latest Python features 2024]

🔧 **Code Analysis**: Use [TOOL:code_analysis:code] or [TOOL:code_analysis:language:code] to analyze code
   Example: [TOOL:code_analysis:python:def hello(): print("world")]

When using tools, the results will be automatically inserted into your response. Use these tools when they would be helpful for answering the user's question.

Provide clear, accurate, and helpful responses. Use markdown formatting for code blocks."""

        if use_rag and query and self.retrieval.is_available():
            # Get relevant context from documents
            context = self.retrieval.get_context_for_query(query, max_tokens=2000)
            
            if context and "No relevant documents found" not in context:
                rag_prompt = f"""

## Available Context
You have access to the following relevant information from the user's documents:

{context}

Use this context to provide more accurate and specific answers when relevant. If the context doesn't contain relevant information for the user's question, rely on your general knowledge."""

                return base_prompt + rag_prompt
                
        return base_prompt

# Global agent instance
rag_agent = RAGAgent()
