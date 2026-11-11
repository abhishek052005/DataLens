from pathlib import Path

import pandas as pd


def profile_data(dataframe: pd.DataFrame) -> dict:
    df = dataframe.copy()

    # Remove duplicate rows
    df = df.drop_duplicates()

    # Drop columns with >90% null
    df = df.loc[:, df.isnull().mean() < 0.9]

    # Drop columns where one value dominates >90%
    df = df.loc[:, df.apply(lambda c: c.value_counts(normalize=True).max() <= 0.9)]

    # Drop ID-like columns (unique in >90% of rows)
    df = df.loc[:, df.nunique() / len(df) < 0.9]
    df = df.loc[:, ~df.columns.astype(str).str.lower().str.contains("id")]

    # Drop free-text columns while measuring string lengths numerically.
    def is_short_text(column: pd.Series) -> bool:
        if not (
            pd.api.types.is_object_dtype(column.dtype)
            or pd.api.types.is_string_dtype(column.dtype)
        ):
            return True
        lengths = column.dropna().map(lambda value: len(str(value)))
        return lengths.empty or lengths.mean() <= 50

    df = df.loc[:, df.apply(is_short_text)]

    # Divide columns into categorical and numerical
    text_cols = df.select_dtypes(include=["object", "string"]).columns.tolist()
    date_cols = [column for column in text_cols if "date" in str(column).lower()]
    numerical_cols = df.select_dtypes(include=["number"]).columns.tolist()
    categorical_cols = [column for column in text_cols if column not in date_cols]

    # Numerical stats
    numerical_stats = {
        column: {
            "min": df[column].min(),
            "max": df[column].max(),
            "mean": df[column].mean(),
            "median": df[column].median(),
            "std": df[column].std(),
            "skew": df[column].skew(),
        }
        for column in numerical_cols
    }

    # Categorical stats
    categorical_stats = {
        column: {
            "unique_count": int(df[column].nunique()),
            "top_5": df[column].value_counts().nlargest(5).to_dict(),
        }
        for column in categorical_cols
    }

    # Date stats
    date_stats = {
        column: {
            "min": df[column].min(),
            "max": df[column].max(),
            "nunique": int(df[column].nunique()),
        }
        for column in date_cols
    }

    return {
        "df": df,
        "row_count": len(df),
        "col_count": len(df.columns),
        "numerical_cols": numerical_cols,
        "categorical_cols": categorical_cols,
        "date_cols": date_cols,
        "numerical_stats": numerical_stats,
        "categorical_stats": categorical_stats,
        "date_stats": date_stats,
    }


if __name__ == "__main__":
    sample_data = Path(__file__).resolve().parents[1] / "data" / "sales_data.csv"
    result = profile_data(pd.read_csv(sample_data))
    print(result["numerical_stats"])
    print(result["categorical_stats"])
    print(result["date_stats"])