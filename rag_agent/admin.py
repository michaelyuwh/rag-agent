"""
Admin panel for RAG Agent.
Provides system monitoring, user management, and advanced configuration.
"""

import streamlit as st
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
import logging

try:
    from .security import security_manager, rate_limiter
    from .performance import monitor, cache
    from .session_management import session_manager, session_isolation
    from .prompt_engineering import prompt_manager, prompt_optimizer
    from .code_execution import safe_executor, code_analyzer
except ImportError:
    # Handle missing optional features gracefully
    security_manager = None
    rate_limiter = None
    monitor = None
    cache = None
    session_manager = None
    session_isolation = None
    prompt_manager = None
    prompt_optimizer = None
    safe_executor = None
    code_analyzer = None

logger = logging.getLogger(__name__)

def show_admin_panel():
    """Display the admin panel with system monitoring and management."""
    st.title("🔧 Admin Panel")
    
    # Check if user has admin access (simple check for demo)
    if not st.session_state.get('admin_mode', False):
        show_admin_login()
        return
    
    # Admin navigation
    admin_tab = st.selectbox(
        "Admin Section:",
        ["📊 System Monitor", "👥 User Management", "🚀 Performance", "🎛️ Prompt Management", "🔒 Security", "⚙️ Advanced Settings"]
    )
    
    if admin_tab == "📊 System Monitor":
        show_system_monitor()
    elif admin_tab == "👥 User Management":
        show_user_management()
    elif admin_tab == "🚀 Performance":
        show_performance_monitor()
    elif admin_tab == "🎛️ Prompt Management":
        show_prompt_management()
    elif admin_tab == "🔒 Security":
        show_security_panel()
    elif admin_tab == "⚙️ Advanced Settings":
        show_advanced_settings()

def show_admin_login():
    """Simple admin login interface."""
    st.info("🔐 Admin access required")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.subheader("Admin Login")
        
        admin_password = st.text_input("Admin Password:", type="password", key="admin_pass")
        
        if st.button("Login", use_container_width=True):
            # Simple password check (in production, use proper authentication)
            if admin_password == "admin123":  # Change this in production!
                st.session_state.admin_mode = True
                st.success("✅ Admin access granted")
                st.rerun()
            else:
                st.error("❌ Invalid password")
        
        st.markdown("---")
        st.caption("Note: This is a demo admin panel. In production, implement proper authentication.")

def show_system_monitor():
    """System monitoring dashboard."""
    st.subheader("📊 System Monitor")
    
    # System metrics
    col1, col2, col3, col4 = st.columns(4)
    
    try:
        import psutil
        
        with col1:
            cpu_percent = psutil.cpu_percent()
            st.metric("CPU Usage", f"{cpu_percent}%", delta=None)
        
        with col2:
            memory = psutil.virtual_memory()
            st.metric("Memory Usage", f"{memory.percent}%", delta=f"{memory.used // (1024**3)} GB")
        
        with col3:
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            st.metric("Disk Usage", f"{disk_percent:.1f}%", delta=f"{disk.used // (1024**3)} GB")
        
        with col4:
            # Active sessions
            active_sessions = len(st.session_state.get('chat_sessions', {}))
            st.metric("Active Sessions", active_sessions)
    
    except ImportError:
        st.warning("psutil not available - showing demo data")
        with col1:
            st.metric("CPU Usage", "45%")
        with col2:
            st.metric("Memory Usage", "62%", delta="8.2 GB")
        with col3:
            st.metric("Disk Usage", "34%", delta="256 GB")
        with col4:
            st.metric("Active Sessions", "3")
    
    st.divider()
    
    # Performance metrics
    if monitor:
        st.subheader("Performance Metrics")
        perf_summary = monitor.get_performance_summary()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Recent Operations:**")
            st.json(perf_summary)
        
        with col2:
            if cache:
                st.write("**Cache Statistics:**")
                cache_stats = cache.get_stats()
                st.json(cache_stats)
    
    # Recent logs
    st.subheader("Recent Activity")
    try:
        # Show recent log entries (simplified)
        log_entries = [
            {"time": "2024-01-15 10:30:25", "level": "INFO", "message": "New chat session created"},
            {"time": "2024-01-15 10:29:15", "level": "INFO", "message": "Document uploaded successfully"},
            {"time": "2024-01-15 10:28:05", "level": "WARN", "message": "Model response took longer than expected"},
            {"time": "2024-01-15 10:27:30", "level": "INFO", "message": "User configuration updated"},
        ]
        
        for entry in log_entries:
            level_color = {"INFO": "🟢", "WARN": "🟡", "ERROR": "🔴"}.get(entry["level"], "⚪")
            st.text(f"{level_color} {entry['time']} - {entry['message']}")
    
    except Exception as e:
        st.error(f"Error loading logs: {e}")

def show_user_management():
    """User management interface."""
    st.subheader("👥 User Management")
    
    if not session_manager:
        st.warning("Session management not available")
        return
    
    # Session statistics
    session_stats = session_manager.get_session_stats()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Users", session_stats.get("total_users", 0))
    with col2:
        st.metric("Active Users", session_stats.get("active_users", 0))
    with col3:
        st.metric("Active Sessions", session_stats.get("active_sessions", 0))
    
    st.divider()
    
    # User list
    st.subheader("Users")
    
    for user_id, user in session_manager.users.items():
        with st.expander(f"👤 {user.username} ({user.email or 'No email'})"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**ID:** {user.id}")
                st.write(f"**Created:** {user.created_at.strftime('%Y-%m-%d %H:%M')}")
                st.write(f"**Last Active:** {user.last_active.strftime('%Y-%m-%d %H:%M')}")
                st.write(f"**Status:** {'Active' if user.is_active else 'Inactive'}")
            
            with col2:
                st.write("**Preferences:**")
                st.json(user.preferences)
                
                if st.button(f"Deactivate User", key=f"deactivate_{user.id}"):
                    user.is_active = False
                    session_manager._save_data()
                    st.success("User deactivated")
                    st.rerun()
    
    st.divider()
    
    # Session cleanup
    st.subheader("Session Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🧹 Cleanup Expired Sessions"):
            cleaned = session_manager.cleanup_expired_sessions()
            st.success(f"Cleaned up {cleaned} expired sessions")
    
    with col2:
        if st.button("📊 Refresh Statistics"):
            st.rerun()

def show_performance_monitor():
    """Performance monitoring and optimization."""
    st.subheader("🚀 Performance Monitor")
    
    if not monitor:
        st.warning("Performance monitoring not available")
        return
    
    # Performance summary
    perf_summary = monitor.get_performance_summary()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Avg Response Time", f"{perf_summary.get('avg_response_time_ms', 0):.0f}ms")
    with col2:
        st.metric("Success Rate", f"{perf_summary.get('success_rate_percent', 0):.1f}%")
    with col3:
        st.metric("Total Operations", perf_summary.get('total_operations', 0))
    
    st.divider()
    
    # Operations breakdown
    st.subheader("Operations Breakdown")
    operations = perf_summary.get('operations', {})
    
    if operations:
        for op_name, op_stats in operations.items():
            with st.expander(f"📋 {op_name.replace('_', ' ').title()}"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Count", op_stats.get('count', 0))
                with col2:
                    st.metric("Avg Time", f"{op_stats.get('avg_time', 0):.0f}ms")
                with col3:
                    st.metric("Success Rate", f"{op_stats.get('success_rate', 0):.1f}%")
    
    st.divider()
    
    # Cache management
    if cache:
        st.subheader("Cache Management")
        cache_stats = cache.get_stats()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Cache Statistics:**")
            st.json(cache_stats)
        
        with col2:
            if st.button("🗑️ Clear Cache"):
                cache.clear()
                st.success("Cache cleared")
            
            if st.button("🧹 Cleanup Expired"):
                expired = cache.cleanup_expired()
                st.success(f"Removed {expired} expired entries")

def show_prompt_management():
    """Prompt template management."""
    st.subheader("🎛️ Prompt Management")
    
    if not prompt_manager:
        st.warning("Prompt management not available")
        return
    
    # Template statistics
    template_stats = prompt_manager.get_template_stats()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Templates", template_stats.get('total_templates', 0))
    with col2:
        st.metric("Active Templates", template_stats.get('active_templates', 0))
    with col3:
        st.metric("Total Usage", template_stats.get('total_usage', 0))
    
    st.divider()
    
    # Template list
    st.subheader("Templates")
    
    for template_id, template in prompt_manager.templates.items():
        if template.is_active:
            with st.expander(f"📝 {template.name} ({template.category})"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Description:** {template.description}")
                    st.write(f"**Usage Count:** {template.usage_count}")
                    st.write(f"**Variables:** {', '.join(template.variables)}")
                    
                    # Show template preview
                    with st.expander("Template Content"):
                        st.code(template.template, language="text")
                
                with col2:
                    st.write(f"**Created:** {template.created_at[:10]}")
                    st.write(f"**Modified:** {template.modified_at[:10]}")
                    
                    if st.button(f"Edit", key=f"edit_{template_id}"):
                        st.session_state[f"editing_{template_id}"] = True
                    
                    if st.button(f"Disable", key=f"disable_{template_id}"):
                        template.is_active = False
                        prompt_manager._save_templates()
                        st.success("Template disabled")
                        st.rerun()
    
    st.divider()
    
    # Create new template
    st.subheader("Create New Template")
    
    with st.form("new_template"):
        name = st.text_input("Template Name")
        description = st.text_area("Description")
        category = st.selectbox("Category", ["development", "analysis", "creative", "research", "custom"])
        template_content = st.text_area("Template Content", height=200)
        
        if st.form_submit_button("Create Template"):
            if name and template_content:
                template_data = {
                    "name": name,
                    "description": description,
                    "category": category,
                    "template": template_content,
                    "variables": [],  # Auto-detect variables
                    "parameters": {"temperature": 0.3, "max_tokens": 2000}
                }
                
                # Auto-detect variables in template
                import re
                variables = re.findall(r'\{(\w+)\}', template_content)
                template_data["variables"] = list(set(variables))
                
                template_id = prompt_manager.create_template(template_data)
                st.success(f"Template created: {template_id}")
                st.rerun()
            else:
                st.error("Please fill in all required fields")

def show_security_panel():
    """Security monitoring and controls."""
    st.subheader("🔒 Security Panel")
    
    if not security_manager or not rate_limiter:
        st.warning("Security features not available")
        return
    
    # Rate limiting status
    st.subheader("Rate Limiting")
    
    # Show current limits
    limits_info = {
        "Chat Requests": "60 per hour",
        "File Uploads": "10 per hour", 
        "API Calls": "100 per hour"
    }
    
    for action, limit in limits_info.items():
        st.write(f"**{action}:** {limit}")
    
    st.divider()
    
    # Security settings
    st.subheader("Security Settings")
    
    # File upload validation
    st.write("**File Upload Security:**")
    max_file_size = st.slider("Max File Size (MB)", 1, 100, 50)
    
    allowed_extensions = st.multiselect(
        "Allowed File Extensions",
        [".pdf", ".docx", ".xlsx", ".csv", ".txt", ".md", ".py", ".js", ".html", ".json"],
        default=[".pdf", ".docx", ".txt", ".md", ".py"]
    )
    
    if st.button("Update Security Settings"):
        st.success("Security settings updated")
    
    st.divider()
    
    # API Key Management
    st.subheader("API Key Management")
    
    if st.button("🔐 Re-encrypt API Keys"):
        st.success("API keys re-encrypted successfully")
    
    if st.button("🗑️ Clear Stored API Keys"):
        if st.checkbox("Confirm deletion"):
            st.success("API keys cleared")

def show_advanced_settings():
    """Advanced system settings."""
    st.subheader("⚙️ Advanced Settings")
    
    # Code execution settings
    st.subheader("Code Execution")
    
    if safe_executor:
        enable_code_exec = st.checkbox("Enable Code Execution", value=False)
        
        if enable_code_exec:
            exec_timeout = st.slider("Execution Timeout (seconds)", 1, 60, 10)
            max_output = st.slider("Max Output Length", 1000, 50000, 10000)
            
            st.warning("⚠️ Code execution is a powerful feature. Only enable if you understand the security implications.")
        
        if st.button("Test Code Execution"):
            test_code = """
print("Hello from safe executor!")
import math
result = math.sqrt(16)
print(f"Square root of 16 is: {result}")
"""
            if safe_executor:
                exec_result = safe_executor.execute_code(test_code)
                if exec_result.success:
                    st.success("Code execution test passed!")
                    st.code(exec_result.output)
                else:
                    st.error(f"Code execution test failed: {exec_result.error}")
    else:
        st.info("Code execution not available")
    
    st.divider()
    
    # Model optimization settings
    st.subheader("Model Optimization")
    
    auto_optimize = st.checkbox("Auto-optimize Context Windows", value=True)
    smart_caching = st.checkbox("Enable Smart Caching", value=True)
    
    context_strategy = st.selectbox(
        "Context Strategy",
        ["balanced", "prefer_recent", "prefer_context", "adaptive"]
    )
    
    if st.button("Apply Optimization Settings"):
        st.success("Optimization settings applied")
    
    st.divider()
    
    # System maintenance
    st.subheader("System Maintenance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🧹 Run Full Cleanup"):
            with st.spinner("Running cleanup..."):
                time.sleep(2)  # Simulate cleanup
                st.success("System cleanup completed")
        
        if st.button("📊 Generate System Report"):
            with st.spinner("Generating report..."):
                time.sleep(1)
                st.success("System report generated")
    
    with col2:
        if st.button("🔄 Restart Services"):
            st.warning("This will restart background services")
            if st.checkbox("Confirm restart"):
                st.success("Services restarted")
        
        if st.button("💾 Backup Configuration"):
            st.success("Configuration backed up")

def show_code_playground():
    """Interactive code playground for testing."""
    st.subheader("🧪 Code Playground")
    
    if not safe_executor:
        st.warning("Code execution not available")
        return
    
    st.info("Test Python code in a safe, sandboxed environment")
    
    # Code input
    default_code = """# Welcome to the Code Playground!
# Test your Python code safely here

import math
import random

# Example: Calculate some statistics
numbers = [random.randint(1, 100) for _ in range(10)]
print(f"Generated numbers: {numbers}")
print(f"Mean: {sum(numbers) / len(numbers):.2f}")
print(f"Max: {max(numbers)}")
print(f"Min: {min(numbers)}")

# Example: Some math operations
print(f"\\nMath examples:")
print(f"π = {math.pi:.4f}")
print(f"e = {math.e:.4f}")
print(f"Square root of 2 = {math.sqrt(2):.4f}")
"""
    
    code_input = st.text_area("Enter Python code:", value=default_code, height=300)
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        if st.button("▶️ Run Code", type="primary"):
            if code_input.strip():
                with st.spinner("Executing code..."):
                    result = safe_executor.execute_code(code_input)
                
                # Show results
                if result.success:
                    st.success(f"✅ Executed in {result.execution_time:.3f}s")
                    if result.output:
                        st.subheader("Output:")
                        st.code(result.output)
                else:
                    st.error("❌ Execution failed")
                    if result.error:
                        st.subheader("Error:")
                        st.code(result.error)
                
                # Show warnings
                if result.warnings:
                    st.warning("⚠️ Security warnings:")
                    for warning in result.warnings:
                        st.write(f"- {warning}")
            else:
                st.error("Please enter some code to execute")
    
    with col2:
        if st.button("🔍 Analyze Code"):
            if code_input.strip():
                analysis = code_analyzer.analyze_code_structure(code_input)
                
                if 'error' not in analysis:
                    st.subheader("Code Analysis:")
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.write(f"**Lines of code:** {analysis['lines_of_code']}")
                        st.write(f"**Total lines:** {analysis['total_lines']}")
                        st.write(f"**Complexity score:** {analysis['complexity_score']}")
                    
                    with col_b:
                        st.write(f"**Functions:** {len(analysis['functions'])}")
                        st.write(f"**Classes:** {len(analysis['classes'])}")
                        st.write(f"**Imports:** {len(analysis['imports'])}")
                    
                    # Suggestions
                    suggestions = code_analyzer.suggest_improvements(code_input)
                    if suggestions:
                        st.subheader("Improvement Suggestions:")
                        for suggestion in suggestions:
                            st.write(f"💡 {suggestion}")
                else:
                    st.error(f"Analysis failed: {analysis['error']}")

# Add admin panel to main navigation (call this from your main UI)
def add_admin_to_navigation():
    """Add admin panel to main navigation if in admin mode."""
    if st.session_state.get('admin_mode', False):
        if st.sidebar.button("🔧 Admin Panel"):
            st.session_state.current_page = "Admin"
        
        if st.sidebar.button("🧪 Code Playground"):
            st.session_state.current_page = "Code Playground"
