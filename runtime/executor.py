"""
Sandbox executor with security constraints and manifest validation
"""

import sys
import io
import traceback
import json
import os
import pandas as pd
import numpy as np
import matplotlib

matplotlib.use("Agg")  # Use non-interactive backend
import matplotlib.pyplot as plt
from typing import Dict, Any, List, Optional
import re
from scipy import stats


class SandboxExecutor:
    """Secure sandbox for executing Python code with resource limits"""

    def __init__(self, artifacts_dir: str = "./artifacts", timeout: int = 10):
        self.artifacts_dir = artifacts_dir
        self.timeout = timeout

        # Ensure artifacts directory exists
        os.makedirs(artifacts_dir, exist_ok=True)

        # Forbidden modules and functions
        self.forbidden_modules = {
            "os",
            "sys",
            "subprocess",
            "socket",
            "http",
            "urllib",
            "requests",
            "pathlib",
            "shutil",
            "glob",
            "tempfile",
            "pickle",
            "shelve",
            "multiprocessing",
            "threading",
            "asyncio",
            "concurrent",
        }

        self.forbidden_functions = {
            "open",
            "file",
            "input",
            "raw_input",
            "exec",
            "eval",
            "compile",
            "reload",
            "__import__",
        }

    def execute(
        self, code: str, df: pd.DataFrame, manifest_schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute code in sandbox and return results

        Args:
            code: Python code to execute
            df: DataFrame to make available as 'df'
            manifest_schema: Expected manifest schema

        Returns:
            Execution result dictionary
        """
        # Validate code for security
        if not self._is_code_safe(code):
            return {
                "exec_ok": False,
                "stdout": "",
                "error": "Code contains forbidden operations",
                "manifest": {},
                "evidence": {},
                "linter_flags": [
                    {
                        "level": "error",
                        "code": "FORBIDDEN_CODE",
                        "msg": "Code contains forbidden operations",
                    }
                ],
            }

        # Capture stdout/stderr
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        try:
            sys.stdout = stdout_capture
            sys.stderr = stderr_capture

            # Create execution namespace
            namespace = {
                "df": df,
                "pd": pd,
                "np": np,
                "plt": plt,
                "matplotlib": matplotlib,
                "stats": stats,
            }
            namespace.update(self._get_safe_builtins())

            # Execute code
            exec(code, namespace)

            # Extract manifest if it exists
            manifest = namespace.get("manifest", {})

            # Generate evidence from the data
            evidence = self._generate_evidence(df, manifest)

            # Run linter
            linter_flags = self._run_linter(manifest, evidence)

            return {
                "exec_ok": True,
                "stdout": stdout_capture.getvalue(),
                "error": "",
                "manifest": manifest,
                "evidence": evidence,
                "linter_flags": linter_flags,
            }

        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            return {
                "exec_ok": False,
                "stdout": stdout_capture.getvalue(),
                "error": error_msg,
                "manifest": {},
                "evidence": {},
                "linter_flags": [
                    {"level": "error", "code": "EXECUTION_ERROR", "msg": str(e)}
                ],
            }

        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

    def _is_code_safe(self, code: str) -> bool:
        """Check if code is safe to execute"""
        # Check for forbidden imports
        import_pattern = r"import\s+(\w+)"
        from_pattern = r"from\s+(\w+)"

        for match in re.finditer(import_pattern, code):
            module = match.group(1).split(".")[0]
            if module in self.forbidden_modules:
                return False

        for match in re.finditer(from_pattern, code):
            module = match.group(1).split(".")[0]
            if module in self.forbidden_modules:
                return False

        # Check for forbidden function calls
        for func in self.forbidden_functions:
            if f"{func}(" in code:
                return False

        # Check for file operations
        if any(
            pattern in code for pattern in ["open(", "file(", "pathlib", "os.", "sys."]
        ):
            return False

        return True

    def _get_safe_builtins(self) -> Dict[str, Any]:
        """Get safe builtins for execution"""
        import builtins

        safe_builtins = {
            "len",
            "range",
            "enumerate",
            "zip",
            "map",
            "filter",
            "sorted",
            "min",
            "max",
            "sum",
            "abs",
            "round",
            "int",
            "float",
            "str",
            "bool",
            "list",
            "dict",
            "tuple",
            "set",
            "type",
            "isinstance",
            "print",
            "repr",
            "dir",
            "hasattr",
            "getattr",
            "setattr",
        }

        return {
            name: getattr(builtins, name)
            for name in safe_builtins
            if hasattr(builtins, name)
        }

    def _generate_evidence(
        self, df: pd.DataFrame, manifest: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate evidence from data and manifest"""
        evidence = {
            "numeric": {},
            "categorical": {},
            "relationships": {},
            "timeseries": {},
        }

        # Extract columns used in charts
        used_columns = set()
        if "charts" in manifest:
            for chart in manifest["charts"]:
                if "columns_used" in chart:
                    used_columns.update(chart["columns_used"])

        # Generate numeric evidence
        for col in df.select_dtypes(include=[np.number]).columns:
            if col in used_columns or not used_columns:
                series = df[col].dropna()
                if not series.empty:
                    evidence["numeric"][col] = {
                        "count": len(series),
                        "mean": float(series.mean()),
                        "std": float(series.std()),
                        "min": float(series.min()),
                        "p01": float(series.quantile(0.01)),
                        "p25": float(series.quantile(0.25)),
                        "p50": float(series.quantile(0.50)),
                        "p75": float(series.quantile(0.75)),
                        "p95": float(series.quantile(0.95)),
                        "p99": float(series.quantile(0.99)),
                        "max": float(series.max()),
                        "skew": float(stats.skew(series)),
                        "kurtosis": float(stats.kurtosis(series)),
                        "n_outliers_z3": int(np.sum(np.abs(stats.zscore(series)) > 3)),
                    }

        # Generate categorical evidence
        for col in df.select_dtypes(include=["object", "category"]).columns:
            if col in used_columns or not used_columns:
                series = df[col].dropna()
                if not series.empty:
                    value_counts = series.value_counts()
                    evidence["categorical"][col] = {
                        "cardinality": series.nunique(),
                        "top_k": [
                            {
                                "value": str(k),
                                "count": int(v),
                                "share": float(v / len(series)),
                            }
                            for k, v in value_counts.head(10).items()
                        ],
                    }

        # Generate correlation evidence
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 1:
            corr_matrix = df[numeric_cols].corr()
            # Get top correlations (excluding diagonal)
            corr_pairs = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i + 1, len(corr_matrix.columns)):
                    col1, col2 = corr_matrix.columns[i], corr_matrix.columns[j]
                    corr_val = corr_matrix.iloc[i, j]
                    if not np.isnan(corr_val):
                        corr_pairs.append([col1, col2, float(corr_val)])

            # Sort by absolute correlation
            corr_pairs.sort(key=lambda x: abs(x[2]), reverse=True)
            evidence["relationships"]["corr_pearson_top"] = corr_pairs[:10]

        # Detect time series
        datetime_cols = df.select_dtypes(include=["datetime64"]).columns
        if len(datetime_cols) > 0:
            evidence["timeseries"]["primary_ts_col"] = datetime_cols[0]
            # Simple seasonality detection
            if len(datetime_cols) > 0:
                ts_col = datetime_cols[0]
                ts_series = df[ts_col].dropna()
                if len(ts_series) > 30:
                    # Check for daily patterns
                    if ts_series.dt.hour.nunique() > 1:
                        evidence["timeseries"]["resample"] = "H"
                    elif ts_series.dt.day.nunique() > 1:
                        evidence["timeseries"]["resample"] = "D"
                    elif ts_series.dt.month.nunique() > 1:
                        evidence["timeseries"]["resample"] = "M"

        return evidence

    def _run_linter(
        self, manifest: Dict[str, Any], evidence: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Run linter rules on manifest and evidence"""
        flags = []

        if "charts" not in manifest:
            return flags

        for chart in manifest["charts"]:
            # Check for missing labels
            if not chart.get("axis", {}).get("x") or not chart.get("title"):
                flags.append(
                    {
                        "level": "warn",
                        "code": "MISSING_LABELS",
                        "msg": "Missing axis labels or title",
                    }
                )

            # Check for high cardinality
            if "columns_used" in chart:
                for col in chart["columns_used"]:
                    if col in evidence.get("categorical", {}):
                        cardinality = evidence["categorical"][col]["cardinality"]
                        if cardinality > 15:
                            flags.append(
                                {
                                    "level": "warn",
                                    "code": "HIGH_CARDINALITY",
                                    "msg": f"Column {col} has {cardinality} unique values, consider top-k",
                                }
                            )

            # Check for high skew without log scale
            if "columns_used" in chart:
                for col in chart["columns_used"]:
                    if col in evidence.get("numeric", {}):
                        skew = abs(evidence["numeric"][col]["skew"])
                        if skew > 2 and not chart.get("axis", {}).get("log_x", False):
                            flags.append(
                                {
                                    "level": "warn",
                                    "code": "HIGH_SKEW_NO_LOG",
                                    "msg": f"Column {col} has skew {skew:.2f}, consider log scale",
                                }
                            )

            # Check for many ticks
            x_ticks = chart.get("axis", {}).get("x_ticks", 0)
            y_ticks = chart.get("axis", {}).get("y_ticks", 0)
            if x_ticks > 20 or y_ticks > 20:
                flags.append(
                    {
                        "level": "warn",
                        "code": "MANY_TICKS",
                        "msg": f"Too many ticks ({x_ticks}x{y_ticks}), consider thinning",
                    }
                )

            # Check for high NA drop
            notes = chart.get("notes", "")
            if "NA dropped:" in notes:
                match = re.search(r"NA dropped: (\d+(?:\.\d+)?)%", notes)
                if match:
                    na_percent = float(match.group(1))
                    if na_percent > 20:
                        flags.append(
                            {
                                "level": "warn",
                                "code": "HIGH_NA_DROP",
                                "msg": f"High NA drop: {na_percent}%",
                            }
                        )

            # Check for empty plot
            n_rows = chart.get("n_rows_plotted", 0)
            if n_rows < 50:
                flags.append(
                    {
                        "level": "warn",
                        "code": "EMPTY_PLOT",
                        "msg": f"Plot has only {n_rows} rows",
                    }
                )

        return flags
