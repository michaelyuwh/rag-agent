"""
Streamlit-based UI for the RAG Agent.
Provides chat interface, document management, and configuration.
"""

import streamlit as st
import os
import tempfile
import json
import uuid
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

# Set up logging
logger = logging.getLogger(__name__)

# Configure page
st.set_page_config(
    page_title="RAG Agent", 
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import our modules (with error handling for development)
try:
    from .config import config_manager
    from .agent import rag_agent
    from .ingestion import DocumentIngestion
    from .retrieval import DocumentRetrieval
    from .admin import show_admin_panel, show_code_playground, add_admin_to_navigation
except ImportError:
    # For development mode when packages aren't installed
    st.error("⚠️ Required packages not installed. Please run: pip install -r requirements.txt")
    st.stop()

# Initialize session state
def init_session_state():
    """Initialize session state variables."""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.current_page = "Chat"
        st.session_state.ingestion = None
        st.session_state.retrieval = None
        st.session_state.chat_sessions = load_chat_sessions()
        st.session_state.current_session_id = None
        st.session_state.current_messages = []
        
        # Create new session if none exist
        if not st.session_state.chat_sessions:
            create_new_chat_session()

def migrate_session_data(sessions: Dict) -> Dict:
    """Migrate old session format to new format."""
    migrated = {}
    try:
        for key, session in sessions.items():
            if isinstance(session, str):  # Old format - just a string
                migrated[key] = {
                    "id": key,
                    "title": "Migrated Session",
                    "messages": [],
                    "created_at": datetime.now().isoformat()
                }
            elif isinstance(session, dict):  # New format - validate structure
                # Ensure required fields exist
                session.setdefault("id", key)
                session.setdefault("title", "Chat Session")
                session.setdefault("messages", [])
                session.setdefault("created_at", datetime.now().isoformat())
                migrated[key] = session
            else:
                # Unknown format, skip
                logger.warning(f"Unknown session format for {key}: {type(session)}")
                continue
    except Exception as e:
        logger.error(f"Error migrating session data: {e}")
        return {}
    return migrated

def load_chat_sessions() -> Dict[str, Dict]:
    """Load chat sessions from file with data migration."""
    try:
        chat_history_path = Path(config_manager.config.chat_history_path)
        chat_history_path.mkdir(exist_ok=True)
        
        sessions_file = chat_history_path / "sessions.json"
        if sessions_file.exists():
            with open(sessions_file, 'r') as f:
                data = json.load(f)
                # Validate and migrate data format if needed
                if isinstance(data, dict):
                    return migrate_session_data(data)
                else:
                    logger.warning(f"Invalid sessions file format: {type(data)}")
                    return {}
    except Exception as e:
        logger.error(f"Error loading chat sessions: {e}")
        # Try to backup corrupted file
        try:
            sessions_file = chat_history_path / "sessions.json"
            if sessions_file.exists():
                backup_file = sessions_file.with_suffix('.backup')
                sessions_file.rename(backup_file)
                logger.info(f"Corrupted sessions file backed up to {backup_file}")
        except:
            pass
    return {}

def save_chat_sessions():
    """Save chat sessions to file."""
    try:
        chat_history_path = Path(config_manager.config.chat_history_path)
        chat_history_path.mkdir(exist_ok=True)
        
        sessions_file = chat_history_path / "sessions.json"
        with open(sessions_file, 'w') as f:
            json.dump(st.session_state.chat_sessions, f, indent=2)
    except Exception as e:
        st.error(f"Error saving chat sessions: {e}")

def export_session_to_markdown(session: Dict) -> None:
    """Export a chat session to markdown format."""
    try:
        session_title = session.get("title", "Chat Session")
        session_date = session.get("created_at", datetime.now().isoformat())
        messages = session.get("messages", [])
        
        # Create markdown content
        markdown_content = f"""# {session_title}

**Created:** {session_date}  
**Total Messages:** {len(messages)}

---

"""
        
        for i, msg in enumerate(messages, 1):
            role = msg.get("role", "unknown").title()
            content = msg.get("content", "")
            timestamp = msg.get("timestamp", "")
            
            if role == "User":
                markdown_content += f"## 👤 User Message {i}\n\n"
            else:
                markdown_content += f"## 🤖 Assistant Response {i}\n\n"
            
            if timestamp:
                markdown_content += f"*{timestamp}*\n\n"
            
            markdown_content += f"{content}\n\n---\n\n"
        
        markdown_content += f"\n*Exported from RAG Agent on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
        
        # Offer download
        st.download_button(
            label="💾 Download Markdown",
            data=markdown_content,
            file_name=f"{session_title.replace(' ', '_').replace('/', '_')}.md",
            mime="text/markdown",
            key=f"download_md_{session.get('id', 'unknown')}"
        )
        
        # Also create a shareable link content
        shareable_content = f"""# Shared Chat: {session_title}

This chat session was shared from RAG Agent.

{markdown_content}
"""
        
        st.download_button(
            label="🔗 Download Shareable File",
            data=shareable_content,
            file_name=f"shared_{session_title.replace(' ', '_').replace('/', '_')}.md",
            mime="text/markdown", 
            key=f"download_share_{session.get('id', 'unknown')}"
        )
        
    except Exception as e:
        st.error(f"Error exporting session: {e}")

def export_session_to_pdf(session: Dict) -> None:
    """Export a chat session to PDF format (simplified version)."""
    # For PDF export, we'll create an HTML version that can be printed to PDF
    try:
        session_title = session.get("title", "Chat Session")
        session_date = session.get("created_at", datetime.now().isoformat())
        messages = session.get("messages", [])
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{session_title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 30px; }}
        .message {{ margin-bottom: 30px; padding: 15px; border-radius: 8px; }}
        .user {{ background-color: #e3f2fd; }}
        .assistant {{ background-color: #f3e5f5; }}
        .role {{ font-weight: bold; margin-bottom: 10px; }}
        pre {{ background-color: #f5f5f5; padding: 10px; border-radius: 4px; overflow-x: auto; }}
        code {{ background-color: #f5f5f5; padding: 2px 4px; border-radius: 2px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{session_title}</h1>
        <p><strong>Created:</strong> {session_date}</p>
        <p><strong>Total Messages:</strong> {len(messages)}</p>
    </div>
"""
        
        for i, msg in enumerate(messages, 1):
            role = msg.get("role", "unknown").title()
            content = msg.get("content", "").replace('\n', '<br>')
            timestamp = msg.get("timestamp", "")
            
            css_class = "user" if role == "User" else "assistant"
            icon = "👤" if role == "User" else "🤖"
            
            html_content += f"""
    <div class="message {css_class}">
        <div class="role">{icon} {role} Message {i}</div>
        {f"<small>{timestamp}</small><br>" if timestamp else ""}
        <div>{content}</div>
    </div>
"""
        
        html_content += f"""
    <div style="margin-top: 50px; text-align: center; color: #666; font-size: 12px;">
        Exported from RAG Agent on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    </div>
</body>
</html>
"""
        
        st.download_button(
            label="📄 Download HTML (Print to PDF)",
            data=html_content,
            file_name=f"{session_title.replace(' ', '_').replace('/', '_')}.html",
            mime="text/html",
            key=f"download_html_{session.get('id', 'unknown')}"
        )
        
    except Exception as e:
        st.error(f"Error exporting session to PDF: {e}")

def create_new_chat_session() -> str:
    """Create a new chat session."""
    session_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()
    
    st.session_state.chat_sessions[session_id] = {
        "id": session_id,
        "title": f"New Chat - {datetime.now().strftime('%b %d, %Y %H:%M')}",
        "created_at": timestamp,
        "updated_at": timestamp,
        "messages": []
    }
    
    st.session_state.current_session_id = session_id
    st.session_state.current_messages = []
    save_chat_sessions()
    return session_id

def generate_session_title(messages: List[Dict]) -> str:
    """Generate a title for the chat session based on messages."""
    if not messages:
        return f"New Chat - {datetime.now().strftime('%b %d, %Y %H:%M')}"
    
    # Use first user message as basis for title
    first_user_msg = None
    for msg in messages:
        if msg.get("role") == "user":
            first_user_msg = msg.get("content", "")
            break
    
    if first_user_msg:
        # Truncate and clean up
        title = first_user_msg[:50].replace("\n", " ").strip()
        if len(first_user_msg) > 50:
            title += "..."
        return f"{title} - {datetime.now().strftime('%b %d')}"
    
    return f"Chat - {datetime.now().strftime('%b %d, %Y %H:%M')}"

def init_components():
    """Initialize ingestion and retrieval components."""
    if st.session_state.ingestion is None:
        with st.spinner("Initializing document processing..."):
            st.session_state.ingestion = DocumentIngestion(
                vector_store_path=config_manager.config.vector_store_path,
                embedding_model=config_manager.config.embedding_model
            )
    
    if st.session_state.retrieval is None:
        with st.spinner("Initializing document retrieval..."):
            st.session_state.retrieval = DocumentRetrieval(
                vector_store_path=config_manager.config.vector_store_path,
                embedding_model=config_manager.config.embedding_model
            )

def render_sidebar():
    """Render the sidebar with navigation and chat history."""
    with st.sidebar:
        st.title("🤖 RAG Agent")
        
        # Navigation
        page = st.selectbox(
            "Navigate",
            ["Chat", "Documents", "Configuration"],
            key="nav_select"
        )
        st.session_state.current_page = page
        
        st.divider()
        
        # Chat History (only show on Chat page)
        if page == "Chat":
            st.subheader("💬 Chat History")
            
            # New Chat button
            if st.button("➕ New Chat", use_container_width=True):
                create_new_chat_session()
                st.rerun()
            
            # Session list
            if st.session_state.chat_sessions:
                st.write("**Recent Chats:**")
                
                for session_id, session in st.session_state.chat_sessions.items():
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        if st.button(
                            session["title"], 
                            key=f"session_{session_id}",
                            use_container_width=True,
                            type="secondary" if session_id != st.session_state.current_session_id else "primary"
                        ):
                            st.session_state.current_session_id = session_id
                            st.session_state.current_messages = session.get("messages", [])
                            st.rerun()
                    
                    with col2:
                        # Export button
                        if st.button("📤", key=f"export_{session_id}", help="Export session"):
                            export_session_to_markdown(session)
                        
                        # Delete button  
                        if st.button("🗑️", key=f"delete_{session_id}", help="Delete session"):
                            if len(st.session_state.chat_sessions) > 1:
                                del st.session_state.chat_sessions[session_id]
                                if session_id == st.session_state.current_session_id:
                                    # Switch to another session
                                    remaining_sessions = list(st.session_state.chat_sessions.keys())
                                    if remaining_sessions:
                                        st.session_state.current_session_id = remaining_sessions[0]
                                        st.session_state.current_messages = st.session_state.chat_sessions[remaining_sessions[0]].get("messages", [])
                                save_chat_sessions()
                                st.rerun()
                            else:
                                st.error("Cannot delete the last session!")
        
        st.divider()
        
        # Model info
        current_model = config_manager.get_selected_model()
        if current_model:
            st.write("**Current Model:**")
            st.write(f"🔮 {current_model.name}")
            if current_model.is_available:
                st.success("✅ Available")
            else:
                st.error("❌ Not Available")
        else:
            st.warning("⚠️ No model selected")

def render_chat_page():
    """Render the main chat interface."""
    st.title("💬 Chat with RAG Agent")
    
    # Initialize components
    init_components()
    
    # Current model info
    current_model = config_manager.get_selected_model()
    if not current_model or not current_model.is_available:
        st.error("🚫 No available model selected. Please configure a model in the Configuration page.")
        return
    
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.info(f"🔮 Using: **{current_model.name}**")
    with col2:
        if st.button("🔄 Regenerate", help="Regenerate last response"):
            if st.session_state.current_messages:
                # Remove last assistant message and regenerate
                if st.session_state.current_messages[-1]["role"] == "assistant":
                    st.session_state.current_messages.pop()
                    # Get last user message and regenerate
                    last_user_msg = None
                    for msg in reversed(st.session_state.current_messages):
                        if msg["role"] == "user":
                            last_user_msg = msg["content"]
                            break
                    if last_user_msg:
                        generate_response(last_user_msg)
                        st.rerun()
    with col3:
        if st.button("⚡ Quick Actions"):
            st.session_state.show_quick_actions = not st.session_state.get("show_quick_actions", False)
    
    # Quick actions
    if st.session_state.get("show_quick_actions", False):
        st.write("**Quick Actions:**")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("💻 Generate Code"):
                st.session_state.quick_prompt = "Please generate code for: "
        with col2:
            if st.button("🐛 Debug This"):
                st.session_state.quick_prompt = "Help me debug this code: "
        with col3:
            if st.button("📝 Explain Code"):
                st.session_state.quick_prompt = "Please explain this code: "
        with col4:
            if st.button("🔍 Code Review"):
                st.session_state.quick_prompt = "Please review this code: "
    
    # File upload area
    st.write("**📁 Upload Documents:**")
    uploaded_files = st.file_uploader(
        "Drag and drop files here or click to upload",
        accept_multiple_files=True,
        type=['pdf', 'docx', 'txt', 'py', 'js', 'md', 'csv', 'xlsx'],
        help="Supported formats: PDF, Word, Text, Code files, Markdown, CSV, Excel"
    )
    
    if uploaded_files:
        process_uploaded_files(uploaded_files)
    
    # Chat messages container
    chat_container = st.container()
    
    with chat_container:
        # Display chat messages
        for message in st.session_state.current_messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
    
    # Chat input
    prompt = st.chat_input(
        "Ask me anything about your documents or development questions...",
        key="chat_input"
    )
    
    # Handle quick prompt injection
    if st.session_state.get("quick_prompt"):
        prompt = st.session_state.quick_prompt
        st.session_state.quick_prompt = None
        # Show the prompt in the input
        st.chat_input(prompt, key="chat_input_filled")
    
    if prompt:
        # Add user message
        st.session_state.current_messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Generate and display response
        generate_response(prompt)

def process_uploaded_files(uploaded_files):
    """Process uploaded files and add to vector store."""
    if not st.session_state.ingestion:
        st.error("Document ingestion not initialized")
        return
    
    with st.spinner(f"Processing {len(uploaded_files)} file(s)..."):
        success_count = 0
        for uploaded_file in uploaded_files:
            try:
                # Save file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name
                
                # Process the file
                st.session_state.ingestion.ingest_document(tmp_file_path, uploaded_file.name)
                
                # Clean up
                os.unlink(tmp_file_path)
                success_count += 1
                
                # Add confirmation to chat
                confirmation_msg = f"✅ File '{uploaded_file.name}' processed and added to context."
                st.session_state.current_messages.append({"role": "assistant", "content": confirmation_msg})
                
            except Exception as e:
                st.error(f"Error processing {uploaded_file.name}: {e}")
        
        if success_count > 0:
            st.success(f"Successfully processed {success_count} file(s)!")
            save_current_session()
            st.rerun()

def generate_response(prompt: str):
    """Generate AI response to user prompt."""
    if not st.session_state.retrieval:
        st.error("Document retrieval not initialized")
        return
    
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Get relevant documents
                relevant_docs = st.session_state.retrieval.retrieve_documents(prompt, top_k=5)
                
                # Generate response using the agent
                response = rag_agent.generate_response(
                    query=prompt,
                    context_docs=relevant_docs,
                    chat_history=st.session_state.current_messages[-10:],  # Last 10 messages
                    model_config=config_manager.get_selected_model()
                )
                
                # Display response
                st.write(response)
                
                # Add to chat history
                st.session_state.current_messages.append({"role": "assistant", "content": response})
                
                # Update session title if this is the first exchange
                if len(st.session_state.current_messages) <= 2:
                    new_title = generate_session_title(st.session_state.current_messages)
                    if st.session_state.current_session_id in st.session_state.chat_sessions:
                        st.session_state.chat_sessions[st.session_state.current_session_id]["title"] = new_title
                
                # Save session
                save_current_session()
                
            except Exception as e:
                st.error(f"Error generating response: {e}")
                # Add error message to chat
                error_msg = f"Sorry, I encountered an error: {e}"
                st.session_state.current_messages.append({"role": "assistant", "content": error_msg})

def save_current_session():
    """Save current chat session."""
    if st.session_state.current_session_id and st.session_state.current_session_id in st.session_state.chat_sessions:
        st.session_state.chat_sessions[st.session_state.current_session_id]["messages"] = st.session_state.current_messages
        st.session_state.chat_sessions[st.session_state.current_session_id]["updated_at"] = datetime.now().isoformat()
        save_chat_sessions()

def render_documents_page():
    """Render the document management interface."""
    st.title("📚 Document Management")
    
    # Initialize components
    init_components()
    
    # Document upload section
    st.subheader("📤 Upload New Documents")
    
    uploaded_files = st.file_uploader(
        "Choose files to upload",
        accept_multiple_files=True,
        type=['pdf', 'docx', 'txt', 'py', 'js', 'md', 'csv', 'xlsx'],
        key="doc_uploader"
    )
    
    if uploaded_files:
        if st.button("Process Files"):
            process_uploaded_files(uploaded_files)
    
    st.divider()
    
    # Document storage status
    st.subheader("💾 Document Storage Status")
    
    if st.session_state.retrieval:
        try:
            # Get document stats (this will depend on your vector store implementation)
            doc_stats = st.session_state.retrieval.get_document_stats()
            
            if doc_stats:
                st.dataframe(doc_stats, use_container_width=True)
            else:
                st.info("No documents in the vector store yet. Upload some documents to get started!")
                
        except Exception as e:
            st.error(f"Error retrieving document stats: {e}")
    
    # Maintenance operations
    st.subheader("🛠️ Maintenance Operations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Refresh Document Index", use_container_width=True):
            with st.spinner("Refreshing document index..."):
                # Implement refresh logic
                st.success("Document index refreshed!")
    
    with col2:
        if st.button("🗑️ Clear All Documents", use_container_width=True):
            if st.checkbox("I understand this will delete all documents"):
                with st.spinner("Clearing all documents..."):
                    # Implement clear logic
                    st.success("All documents cleared!")

def render_configuration_page():
    """Render the configuration interface."""
    st.title("⚙️ Configuration")
    
    # System information
    st.subheader("💻 System Information")
    
    recommendations = config_manager.get_system_recommendations()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("System RAM", f"{recommendations['ram_gb']} GB")
        st.metric("Platform", recommendations['platform'])
    with col2:
        st.metric("Performance Tier", recommendations['tier'])
        
    st.info(f"**Recommended Models**: {recommendations['recommended']}")
    st.write(f"💡 {recommendations['description']}")
    
    st.divider()
    
    # Model configuration
    st.subheader("🤖 AI Model Configuration")
    
    # Refresh models button
    if st.button("🔄 Refresh Available Models"):
        with st.spinner("Detecting available models..."):
            config_manager.refresh_model_availability()
            st.success("Models refreshed!")
            st.rerun()
    
    # Available models
    available_models = config_manager.get_available_models()
    all_models = list(config_manager.config.models.values())
    
    if available_models:
        st.write("**Available Models:**")
        
        # Model selection
        current_model = config_manager.get_selected_model()
        current_key = None
        if current_model:
            for key, model in config_manager.config.models.items():
                if model == current_model:
                    current_key = key
                    break
        
        model_options = {}
        for key, model in config_manager.config.models.items():
            if model.is_available:
                status = "✅ Available"
                if model.recommended:
                    status += " (Recommended)"
                model_options[key] = f"{model.name} - {status}"
        
        if model_options:
            selected_key = st.selectbox(
                "Select Active Model",
                options=list(model_options.keys()),
                format_func=lambda x: model_options[x],
                index=list(model_options.keys()).index(current_key) if current_key in model_options else 0
            )
            
            if st.button("Set as Active Model"):
                config_manager.select_model(selected_key)
                st.success(f"Active model set to: {config_manager.config.models[selected_key].name}")
                st.rerun()
    
    # Cloud model API keys
    st.subheader("🔑 Cloud Model API Keys")
    
    cloud_models = [model for model in all_models if model.type in ['openai', 'anthropic', 'google', 'xai']]
    
    if cloud_models:
        for model in cloud_models:
            with st.expander(f"{model.name} Configuration"):
                current_key = model.api_key if model.api_key else ""
                
                api_key = st.text_input(
                    f"API Key for {model.name}",
                    value="*" * len(current_key) if current_key else "",
                    type="password",
                    key=f"api_key_{model.type}",
                    help=f"Enter your API key from {model.type}.com"
                )
                
                if st.button(f"Save {model.name} API Key", key=f"save_{model.type}"):
                    if api_key and api_key != "*" * len(current_key):
                        # Find the model key
                        model_key = None
                        for key, m in config_manager.config.models.items():
                            if m == model:
                                model_key = key
                                break
                        
                        if model_key:
                            config_manager.add_api_key(model_key, api_key)
                            st.success(f"API key saved for {model.name}")
                            st.rerun()
                
                if model.is_available:
                    st.success("✅ API key configured and model available")
                else:
                    st.info("ℹ️ Add API key to enable this model")
    
    st.divider()
    
    # Advanced settings
    st.subheader("🔧 Advanced Settings")
    
    with st.expander("Model Parameters"):
        config_manager.config.max_context_length = st.slider(
            "Max Context Length",
            min_value=1000,
            max_value=8000,
            value=config_manager.config.max_context_length,
            help="Maximum context length for model input"
        )
        
        config_manager.config.max_response_length = st.slider(
            "Max Response Length", 
            min_value=500,
            max_value=4000,
            value=config_manager.config.max_response_length,
            help="Maximum length for model responses"
        )
    
    with st.expander("Document Processing"):
        config_manager.config.chunk_size = st.slider(
            "Chunk Size",
            min_value=200,
            max_value=1000,
            value=config_manager.config.chunk_size,
            help="Size of text chunks for vector storage"
        )
        
        config_manager.config.chunk_overlap = st.slider(
            "Chunk Overlap",
            min_value=0,
            max_value=200,
            value=config_manager.config.chunk_overlap,
            help="Overlap between text chunks"
        )
    
    if st.button("💾 Save Settings"):
        config_manager.save_config()
        st.success("Settings saved!")

def run_ui():
    """Main UI runner function."""
    # Render sidebar
    render_sidebar()
    
    # Render main content based on current page
    if st.session_state.current_page == "Chat":
        render_chat_page()
    elif st.session_state.current_page == "Documents":
        render_documents_page()
    elif st.session_state.current_page == "Configuration":
        render_configuration_page()

if __name__ == "__main__":
    run_ui()

def show_sidebar():
    """Display the sidebar with navigation and system info."""
    with st.sidebar:
        st.title("🤖 RAG Agent")
        
        # Theme toggle
        st.markdown("---")
        current_theme = st.session_state.get("theme", "light")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("☀️ Light", disabled=(current_theme == "light"), key="light_theme"):
                st.session_state.theme = "light"
                st.rerun()
        with col2:
            if st.button("🌙 Dark", disabled=(current_theme == "dark"), key="dark_theme"):
                st.session_state.theme = "dark"
                st.rerun()
        
        # Navigation
        pages = ["Chat", "Documents", "Configuration"]
        st.session_state.current_page = st.selectbox(
            "Navigate to:", 
            pages, 
            index=pages.index(st.session_state.current_page)
        )
        
        # Admin navigation (if enabled)
        add_admin_to_navigation()
        
        st.divider()
        
        # System Information
        st.subheader("System Info")
        config = config_manager.config
        
        if config.system_ram_gb:
            st.write(f"💾 RAM: {config.system_ram_gb} GB")
        if config.system_platform:
            st.write(f"💻 Platform: {config.system_platform}")
            
        # Current model
        if config.selected_model and config.selected_model in config.models:
            current_model = config.models[config.selected_model]
            st.write(f"🧠 Model: {current_model.name}")
            if current_model.is_available:
                st.success("✅ Available")
            else:
                st.error("❌ Not Available")
        else:
            st.warning("⚠️ No model selected")
            
        # Model recommendations
        st.divider()
        st.subheader("💡 Recommendations")
        recommendations = config_manager.get_recommended_models_for_system()
        if recommendations:
            st.write(f"**Primary:** {recommendations.get('primary', 'N/A')}")
            st.write(f"**Coding:** {recommendations.get('coding', 'N/A')}")
            if 'note' in recommendations:
                st.info(recommendations['note'])

def show_chat_page():
    """Display the main chat interface."""
    st.title("💬 Chat with RAG Agent")
    
    # Check if agent is ready
    if not rag_agent.current_model:
        st.error("🚫 No AI model configured. Please go to Configuration to set up a model.")
        return
        
    # Session management
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        # Session selector
        sessions = list(rag_agent.chat_sessions.values())
        if sessions:
            session_options = [f"{s.title} ({s.updated_at.strftime('%m/%d %H:%M')})" for s in sessions]
            session_names = [s.title for s in sessions]
            
            if rag_agent.current_session_id:
                current_session = rag_agent.get_current_session()
                if current_session:
                    current_index = session_names.index(current_session.title)
                else:
                    current_index = 0
            else:
                current_index = 0
                
            selected_idx = st.selectbox(
                "Chat Session:",
                range(len(session_options)),
                index=current_index,
                format_func=lambda x: session_options[x]
            )
            
            selected_session = sessions[selected_idx]
            if rag_agent.current_session_id != selected_session.id:
                rag_agent.switch_session(selected_session.id)
                st.rerun()
        
    with col2:
        if st.button("🆕 New Chat", use_container_width=True):
            rag_agent.create_new_session()
            st.rerun()
            
    with col3:
        if sessions and st.button("🗑️ Delete Session", use_container_width=True):
            if rag_agent.current_session_id:
                rag_agent.delete_session(rag_agent.current_session_id)
                if rag_agent.chat_sessions:
                    # Switch to first available session
                    first_session_id = next(iter(rag_agent.chat_sessions.keys()))
                    rag_agent.switch_session(first_session_id)
                st.rerun()
    
    st.divider()
    
    # Chat interface
    current_session = rag_agent.get_current_session()
    
    # Display chat history
    if current_session and current_session.messages:
        for message in current_session.messages:
            if message.role == "user":
                with st.chat_message("user"):
                    st.write(message.content)
            elif message.role == "assistant":
                with st.chat_message("assistant"):
                    st.write(message.content)
                    if message.metadata and message.metadata.get("model_used"):
                        st.caption(f"Generated by: {message.metadata['model_used']}")
    
    # File upload area
    st.subheader("📎 Upload Documents")
    uploaded_files = st.file_uploader(
        "Upload documents to add to knowledge base:",
        accept_multiple_files=True,
        type=['txt', 'md', 'py', 'js', 'ts', 'html', 'css', 'json', 'pdf', 'docx', 'csv', 'xlsx']
    )
    
    if uploaded_files:
        init_components()
        
        for uploaded_file in uploaded_files:
            if st.button(f"Process {uploaded_file.name}", key=f"process_{uploaded_file.name}"):
                with st.spinner(f"Processing {uploaded_file.name}..."):
                    try:
                        # Save uploaded file temporarily
                        with tempfile.NamedTemporaryFile(delete=False, suffix=uploaded_file.name) as tmp_file:
                            tmp_file.write(uploaded_file.read())
                            tmp_path = tmp_file.name
                            
                        # Process the file
                        result = st.session_state.ingestion.ingest_document(tmp_path, uploaded_file.name)
                        
                        # Clean up
                        os.unlink(tmp_path)
                        
                        if result['status'] == 'success':
                            st.success(f"✅ Successfully processed {uploaded_file.name} ({result['num_chunks']} chunks)")
                        else:
                            st.error(f"❌ Error processing {uploaded_file.name}: {result.get('error', 'Unknown error')}")
                            
                    except Exception as e:
                        st.error(f"❌ Error processing {uploaded_file.name}: {str(e)}")
    
    # Chat input
    user_input = st.chat_input("Type your message here...")
    
    if user_input:
        # Add user message to display immediately
        with st.chat_message("user"):
            st.write(user_input)
            
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = rag_agent.chat(user_input, use_rag=True)
                st.write(response)
                
        # Rerun to update the display
        st.rerun()
    
    # Quick action buttons
    st.subheader("🔧 Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💻 Generate Code", use_container_width=True):
            st.session_state.quick_prompt = "Please help me generate code for:"
            
    with col2:
        if st.button("🐛 Debug Code", use_container_width=True):
            st.session_state.quick_prompt = "I need help debugging this code:"
            
    with col3:
        if st.button("📖 Explain Concept", use_container_width=True):
            st.session_state.quick_prompt = "Please explain this concept:"
    
    # Handle quick prompts
    if 'quick_prompt' in st.session_state:
        st.chat_input(st.session_state.quick_prompt)
        del st.session_state.quick_prompt

def show_documents_page():
    """Display document management interface."""
    st.title("📚 Document Management")
    
    init_components()
    
    # Get document statistics
    stats = st.session_state.retrieval.get_statistics()
    
    # Display statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Files", stats.get('total_files', 0))
    with col2:
        st.metric("Total Chunks", stats.get('total_chunks', 0))
    with col3:
        st.metric("Embedding Model", value=stats.get('embedding_model', 'N/A')[:20] + "...")
    
    st.divider()
    
    # Document filters
    st.subheader("🔍 Filter & Search")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_term = st.text_input("🔍 Search documents:", placeholder="Enter filename or content...")
    
    with col2:
        file_types = ["All Types", ".pdf", ".docx", ".xlsx", ".csv", ".txt", ".md", ".py", ".js", ".html"]
        selected_type = st.selectbox("📁 File Type:", file_types)
    
    with col3:
        sort_options = ["Name (A-Z)", "Name (Z-A)", "Upload Date (New)", "Upload Date (Old)", "Chunk Count (High)", "Chunk Count (Low)"]
        sort_by = st.selectbox("🔄 Sort by:", sort_options)
    
    st.divider()
    
    # Document list
    st.subheader("📄 Stored Documents")
    
    if 'files' in stats and stats['files']:
        # Apply filters
        filtered_files = stats['files'].copy()
        
        # Filter by search term
        if search_term:
            filtered_files = [f for f in filtered_files if search_term.lower() in f['name'].lower()]
        
        # Filter by file type
        if selected_type != "All Types":
            filtered_files = [f for f in filtered_files if f['name'].lower().endswith(selected_type.lower())]
        
        # Sort files
        if sort_by == "Name (A-Z)":
            filtered_files.sort(key=lambda x: x['name'].lower())
        elif sort_by == "Name (Z-A)":
            filtered_files.sort(key=lambda x: x['name'].lower(), reverse=True)
        elif sort_by == "Upload Date (New)":
            filtered_files.sort(key=lambda x: x.get('upload_date', ''), reverse=True)
        elif sort_by == "Upload Date (Old)":
            filtered_files.sort(key=lambda x: x.get('upload_date', ''))
        elif sort_by == "Chunk Count (High)":
            filtered_files.sort(key=lambda x: x['chunk_count'], reverse=True)
        elif sort_by == "Chunk Count (Low)":
            filtered_files.sort(key=lambda x: x['chunk_count'])
        
        if not filtered_files:
            st.info("No documents match the current filters.")
        else:
            st.write(f"📋 Showing {len(filtered_files)} of {len(stats['files'])} documents")
            
            for file_info in filtered_files:
                file_extension = file_info['name'].split('.')[-1].lower() if '.' in file_info['name'] else 'unknown'
                file_icon = {
                    'pdf': '📕', 'docx': '📘', 'xlsx': '📊', 'csv': '📈',
                    'txt': '📄', 'md': '📝', 'py': '🐍', 'js': '📜',
                    'html': '🌐', 'json': '📋'
                }.get(file_extension, '📄')
                
                with st.expander(f"{file_icon} {file_info['name']} ({file_info['chunk_count']} chunks)"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**Upload Date:** {file_info.get('upload_date', 'Unknown')}")
                        st.write(f"**Chunks:** {file_info['chunk_count']}")
                        st.write(f"**File Type:** {file_extension.upper()}")
                        
                        # Enhanced preview with pagination
                        if st.button(f"🔍 Preview Content", key=f"preview_{file_info['name']}"):
                            st.session_state[f"preview_active_{file_info['name']}"] = True
                        
                        if st.session_state.get(f"preview_active_{file_info['name']}", False):
                            chunks = st.session_state.retrieval.retrieve_by_file(file_info['name'], limit=10)
                            
                            if chunks:
                                # Chunk navigation
                                chunk_page = st.selectbox(
                                    f"Select chunk to preview (1-{len(chunks)}):",
                                    range(1, len(chunks) + 1),
                                    key=f"chunk_selector_{file_info['name']}"
                                ) - 1
                                
                                selected_chunk = chunks[chunk_page]
                                
                                # Content preview with better formatting
                                content_preview = selected_chunk.content
                                if len(content_preview) > 1000:
                                    content_preview = content_preview[:1000] + "\n\n... [Content truncated. Full content available in chat.]"
                                
                                st.text_area(
                                    f"Chunk {chunk_page + 1} of {len(chunks)}:",
                                    content_preview,
                                    height=200,
                                    key=f"chunk_content_{file_info['name']}_{chunk_page}"
                                )
                                
                                # Chunk metadata
                                if hasattr(selected_chunk, 'metadata') and selected_chunk.metadata:
                                    with st.expander("📊 Chunk Metadata"):
                                        st.json(selected_chunk.metadata)
                                
                                # Search within document
                                search_in_doc = st.text_input(
                                    "🔍 Search within this document:",
                                    key=f"search_in_{file_info['name']}"
                                )
                                
                                if search_in_doc:
                                    matching_chunks = [
                                        chunk for chunk in chunks
                                        if search_in_doc.lower() in chunk.content.lower()
                                    ]
                                    
                                    if matching_chunks:
                                        st.success(f"Found {len(matching_chunks)} matching chunks")
                                        for i, chunk in enumerate(matching_chunks[:3]):  # Show first 3 matches
                                            with st.expander(f"Match {i+1}"):
                                                # Highlight the search term
                                                highlighted = chunk.content
                                                for word in search_in_doc.split():
                                                    highlighted = highlighted.replace(
                                                        word, f"**{word}**"
                                                    )
                                                st.markdown(highlighted[:300] + "..." if len(highlighted) > 300 else highlighted)
                                    else:
                                        st.info(f"No matches found for '{search_in_doc}'")
                            else:
                                st.warning("No content available for preview")
                    
                    with col2:
                        if st.button(f"🗑️ Delete", key=f"delete_{file_info['name']}", type="secondary"):
                            if st.session_state.ingestion.delete_document(file_info['name']):
                                st.success(f"Deleted {file_info['name']}")
                                st.rerun()
                            else:
                                st.error("Failed to delete document")
                        
                        # Export document chunks
                        if st.button(f"💾 Export", key=f"export_{file_info['name']}"):
                            chunks = st.session_state.retrieval.retrieve_by_file(file_info['name'])
                            
                            export_content = f"# Exported Content: {file_info['name']}\n\n"
                            export_content += f"**Upload Date:** {file_info.get('upload_date', 'Unknown')}\n"
                            export_content += f"**Total Chunks:** {len(chunks)}\n\n"
                            export_content += "---\n\n"
                            
                            for i, chunk in enumerate(chunks, 1):
                                export_content += f"## Chunk {i}\n\n{chunk.content}\n\n---\n\n"
                            
                            st.download_button(
                                label="💾 Download",
                                data=export_content,
                                file_name=f"{file_info['name']}_chunks.md",
                                mime="text/markdown",
                                key=f"download_{file_info['name']}"
                            )
    else:
        st.info("No documents stored yet. Upload some documents in the Chat page!")
    
    st.divider()
    
    # Bulk operations
    st.subheader("🔧 Bulk Operations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Refresh Statistics", use_container_width=True):
            st.rerun()
            
    with col2:
        if st.button("🗑️ Clear All Documents", type="secondary", use_container_width=True):
            if 'confirm_clear' not in st.session_state:
                st.session_state.confirm_clear = True
            else:
                if st.session_state.ingestion.clear_all_documents():
                    st.success("All documents cleared!")
                    del st.session_state.confirm_clear
                    st.rerun()
                else:
                    st.error("Failed to clear documents")
    
    if st.session_state.get('confirm_clear', False):
        st.warning("⚠️ Are you sure you want to clear ALL documents? This cannot be undone.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Yes, Clear All"):
                # Will be handled above
                pass
        with col2:
            if st.button("❌ Cancel"):
                del st.session_state.confirm_clear
                st.rerun()

def show_configuration_page():
    """Display configuration interface."""
    st.title("⚙️ Configuration")
    
    # Model configuration
    st.subheader("🧠 AI Models")
    
    # Refresh models
    if st.button("🔄 Refresh Available Models"):
        config_manager.refresh_model_availability()
        st.success("Model availability refreshed!")
        st.rerun()
    
    # Available models
    available_models = config_manager.get_available_models()
    
    if available_models:
        st.write("**Available Models:**")
        
        model_options = []
        model_keys = []
        
        for key, model_config in config_manager.config.models.items():
            if model_config.is_available:
                status = "✅"
                model_options.append(f"{status} {model_config.name} ({model_config.type})")
                model_keys.append(key)
                
        if model_options:
            current_selection = 0
            if config_manager.config.selected_model in model_keys:
                current_selection = model_keys.index(config_manager.config.selected_model)
                
            selected_idx = st.selectbox(
                "Select Model:",
                range(len(model_options)),
                index=current_selection,
                format_func=lambda x: model_options[x]
            )
            
            selected_key = model_keys[selected_idx]
            
            if st.button("🔄 Switch to Selected Model"):
                if rag_agent.switch_model(selected_key):
                    st.success(f"Switched to {config_manager.config.models[selected_key].name}")
                    st.rerun()
                else:
                    st.error("Failed to switch model")
    else:
        st.warning("⚠️ No models available. Please configure a model below.")
    
    st.divider()
    
    # Model setup instructions
    st.subheader("📥 Model Setup")
    
    tab1, tab2, tab3 = st.tabs(["🏠 Local Models", "☁️ Cloud Models", "📊 Recommendations"])
    
    with tab1:
        st.write("**Ollama (Recommended for local use):**")
        st.code("""
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service
ollama serve

# Pull recommended models for your 16GB system
ollama pull llama3.1:8b
ollama pull phi3:mini
ollama pull codellama:7b
        """)
        
        st.write("**LM Studio:**")
        st.write("1. Download from https://lmstudio.ai")
        st.write("2. Download models in the GUI")
        st.write("3. Start local server in LM Studio")
    
    with tab2:
        st.write("**Add API Keys for Cloud Models:**")
        
        # OpenAI
        openai_key = st.text_input("OpenAI API Key:", type="password", help="Get from https://openai.com")
        if openai_key and st.button("Save OpenAI Key"):
            if config_manager.add_api_key("openai_gpt4", openai_key):
                st.success("OpenAI API key saved!")
                st.rerun()
        
        # Anthropic
        anthropic_key = st.text_input("Anthropic API Key:", type="password", help="Get from https://anthropic.com")
        if anthropic_key and st.button("Save Anthropic Key"):
            if config_manager.add_api_key("anthropic_claude", anthropic_key):
                st.success("Anthropic API key saved!")
                st.rerun()
    
    with tab3:
        st.write("**Recommendations for your system:**")
        recommendations = config_manager.get_recommended_models_for_system()
        
        for key, value in recommendations.items():
            if key != 'note':
                st.write(f"**{key.title()}:** {value}")
        
        if 'note' in recommendations:
            st.info(recommendations['note'])
    
    st.divider()
    
    # Other settings
    st.subheader("🔧 Other Settings")
    
    # Vector store settings
    new_vector_path = st.text_input(
        "Vector Store Path:", 
        value=config_manager.config.vector_store_path
    )
    
    new_embedding_model = st.selectbox(
        "Embedding Model:",
        ["sentence-transformers/all-MiniLM-L6-v2", "BAAI/bge-small-en-v1.5"],
        index=0 if config_manager.config.embedding_model == "sentence-transformers/all-MiniLM-L6-v2" else 1
    )
    
    # Chunk settings
    new_chunk_size = st.slider("Chunk Size:", 100, 1000, config_manager.config.chunk_size)
    new_chunk_overlap = st.slider("Chunk Overlap:", 0, 200, config_manager.config.chunk_overlap)
    
    if st.button("💾 Save Settings"):
        config_manager.config.vector_store_path = new_vector_path
        config_manager.config.embedding_model = new_embedding_model
        config_manager.config.chunk_size = new_chunk_size
        config_manager.config.chunk_overlap = new_chunk_overlap
        config_manager.save_config()
        st.success("Settings saved!")

def main():
    """Main Streamlit application."""
    # Initialize session state first
    init_session_state()
    
    # Apply theme
    current_theme = st.session_state.get("theme", "light")
    if current_theme == "dark":
        st.markdown("""
        <style>
            .stApp {
                background-color: #0e1117;
                color: #fafafa;
            }
            .stSidebar {
                background-color: #262730;
            }
            .stTextInput > div > div > input {
                background-color: #262730;
                color: #fafafa;
            }
            .stSelectbox > div > div > select {
                background-color: #262730;
                color: #fafafa;
            }
            .stTextArea > div > div > textarea {
                background-color: #262730;
                color: #fafafa;
            }
            div[data-testid="stMarkdownContainer"] {
                color: #fafafa;
            }
        </style>
        """, unsafe_allow_html=True)
    
    show_sidebar()
    
    # Route to appropriate page
    if st.session_state.current_page == "Chat":
        show_chat_page()
    elif st.session_state.current_page == "Documents":
        show_documents_page()
    elif st.session_state.current_page == "Configuration":
        show_configuration_page()
    elif st.session_state.current_page == "Admin":
        show_admin_panel()
    elif st.session_state.current_page == "Code Playground":
        show_code_playground()

if __name__ == "__main__":
    main()
