"""
data_analyzer.py — Statistical analysis helpers for DataMind AI
"""

import pandas as pd
import numpy as np
from typing import Dict, Any


# ─────────────────────────────────────────────
# MAIN ANALYZER
# ─────────────────────────────────────────────

def analyze_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    """Return a comprehensive statistical summary of the dataframe."""
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    result: Dict[str, Any] = {
        "shape": {"rows": int(df.shape[0]), "cols": int(df.shape[1])},
        "missing_total": int(df.isnull().sum().sum()),
        "missing_pct": round(df.isnull().sum().sum() / (df.shape[0] * df.shape[1]) * 100, 2),
        "duplicate_rows": int(df.duplicated().sum()),
        "key_stats": {},
        "cat_stats": {},
        "strong_correlations": [],
    }

    # Numeric stats
    for col in numeric_cols:
        s = df[col].dropna()
        if len(s) == 0:
            continue
        result["key_stats"][col] = {
            "mean": round(float(s.mean()), 2),
            "median": round(float(s.median()), 2),
            "std": round(float(s.std()), 2),
            "min": round(float(s.min()), 2),
            "max": round(float(s.max()), 2),
            "q1": round(float(s.quantile(0.25)), 2),
            "q3": round(float(s.quantile(0.75)), 2),
            "skew": round(float(s.skew()), 3),
            "kurtosis": round(float(s.kurtosis()), 3),
            "cv": round(float(s.std() / s.mean() * 100), 1) if s.mean() != 0 else 0,
            "missing": int(df[col].isnull().sum()),
            "missing_pct": round(df[col].isnull().sum() / len(df) * 100, 1),
        }

    # Categorical stats
    for col in cat_cols:
        vc = df[col].value_counts()
        result["cat_stats"][col] = {
            "unique": int(df[col].nunique()),
            "top": str(vc.index[0]) if len(vc) > 0 else "",
            "top_count": int(vc.iloc[0]) if len(vc) > 0 else 0,
            "top_pct": round(vc.iloc[0] / len(df) * 100, 1) if len(vc) > 0 else 0,
            "missing": int(df[col].isnull().sum()),
            "missing_pct": round(df[col].isnull().sum() / len(df) * 100, 1),
        }

    # Strong correlations
    if len(numeric_cols) >= 2:
        try:
            corr = df[numeric_cols].corr()
            seen = set()
            for i, c1 in enumerate(numeric_cols):
                for c2 in numeric_cols[i + 1:]:
                    pair = tuple(sorted([c1, c2]))
                    if pair in seen:
                        continue
                    seen.add(pair)
                    val = corr.loc[c1, c2]
                    if abs(val) >= 0.5:
                        result["strong_correlations"].append({
                            "col1": c1, "col2": c2,
                            "r": round(float(val), 3),
                            "strength": "Strong" if abs(val) >= 0.75 else "Moderate",
                        })
        except Exception:
            pass

    return result


# ─────────────────────────────────────────────
# ANOMALY DETECTOR
# ─────────────────────────────────────────────

def detect_anomalies(df: pd.DataFrame) -> Dict[str, Any]:
    """Detect outliers, duplicates, constant columns, and high-missing columns."""
    anomalies: Dict[str, Any] = {}
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()

    # Outliers via IQR
    outliers: Dict[str, Any] = {}
    for col in numeric_cols:
        s = df[col].dropna()
        if len(s) < 4:
            continue
        q1, q3 = s.quantile(0.25), s.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        mask = (s < lower) | (s > upper)
        count = int(mask.sum())
        if count > 0:
            outliers[col] = {
                "count": count,
                "pct": round(count / len(s) * 100, 1),
                "lower_bound": round(float(lower), 2),
                "upper_bound": round(float(upper), 2),
                "extreme_min": round(float(s.min()), 2),
                "extreme_max": round(float(s.max()), 2),
            }
    anomalies["outliers"] = outliers

    # Duplicate rows
    dup_count = int(df.duplicated().sum())
    anomalies["duplicate_rows"] = {
        "count": dup_count,
        "pct": round(dup_count / len(df) * 100, 1),
    }

    # Constant columns
    anomalies["constant_columns"] = [
        col for col in df.columns if df[col].nunique() <= 1
    ]

    # High missing (>20%)
    anomalies["high_missing"] = [
        col for col in df.columns
        if df[col].isnull().sum() / len(df) > 0.2
    ]

    # High skewness (>2 or <-2)
    skewed = {}
    for col in numeric_cols:
        s = df[col].dropna()
        if len(s) >= 4:
            sk = float(s.skew())
            if abs(sk) > 2:
                skewed[col] = round(sk, 3)
    anomalies["high_skewness"] = skewed

    return anomalies


# ─────────────────────────────────────────────
# COLUMN INSIGHTS
# ─────────────────────────────────────────────

def get_column_insights(df: pd.DataFrame) -> Dict[str, Any]:
    """Per-column insights including top values and distributions."""
    insights: Dict[str, Any] = {}
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    for col in numeric_cols[:10]:
        s = df[col].dropna()
        if len(s) == 0:
            continue
        insights[col] = {
            "type": "numeric",
            "range": round(float(s.max() - s.min()), 2),
            "above_mean": int((s > s.mean()).sum()),
            "below_mean": int((s < s.mean()).sum()),
            "zeros": int((s == 0).sum()),
            "negatives": int((s < 0).sum()),
        }

    for col in cat_cols[:10]:
        vc = df[col].value_counts().head(5)
        insights[col] = {
            "type": "categorical",
            "unique": int(df[col].nunique()),
            "top_5": {str(k): int(v) for k, v in vc.items()},
            "concentration": round(float(vc.iloc[0] / len(df) * 100), 1) if len(vc) > 0 else 0,
        }

    return insights
