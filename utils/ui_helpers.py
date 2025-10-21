"""
UI Helper Functions
Provides user-friendly error display and notification utilities for Streamlit
"""

import streamlit as st
from typing import Dict, Any, Optional
from utils.logger import ErrorHandler, RecoveryAction


def display_error(
    error_info: Dict[str, str],
    show_technical_details: bool = True,
    show_recovery_suggestion: bool = True
):
    """
    Display user-friendly error message in Streamlit UI
    
    Args:
        error_info: Error information dictionary from ErrorHandler
        show_technical_details: Whether to show technical details in expander
        show_recovery_suggestion: Whether to show recovery suggestions
    """
    # Display user-friendly message
    st.error(f"⚠️ {error_info['user_message']}")
    
    # Show recovery suggestion if available
    if show_recovery_suggestion:
        category = error_info.get('category', 'general')
        error_type = error_info.get('error_type', 'default')
        recovery_action = RecoveryAction.get_recovery_action(category, error_type)
        
        if recovery_action == RecoveryAction.RETRY:
            st.info("💡 **Suggestion:** Please try again in a few moments.")
        elif recovery_action == RecoveryAction.NOTIFY_USER:
            st.warning("💡 **Action Required:** Please check your settings and update the configuration.")
        elif recovery_action == RecoveryAction.FALLBACK:
            st.info("💡 **Note:** The system will attempt to use an alternative method.")
        elif recovery_action == RecoveryAction.SKIP:
            st.info("💡 **Note:** This operation will be skipped. You can continue with other tasks.")
        elif recovery_action == RecoveryAction.ABORT:
            st.error("💡 **Action Required:** This operation cannot continue. Please contact support.")
    
    # Show technical details in expander
    if show_technical_details:
        with st.expander("🔧 Technical Details (for debugging)"):
            st.text(f"Category: {error_info.get('category', 'N/A')}")
            st.text(f"Error Type: {error_info.get('error_type', 'N/A')}")
            st.text(f"Technical Message: {error_info.get('technical_message', 'N/A')}")
            
            if 'context' in error_info:
                st.text("Context:")
                st.json(error_info['context'])
            
            if 'stack_trace' in error_info:
                st.text("Stack Trace:")
                st.code(error_info['stack_trace'], language='python')


def display_success(message: str, icon: str = "✅"):
    """
    Display success message
    
    Args:
        message: Success message to display
        icon: Icon to show with message
    """
    st.success(f"{icon} {message}")


def display_info(message: str, icon: str = "ℹ️"):
    """
    Display info message
    
    Args:
        message: Info message to display
        icon: Icon to show with message
    """
    st.info(f"{icon} {message}")


def display_warning(message: str, icon: str = "⚠️"):
    """
    Display warning message
    
    Args:
        message: Warning message to display
        icon: Icon to show with message
    """
    st.warning(f"{icon} {message}")


def show_loading_spinner(message: str = "Processing..."):
    """
    Context manager for showing loading spinner
    
    Args:
        message: Loading message to display
        
    Returns:
        Streamlit spinner context manager
    """
    return st.spinner(message)


def display_agent_status(
    agent_name: str,
    status: str,
    details: Optional[Dict[str, Any]] = None
):
    """
    Display agent execution status in UI
    
    Args:
        agent_name: Name of the agent
        status: Status (started, completed, failed)
        details: Additional details to display
    """
    if status == 'started':
        st.info(f"🤖 {agent_name} is working...")
    elif status == 'completed':
        st.success(f"✅ {agent_name} completed successfully")
        if details:
            with st.expander("View Details"):
                st.json(details)
    elif status == 'failed':
        st.error(f"❌ {agent_name} failed")
        if details:
            with st.expander("View Error Details"):
                st.json(details)


def confirm_action(
    message: str,
    button_text: str = "Confirm",
    key: Optional[str] = None
) -> bool:
    """
    Show confirmation dialog
    
    Args:
        message: Confirmation message
        button_text: Text for confirmation button
        key: Unique key for the button
        
    Returns:
        True if user confirmed, False otherwise
    """
    st.warning(message)
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button(button_text, key=key, type="primary"):
            return True
    with col2:
        if st.button("Cancel", key=f"{key}_cancel" if key else None):
            return False
    return False


def display_validation_errors(errors: list):
    """
    Display validation errors in a formatted way
    
    Args:
        errors: List of validation error messages
    """
    if errors:
        st.error("⚠️ Please fix the following errors:")
        for i, error in enumerate(errors, 1):
            st.markdown(f"{i}. {error}")


def display_progress(
    current: int,
    total: int,
    message: str = "Progress"
) -> None:
    """
    Display progress bar
    
    Args:
        current: Current progress value
        total: Total value
        message: Progress message
    """
    progress = current / total if total > 0 else 0
    st.progress(progress, text=f"{message}: {current}/{total}")


def display_metric_card(
    label: str,
    value: Any,
    delta: Optional[Any] = None,
    help_text: Optional[str] = None
):
    """
    Display metric in a card format
    
    Args:
        label: Metric label
        value: Metric value
        delta: Change in value (optional)
        help_text: Help text to display (optional)
    """
    st.metric(
        label=label,
        value=value,
        delta=delta,
        help=help_text
    )


def display_empty_state(
    message: str,
    icon: str = "📭",
    action_text: Optional[str] = None,
    action_callback: Optional[callable] = None
):
    """
    Display empty state with optional action
    
    Args:
        message: Empty state message
        icon: Icon to display
        action_text: Text for action button (optional)
        action_callback: Callback for action button (optional)
    """
    st.markdown(
        f"""
        <div style="text-align: center; padding: 3rem;">
            <h1>{icon}</h1>
            <p style="font-size: 1.2rem; color: #666;">{message}</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    if action_text and action_callback:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button(action_text, use_container_width=True):
                action_callback()
