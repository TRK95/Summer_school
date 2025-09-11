import os
import io
import json
import sys
import pandas as pd
import streamlit as st
from datetime import datetime

# Ensure project root is on path so we can import main.py
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from main import EDAOrchestrator
from runtime.history_db import HistoryDB

# Initialize history database
@st.cache_resource
def get_history_db():
    return HistoryDB()

@st.cache_data(ttl=5)  # Cache for 5 seconds, then auto-refresh
def get_cached_sessions(limit=30):
    """Get sessions with auto-refresh every 5 seconds"""
    history_db = get_history_db()
    return history_db.get_session_history(limit=limit)

def clear_sessions_cache():
    """Clear the sessions cache to force immediate refresh"""
    get_cached_sessions.clear()

def format_timestamp(ts):
    """Format timestamp for display"""
    return datetime.fromisoformat(ts).strftime("%Y-%m-%d %H:%M")


# Configure the page with modern CSS
st.set_page_config(page_title="Automated EDA", layout="wide")

# Modern clean CSS with improved typography and alignment
st.markdown("""
<style>
    /* Global typography improvements */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 90rem;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%) !important;
        border-right: 2px solid #e2e8f0 !important;
        padding-top: 1.5rem !important;
    }
    
    /* Sidebar container */
    .sidebar-container {
        padding: 0 1rem;
    }
    
    /* Main content area */
    .main-content {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border: 1px solid #e9ecef;
    }
    
    /* Title styling */
    .main h1 {
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        color: #1f2937 !important;
        margin-bottom: 0.5rem !important;
        line-height: 1.2 !important;
    }
    
    /* Caption styling */
    .main .caption {
        font-size: 1.1rem !important;
        color: #6b7280 !important;
        margin-bottom: 2rem !important;
        font-weight: 400 !important;
    }
    
    /* Settings container styling */
    .settings-container {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1.5rem 0 2rem 0;
        border: 1px solid #e9ecef;
    }
    
    /* Input labels */
    .stTextInput > label,
    .stSelectbox > label,
    .stSlider > label {
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        color: #374151 !important;
        margin-bottom: 0.5rem !important;
    }
    
    /* Input fields */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > div {
        font-size: 0.9rem !important;
        border-radius: 6px !important;
        border: 1px solid #d1d5db !important;
    }
    
    /* Primary button styling */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #3b82f6, #1d4ed8) !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.75rem 1.5rem !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        color: white !important;
        transition: all 0.2s ease !important;
        height: auto !important;
        min-height: 2.75rem !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        min-width: 120px !important;
    }
    
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #2563eb, #1e40af) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3) !important;
    }
    
    /* Sidebar title */
    .sidebar-title {
        font-size: 1.6rem !important;
        font-weight: 800 !important;
        color: #1e293b !important;
        margin-bottom: 2rem !important;
        padding: 0 0.5rem !important;
        text-align: center !important;
        background: linear-gradient(135deg, #3b82f6, #8b5cf6) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
    }
    
    /* New chat button */
    .new-chat-btn {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        margin-bottom: 2rem !important;
        padding: 0 1rem !important;
    }
    
    .new-chat-btn button {
        background: linear-gradient(135deg, #3b82f6, #1d4ed8) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        width: 90% !important;
        max-width: 200px !important;
        padding: 0.9rem 1.2rem !important;
        font-size: 1rem !important;
        font-weight: 700 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.25) !important;
        text-align: center !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 0.5rem !important;
    }
    .new-chat-btn button:hover {
        background: linear-gradient(135deg, #2563eb, #1e40af) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.35) !important;
    }
    .new-chat-btn button:active {
        transform: translateY(0px) !important;
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.25) !important;
    }
    
    /* Session groups */
    .session-group {
        font-size: 0.8rem !important;
        color: #6b7280 !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.8px !important;
        margin: 1.25rem 0 0.75rem 0 !important;
        padding: 0 0.5rem !important;
    }
    
    /* Session buttons */
    .stButton>button {
        background-color: transparent !important;
        color: #374151 !important;
        border: none !important;
        border-radius: 6px !important;
        width: 100% !important;
        text-align: left !important;
        padding: 0.6rem 0.75rem !important;
        font-size: 0.85rem !important;
        margin: 0.2rem 0 !important;
        font-weight: 400 !important;
        transition: all 0.15s ease !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        min-width: 100px !important;
    }
    .stButton>button:hover {
        background-color: #f3f4f6 !important;
        color: #1f2937 !important;
    }
    
    /* Session item container - ChatGPT style */
    .session-item {
        background: transparent !important;
        border-radius: 8px !important;
        margin: 0 !important;
        padding: 0.1rem 0.5rem !important;
        transition: all 0.2s ease !important;
        position: relative !important;
        overflow: hidden !important;
        width: 100% !important;
    }
    .session-item:hover {
        background: rgba(0, 0, 0, 0.05) !important;
    }
    
    /* Override Streamlit container spacing for sessions */
    .session-item .stContainer > div {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        margin-top: 0 !important;
        margin-bottom: 0 !important;
        gap: 0 !important;
        overflow: hidden !important;
    }
    
    /* Override Streamlit column spacing for sessions */
    .session-item .stColumns {
        gap: 0.25rem !important;
        margin: 0 !important;
        padding: 0 !important;
        overflow: hidden !important;
        width: 100% !important;
    }
    
    .session-item .stColumns > div {
        padding: 0 !important;
        margin: 0 !important;
        overflow: hidden !important;
    }
    
    /* Session item buttons - override Streamlit defaults */
    .session-item .stButton > button {
        background: transparent !important;
        border: none !important;
        color: #374151 !important;
        font-size: 0.85rem !important;
        font-weight: 400 !important;
        text-align: left !important;
        padding: 0.25rem 0.1rem !important;
        margin: 0 !important;
        border-radius: 6px !important;
        transition: all 0.2s ease !important;
        width: 100% !important;
        min-height: 24px !important;
        max-height: 24px !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        white-space: nowrap !important;
        line-height: 1.1 !important;
        max-width: 100% !important;
        word-wrap: normal !important;
        word-break: normal !important;
        display: block !important;
    }
    
    .session-item .stButton > button:hover {
        background: rgba(59, 130, 246, 0.1) !important;
        color: #1e40af !important;
    }
    
    /* Delete button specific styling */
    .session-item .stButton:last-child > button {
        width: 20px !important;
        height: 20px !important;
        min-width: 20px !important;
        min-height: 20px !important;
        max-height: 20px !important;
        padding: 0 !important;
        font-size: 0.7rem !important;
        border-radius: 4px !important;
        opacity: 0 !important;
        background: rgba(239, 68, 68, 0.1) !important;
        color: #dc2626 !important;
        text-align: center !important;
        transition: all 0.2s ease !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    
    .session-item:hover .stButton:last-child > button {
        opacity: 0.8 !important;
    }
    
    .session-item .stButton:last-child > button:hover {
        background: #ef4444 !important;
        color: white !important;
        transform: scale(1.05) !important;
        opacity: 1 !important;
    }
    
    /* Remove button styling overrides for session items */
    .session-item .stButton > button {
        all: unset !important;
        display: block !important;
        width: 100% !important;
        max-width: 100% !important;
        min-height: 24px !important;
        max-height: 24px !important;
        color: #374151 !important;
        font-size: 0.85rem !important;
        font-weight: 400 !important;
        text-align: left !important;
        cursor: pointer !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        white-space: nowrap !important;
        background: transparent !important;
        border: none !important;
        padding: 0.25rem 0.1rem !important;
        border-radius: 6px !important;
        transition: all 0.2s ease !important;
        line-height: 1.1 !important;
        box-sizing: border-box !important;
        word-wrap: normal !important;
        word-break: normal !important;
        hyphens: none !important;
    }
    
    /* Force single line for button text content */
    .session-item .stButton > button * {
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        white-space: nowrap !important;
        display: inline !important;
        max-width: 100% !important;
    }
    
    /* Target Streamlit's internal button text elements */
    .session-item .stButton div,
    .session-item .stButton span,
    .session-item .stButton p {
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        white-space: nowrap !important;
        max-width: 100% !important;
        display: inline !important;
        word-wrap: normal !important;
    }
    
    /* Override any flex display that might cause wrapping */
    .session-item .stButton > button > div {
        display: inline !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        white-space: nowrap !important;
        width: 100% !important;
        max-width: 100% !important;
    }
    
    /* Remove bulk action styles since we're removing them */
    
    /* Ensure buttons in narrow columns display properly */
    .stButton > button[data-testid="baseButton-secondary"] {
        font-size: 0.9rem !important;
        padding: 0.6rem 1rem !important;
        white-space: normal !important;
        word-wrap: break-word !important;
        min-width: 140px !important;
        height: auto !important;
        line-height: 1.2 !important;
    }
    
    /* Step headers */
    .main h2 {
        font-size: 1.6rem !important;
        font-weight: 700 !important;
        color: #1f2937 !important;
        margin: 2rem 0 1rem 0 !important;
        padding-bottom: 0.5rem !important;
        border-bottom: 2px solid #e5e7eb !important;
    }
    
    .main h3 {
        font-size: 1.3rem !important;
        font-weight: 600 !important;
        color: #374151 !important;
        margin: 1.5rem 0 0.75rem 0 !important;
    }
    
    .main h4 {
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        color: #4b5563 !important;
        margin: 1rem 0 0.5rem 0 !important;
    }
    
    /* Plan items styling */
    .plan-item {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.75rem 0;
        border-left: 4px solid #3b82f6;
    }
    
    /* Success/error messages */
    .stSuccess, .stError, .stInfo, .stWarning {
        border-radius: 8px !important;
        font-size: 0.95rem !important;
        padding: 0.75rem 1rem !important;
        margin: 0.75rem 0 !important;
    }
    
    /* File uploader */
    .stFileUploader {
        margin: 1.5rem 0 !important;
    }
    
    .stFileUploader > label {
        font-size: 1rem !important;
        font-weight: 600 !important;
        color: #374151 !important;
    }
    
    /* Data preview styling */
    .stDataFrame {
        margin: 1rem 0 !important;
        border-radius: 8px !important;
        overflow: hidden !important;
        border: 1px solid #e5e7eb !important;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        font-size: 1rem !important;
        font-weight: 600 !important;
        color: #374151 !important;
    }
    
    /* Divider improvements */
    hr {
        margin: 1.5rem 0 !important;
        border-color: #e5e7eb !important;
    }
</style>

<script>
// Auto-refresh for sidebar updates
let lastSessionCount = 0;
let refreshInterval;

function checkForUpdates() {
    // Check if we're viewing a session or actively using the app
    const isActivelyUsing = document.querySelector('[data-testid="stFileUploader"]') !== null ||
                           document.querySelector('.stButton button:hover') !== null ||
                           document.querySelector('input:focus') !== null;
    
    if (!isActivelyUsing) {
        // Get current session count from the sidebar
        const sessionCountElement = document.querySelector('.sidebar-title').parentElement;
        if (sessionCountElement) {
            const currentText = sessionCountElement.textContent;
            const match = currentText.match(/(\d+) conversations total/);
            const currentCount = match ? parseInt(match[1]) : 0;
            
            if (lastSessionCount !== 0 && currentCount !== lastSessionCount) {
                // Session count changed, trigger a subtle refresh
                window.parent.postMessage({
                    type: 'streamlit:rerun'
                }, '*');
            }
            lastSessionCount = currentCount;
        }
    }
}

// Start checking every 15 seconds
refreshInterval = setInterval(checkForUpdates, 15000);

// Clean up on page unload
window.addEventListener('beforeunload', function() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
});
</script>
""", unsafe_allow_html=True)

# Initialize session state
if "viewing_session" not in st.session_state:
    st.session_state.viewing_session = None
if "selected_dataset" not in st.session_state:
    st.session_state.selected_dataset = None
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = datetime.now()

# Auto-refresh mechanism - refresh every 30 seconds
current_time = datetime.now()
if (current_time - st.session_state.last_refresh).seconds > 30:
    st.session_state.last_refresh = current_time
    clear_sessions_cache()

# Get history database
history_db = get_history_db()

# Create sidebar for history
with st.sidebar:
    # Modern title without emoji
    st.markdown('<div class="sidebar-title">Chat History</div>', unsafe_allow_html=True)
    
    # New Chat button
    st.markdown('<div class="new-chat-btn">', unsafe_allow_html=True)
    if st.button("✨ Start new analysis", use_container_width=False):
        # Clear session state for new analysis
        for key in list(st.session_state.keys()):
            if key not in ["viewing_session"]:
                del st.session_state[key]
        st.session_state.viewing_session = None
        # Clear cache to ensure fresh session list
        clear_sessions_cache()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Auto-refresh indicator (hidden)
    refresh_placeholder = st.empty()
    
    # Get recent sessions with auto-refresh
    sessions = get_cached_sessions(limit=30)
    
    if not sessions:
        st.write("No previous sessions")
    else:
        # Group by time
        from datetime import datetime, timedelta
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        week_ago = today - timedelta(days=7)
        
        groups = {"Today": [], "Yesterday": [], "This week": [], "Older": []}
        
        for session in sessions:
            try:
                session_date = datetime.fromisoformat(session['timestamp']).date()
                if session_date == today:
                    groups["Today"].append(session)
                elif session_date == yesterday:
                    groups["Yesterday"].append(session)
                elif session_date > week_ago:
                    groups["This week"].append(session)
                else:
                    groups["Older"].append(session)
            except:
                groups["Older"].append(session)
        
        # Display groups
        for group_name, group_sessions in groups.items():
            if group_sessions:
                st.markdown(f'<div class="session-group">{group_name}</div>', unsafe_allow_html=True)
                
                for session in group_sessions:
                    # Format display
                    try:
                        time_str = datetime.fromisoformat(session['timestamp']).strftime("%H:%M")
                    except:
                        time_str = "Time"
                    
                    dataset = os.path.basename(session['csv_path'])
                    if len(dataset) > 20:
                        dataset = dataset[:17] + "..."
                    
                    status = "✓" if session.get('success') else "✗"
                    
                    # For Today section, show time + dataset + status (original format)
                    # For other sections, show just dataset + status (new format)
                    if group_name == "Today":
                        display_text = f"{time_str} • {dataset} {status}"
                    else:
                        display_text = f"{dataset} {status}"
                    
                    # Create session item in ChatGPT style using columns
                    session_id = session['session_id']
                    
                    # Create the session container
                    with st.container():
                        st.markdown('<div class="session-item">', unsafe_allow_html=True)
                        
                        # Create columns for content and delete button
                        content_col, delete_col = st.columns([10, 1])
                        
                        with content_col:
                            # Session content button (full width, no visible styling)
                            if st.button(
                                display_text, 
                                key=f"sess_{session_id}",
                                help=f"View session from {time_str}",
                                use_container_width=True
                            ):
                                st.session_state.viewing_session = session_id
                                st.rerun()
                        
                        with delete_col:
                            # Delete button (small, appears on hover)
                            if st.button(
                                "🗑️", 
                                key=f"del_{session_id}",
                                help="Delete this session",
                                type="secondary"
                            ):
                                # Delete session from database
                                history_db.delete_session(session_id)
                                # Clear viewing session if it was the deleted one
                                if st.session_state.get('viewing_session') == session_id:
                                    st.session_state.viewing_session = None
                                # Clear cache to immediately update sidebar
                                clear_sessions_cache()
                                st.rerun()
                        
                        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style='text-align: center; margin-top: 1.5rem; padding: 0.75rem; 
                    background: rgba(59, 130, 246, 0.1); border-radius: 8px; 
                    color: #1e40af; font-size: 0.85rem; font-weight: 600;'>
            📊 {len(sessions)} conversations total
        </div>
        """, unsafe_allow_html=True)

# Main content area
st.markdown("<div class='main-content'>", unsafe_allow_html=True)

# Header section with improved typography
st.title("Automated EDA & Visualization")
st.markdown('<p class="caption">Upload a CSV, set a goal, and let the agents do the rest.</p>', unsafe_allow_html=True)

# Settings section with better structure
st.markdown("<div class='settings-container'>", unsafe_allow_html=True)
st.markdown("### ⚙️ Analysis Configuration")

settings_col1, settings_col2 = st.columns([2.5, 1.5])
with settings_col1:
    input_col1, input_col2, input_col3 = st.columns([2, 1, 2])
    with input_col1:
        goal = st.text_input("🎯 Analysis goal", value="General EDA", help="Describe what you want to discover from your data")
    with input_col2:
        max_items = st.slider("📊 Max items", min_value=3, max_value=12, value=8, help="Maximum number of analysis items to generate")
    with input_col3:
        api_key = st.text_input("🔑 DeepSeek API Key", 
                              value=os.getenv("DEEPSEEK_API_KEY", ""), 
                              type="password",
                              help="Your DeepSeek API key for AI analysis")

with settings_col2:
    st.markdown("<br>", unsafe_allow_html=True)  # Add spacing
    run_button = st.button("🚀 Run Analysis", type="primary", use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)

# File upload section
st.markdown("### 📁 Data Upload")
uploaded_file = st.file_uploader("Choose a CSV file to analyze", type=["csv"], help="Upload your dataset in CSV format") 

if st.session_state.viewing_session:
    # Display session details with improved layout
    session = history_db.get_session_details(st.session_state.viewing_session)
    
    # Session header
    st.markdown("## 📊 Session Analysis")
    
    # Session info cards
    info_col1, info_col2, info_col3 = st.columns(3)
    with info_col1:
        st.markdown(f"""
        <div style='background: #f0f9ff; padding: 1rem; border-radius: 8px; border-left: 4px solid #0ea5e9;'>
            <h4 style='margin: 0; color: #0c4a6e;'>📄 Dataset</h4>
            <p style='margin: 0; font-size: 1rem; color: #075985;'>{os.path.basename(session.get('csv_path', 'Unknown'))}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with info_col2:
        st.markdown(f"""
        <div style='background: #f0fdf4; padding: 1rem; border-radius: 8px; border-left: 4px solid #22c55e;'>
            <h4 style='margin: 0; color: #14532d;'>📅 Date</h4>
            <p style='margin: 0; font-size: 1rem; color: #166534;'>{format_timestamp(session.get('timestamp', ''))}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with info_col3:
        st.markdown(f"""
        <div style='background: #fefce8; padding: 1rem; border-radius: 8px; border-left: 4px solid #eab308;'>
            <h4 style='margin: 0; color: #713f12;'>🎯 Goal</h4>
            <p style='margin: 0; font-size: 1rem; color: #a16207;'>{session.get('user_goal', 'No goal specified')}</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Show plan versions in tabs
    if session.get('plan_versions'):
        st.markdown("### 📋 Analysis Plans")
        try:
            plan_tabs = st.tabs([f"Version {p['version_number']}" for p in session['plan_versions']])
            for tab, plan in zip(plan_tabs, session['plan_versions']):
                with tab:
                    if plan.get('approved'):
                        st.success("✅ This plan was approved")
                    if plan.get('user_feedback'):
                        st.info(f"💬 Feedback: {plan['user_feedback']}")
                    
                    try:
                        items = json.loads(plan['plan_items'])
                        for item in items:
                            with st.container():
                                st.markdown(f"""
                                <div class='plan-item'>
                                    <h4>📌 Item {item.get('id', 'Unknown')}</h4>
                                    <p><strong>Goal:</strong> {item.get('goal', 'N/A')}</p>
                                    <p><strong>Plots:</strong> {', '.join(item.get('plots', []))}</p>
                                    <p><strong>Columns:</strong> {', '.join(item.get('columns', []))}</p>
                                    {f"<p><strong>Notes:</strong> {item['notes']}</p>" if item.get('notes') else ""}
                                </div>
                                """, unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Error parsing plan items: {str(e)}")
        except Exception as e:
            st.error(f"Error displaying plan versions: {str(e)}")
    else:
        st.info("📝 No analysis plans found for this session.")
    
    # Show execution results
    if session.get('execution_results'):
        st.markdown("### 🔄 Execution Results")
        try:
            for result in session['execution_results']:
                with st.expander(f"📊 Item {result.get('item_id', 'Unknown')}", expanded=True):
                    status_col, retry_col = st.columns([2, 1])
                    with status_col:
                        status = "✅ Success" if result.get('success') else "❌ Failed"
                        st.markdown(f"**Status**: {status}")
                    with retry_col:
                        if result.get('retry_count', 0) > 0:
                            st.warning(f"🔄 {result['retry_count']} retries")
                    
                    # Show generated plots
                    try:
                        # Try to get charts from exec_result manifest (newer format)
                        exec_result = json.loads(result['exec_result'])
                        charts = []
                        if exec_result.get('manifest', {}).get('charts'):
                            charts = exec_result['manifest']['charts']
                        
                        # If no charts in manifest, try expected_outputs from code_output (common format)
                        if not charts and result.get('code_output'):
                            try:
                                code_output = json.loads(result['code_output'])
                                expected_outputs = code_output.get('expected_outputs', [])
                                # Convert expected_outputs to charts format
                                charts = [{'saved_path': path} for path in expected_outputs]
                            except Exception:
                                pass
                        
                        if charts:
                            plot_cols = st.columns(2)
                            for idx, chart in enumerate(charts):
                                if os.path.exists(chart['saved_path']):
                                    with plot_cols[idx % 2]:
                                        st.image(chart['saved_path'], use_container_width=True, caption=f"Chart {idx + 1}")
                        else:
                            st.info("📝 No visualizations found for this item.")
                    except Exception as e:
                        st.warning(f"Could not display plots: {str(e)}")
                    
                    if result.get('error'):
                        st.error(f"❌ Error: {result['error']}")
        except Exception as e:
            st.error(f"Error displaying execution results: {str(e)}")
    else:
        st.info("🔄 No execution results found for this session.")
    
    # Show final report if successful
    if session.get('success') and session.get('report_path'):
        st.markdown("### 📄 Final Report")
        try:
            report_path = session['report_path']
            if os.path.exists(report_path):
                with open(report_path, 'r', encoding='utf-8') as f:
                    st.markdown(f.read())
            else:
                st.warning(f"Report file not found: {report_path}")
        except Exception as e:
            st.error(f"Could not load report: {str(e)}")
    else:
        st.info("📄 No final report available for this session.")

elif uploaded_file is not None:
    try:
        # Read uploaded CSV into a temp path so orchestrator can read it again
        csv_bytes = uploaded_file.getvalue()
        df_preview = pd.read_csv(io.BytesIO(csv_bytes))
        
        # Data preview section with improved styling
        st.markdown("## 👀 Data Preview")
        
        # Data info cards
        preview_col1, preview_col2, preview_col3, preview_col4 = st.columns(4)
        with preview_col1:
            st.metric("📊 Rows", f"{len(df_preview):,}")
        with preview_col2:
            st.metric("📋 Columns", len(df_preview.columns))
        with preview_col3:
            st.metric("💾 Size", f"{df_preview.memory_usage(deep=True).sum() / 1024:.1f} KB")
        with preview_col4:
            numeric_cols = len(df_preview.select_dtypes(include=['number']).columns)
            st.metric("🔢 Numeric", numeric_cols)
        
        # Show preview table
        st.dataframe(df_preview.head(50), use_container_width=True)

        # Save to a temp file path
        tmp_dir = os.path.join("./logs", "ui_uploads")
        os.makedirs(tmp_dir, exist_ok=True)
        tmp_csv_path = os.path.join(tmp_dir, uploaded_file.name)
        with open(tmp_csv_path, "wb") as f:
            f.write(csv_bytes)

        # Initialize orchestrator once per session
        if "orchestrator" not in st.session_state:
            st.session_state["orchestrator"] = EDAOrchestrator(api_key=api_key or None)
        else:
            # If API key changes, re-init orchestrator
            if api_key and api_key != os.getenv("DEEPSEEK_API_KEY", ""):
                st.session_state["orchestrator"] = EDAOrchestrator(api_key=api_key)

        # Mark analysis as started on click and reset caches for a fresh run
        if run_button:
            st.session_state["analysis_ready"] = True
            st.session_state["tmp_csv_path"] = tmp_csv_path
            st.session_state["goal"] = goal
            st.session_state["max_items"] = max_items
            st.session_state.pop("profile", None)
            st.session_state.pop("df", None)
            st.session_state.pop("sample_rows", None)
            st.session_state.pop("plan_versions", None)
            st.session_state.pop("selected_version_index", None)
            
            # Start a new session in the database
            session_id = history_db.start_session(tmp_csv_path, goal, max_items)
            st.session_state["session_id"] = session_id

        # Proceed if a run has been initiated
        if st.session_state.get("analysis_ready"):
            orchestrator = st.session_state["orchestrator"]

            # Progress indicator
            st.markdown("---")
            st.markdown("## 🔄 Analysis Progress")
            
            progress_col1, progress_col2, progress_col3, progress_col4, progress_col5 = st.columns(5)
            
            # Step 1: Profile (cache)
            with progress_col1:
                st.markdown("### 1️⃣ Profile")
                if "profile" not in st.session_state:
                    with st.spinner("Profiling data..."):
                        profile = orchestrator.profiler.profile(st.session_state.get("tmp_csv_path", tmp_csv_path))
                    st.session_state["profile"] = profile
                profile = st.session_state["profile"]
                st.success(f"✅ {profile.get('rows_total', 0):,} rows\n{len(profile.get('columns', []))} columns")

            # Step 2: Load Data (cache)
            with progress_col2:
                st.markdown("### 2️⃣ Load")
                if "df" not in st.session_state:
                    with st.spinner("Loading data..."):
                        st.session_state["df"] = pd.read_csv(st.session_state.get("tmp_csv_path", tmp_csv_path))
                df = st.session_state["df"]
                st.success(f"✅ {df.shape[0]:,} × {df.shape[1]}")

            # Step 3: Plan indicator
            with progress_col3:
                st.markdown("### 3️⃣ Plan")
                if "plan_versions" in st.session_state:
                    st.success(f"✅ {len(st.session_state['plan_versions'])} versions")
                else:
                    st.info("⏳ Pending")

            # Step 4: Execute indicator
            with progress_col4:
                st.markdown("### 4️⃣ Execute")
                st.info("⏳ Pending")

            # Step 5: Report indicator
            with progress_col5:
                st.markdown("### 5️⃣ Report")
                st.info("⏳ Pending")

            st.markdown("---")

            # Step 3: Planner (with approval gating and unlimited regenerations)
            st.markdown("## 📋 Analysis Planning")
            st.markdown("Review and approve the generated analysis plan, or request modifications.")
            
            if "plan_versions" not in st.session_state:
                with st.spinner("🤖 Generating analysis plan..."):
                    try:
                        sample_rows = df.sample(n=min(8, len(df)), random_state=42).to_dict(orient='records')
                    except Exception:
                        sample_rows = []
                    st.session_state["sample_rows"] = sample_rows
                    plan_resp = orchestrator.planner.plan(profile, st.session_state.get("goal", goal), st.session_state.get("max_items", max_items), data_samples=sample_rows)
                    st.session_state["plan_versions"] = [
                        {"label": "Original", "items": plan_resp.get("eda_plan", [])}
                    ]

            plan_versions = st.session_state.get("plan_versions", [])
            
            # Render all versions with improved styling
            approved_index = None
            for idx, version in enumerate(plan_versions):
                st.markdown(f"### {idx+1}. {version.get('label','Version')} Plan")
                
                items = version.get("items", [])
                if items:
                    # Create a grid layout for plan items
                    for i in range(0, len(items), 2):
                        item_cols = st.columns(2)
                        for j, col in enumerate(item_cols):
                            if i + j < len(items):
                                item = items[i + j]
                                with col:
                                    item_id = item.get("id", "unknown")
                                    goal_txt = item.get("goal", "")
                                    priority = str(item.get("priority", "")).strip()
                                    plots = ", ".join(item.get("plots", []))
                                    columns = ", ".join(item.get("columns", []))
                                    notes = item.get("notes", "")

                                    # Priority color coding
                                    priority_colors = {
                                        "high": "#ef4444",
                                        "medium": "#f59e0b", 
                                        "low": "#10b981"
                                    }
                                    priority_color = priority_colors.get(priority.lower(), "#6b7280")

                                    st.markdown(f"""
                                    <div style='background: #f8fafc; border-radius: 8px; padding: 1rem; margin: 0.5rem 0; border-left: 4px solid {priority_color};'>
                                        <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;'>
                                            <h4 style='margin: 0; color: #1e293b;'>📊 Item {item_id}</h4>
                                            <span style='background: {priority_color}; color: white; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.8rem; font-weight: 600;'>{priority.upper() if priority else "NORMAL"}</span>
                                        </div>
                                        <p style='margin: 0.5rem 0; color: #475569; font-size: 0.9rem;'><strong>Goal:</strong> {goal_txt}</p>
                                        <p style='margin: 0.5rem 0; color: #475569; font-size: 0.9rem;'><strong>Plots:</strong> {plots}</p>
                                        <p style='margin: 0.5rem 0; color: #475569; font-size: 0.9rem;'><strong>Columns:</strong> {columns}</p>
                                        {f"<p style='margin: 0.5rem 0; color: #475569; font-size: 0.9rem;'><strong>Notes:</strong> {notes}</p>" if notes else ""}
                                    </div>
                                    """, unsafe_allow_html=True)
                else:
                    st.info("📝 Plan is empty.")
                
                # Approval button with better styling - centered
                approval_col1, approval_col2, approval_col3 = st.columns([1, 2, 1])
                with approval_col2:
                    if st.button(f"✅ Approve Plan {idx+1}", key=f"approve_plan_{idx}", use_container_width=True):
                        approved_index = idx
                        # Save approved plan to database
                        if "session_id" in st.session_state:
                            history_db.save_plan_version(
                                st.session_state["session_id"],
                                version_number=idx+1,
                                plan_items=items,
                                approved=True
                            )
                
                st.markdown("---")

            # Request changes form (below the latest rendered plan)
            with st.expander("🔄 Request Changes (Generate New Version)", expanded=False):
                st.markdown("Describe what you'd like to adjust in the analysis plan:")
                feedback = st.text_area("Your feedback", 
                                       placeholder="E.g., 'Focus more on correlation analysis', 'Add time series plots', 'Remove redundant visualizations'...",
                                       key="feedback_text",
                                       height=100)
                
                feedback_col1, feedback_col2, feedback_col3 = st.columns([1, 2, 1])
                with feedback_col2:
                    if st.button("🔄 Generate Updated Plan", key="request_changes", use_container_width=True):
                        with st.spinner("🤖 Generating updated plan..."):
                            plan_resp = orchestrator.planner.plan(
                                st.session_state["profile"],
                                st.session_state.get("goal", goal),
                                st.session_state.get("max_items", max_items),
                                data_samples=st.session_state.get("sample_rows", []),
                                user_feedback=feedback or "Please improve the plan per my comments."
                            )
                            new_items = plan_resp.get("eda_plan", [])
                            version_label = f"Updated {len(plan_versions)}"
                            plan_versions.append({"label": version_label, "items": new_items})
                            st.session_state["plan_versions"] = plan_versions
                            
                            # Save new plan version to database
                            if "session_id" in st.session_state:
                                history_db.save_plan_version(
                                    st.session_state["session_id"],
                                    version_number=len(plan_versions),
                                    plan_items=new_items,
                                    user_feedback=feedback,
                                    approved=False
                                )
                        # Immediately rerun to render the new plan version without another click
                        st.rerun()

            if approved_index is None:
                st.info("👆 Please approve a plan version to proceed to execution.")
                st.stop()

            selected_plan_items = plan_versions[approved_index]["items"]

            # Step 4: Execute per item (show plots as they are produced)
            st.markdown("## 🔄 Execution & Visualization")
            st.markdown("Generating code and executing analysis items...")
            
            highlights = []
            execution_progress = st.progress(0)
            total_items = len(selected_plan_items)
            
            for i, item in enumerate(selected_plan_items, 1):
                # Update progress
                execution_progress.progress(i / total_items)
                
                # Item execution header
                exec_col1, exec_col2 = st.columns([3, 1])
                with exec_col1:
                    st.markdown(f"### 📊 Item {item.get('id', f'item_{i}')} - {item.get('goal', 'Analysis')}")
                with exec_col2:
                    st.markdown(f"**Progress:** {i}/{total_items}")
                
                with st.spinner("🤖 Generating code and executing..."):
                    code_output = orchestrator.coder.write_code(item, st.session_state["profile"], orchestrator.artifacts_dir)
                    
                    # Initial execution
                    exec_result = orchestrator.executor.execute(
                        code_output["python"],
                        st.session_state["df"],
                        code_output["manifest_schema"]
                    )
                    
                    # Try to execute the code with retries if needed (similar to main.py)
                    max_retries = 3
                    retry_count = 0
                    success = False
                    critique_result = {}  # Initialize critique_result

                    while retry_count < max_retries and not success:
                        if retry_count > 0:
                            st.info(f"🔄 Retry attempt {retry_count}/{max_retries}...")

                        if exec_result["exec_ok"]:
                            success = True
                        else:
                            error_msg = exec_result.get('error', 'Unknown error')
                            st.warning(f"⚠️ Failed: {error_msg}")
                            
                            # Check if it's an indentation error
                            if "IndentationError" in error_msg or "unexpected indent" in error_msg:
                                try:
                                    import autopep8
                                    st.info("🔧 Attempting to fix indentation with autopep8...")
                                    # Fix indentation using autopep8
                                    fixed_code = autopep8.fix_code(code_output["python"])
                                    # Try executing the fixed code
                                    exec_result = orchestrator.executor.execute(
                                        fixed_code, st.session_state["df"], code_output["manifest_schema"]
                                    )
                                    retry_count += 1
                                    continue
                                except Exception as e:
                                    st.warning(f"❌ Autopep8 fix failed: {str(e)}")
                                    # Fall through to critic logic since autopep8 failed
                            
                            # For non-indentation errors OR when autopep8 fails, use the critic
                            critique_result = orchestrator.critic.critique(code_output, exec_result)
                            
                            if critique_result["status"] == "fix":
                                st.info("🔧 Generating new code based on critic's feedback...")
                                # Get new code from CodeWriter with critic's feedback
                                item["critic_feedback"] = critique_result["notes"]  # Add critic's feedback to help generate better code
                                code_output = orchestrator.coder.write_code(item, st.session_state["profile"], orchestrator.artifacts_dir)
                                # Execute the new code
                                exec_result = orchestrator.executor.execute(
                                    code_output["python"], st.session_state["df"], code_output["manifest_schema"]
                                )
                                retry_count += 1
                            else:
                                st.warning("❌ Critic could not determine how to fix")
                                break

                    if not success:
                        st.error(f"❌ Failed after {retry_count} retries")

                # Show plots for this item with improved layout
                # First try to get charts from exec_result manifest (actual saved paths)
                charts = []
                if success and exec_result and exec_result.get("manifest", {}).get("charts"):
                    charts = exec_result["manifest"]["charts"]
                    st.info(f"📊 Found {len(charts)} charts in manifest")
                # Fallback to expected_outputs if no charts in manifest
                elif not charts:
                    expected = code_output.get("expected_outputs", [])
                    # Create chart objects from expected outputs that actually exist
                    charts = []
                    for path in expected:
                        # Check if the file exists as provided
                        if os.path.exists(path):
                            chart_path = path
                        else:
                            # Try to find the file in the artifacts directory with timestamped subdirectory
                            filename = os.path.basename(path)
                            # Look for the file in timestamped directories
                            artifacts_base = orchestrator.artifacts_dir
                            chart_path = None
                            
                            # Check timestamped subdirectories
                            for subdir in os.listdir(artifacts_base):
                                if os.path.isdir(os.path.join(artifacts_base, subdir)):
                                    potential_path = os.path.join(artifacts_base, subdir, filename)
                                    if os.path.exists(potential_path):
                                        chart_path = potential_path
                                        break
                            
                            # If still not found, check the base artifacts directory
                            if not chart_path:
                                potential_path = os.path.join(artifacts_base, filename)
                                if os.path.exists(potential_path):
                                    chart_path = potential_path
                        
                        if chart_path and os.path.exists(chart_path):
                            # Extract chart info from filename
                            filename = os.path.basename(chart_path)
                            chart_type = "histogram" if "histogram" in filename else "boxplot" if "boxplot" in filename else "plot"
                            column_name = filename.split('_')[0] if '_' in filename else "unknown"
                            
                            charts.append({
                                "saved_path": chart_path,
                                "chart_type": chart_type,
                                "columns_used": [column_name] if column_name != "unknown" else []
                            })
                    
                    if expected:
                        st.warning(f"⚠️ No charts in manifest, using expected outputs: {len(charts)} found")
                
                if charts:
                    st.markdown("#### 📈 Generated Visualizations")
                    # Create responsive columns based on number of plots
                    num_plots = len(charts)
                    if num_plots == 1:
                        cols = st.columns(1)
                    elif num_plots == 2:
                        cols = st.columns(2)
                    else:
                        cols = st.columns(3)
                    
                    for j, chart in enumerate(charts):
                        chart_path = chart.get("saved_path", "")
                        if chart_path and os.path.exists(chart_path):
                            with cols[j % len(cols)]:
                                # Create a more informative caption
                                chart_type = chart.get("chart_type", "plot")
                                columns_used = chart.get("columns_used", [])
                                col_text = f" ({', '.join(columns_used)})" if columns_used else ""
                                caption = f"Item {item.get('id', f'item_{i}')} - {chart_type.title()}{col_text}"
                                
                                st.image(chart_path, use_container_width=True, caption=caption)
                        else:
                            st.warning(f"⚠️ Image file not found: {chart_path}")
                else:
                    # Debug information when no charts are found
                    st.info("📝 No visualizations found.")
                    if success and exec_result:
                        manifest = exec_result.get("manifest", {})
                        expected = code_output.get("expected_outputs", [])
                        with st.expander("🔍 Debug Info", expanded=False):
                            st.write(f"**Execution successful:** {success}")
                            st.write(f"**Expected outputs:** {expected}")
                            st.write(f"**Manifest keys:** {list(manifest.keys())}")
                            if "charts" in manifest:
                                st.write(f"**Charts in manifest:** {len(manifest['charts'])}")
                                for i, chart in enumerate(manifest.get('charts', [])):
                                    st.write(f"  Chart {i+1}: {chart.get('saved_path', 'No path')}")
                            else:
                                st.write("**No 'charts' key in manifest**")
                            
                            # Show the generated code for debugging
                            st.write("**Generated Python Code:**")
                            st.code(code_output.get("python", "No code found"), language="python")
                            
                            # Check if expected files exist
                            st.write("**File Existence Check:**")
                            for expected_file in expected:
                                exists = os.path.exists(expected_file)
                                st.write(f"  {expected_file}: {'✓ Exists' if exists else '✗ Missing'}")
                            
                            # Show what files actually exist in artifacts directory
                            st.write("**Files in Artifacts Directory:**")
                            artifacts_base = orchestrator.artifacts_dir
                            try:
                                if os.path.exists(artifacts_base):
                                    for root, dirs, files in os.walk(artifacts_base):
                                        for file in files:
                                            if file.endswith('.png'):
                                                full_path = os.path.join(root, file)
                                                rel_path = os.path.relpath(full_path, artifacts_base)
                                                st.write(f"  ✓ Found: {rel_path}")
                                else:
                                    st.write(f"  Artifacts directory doesn't exist: {artifacts_base}")
                            except Exception as e:
                                st.write(f"  Error listing files: {str(e)}")
                            
                            # Show execution stdout for more details
                            stdout = exec_result.get("stdout", "")
                            if stdout:
                                st.write("**Execution Output:**")
                                st.code(stdout, language="text")

                # Execution status
                if success and exec_result and exec_result.get("exec_ok"):
                    # Get actual artifacts from manifest charts
                    artifacts = []
                    if exec_result.get("manifest", {}).get("charts"):
                        artifacts = [chart.get("saved_path", "") for chart in exec_result["manifest"]["charts"] 
                                   if chart.get("saved_path") and os.path.exists(chart.get("saved_path", ""))]
                    # Fallback to expected outputs if no charts in manifest
                    if not artifacts:
                        artifacts = [path for path in code_output.get("expected_outputs", []) if os.path.exists(path)]
                    
                    highlight = {
                        "title": code_output.get("title", f"Item {item.get('id', f'item_{i}')}"),
                        "artifacts": artifacts,
                        "manifest": exec_result.get("manifest", {}),
                        "evidence": exec_result.get("evidence", {}),
                        "notes": exec_result.get("stdout") or "Analysis completed successfully",
                    }
                    highlights.append(highlight)
                    if retry_count > 0:
                        st.success(f"✅ Execution completed successfully after {retry_count} retries")
                    else:
                        st.success("✅ Execution completed successfully")
                else:
                    error_msg = exec_result.get('error', 'Unknown error') if exec_result else 'Execution failed'
                    st.error(f"❌ Execution failed: {error_msg}")
                
                # Save execution result to database
                if "session_id" in st.session_state:
                    history_db.save_execution_result(
                        session_id=st.session_state["session_id"],
                        item_id=item.get('id', f'item_{i}'),
                        code_output=code_output,
                        exec_result=exec_result or {},
                        critique_result=critique_result,
                        success=success,
                        retry_count=retry_count,
                        error=exec_result.get('error') if exec_result else 'Execution failed'
                    )
                
                st.markdown("---")

            # Step 5: Reporter
            st.markdown("## 📄 Final Report")
            st.markdown("Generating comprehensive analysis report...")
            
            with st.spinner("📝 Generating final report..."):
                final_report = orchestrator.reporter.report(highlights, st.session_state["profile"])
            
            if final_report and final_report.get("markdown"):
                # Report container with better styling
                st.markdown("""
                <div style='background: #fefefe; border-radius: 8px; padding: 2rem; margin: 1rem 0; border: 1px solid #e5e7eb;'>
                """, unsafe_allow_html=True)
                st.markdown(final_report.get("markdown"))
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Save the report and complete the session
                if "session_id" in st.session_state:
                    # Save report to file
                    import tempfile
                    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md', dir='./report') as f:
                        f.write(final_report.get("markdown", ""))
                        report_path = f.name
                    
                    # Complete the session in database
                    history_db.complete_session(
                        session_id=st.session_state["session_id"],
                        success=True,
                        profile=st.session_state["profile"],
                        report_path=report_path,
                        artifacts_dir=orchestrator.artifacts_dir
                    )
                    
                    # Clear cache to refresh sidebar immediately
                    clear_sessions_cache()
            else:
                st.info("📝 No report generated.")
                # Complete session as unsuccessful if no report
                if "session_id" in st.session_state:
                    history_db.complete_session(
                        session_id=st.session_state["session_id"],
                        success=False,
                        profile=st.session_state.get("profile", {}),
                        error="No report generated"
                    )
                    clear_sessions_cache()
    except Exception as e:
        st.error(f"❌ Analysis Error: {str(e)}")
        
        # Complete session with error if it was started
        if "session_id" in st.session_state:
            history_db.complete_session(
                session_id=st.session_state["session_id"],
                success=False,
                profile=st.session_state.get("profile", {}),
                error=str(e)
            )
            clear_sessions_cache()
        
        # Provide more specific error guidance
        error_msg = str(e).lower()
        if "lower" in error_msg or "upper" in error_msg:
            st.warning("🔧 **Data Type Issue**: There seems to be a problem with data types in the analysis plan. This has been fixed - please try again.")
        elif "csv" in error_msg or "parse" in error_msg:
            st.info("💡 **CSV Format**: Please ensure your file is a valid CSV format with proper headers.")
        elif "api" in error_msg or "key" in error_msg:
            st.info("🔑 **API Key**: Please check that your DeepSeek API key is valid and has sufficient credits.")
        else:
            st.info("💡 **General Error**: Please try uploading your file again or contact support if the issue persists.")
        
        # Show error details in expander for debugging
        with st.expander("🔍 Error Details (for debugging)", expanded=False):
            st.code(str(e))
            import traceback
            st.code(traceback.format_exc())
else:
    # Welcome state with improved styling
    st.markdown("## 🚀 Welcome to Automated EDA")
    st.markdown("""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                color: white; padding: 2rem; border-radius: 12px; margin: 2rem 0; text-align: center;'>
        <h3 style='margin: 0 0 1rem 0; color: white;'>🎯 Get Started in 3 Simple Steps</h3>
        <div style='display: flex; justify-content: space-around; align-items: center; flex-wrap: wrap;'>
            <div style='text-align: center; margin: 1rem;'>
                <div style='font-size: 2rem; margin-bottom: 0.5rem;'>📁</div>
                <div style='font-weight: 600;'>Upload CSV</div>
                <div style='font-size: 0.9rem; opacity: 0.9;'>Choose your dataset</div>
            </div>
            <div style='font-size: 1.5rem; color: rgba(255,255,255,0.7);'>→</div>
            <div style='text-align: center; margin: 1rem;'>
                <div style='font-size: 2rem; margin-bottom: 0.5rem;'>🎯</div>
                <div style='font-weight: 600;'>Set Goal</div>
                <div style='font-size: 0.9rem; opacity: 0.9;'>Define your analysis</div>
            </div>
            <div style='font-size: 1.5rem; color: rgba(255,255,255,0.7);'>→</div>
            <div style='text-align: center; margin: 1rem;'>
                <div style='font-size: 2rem; margin-bottom: 0.5rem;'>🚀</div>
                <div style='font-weight: 600;'>Run Analysis</div>
                <div style='font-size: 0.9rem; opacity: 0.9;'>Get insights automatically</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Feature highlights
    feature_col1, feature_col2, feature_col3 = st.columns(3)
    
    with feature_col1:
        st.markdown("""
        <div style='background: #f0f9ff; padding: 1.5rem; border-radius: 8px; text-align: center; border-left: 4px solid #0ea5e9;'>
            <div style='font-size: 2rem; margin-bottom: 1rem;'>🤖</div>
            <h4 style='color: #0c4a6e; margin: 0.5rem 0;'>AI-Powered</h4>
            <p style='color: #075985; margin: 0; font-size: 0.9rem;'>Advanced algorithms analyze your data and generate insights automatically</p>
        </div>
        """, unsafe_allow_html=True)
    
    with feature_col2:
        st.markdown("""
        <div style='background: #f0fdf4; padding: 1.5rem; border-radius: 8px; text-align: center; border-left: 4px solid #22c55e;'>
            <div style='font-size: 2rem; margin-bottom: 1rem;'>📊</div>
            <h4 style='color: #14532d; margin: 0.5rem 0;'>Smart Visualizations</h4>
            <p style='color: #166534; margin: 0; font-size: 0.9rem;'>Automatically generates relevant charts and plots based on your data</p>
        </div>
        """, unsafe_allow_html=True)
    
    with feature_col3:
        st.markdown("""
        <div style='background: #fefce8; padding: 1.5rem; border-radius: 8px; text-align: center; border-left: 4px solid #eab308;'>
            <div style='font-size: 2rem; margin-bottom: 1rem;'>📝</div>
            <h4 style='color: #713f12; margin: 0.5rem 0;'>Detailed Reports</h4>
            <p style='color: #a16207; margin: 0; font-size: 0.9rem;'>Comprehensive analysis reports with actionable insights</p>
        </div>
        """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)  # Close main-content div