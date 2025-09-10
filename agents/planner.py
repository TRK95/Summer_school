"""
EDA Planner Agent - converts profile + user goal into prioritized EDA plan
"""

import json
from typing import Dict, Any, List, Optional
from llm.deepseek_client import DeepSeekClient


class PlannerAgent:
    """Agent that creates EDA plans based on data profile and user goals"""

    def __init__(self, llm_client: DeepSeekClient):
        self.llm_client = llm_client

    def plan(
        self,
        profile: Dict[str, Any],
        user_goal: str = "General EDA",
        max_items: int = 8,
        data_samples: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Create an EDA plan based on profile and user goal

        Args:
            profile: Data profile from profiler
            user_goal: User's specific goal or "General EDA"
            max_items: Maximum number of plan items
            data_samples: Optional list of data samples for context

        Returns:
            EDA plan dictionary
        """
        user_message = self._build_planner_prompt(profile, user_goal, max_items, data_samples)

        try:
            response = self.llm_client.complete_with_system_prompt(user_message)
            return response
        except Exception as e:
            # Fallback to basic plan if LLM fails
            return self._create_fallback_plan(profile, max_items)

    def _build_planner_prompt(
        self, profile: Dict[str, Any], user_goal: str, max_items: int, data_samples: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Build the planner prompt"""
        # Include up to 8 sample rows to give the planner concrete context
        samples_json = json.dumps((data_samples or [])[:8], indent=2)
        prompt = f"""
            {{
            "role": "planner",
            "step": "plan",
            "profile": {json.dumps(profile, indent=2)},
            "samples": {samples_json},
            "user_goal": "{user_goal}",
            "constraints": {{"max_items": {max_items}}},
            "output_contract": "Return {{\\"eda_plan\\":[{{id,goal,plots,priority,columns,notes}}]}}",
            "available_plot_types": {json.dumps(plot_types)}
            }}
            
            Based on the profile above, create a prioritized EDA plan. Focus on:
            1. Data quality issues (missing values, outliers)
            2. Distribution analysis for numeric columns
            3. Categorical analysis for non-numeric columns
            4. Relationships between variables
            5. Time series patterns if applicable
            6. Anomaly detection and unusual patterns
            7. Segmentation opportunities in the data
            8. Multivariate relationships and interaction effects
            9. Potential biases or imbalances in representation

            Guidance on visualization diversity:
            - Use a variety of plot types to avoid redundancy.
            - Histograms/boxplots → distributions and outliers
            - Bar charts → categorical frequencies and comparisons
            - Scatter plots → relationships between numeric variables
            - Line plots → time or ordered data
            - Heatmaps → correlations or matrix-style comparisons
            - Combine multiple plot types when appropriate for deeper insights.

            Available plot types: {", ".join(plot_types)}

            
            Return a JSON object with an "eda_plan" array containing plan items.
            Each item should have: id, goal, plots, priority (1=highest), columns, notes.
            """
        return prompt

    def _create_fallback_plan(
        self, profile: Dict[str, Any], max_items: int
    ) -> Dict[str, Any]:
        """Create a basic fallback plan if LLM fails"""
        plan_items = []
        priority = 1

        columns = profile.get("columns", [])

        # Basic data overview
        if columns:
            plan_items.append(
                {
                    "id": "data_overview",
                    "goal": "Basic data overview and missing values",
                    "plots": ["bar"],
                    "priority": priority,
                    "columns": [col["name"] for col in columns[:5]],  # First 5 columns
                    "notes": "Check data completeness and basic structure",
                }
            )
            priority += 1

        # Numeric distributions
        numeric_cols = [col["name"] for col in columns if col.get("numeric")]
        if numeric_cols:
            for col in numeric_cols[:3]:  # First 3 numeric columns
                plan_items.append(
                    {
                        "id": f"dist_{col}",
                        "goal": f"Distribution analysis for {col}",
                        "plots": ["histogram", "boxplot"],
                        "priority": priority,
                        "columns": [col],
                        "notes": "Check for skewness and outliers",
                    }
                )
                priority += 1

        # Categorical analysis
        categorical_cols = [
            col["name"]
            for col in columns
            if not col.get("numeric") and col.get("top_values")
        ]
        if categorical_cols:
            for col in categorical_cols[:2]:  # First 2 categorical columns
                plan_items.append(
                    {
                        "id": f"cat_{col}",
                        "goal": f"Categorical analysis for {col}",
                        "plots": ["bar"],
                        "priority": priority,
                        "columns": [col],
                        "notes": "Check value distribution and cardinality",
                    }
                )
                priority += 1

        # Relationships
        if len(numeric_cols) >= 2:
            plan_items.append(
                {
                    "id": "correlations",
                    "goal": "Correlation analysis between numeric variables",
                    "plots": ["heatmap"],
                    "priority": priority,
                    "columns": numeric_cols[:5],  # First 5 numeric columns
                    "notes": "Identify strong correlations",
                }
            )

        return {"eda_plan": plan_items[:max_items]}
