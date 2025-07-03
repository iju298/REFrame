import pandas as pd
import plotly.express as px
import plotly.io as pio

def save_fig_to_html(fig, output_path: str):
    """
    Plotly figure 객체를 HTML 파일로 저장합니다.

    Parameters:
    - fig: Plotly 그래프 객체
    - output_path (str): 저장할 HTML 파일 경로
    """
    if fig is None:
        print("⚠️ 저장할 fig 객체가 없습니다.")
        return
    fig.write_html(output_path)
    print(f"✅ 그래프가 HTML로 저장되었습니다: {output_path}")


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


def sum_upper_region(df):
    # 상위 행정구역은 아래 접미사로 끝나는 값만 선택
    upper_suffixes = ("특별시", "광역시", "특별자치시", "도")

    # 조건: 행정구역명이 상위 행정구역으로 끝나고, 항목은 '주택_계', 주택 종류는 '계'
    filtered_df = df[
        df['행정구역별(시군구)'].apply(lambda x: str(x).endswith(upper_suffixes)) &
        (df['항목'] == '주택_계') &
        (df['주택의 종류별'] == '계')
    ].copy()

    filtered_df.reset_index(drop=True, inplace=True)

    return filtered_df



def plot_empty_upper(df, title = '상위 행정구역별 빈집 수 (2022 vs 2023)', save=True, path='./plot'):
    
    # Long-form 변환
    long_df = pd.melt(
        df,
        id_vars=['행정구역별(시군구)'],
        value_vars=['2022 년', '2023 년'],
        var_name='연도',
        value_name='빈집수'
    )

    long_df['빈집수'] = pd.to_numeric(long_df['빈집수'], errors='coerce')
    fig = px.bar(
        long_df,
        x='행정구역별(시군구)',
        y='빈집수',
        color='연도',
        barmode='group',
        title=title,
        labels={'행정구역별(시군구)': '행정구역', '빈집수': '빈집 수'}
    )

    fig.update_layout(xaxis_tickangle=45)

    if save:
        save_fig_to_html(fig, output_path=f'{path}/{title}.html')
    
    return fig
