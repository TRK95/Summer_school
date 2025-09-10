"""
Reporter Agent - generates final markdown report
"""

import json
from typing import Dict, Any, List
from llm.deepseek_client import DeepSeekClient


class ReporterAgent:
    """Agent that generates final markdown reports"""

    def __init__(self, llm_client: DeepSeekClient):
        self.llm_client = llm_client

    def report(
        self, highlights: List[Dict[str, Any]], profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate final markdown report

        Args:
            highlights: List of analysis highlights with artifacts and evidence
            profile: Original data profile

        Returns:
            Report with markdown content and next questions
        """
        user_message = self._build_reporter_prompt(highlights, profile)

        try:
            response = self.llm_client.complete_with_system_prompt(user_message)
            return response
        except Exception as e:
            # Fallback to basic report if LLM fails
            return self._create_fallback_report(highlights, profile)

    def _build_reporter_prompt(
        self, highlights: List[Dict[str, Any]], profile: Dict[str, Any]
    ) -> str:
        """Build the reporter prompt"""
        prompt = f"""
            {{
            "role": "reporter",
            "step": "report",
            "inputs": {{
                "highlights": {json.dumps(highlights, indent=2)},
                "profile": {json.dumps(profile, indent=2)}
            }},
            "output_contract": "Return {{\\"markdown\\":\\"...\\",\\"next_questions\\":[\\"...\\"]}}"
            }}

            Generate a comprehensive EDA report in markdown format. Include:
            1. Executive summary of key findings
            2. Data quality assessment
            3. Distribution analysis results
            4. Relationship insights
            5. Figure references (use only filenames, not full paths)
            6. Next questions for further analysis

            Focus on actionable insights and patterns discovered in the data.
            Reference figures using only the filename (e.g., "fig_q1_1.png").

            Return JSON with markdown content and next_questions array.
            """
        return prompt

    def _create_fallback_report(
        self, highlights: List[Dict[str, Any]], profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create fallback report if LLM fails"""
        markdown_parts = []

        # Header
        markdown_parts.append("# EDA Analysis Report")
        markdown_parts.append("")

        # Data overview
        rows_total = profile.get("rows_total", 0)
        columns = profile.get("columns", [])
        markdown_parts.append("## Data Overview")
        markdown_parts.append(f"- **Total Rows**: {rows_total:,}")
        markdown_parts.append(f"- **Total Columns**: {len(columns)}")
        markdown_parts.append("")

        # Column summary
        if columns:
            markdown_parts.append("### Column Summary")
            for col in columns[:10]:  # First 10 columns
                name = col.get("name", "Unknown")
                dtype = col.get("dtype", "Unknown")
                missing = col.get("missing", 0)
                missing_pct = (missing / rows_total * 100) if rows_total > 0 else 0
                markdown_parts.append(
                    f"- **{name}**: {dtype} ({missing_pct:.1f}% missing)"
                )
            markdown_parts.append("")

        # Analysis highlights
        if highlights:
            markdown_parts.append("## Analysis Results")
            for i, highlight in enumerate(highlights, 1):
                title = highlight.get("title", f"Analysis {i}")
                artifacts = highlight.get("artifacts", [])
                notes = highlight.get("notes", "")

                markdown_parts.append(f"### {title}")
                if notes:
                    markdown_parts.append(notes)

                if artifacts:
                    markdown_parts.append("**Generated Figures:**")
                    for artifact in artifacts:
                        filename = artifact.split("/")[-1]  # Extract filename only
                        markdown_parts.append(f"- {filename}")
                markdown_parts.append("")

        # Next questions
        next_questions = [
            "What are the strongest correlations between variables?",
            "Are there any temporal patterns in the data?",
            "What are the main outliers and their potential causes?",
            "How do categorical variables interact with numeric ones?",
            "What additional features could be engineered from existing data?",
        ]

        markdown_parts.append("## Next Questions")
        for question in next_questions:
            markdown_parts.append(f"- {question}")

        return {"markdown": "\n".join(markdown_parts), "next_questions": next_questions}
