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
            # Step 1: Profile the data
            print("\n📋 Step 1: Profiling data...")
            profile = self.profiler.profile(csv_path)
            self.execution_log["profile"] = profile
            print(
                f"✅ Profiled {profile['rows_total']} rows, {len(profile['columns'])} columns"
            )

            # Step 2: Load data for execution
            print("\n📂 Step 2: Loading data...")
            df = pd.read_csv(csv_path)
            print(f"✅ Loaded DataFrame: {df.shape}")

            # Step 3: Plan EDA
            print("\n🎯 Step 3: Planning EDA...")
            eda_plan = self.planner.plan(profile, user_goal, max_items)
            self.execution_log["eda_plan"] = eda_plan.get("eda_plan", [])
            print(f"✅ Created plan with {len(self.execution_log['eda_plan'])} items")

            # Step 4: Execute each plan item
            print("\n🔧 Step 4: Executing analysis...")
            highlights = []

            for i, item in enumerate(self.execution_log["eda_plan"], 1):
                print(
                    f"  📊 Processing item {i}/{len(self.execution_log['eda_plan'])}: {item.get('id', 'unknown')}"
                )

                # Generate code
                code_output = self.coder.write_code(item, profile, self.artifacts_dir)

                # Execute code
                exec_result = self.executor.execute(
                    code_output["python"], df, code_output["manifest_schema"]
                )

                # Critique and potentially fix
                critique_result = self.critic.critique(code_output, exec_result)

                # If fix needed, try again
                if critique_result["status"] == "fix" and critique_result.get(
                    "fix_patch"
                ):
                    print(f"    🔧 Applying fix...")
                    fixed_code = (
                        code_output["python"] + "\n" + critique_result["fix_patch"]
                    )
                    exec_result = self.executor.execute(
                        fixed_code, df, code_output["manifest_schema"]
                    )

                # Store results
                exec_summary = {
                    "item": item,
                    "code_output": code_output,
                    "exec_result": exec_result,
                    "critique_result": critique_result,
                }
                self.execution_log["exec_results"].append(exec_summary)

                # Create highlight for reporter
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
                else:
                    print(f"    ❌ Failed: {exec_result.get('error', 'Unknown error')}")

            # Step 5: Generate final report
            print("\n📝 Step 5: Generating report...")
            final_report = self.reporter.report(highlights, profile)
            self.execution_log["final_report"] = final_report

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

            # Summary
            print(f"\n🎉 EDA Analysis Complete!")
            print(f"📊 Generated {len(highlights)} successful analyses")
            print(f"🖼️  Plots saved to: {self.artifacts_dir}")
            print(f"📝 Report: {report_path}")
            print(f"📋 Log: {log_path}")

            return {
                "success": True,
                "profile": profile,
                "highlights": highlights,
                "report": final_report,
                "artifacts_dir": self.artifacts_dir,
                "report_path": report_path,
                "log_path": log_path,
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

            return {"success": False, "error": error_msg, "error_log_path": error_path}


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
