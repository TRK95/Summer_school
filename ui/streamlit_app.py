import os
import io
import json
import sys
import pandas as pd
import streamlit as st

# Ensure project root is on path so we can import main.py
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from main import EDAOrchestrator


st.set_page_config(page_title="Automated EDA", layout="wide")
st.title("🤖 Automated EDA & Visualization")
st.caption("Upload a CSV, set a goal, and let the agents do the rest.")

with st.sidebar:
    st.header("Settings")
    goal = st.text_input("Analysis goal", value="General EDA")
    max_items = st.slider("Max plan items", min_value=3, max_value=12, value=8)
    api_key = st.text_input("DeepSeek API Key", value=os.getenv("DEEPSEEK_API_KEY", ""), type="password")
    run_button = st.button("Run Analysis", type="primary")

uploaded_file = st.file_uploader("Upload CSV file", type=["csv"]) 

if uploaded_file is not None:
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


