"""
Deterministic CSV profiler that generates profile JSON
"""

import pandas as pd
import numpy as np
import json
from typing import Dict, Any, List, Optional
import os


class CSVProfiler:
    """Deterministic CSV profiler that analyzes data and generates structured profile"""

    def __init__(self, sample_size: int = 10000):
        self.sample_size = sample_size

    def profile(self, csv_path: str) -> Dict[str, Any]:
        """
        Profile a CSV file and return structured profile JSON

        Args:
            csv_path: Path to the CSV file

        Returns:
            Profile dictionary matching the schema
        """
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        # Load data with sampling for large files
        df = self._load_data(csv_path)

        # Calculate memory estimate
        memory_estimate = df.memory_usage(deep=True).sum() / 1024 / 1024  # MB

        # Profile each column
        columns = []
        for col in df.columns:
            col_profile = self._profile_column(df, col)
            columns.append(col_profile)

        # Detect suspected target column
        suspected_target = self._detect_target_column(df, columns)

        profile = {
            "rows_total": len(df),
            "rows_sampled": len(df),
            "memory_estimate_mb": round(memory_estimate, 2),
            "columns": columns,
            "suspected_target": suspected_target,
        }

        return profile

    def _load_data(self, csv_path: str) -> pd.DataFrame:
        """Load CSV data with sampling for large files"""
        try:
            # First, try to read a small sample to check structure
            sample_df = pd.read_csv(csv_path, nrows=1000)

            # If file is small enough, load all
            file_size = os.path.getsize(csv_path)
            if file_size < 50 * 1024 * 1024:  # 50MB
                return pd.read_csv(csv_path)

            # For large files, sample
            total_rows = sum(1 for _ in open(csv_path)) - 1  # Subtract header
            if total_rows <= self.sample_size:
                return pd.read_csv(csv_path)

            # Sample rows
            skip_rows = np.random.choice(
                range(1, total_rows + 1),
                size=total_rows - self.sample_size,
                replace=False,
            )
            return pd.read_csv(csv_path, skiprows=skip_rows)

        except Exception as e:
            raise Exception(f"Failed to load CSV: {e}")

    def _profile_column(self, df: pd.DataFrame, col: str) -> Dict[str, Any]:
        """Profile a single column"""
        series = df[col]

        # Basic info
        missing = series.isnull().sum()
        dtype = str(series.dtype)

        # Determine if numeric
        is_numeric = pd.api.types.is_numeric_dtype(series)

        column_profile = {
            "name": col,
            "dtype": dtype,
            "missing": int(missing),
            "numeric": None,
            "top_values": {},
        }

        # Numeric statistics
        if is_numeric and not series.empty:
            numeric_stats = self._get_numeric_stats(series)
            column_profile["numeric"] = numeric_stats

        # Top values for categorical data
        if not is_numeric or series.nunique() < 20:
            top_values = series.value_counts().head(10)
            column_profile["top_values"] = {
                str(k): int(v) for k, v in top_values.items()
            }

        return column_profile

    def _get_numeric_stats(self, series: pd.Series) -> Dict[str, Any]:
        """Get numeric statistics for a series"""
        clean_series = series.dropna()

        if clean_series.empty:
            return {
                "min": 0.0,
                "max": 0.0,
                "mean": 0.0,
                "std": 0.0,
                "quantiles": {
                    "0.0": 0.0,
                    "0.25": 0.0,
                    "0.5": 0.0,
                    "0.75": 0.0,
                    "1.0": 0.0,
                },
            }

        quantiles = clean_series.quantile([0.0, 0.25, 0.5, 0.75, 1.0])

        return {
            "min": float(clean_series.min()),
            "max": float(clean_series.max()),
            "mean": float(clean_series.mean()),
            "std": float(clean_series.std()),
            "quantiles": {
                "0.0": float(quantiles[0.0]),
                "0.25": float(quantiles[0.25]),
                "0.5": float(quantiles[0.5]),
                "0.75": float(quantiles[0.75]),
                "1.0": float(quantiles[1.0]),
            },
        }

    def _detect_target_column(
        self, df: pd.DataFrame, columns: List[Dict]
    ) -> Optional[str]:
        """Detect suspected target column based on heuristics"""
        target_candidates = []

        for col_info in columns:
            col_name = col_info["name"]
            col_series = df[col_name]

            # Skip if too many missing values
            if col_info["missing"] > len(df) * 0.5:
                continue

            # Check for common target patterns
            if any(
                keyword in col_name.lower()
                for keyword in [
                    "target",
                    "label",
                    "y",
                    "outcome",
                    "result",
                    "class",
                    "category",
                ]
            ):
                target_candidates.append((col_name, 0.9))

            # Check for binary columns
            if col_series.nunique() == 2:
                target_candidates.append((col_name, 0.7))

            # Check for categorical with reasonable cardinality
            if (
                not pd.api.types.is_numeric_dtype(col_series)
                and 2 <= col_series.nunique() <= 20
            ):
                target_candidates.append((col_name, 0.5))

        if target_candidates:
            # Return the highest scoring candidate
            target_candidates.sort(key=lambda x: x[1], reverse=True)
            return target_candidates[0][0]

        return None
