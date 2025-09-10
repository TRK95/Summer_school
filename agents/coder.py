"""
Code Writer Agent - generates Python code for EDA visualizations
"""

import json
from typing import Dict, Any
from llm.deepseek_client import DeepSeekClient


class CodeWriterAgent:
    """Agent that writes Python code for EDA visualizations"""

    def __init__(self, llm_client: DeepSeekClient):
        self.llm_client = llm_client

    def write_code(
        self,
        item: Dict[str, Any],
        profile: Dict[str, Any],
        save_dir: str = "./artifacts",
    ) -> Dict[str, Any]:
        """
        Write Python code for a single EDA plan item

        Args:
            item: Single plan item from EDA plan
            profile: Data profile
            save_dir: Directory to save plots

        Returns:
            Code output with title, python code, expected outputs, and manifest schema
        """
        user_message = self._build_coder_prompt(item, profile, save_dir)

        try:
            response = self.llm_client.complete_with_system_prompt(user_message)
            return response
        except Exception as e:
            # Fallback to basic code if LLM fails
            return self._create_fallback_code(item, save_dir)

    def _build_coder_prompt(
        self, item: Dict[str, Any], profile: Dict[str, Any], save_dir: str
    ) -> str:
        """Build the coder prompt"""
        prompt = f"""
            {{
            "role": "coder",
            "step": "code",
            "item": {json.dumps(item, indent=2)},
            "profile": {json.dumps(profile, indent=2)},
            "constraints": {{
                "save_dir": "{save_dir}",
                "rules": [
                "No seaborn", "Label axes and titles", "Handle missing values",
                "Use df already loaded", "Save PNG under save_dir; do not call plt.show()"
                ]
            }},
            "output_contract": "Return {{\\"title\\",\\"python\\",\\"expected_outputs\\":[\\"...png\\"],\\"manifest_schema\\":{{...}}}}"
            }}

            Write Python code to create the requested visualization. The code should:
            1. Use matplotlib (not seaborn)
            2. Handle missing values appropriately
            3. Add proper labels and titles
            4. Save plots to {save_dir} directory
            5. Never call plt.show()
            6. Create a manifest object describing the chart

            Return JSON with title, python code, expected_outputs, and manifest_schema.
            """
        return prompt

    def _create_fallback_code(
        self, item: Dict[str, Any], save_dir: str
    ) -> Dict[str, Any]:
        """Create fallback code if LLM fails"""
        item_id = item.get("id", "unknown")
        goal = item.get("goal", "Visualization")
        columns = item.get("columns", [])
        plots = item.get("plots", ["histogram"])

        # Generate basic code based on plot type
        if "histogram" in plots and columns:
            col = columns[0]
            python_code = f"""
                import matplotlib.pyplot as plt
                import numpy as np

                # Create histogram
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.hist(df['{col}'].dropna(), bins=50, alpha=0.7, edgecolor='black')
                ax.set_xlabel('{col}')
                ax.set_ylabel('Frequency')
                ax.set_title('Distribution of {col}')
                plt.tight_layout()
                plt.savefig('{save_dir}/fig_{item_id}_1.png', dpi=300, bbox_inches='tight')
                plt.close()

                # Create manifest
                manifest = {{
                    "id": "{item_id}",
                    "charts": [
                        {{
                            "saved_path": "{save_dir}/fig_{item_id}_1.png",
                            "chart_type": "histogram",
                            "columns_used": ["{col}"],
                            "n_rows_plotted": len(df['{col}'].dropna()),
                            "axis": {{
                                "x": "{col}",
                                "y": "Frequency",
                                "log_x": False,
                                "log_y": False,
                                "x_ticks": 50,
                                "y_ticks": 0
                            }},
                            "encodings": {{
                                "hue": None,
                                "facet": None
                            }},
                            "params": {{
                                "bins": 50,
                                "clip_quantiles": [0.01, 0.99],
                                "rolling_window": None
                            }},
                            "notes": f"NA dropped: {{df['{col}'].isnull().sum() / len(df) * 100:.1f}}%"
                        }}
                    ]
                }}
                """
        elif "boxplot" in plots and columns:
            col = columns[0]
            python_code = f"""
                import matplotlib.pyplot as plt

                # Create boxplot
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.boxplot(df['{col}'].dropna())
                ax.set_ylabel('{col}')
                ax.set_title('Boxplot of {col}')
                plt.tight_layout()
                plt.savefig('{save_dir}/fig_{item_id}_1.png', dpi=300, bbox_inches='tight')
                plt.close()

                # Create manifest
                manifest = {{
                    "id": "{item_id}",
                    "charts": [
                        {{
                            "saved_path": "{save_dir}/fig_{item_id}_1.png",
                            "chart_type": "box",
                            "columns_used": ["{col}"],
                            "n_rows_plotted": len(df['{col}'].dropna()),
                            "axis": {{
                                "x": "Box",
                                "y": "{col}",
                                "log_x": False,
                                "log_y": False,
                                "x_ticks": 1,
                                "y_ticks": 0
                            }},
                            "encodings": {{
                                "hue": None,
                                "facet": None
                            }},
                            "params": {{
                                "bins": None,
                                "clip_quantiles": [0.01, 0.99],
                                "rolling_window": None
                            }},
                            "notes": f"NA dropped: {{df['{col}'].isnull().sum() / len(df) * 100:.1f}}%"
                        }}
                    ]
                }}
                """
        else:
            # Default to bar plot
            col = columns[0] if columns else "unknown"
            python_code = f"""
                import matplotlib.pyplot as plt

                # Create bar plot
                fig, ax = plt.subplots(figsize=(10, 6))
                value_counts = df['{col}'].value_counts().head(10)
                ax.bar(range(len(value_counts)), value_counts.values)
                ax.set_xlabel('{col}')
                ax.set_ylabel('Count')
                ax.set_title('Top 10 values in {col}')
                ax.set_xticks(range(len(value_counts)))
                ax.set_xticklabels(value_counts.index, rotation=45)
                plt.tight_layout()
                plt.savefig('{save_dir}/fig_{item_id}_1.png', dpi=300, bbox_inches='tight')
                plt.close()

                # Create manifest
                manifest = {{
                    "id": "{item_id}",
                    "charts": [
                        {{
                            "saved_path": "{save_dir}/fig_{item_id}_1.png",
                            "chart_type": "bar",
                            "columns_used": ["{col}"],
                            "n_rows_plotted": len(df['{col}'].dropna()),
                            "axis": {{
                                "x": "{col}",
                                "y": "Count",
                                "log_x": False,
                                "log_y": False,
                                "x_ticks": len(value_counts),
                                "y_ticks": 0
                            }},
                            "encodings": {{
                                "hue": None,
                                "facet": None
                            }},
                            "params": {{
                                "bins": None,
                                "clip_quantiles": [0.01, 0.99],
                                "rolling_window": None
                            }},
                            "notes": f"NA dropped: {{df['{col}'].isnull().sum() / len(df) * 100:.1f}}%"
                        }}
                    ]
                }}
                """

        return {
            "title": goal,
            "python": python_code,
            "expected_outputs": [f"{save_dir}/fig_{item_id}_1.png"],
            "manifest_schema": {
                "id": item_id,
                "charts": [
                    {
                        "saved_path": f"{save_dir}/fig_{item_id}_1.png",
                        "chart_type": plots[0] if plots else "bar",
                        "columns_used": columns,
                        "n_rows_plotted": 0,
                        "axis": {
                            "x": columns[0] if columns else "x",
                            "y": "y",
                            "log_x": False,
                            "log_y": False,
                            "x_ticks": 0,
                            "y_ticks": 0,
                        },
                        "encodings": {"hue": None, "facet": None},
                        "params": {
                            "bins": 50,
                            "clip_quantiles": [0.01, 0.99],
                            "rolling_window": None,
                        },
                        "notes": "Generated by fallback code",
                    }
                ],
            },
        }
