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

def format_timestamp(ts):
    """Format timestamp for display"""
    return datetime.fromisoformat(ts).strftime("%Y-%m-%d %H:%M")


# Configure the page with custom CSS
st.set_page_config(page_title="Automated EDA", layout="wide")

# Custom CSS for ChatGPT-like interface
st.markdown("""
<style>
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #202123;
    }
    
    /* History item styling */
    .history-item {
        padding: 12px;
        border-radius: 5px;
        margin: 4px 0;
        cursor: pointer;
        transition: background-color 0.3s;
    }
    .history-item:hover {
        background-color: #2A2B32;
    }
    .history-item.selected {
        background-color: #343541;
    }
    
    /* Dataset group styling */
    .dataset-group {
        margin: 10px 0;
        padding: 5px;
        border-top: 1px solid #444654;
    }
    
    /* Main content area styling */
    .main-content {
        background-color: #343541;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    
    /* Button styling */
    .stButton>button {
        background-color: #444654;
        color: white;
        border: none;
        border-radius: 5px;
        width: 100%;
        text-align: left;
        padding: 10px;
    }
    .stButton>button:hover {
        background-color: #2A2B32;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "viewing_session" not in st.session_state:
    st.session_state.viewing_session = None
if "selected_dataset" not in st.session_state:
    st.session_state.selected_dataset = None

# Get history database
history_db = get_history_db()

# Create sidebar for history
with st.sidebar:
    st.title("📚 Chat History")
    
    # Get recent sessions
    sessions = history_db.get_session_history(limit=50)  # Increased limit for more history
    
    # Group sessions by dataset
    datasets = {}
    for session in sessions:
        dataset_name = os.path.basename(session["csv_path"])
        if dataset_name not in datasets:
            datasets[dataset_name] = []
        datasets[dataset_name].append(session)
    
    # Display sessions grouped by dataset
    for dataset_name, dataset_sessions in datasets.items():
        st.markdown(f"<div class='dataset-group'>", unsafe_allow_html=True)
        st.markdown(f"### 📊 {dataset_name}")
        
        for session in sorted(dataset_sessions, key=lambda x: x['timestamp'], reverse=True):
            # Format the session entry
            timestamp = format_timestamp(session['timestamp'])
            success_icon = "✅" if session['success'] else "❌"
            goal_preview = session['user_goal'][:30] + "..." if len(session.get('user_goal', '')) > 30 else session.get('user_goal', '')
            
            # Create a styled button for each session
            button_style = "selected" if st.session_state.viewing_session == session["session_id"] else ""
            st.markdown(
                f"""<div class='history-item {button_style}'>""",
                unsafe_allow_html=True
            )
            if st.button(
                f"{success_icon} {timestamp}\n{goal_preview}",
                key=f"session_{session['session_id']}",
                help=f"Goal: {session.get('user_goal', 'N/A')}\nDataset: {dataset_name}",
            ):
                st.session_state.viewing_session = session["session_id"]
                st.session_state.selected_dataset = dataset_name
            st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

# Main content area
st.markdown("<div class='main-content'>", unsafe_allow_html=True)
st.title("🤖 Automated EDA & Visualization")
st.caption("Upload a CSV, set a goal, and let the agents do the rest.")

# Settings in a horizontal container at the top
settings_container = st.container()
with settings_container:
    col1, col2, col3, col4 = st.columns([2, 1, 2, 1])
    with col1:
        goal = st.text_input("Analysis goal", value="General EDA")
    with col2:
        max_items = st.slider("Max items", min_value=3, max_value=12, value=8)
    with col3:
        api_key = st.text_input("DeepSeek API Key", 
                              value=os.getenv("DEEPSEEK_API_KEY", ""), 
                              type="password")
    with col4:
        run_button = st.button("Run Analysis", type="primary")

uploaded_file = st.file_uploader("Upload CSV file", type=["csv"]) 

if st.session_state.viewing_session:
    # Display session details
    session = history_db.get_session_details(st.session_state.viewing_session)
    
    st.header(f"Session Details - {os.path.basename(session['csv_path'])}")
    st.text(f"Date: {format_timestamp(session['timestamp'])}")
    st.text(f"Goal: {session['goal']}")
    
    # Show plan versions in tabs
    if session['plan_versions']:
        st.subheader("Analysis Plans")
        plan_tabs = st.tabs([f"Version {p['version_number']}" for p in session['plan_versions']])
        for tab, plan in zip(plan_tabs, session['plan_versions']):
            with tab:
                if plan['approved']:
                    st.success("✅ This plan was approved")
                if plan['user_feedback']:
                    st.info(f"💬 Feedback: {plan['user_feedback']}")
                
                items = json.loads(plan['plan_items'])
                for item in items:
                    st.markdown(f"**Item {item['id']}**")
                    st.markdown(f"Goal: {item['goal']}")
                    st.markdown(f"Plots: {', '.join(item['plots'])}")
                    st.markdown(f"Columns: {', '.join(item['columns'])}")
                    if item.get('notes'):
                        st.markdown(f"Notes: {item['notes']}")
                    st.divider()
    
    # Show execution results
    if session['execution_results']:
        st.subheader("Execution Results")
        for result in session['execution_results']:
            with st.expander(f"Item {result['item_id']}", expanded=True):
                status = "✅ Success" if result['success'] else "❌ Failed"
                st.markdown(f"**Status**: {status}")
                
                # Show generated plots
                exec_result = json.loads(result['exec_result'])
                if exec_result.get('manifest', {}).get('charts'):
                    for chart in exec_result['manifest']['charts']:
                        if os.path.exists(chart['saved_path']):
                            st.image(chart['saved_path'], use_container_width=True)
                
                if result['retry_count'] > 0:
                    st.warning(f"Required {result['retry_count']} retries")
                if result['error']:
                    st.error(f"Error: {result['error']}")
    
    # Show final report if successful
    if session['success'] and session['report_path']:
        st.subheader("Final Report")
        try:
            with open(session['report_path'], 'r') as f:
                st.markdown(f.read())
        except Exception as e:
            st.error(f"Could not load report: {str(e)}")

elif uploaded_file is not None:
    try:
        # Read uploaded CSV into a temp path so orchestrator can read it again
        csv_bytes = uploaded_file.getvalue()
        df_preview = pd.read_csv(io.BytesIO(csv_bytes))
        st.subheader("Data preview")
        st.dataframe(df_preview.head(50))

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

        # Proceed if a run has been initiated
        if st.session_state.get("analysis_ready"):
            orchestrator = st.session_state["orchestrator"]

            # Step 1: Profile (cache)
            st.subheader("Step 1: Profile data")
            if "profile" not in st.session_state:
                with st.spinner("Profiling data..."):
                    profile = orchestrator.profiler.profile(st.session_state.get("tmp_csv_path", tmp_csv_path))
                st.session_state["profile"] = profile
            profile = st.session_state["profile"]
            st.success(f"Profiled {profile.get('rows_total', 0)} rows, {len(profile.get('columns', []))} columns")

            # Step 2: Load Data (cache)
            st.subheader("Step 2: Load data")
            if "df" not in st.session_state:
                with st.spinner("Loading data..."):
                    st.session_state["df"] = pd.read_csv(st.session_state.get("tmp_csv_path", tmp_csv_path))
            df = st.session_state["df"]
            st.success(f"Loaded DataFrame: {df.shape}")

            # Step 3: Planner (with approval gating and unlimited regenerations)
            st.subheader("Step 3: Planner - EDA Plan (Versions)")
            if "plan_versions" not in st.session_state:
                with st.spinner("Generating plan..."):
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
            # Render all versions
            approved_index = None
            for idx, version in enumerate(plan_versions):
                st.markdown(f"### {idx+1}. {version.get('label','Version')} Plan")
                items = version.get("items", [])
                if items:
                    for item in items:
                        item_id = item.get("id", "unknown")
                        goal_txt = item.get("goal", "")
                        priority = item.get("priority", "")
                        plots = ", ".join(item.get("plots", []))
                        columns = ", ".join(item.get("columns", []))
                        notes = item.get("notes", "")

                        st.markdown(f"**Item {item_id}**")
                        st.markdown(f"**Priority**: {priority}")
                        st.markdown(f"**Goal**: {goal_txt}")
                        st.markdown(f"**Plots**: {plots}")
                        st.markdown(f"**Columns**: {columns}")
                        st.markdown(f"**Notes**: {notes}")
                        st.divider()
                else:
                    st.info("Plan is empty.")
                if st.button("✅ Approve this plan", key=f"approve_plan_{idx}"):
                    approved_index = idx

            # Request changes form (below the latest rendered plan)
            with st.expander("Request changes (generate a new version)", expanded=True):
                feedback = st.text_area("Describe what to adjust for the next version", key="feedback_text")
                if st.button("✏️ Generate updated plan", key="request_changes"):
                    with st.spinner("Generating updated plan..."):
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
                    # Immediately rerun to render the new plan version without another click
                    st.rerun()

            if approved_index is None:
                st.info("Approve any plan version to proceed to execution.")
                st.stop()

            selected_plan_items = plan_versions[approved_index]["items"]

            # Step 4: Execute per item (show plots as they are produced)
            st.subheader("Step 4: Execute items and show plots")
            highlights = []
            for i, item in enumerate(selected_plan_items, 1):
                st.markdown(f"#### Item {item.get('id', f'item_{i}')} - Running")
                with st.spinner("Generating code and executing..."):
                    code_output = orchestrator.coder.write_code(item, st.session_state["profile"], orchestrator.artifacts_dir)
                    exec_result = orchestrator.executor.execute(
                        code_output["python"],
                        st.session_state["df"],
                        code_output["manifest_schema"]
                    )

                # Show plots for this item
                expected = code_output.get("expected_outputs", [])
                if expected:
                    cols = st.columns(3)
                    for j, out_path in enumerate(expected):
                        if os.path.exists(out_path):
                            with cols[j % 3]:
                                st.image(out_path, use_container_width=True, caption=f"Item {item.get('id', f'item_{i}')} - Plot {j+1}")
                else:
                    st.info("No expected outputs declared for this item.")

                # Collect highlight if execution succeeded
                if exec_result.get("exec_ok"):
                    highlight = {
                        "title": code_output.get("title", f"Item {item.get('id', f'item_{i}')}"),
                        "artifacts": expected,
                        "manifest": exec_result.get("manifest", {}),
                        "evidence": exec_result.get("evidence", {}),
                        "notes": exec_result.get("stdout") or "Analysis completed successfully",
                    }
                    highlights.append(highlight)
                    st.success("Execution succeeded")
                else:
                    st.error(exec_result.get("error", "Execution failed"))
                st.divider()

            # Step 5: Reporter
            st.subheader("Step 5: Report")
            with st.spinner("Generating report..."):
                final_report = orchestrator.reporter.report(highlights, st.session_state["profile"])
            if final_report and final_report.get("markdown"):
                st.markdown(final_report.get("markdown"))
            else:
                st.info("No report available.")
    except Exception as e:
        st.error(f"Failed to parse CSV: {e}")
else:
    st.info("Upload a CSV to get started.")


