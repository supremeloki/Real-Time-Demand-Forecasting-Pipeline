import pandas as pd
import numpy as np
import random
from typing import Dict, Any, List

class DataSanitizer:
    def __init__(self, imputation_strategy: str = "mean", outlier_threshold: float = 3.0):
        self._imputation_strategy = imputation_strategy
        self._outlier_threshold = outlier_threshold
        self._learned_means: Dict[str, float] = {}

    def _impute_missing(self, series: pd.Series, column_name: str) -> pd.Series:
        if series.isnull().any():
            if self._imputation_strategy == "mean":
                if column_name not in self._learned_means:
                    self._learned_means[column_name] = series.mean()
                return series.fillna(self._learned_means[column_name])
            elif self._imputation_strategy == "median":
                return series.fillna(series.median())
            elif self._imputation_strategy == "zero":
                return series.fillna(0)
            else:
                return series.fillna(series.mode()[0] if not series.empty else 0)
        return series

    def _remove_outliers_iqr(self, series: pd.Series) -> pd.Series:
        q1, q3 = series.quantile(0.25), series.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - self._outlier_threshold * iqr
        upper_bound = q3 + self._outlier_threshold * iqr
        return series[(series >= lower_bound) & (series <= upper_bound)]

    def cleanse_data(self, data_frame: pd.DataFrame, numerical_columns: List[str] | None = None) -> pd.DataFrame:
        cleaned_df = data_frame.copy()
        for col in numerical_columns if numerical_columns else cleaned_df.select_dtypes(include=np.number).columns:
            if col in cleaned_df.columns:
                cleaned_df[col] = self._impute_missing(cleaned_df[col], col)
                cleaned_df[col] = self._remove_outliers_iqr(cleaned_df[col])
        return cleaned_df

if __name__ == '__main__':
    data = {
        'value_a': [10, 12, np.nan, 15, 100, 13, 11, 14, 16, 5],
        'value_b': [1, 2, 3, 4, np.nan, 6, 7, 8, 9, 10],
        'category': ['X', 'Y', 'X', 'Y', 'X', 'Y', 'X', 'Y', 'X', 'Y']
    }
    df = pd.DataFrame(data)

    sanitizer = DataSanitizer(imputation_strategy="mean", outlier_threshold=1.5)

    print("--- Original Data ---")
    print(df)

    cleaned_df = sanitizer.cleanse_data(df, numerical_columns=['value_a', 'value_b'])
    print("\n--- Cleaned Data ---")
    print(cleaned_df)