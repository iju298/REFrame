import pandas as pd


def combine_region_names(df, col='행정구역별(시군구)'):
    new_region_col = []
    current_province = ""

    for val in df[col]:
        if pd.isna(val):
            new_region_col.append(None)
            continue

        if any(suffix in val for suffix in ["특별시", "광역시", "특별자치시", "도"]):
            current_province = val
            new_region_col.append(val)
        else:
            full_name = f"{current_province} {val}"
            new_region_col.append(full_name)

    df.insert(1, '결합행정구역', new_region_col)

    return df


def preprocess_df(df):

    # 열의 전체 데이터가 nan인 경우
    df = df.dropna(axis=1, how='all')

    df = combine_region_names(df)

    return df