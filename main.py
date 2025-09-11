"""
Main orchestrator for Automated EDA & Visualization by Multi-Agent Chat
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llm.deepseek_client import DeepSeekClient
from agents import PlannerAgent, CodeWriterAgent, CriticAgent, ReporterAgent
from runtime.profiler import CSVProfiler
from runtime.executor import SandboxExecutor
from runtime.history_db import HistoryDB


class EDAOrchestrator:
    """Main orchestrator that coordinates all agents for EDA analysis"""

    def __init__(
        self, api_key: Optional[str] = None, artifacts_dir: str = "./artifacts"
    ):
        self.artifacts_dir = artifacts_dir
        self.logs_dir = "./logs"
        self.report_dir = "./report"

        # Ensure directories exist
        os.makedirs(self.artifacts_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)
        os.makedirs(self.report_dir, exist_ok=True)

        # Initialize components
        self.llm_client = DeepSeekClient(api_key)
        self.profiler = CSVProfiler()
        self.executor = SandboxExecutor(artifacts_dir)
        self.history_db = HistoryDB(os.path.join(self.logs_dir, "history.db"))

        # Initialize agents
        self.planner = PlannerAgent(self.llm_client)
        self.coder = CodeWriterAgent(self.llm_client)
        self.critic = CriticAgent(self.llm_client)
        self.reporter = ReporterAgent(self.llm_client)

        # Execution log
        self.execution_log = {
            "timestamp": datetime.now().isoformat(),
            "profile": {},
            "eda_plan": [],
            "exec_results": [],
            "final_report": {},
        }

    def run_eda(
        self, csv_path: str, user_goal: str = "General EDA", max_items: int = 8
    ) -> Dict[str, Any]:
        """
        Run complete EDA analysis pipeline

        Args:
            csv_path: Path to CSV file
            user_goal: User's analysis goal
            max_items: Maximum number of EDA items

        Returns:
            Complete execution results
        """
        print(f"🚀 Starting EDA analysis for: {csv_path}")
        print(f"📊 User goal: {user_goal}")

        try:
            # Start a new session in history DB
            session_id = self.history_db.start_session(csv_path, user_goal, max_items)
            
            # Prepare per-run log directory
            run_ts = datetime.now().strftime('%Y%m%d-%H%M%S')
            run_dir = os.path.join(self.logs_dir, f"run-{run_ts}")
            os.makedirs(run_dir, exist_ok=True)
            # Step 1: Profile the data
            print("\n📋 Step 1: Profiling data...")
            profile = self.profiler.profile(csv_path)
            self.execution_log["profile"] = profile
            print(f"✅ Profiled {profile['rows_total']} rows, {len(profile['columns'])} columns")

            # Save profile
            with open(os.path.join(run_dir, "profile.json"), 'w') as f:
                json.dump(profile, f, indent=2)
            
            # Step 2: Load data for execution
            print("\n📂 Step 2: Loading data...")
            df = pd.read_csv(csv_path)
            print(f"✅ Loaded DataFrame: {df.shape}")

            # Step 3: Plan EDA
            print("\n🎯 Step 3: Planning EDA...")
            # Provide a small random sample of rows to the planner for better grounding
            try:
                sample_rows = df.sample(n=min(8, len(df)), random_state=42).to_dict(orient='records')
            except Exception:
                sample_rows = []
            eda_plan_resp = self.planner.plan(profile, user_goal, max_items, data_samples=sample_rows)
            self.execution_log["eda_plan"] = eda_plan_resp.get("eda_plan", [])
            print(f"✅ Created plan with {len(self.execution_log['eda_plan'])} items")

            # Save planner output and prompt
            with open(os.path.join(run_dir, "plan.json"), 'w') as f:
                json.dump(eda_plan_resp, f, indent=2)
            if eda_plan_resp.get("prompt"):
                with open(os.path.join(run_dir, "planner_prompt.txt"), 'w') as f:
                    f.write(eda_plan_resp["prompt"])
            
            # NEW: Ask for user approval before proceeding
            while True:
                print("\n🛑 Review the proposed EDA plan:")
                for i, item in enumerate(self.execution_log["eda_plan"], 1):
                    print(f"  {i}. id={item.get('id')} priority={item.get('priority')} goal={item.get('goal')} plots={','.join(item.get('plots', []))} columns={','.join(item.get('columns', []))}")
                approve = input("\nDo you approve this plan? (y/n): ").strip().lower()
                if approve in ("y", "yes"):
                    # Save approved plan version
                    self.history_db.save_plan_version(
                        session_id, 
                        version_number=1, 
                        plan_items=self.execution_log["eda_plan"],
                        approved=True
                    )
                    break
                # gather feedback and regenerate
                reasons = input("Please describe what to change (e.g., add/remove items, change plots, priorities, columns): ").strip()
                if not reasons:
                    print("No feedback provided. Keeping the existing plan. Proceeding...")
                    # Save current plan as approved
                    self.history_db.save_plan_version(
                        session_id,
                        version_number=1,
                        plan_items=self.execution_log["eda_plan"],
                        approved=True
                    )
                    break
                print("\n🔄 Regenerating plan based on your feedback...")
                eda_plan_resp = self.planner.plan(profile, user_goal, max_items, data_samples=sample_rows, user_feedback=reasons)
                self.execution_log["eda_plan"] = eda_plan_resp.get("eda_plan", [])
                # Save the new plan version
                self.history_db.save_plan_version(
                    session_id,
                    version_number=len(self.execution_log.get("plan_versions", [])) + 1,
                    plan_items=self.execution_log["eda_plan"],
                    user_feedback=reasons
                )
                with open(os.path.join(run_dir, "plan.json"), 'w') as f:
                    json.dump(eda_plan_resp, f, indent=2)
                if eda_plan_resp.get("prompt"):
                    with open(os.path.join(run_dir, "planner_prompt.txt"), 'w') as f:
                        f.write(eda_plan_resp["prompt"])

            # Step 4: Execute each plan item
            print("\n🔧 Step 4: Executing analysis...")
            highlights = []

            for i, item in enumerate(self.execution_log["eda_plan"], 1):
                print(
                    f"  📊 Processing item {i}/{len(self.execution_log['eda_plan'])}: {item.get('id', 'unknown')}"
                )

                # Generate code
                code_output = self.coder.write_code(item, profile, self.artifacts_dir)
                # Save code writer output
                item_id = item.get('id', f'item_{i}')
                with open(os.path.join(run_dir, f"code_{item_id}.json"), 'w') as f:
                    json.dump(code_output, f, indent=2)
                
                # Execute code
                exec_result = self.executor.execute(
                    code_output["python"], df, code_output["manifest_schema"]
                )
                # Save executor result
                with open(os.path.join(run_dir, f"exec_{item_id}.json"), 'w') as f:
                    json.dump(exec_result, f, indent=2)
                
                # Critique and potentially fix
                critique_result = self.critic.critique(code_output, exec_result)
                # Save critic output
                with open(os.path.join(run_dir, f"critic_{item_id}.json"), 'w') as f:
                    json.dump(critique_result, f, indent=2)
                
                # If fix needed, try again
                if critique_result["status"] == "fix" and critique_result.get(
                    "fix_patch"
                ):
                    print(f"    🔧 Applying fix...")
                    fixed_code = code_output["python"] + "\n" + critique_result["fix_patch"]
                    exec_result = self.executor.execute(fixed_code, df, code_output["manifest_schema"])
                    # Save post-fix executor result
                    with open(os.path.join(run_dir, f"exec_{item_id}_after_fix.json"), 'w') as f:
                        json.dump(exec_result, f, indent=2)
                
                # Store results
                exec_summary = {
                    "item": item,
                    "code_output": code_output,
                    "exec_result": exec_result,
                    "critique_result": critique_result,
                }
                self.execution_log["exec_results"].append(exec_summary)
                
                # Save execution result to history DB
                self.history_db.save_execution_result(
                    session_id=session_id,
                    item_id=item.get('id', f'item_{i}'),
                    code_output=code_output,
                    exec_result=exec_result,
                    critique_result=critique_result,
                    success=exec_result.get("exec_ok", False),
                    retry_count=retry_count,
                    error=exec_result.get("error")
                )

                # Create highlight for reporter
                # Try to execute the code with retries if needed
                max_retries = 3
                retry_count = 0
                success = False

                while retry_count < max_retries and not success:
                    if retry_count > 0:
                        print(f"    🔄 Retry attempt {retry_count}/{max_retries}...")

                    if exec_result["exec_ok"]:
                        highlight = {
                            "title": code_output["title"],
                            "artifacts": code_output["expected_outputs"],
                            "manifest": exec_result["manifest"],
                            "evidence": exec_result["evidence"],
                            "notes": exec_result["stdout"]
                            or "Analysis completed successfully",
                        }
                        highlights.append(highlight)
                        print(
                            f"    ✅ Success: {len(code_output['expected_outputs'])} plots generated"
                        )
                        success = True
                    else:
                        error_msg = exec_result.get('error', 'Unknown error')
                        print(f"    ⚠️ Failed: {error_msg}")
                        
                        # Check if it's an indentation error
                        if "IndentationError" in error_msg or "unexpected indent" in error_msg:
                            try:
                                import autopep8
                                print(f"    🔧 Attempting to fix indentation with autopep8...")
                                # Fix indentation using autopep8
                                fixed_code = autopep8.fix_code(code_output["python"])
                                # Try executing the fixed code
                                exec_result = self.executor.execute(
                                    fixed_code, df, code_output["manifest_schema"]
                                )
                                retry_count += 1
                                continue
                            except Exception as e:
                                print(f"    ❌ Autopep8 fix failed: {str(e)}")
                        
                        # For non-indentation errors, use the critic
                        critique_result = self.critic.critique(code_output, exec_result)
                        
                        if critique_result["status"] == "fix":
                            print(f"    🔧 Generating new code based on critic's feedback...")
                            # Get new code from CodeWriter with critic's feedback
                            item["critic_feedback"] = critique_result["notes"]  # Add critic's feedback to help generate better code
                            code_output = self.coder.write_code(item, profile, self.artifacts_dir)
                            exec_result = self.executor.execute(
                                code_output["python"], df, code_output["manifest_schema"]
                            )
                            retry_count += 1
                        else:
                            print(f"    ❌ Critic could not determine how to fix")
                            break

                if not success:
                    print(f"    ❌ Failed after {retry_count} retries")

            # Step 5: Generate final report
            print("\n📝 Step 5: Generating report...")
            # Save highlights for reporter
            with open(os.path.join(run_dir, "highlights.json"), 'w') as f:
                json.dump(highlights, f, indent=2)

            final_report = self.reporter.report(highlights, profile)
            self.execution_log["final_report"] = final_report
            # Save reporter output
            with open(os.path.join(run_dir, "reporter_output.json"), 'w') as f:
                json.dump(final_report, f, indent=2)
            
            # Save report
            report_path = os.path.join(self.report_dir, "report.md")
            with open(report_path, "w") as f:
                f.write(final_report["markdown"])
            print(f"✅ Report saved to: {report_path}")

            # Save execution log
            log_path = os.path.join(self.logs_dir, "last_run.json")
            with open(log_path, "w") as f:
                json.dump(self.execution_log, f, indent=2)
            print(f"✅ Execution log saved to: {log_path}")
            # Also save a copy into the per-run directory
            with open(os.path.join(run_dir, "execution_log.json"), 'w') as f:
                json.dump(self.execution_log, f, indent=2)
            
            # Summary
            print(f"\n🎉 EDA Analysis Complete!")
            print(f"📊 Generated {len(highlights)} successful analyses")
            print(f"🖼️  Plots saved to: {self.artifacts_dir}")
            print(f"📝 Report: {report_path}")
            print(f"📋 Log: {log_path}")

            # Update session with completion details
            self.history_db.complete_session(
                session_id=session_id,
                success=True,
                profile=profile,
                report_path=report_path,
                artifacts_dir=self.artifacts_dir
            )
            
            return {
                "success": True,
                "profile": profile,
                "highlights": highlights,
                "report": final_report,
                "artifacts_dir": self.artifacts_dir,
                "report_path": report_path,
                "log_path": log_path,
                "session_id": session_id
            }

        except Exception as e:
            error_msg = f"EDA analysis failed: {str(e)}"
            print(f"❌ {error_msg}")

            # Save error log
            error_log = {
                "timestamp": datetime.now().isoformat(),
                "error": error_msg,
                "execution_log": self.execution_log,
            }
            error_path = os.path.join(self.logs_dir, "error_run.json")
            with open(error_path, "w") as f:
                json.dump(error_log, f, indent=2)

            # Update session with error details
            if 'session_id' in locals():
                self.history_db.complete_session(
                    session_id=session_id,
                    success=False,
                    profile={},
                    error=error_msg
                )

            return {
                "success": False, 
                "error": error_msg, 
                "error_log_path": error_path,
                "session_id": session_id if 'session_id' in locals() else None
            }


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Automated EDA & Visualization by Multi-Agent Chat"
    )
    parser.add_argument("csv_path", help="Path to CSV file")
    parser.add_argument("--goal", default="General EDA", help="Analysis goal")
    parser.add_argument("--max-items", type=int, default=8, help="Maximum EDA items")
    parser.add_argument(
        "--api-key", help="DeepSeek API key (or set DEEPSEEK_API_KEY env var)"
    )

    args = parser.parse_args()

    # Check if CSV exists
    if not os.path.exists(args.csv_path):
        print(f"❌ CSV file not found: {args.csv_path}")
        sys.exit(1)

    # Initialize orchestrator
    orchestrator = EDAOrchestrator(api_key=args.api_key)

    # Run EDA
    result = orchestrator.run_eda(args.csv_path, args.goal, args.max_items)

    if result["success"]:
        print("\n🎯 Next Questions:")
        for question in result["report"]["next_questions"]:
            print(f"  • {question}")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
