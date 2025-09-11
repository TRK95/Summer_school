"""
Critic Agent - reviews code execution results and proposes fixes
"""

import json
from typing import Dict, Any
from llm.deepseek_client import DeepSeekClient


class CriticAgent:
    """Agent that critiques code execution results and proposes fixes"""

    def __init__(self, llm_client: DeepSeekClient):
        self.llm_client = llm_client

    def critique(
        self, code_output: Dict[str, Any], exec_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Critique code execution results and propose fixes if needed

        Args:
            code_output: Output from code writer
            exec_result: Result from executor

        Returns:
            Critique result with status, fix_patch, and notes
        """
        user_message = self._build_critic_prompt(code_output, exec_result)

        try:
            response = self.llm_client.complete_with_system_prompt(user_message)
            return response
        except Exception as e:
            # Fallback to basic critique if LLM fails
            return self._create_fallback_critique(exec_result)

    def _build_critic_prompt(
        self, code_output: Dict[str, Any], exec_result: Dict[str, Any]
    ) -> str:
        """Build the critic prompt"""
        prompt = f"""
            {{
            "role": "critic",
            "step": "critique",
            "code": {json.dumps(code_output, indent=2)},
            "exec_result": {json.dumps(exec_result, indent=2)},
            "output_contract": "Return {{\\"status\\":\\"ok|fix\\",\\"fix_patch\\":\\"<if any>\\",\\"notes\\":\\"...\\"}}"
            }}

            Review the code execution result. Check for:
            1. Missing or incorrect manifest information
            2. Poor visualization choices (e.g., high skew without log scale)
            3. Missing labels or titles

            If issues are found, provide a fix_patch with corrected code.
            If everything looks good, return status "ok".

            Return JSON with status, fix_patch (if needed), and notes explaining your decision.
            """
        return prompt

    def _create_fallback_critique(self, exec_result: Dict[str, Any]) -> Dict[str, Any]:
        """Create fallback critique if LLM fails"""
        exec_ok = exec_result.get("exec_ok", False)
        linter_flags = exec_result.get("linter_flags", [])

        if not exec_ok:
            return {
                "status": "fix",
                "fix_patch": "# Code execution failed - needs debugging",
                "notes": f"Execution error: {exec_result.get('error', 'Unknown error')}",
            }

        # Check for critical linter flags
        critical_flags = [flag for flag in linter_flags if flag.get("level") == "error"]
        if critical_flags:
            return {
                "status": "fix",
                "fix_patch": "# Critical linter errors detected",
                "notes": f"Critical issues: {[flag.get('msg') for flag in critical_flags]}",
            }

        # Check for high-priority warnings
        high_priority_warnings = [
            flag
            for flag in linter_flags
            if flag.get("code") in ["HIGH_SKEW_NO_LOG", "MISSING_LABELS", "EMPTY_PLOT"]
        ]

        if high_priority_warnings:
            return {
                "status": "fix",
                "fix_patch": "# High priority warnings detected",
                "notes": f"Warnings to address: {[flag.get('msg') for flag in high_priority_warnings]}",
            }

        return {
            "status": "ok",
            "fix_patch": "",
            "notes": "Code executed successfully with no critical issues",
        }
