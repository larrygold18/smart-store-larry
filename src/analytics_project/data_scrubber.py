# src/analytics_project/data_scrubber.py
from __future__ import annotations
import re
from typing import Dict, List, Optional, Union
import pandas as pd

StrOrList = Union[str, List[str]]


def _to_list(x: StrOrList) -> List[str]:
    return [x] if isinstance(x, str) else list(x)


class DataScrubber:
    @staticmethod
    def _snake(s: str) -> str:
        s = s.strip()
        s = re.sub(r"[^A-Za-z0-9]+", "_", s)
        s = re.sub(r"_+", "_", s)
        return s.strip("_").lower()

    def standardize_columns(
        self, df: pd.DataFrame, mapping: Optional[Dict[str, str]] = None, snake_case: bool = True
    ) -> pd.DataFrame:
        df = df.copy()
        if mapping:
            df = df.rename(columns=mapping)
        new_cols, seen = [], {}
        for c in df.columns:
            nc = self._snake(c) if snake_case else c
            base, i = nc, seen.get(nc, 0)
            while nc in new_cols:
                i += 1
                nc = f"{base}_{i}"
            seen[base] = i
            new_cols.append(nc)
        df.columns = new_cols
        return df

    def trim_whitespace(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        for c in df.columns:
            if pd.api.types.is_string_dtype(df[c]) or df[c].dtype == "object":
                df[c] = df[c].astype("string").str.replace(r"\s+", " ", regex=True).str.strip()
        return df

    def to_datetime(
        self,
        df: pd.DataFrame,
        columns: StrOrList,
        dayfirst: bool = False,
        utc: bool = False,
        errors: str = "coerce",
    ) -> pd.DataFrame:
        df = df.copy()
        for c in _to_list(columns):
            df[c] = pd.to_datetime(df[c], dayfirst=dayfirst, utc=utc, errors=errors)
        return df

    def to_numeric(
        self, df: pd.DataFrame, columns: StrOrList, errors: str = "coerce"
    ) -> pd.DataFrame:
        df = df.copy()
        for c in _to_list(columns):
            df[c] = pd.to_numeric(df[c], errors=errors)
        return df

    def drop_duplicates(self, df: pd.DataFrame, subset: Optional[List[str]] = None) -> pd.DataFrame:
        return df.drop_duplicates(subset=subset).reset_index(drop=True)

    def drop_empty_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.dropna(how="all").reset_index(drop=True)

    def fill_missing(self, df: pd.DataFrame, strategies: Dict[str, Dict]) -> pd.DataFrame:
        df = df.copy()
        for col, spec in strategies.items():
            method = spec.get("method", "constant").lower()
            if method == "constant":
                df[col] = df[col].fillna(spec.get("value"))
            elif method == "median":
                df[col] = df[col].fillna(df[col].median())
            elif method == "mean":
                df[col] = df[col].fillna(df[col].mean())
            elif method == "mode":
                mode_series = df[col].mode(dropna=True)
                if len(mode_series) > 0:
                    df[col] = df[col].fillna(mode_series.iloc[0])
            else:
                raise ValueError(f"Unsupported fill method: {method} for column {col}")
        return df

    def normalize_categories(
        self, df: pd.DataFrame, columns: StrOrList, case: str = "lower"
    ) -> pd.DataFrame:
        df = df.copy()
        for c in _to_list(columns):
            if pd.api.types.is_string_dtype(df[c]) or df[c].dtype == "object":
                ser = df[c].astype("string").str.replace(r"\s+", " ", regex=True).str.strip()
                if case == "lower":
                    ser = ser.str.lower()
                elif case == "upper":
                    ser = ser.str.upper()
                elif case == "title":
                    ser = ser.str.title()
                df[c] = ser
        return df

    def remove_outliers_iqr(
        self, df: pd.DataFrame, columns: StrOrList, factor: float = 1.5
    ) -> pd.DataFrame:
        df = df.copy()
        mask = pd.Series(True, index=df.index)
        for c in _to_list(columns):
            if not pd.api.types.is_numeric_dtype(df[c]):
                continue
            q1, q3 = df[c].quantile(0.25), df[c].quantile(0.75)
            iqr = q3 - q1
            low, high = q1 - factor * iqr, q3 + factor * iqr
            mask &= df[c].between(low, high) | df[c].isna()
        return df.loc[mask].reset_index(drop=True)

    def validate_schema(self, df: pd.DataFrame, required_cols: Dict[str, str]) -> None:
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        tmp = df.copy()
        for c, dt in required_cols.items():
            if dt.startswith("datetime64"):
                tmp[c] = pd.to_datetime(tmp[c], errors="raise")
            else:
                tmp[c] = tmp[c].astype(dt)
