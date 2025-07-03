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
    # '부'로 끝나는 행 제거
    df = df[~df[col].astype(str).str.strip().str.endswith('부')].copy()

    new_region_col = []
    current_province = ""

    for val in df[col]:
        if pd.isna(val):
            new_region_col.append(None)
            continue

        if str(val).endswith(("특별시", "광역시", "특별자치시", "도")):
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
    df = df[df['항목']=='주택_계'] #건축연도 무시
 
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



def plot_bar_by_house_type_split_by_year(df, title = '상위 10개 지역(2023년 기준)의 주택 유형별 주택 수', save=True, path='./plot'):
   

    # 1. 2023년 전체 주택 수 기준 상위 10개 하위 행정구역
    top10_df = df[
        (df['항목'].str.strip() == '주택_계') &
        (df['주택의 종류별'].str.strip() == '계') &
        (df['행정구역별(시군구)'] != df['결합행정구역'])
    ].copy()

    top10_df['2023 년'] = pd.to_numeric(top10_df['2023 년'], errors='coerce')
    top10_df = top10_df.sort_values(by='2023 년', ascending=False)

    top10_regions = top10_df.head(10)['결합행정구역'].tolist()

    # 2. 주택유형 필터링
    house_types = ['아파트', '다세대주택', '단독주택', '연립주택', '비주거용 건물 내 주택']
    filtered_df = df[
        (df['항목'].str.strip() == '주택_계') &
        (df['주택의 종류별'].isin(house_types)) &
        (df['결합행정구역'].isin(top10_regions))
    ].copy()

    # 3. 연도별 long-form 변환
    long_df = pd.melt(
        filtered_df,
        id_vars=['결합행정구역', '주택의 종류별'],
        value_vars=['2022 년', '2023 년'],
        var_name='연도',
        value_name='주택수'
    )

    long_df['주택수'] = pd.to_numeric(long_df['주택수'], errors='coerce')

    # 4. 카테고리 순서 고정 (명시적)
    long_df['주택의 종류별'] = pd.Categorical(
        long_df['주택의 종류별'],
        categories=house_types,
        ordered=True
    )

    long_df['결합행정구역'] = pd.Categorical(
        long_df['결합행정구역'],
        categories=top10_regions,
        ordered=True
    )

    # 5. 그래프 생성
    fig = px.bar(
        long_df,
        x='주택의 종류별',
        y='주택수',
        color='결합행정구역',
        barmode='group',
        facet_row='연도',
        title=title,
        labels={
            '주택의 종류별': '주택 유형',
            '주택수': '주택 수',
            '결합행정구역': '지역'
        },
        category_orders={
            '주택의 종류별': house_types,
            '결합행정구역': top10_regions
        }
    )

    # 6. 하단만 X축 레이블 표시
    fig.update_xaxes(showticklabels=True, row=1)
    fig.update_xaxes(showticklabels=True, row=2)

    
    if save:
        save_fig_to_html(fig, output_path=f'{path}/{title}.html')
    
    return fig
