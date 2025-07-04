import pandas as pd
import re
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

def preprocess_df(df):
    '''
    원본 데이터 구조 변경 
    '''
    columns = df.columns[1:]

    reshaped_data = []

    for idx, row in df.iterrows():
        region = row['행정구역']
        for col in columns:
            value = row[col]
            if pd.isna(value):
                continue
            try:
                value = int(float(str(value).replace(",", "")))
            except ValueError:
                continue
            
            match = re.match(r'(\d{4})년(?:_(남|여))?_거주자_([0-9~세\s이상]+)', col)
            if match:
                year, gender, age_group = match.groups()
                gender = gender if gender else '전체'
                reshaped_data.append({
                    '행정구역': region,
                    '연도': int(year),
                    '성별': gender,
                    '연령대': age_group.strip(),
                    '인구수': value
                })

    result_df = pd.DataFrame(reshaped_data)

    return result_df
    

def decline_index(df):
        
    # 연령 숫자 추출 (예: '20~24세' → 20)
    df['연령숫자'] = df['연령대'].str.extract(r'(\d+)').astype(float)

    # 조건: 20~39세 여성
    young_women_mask = (
        (df['성별'] == '여') &
        (df['연령숫자'] >= 20) & (df['연령숫자'] < 40)
    )

    # 조건: 65세 이상 전체
    elderly_mask = df['연령숫자'] >= 65

    # 20~39세 여성 인구 합계
    young_women = df[young_women_mask].groupby(['행정구역', '연도'])['인구수'].sum().reset_index()
    young_women = young_women.rename(columns={'인구수': '20~39세_여성'})

    # 65세 이상 전체 인구 합계
    elderly = df[elderly_mask].groupby(['행정구역', '연도'])['인구수'].sum().reset_index()
    elderly = elderly.rename(columns={'인구수': '65세_이상_전체'})

    # 병합 및 지방소멸지수 계산
    merged = pd.merge(young_women, elderly, on=['행정구역', '연도'])
    merged['지방소멸지수'] = merged['20~39세_여성'] / merged['65세_이상_전체']

    return merged
'''    
def get_low_extinction_regions(df, n=None, thresh=None):
  
    year = 2024
    year_df = df[df['연도'] == year]

    if year_df.empty:
        raise ValueError(f"{year}년 데이터가 존재하지 않습니다.")
    if n is not None and thresh is not None:
        raise ValueError("n과 thresh 중 하나만 지정하세요.")
    
    # 2024년 기준 소멸지수 낮은 지역 선택
    if n is not None:
        selected_df = year_df.nsmallest(n, '지방소멸지수')
    elif thresh is not None:
        selected_df = year_df[year_df['지방소멸지수'] <= thresh].sort_values('지방소멸지수')
    else:
        raise ValueError("n 또는 thresh 중 하나는 반드시 지정해야 합니다.")

    # 행정구역 정렬 순서 확보
    selected_regions = selected_df['행정구역'].tolist()

    # 전체 연도 데이터 중 해당 지역만 필터링
    filtered_df = df[df['행정구역'].isin(selected_regions)].copy()

    # 연도 숫자형 → 문자열 및 정렬 가능하게 변환
    filtered_df['연도'] = filtered_df['연도'].astype(int)

    # 카테고리형으로 행정구역 순서 지정
    filtered_df['행정구역'] = pd.Categorical(
        filtered_df['행정구역'],
        categories=selected_regions,
        ordered=True
    )

    # 정렬: 행정구역(지방소멸지수 낮은 순), 연도(내림차순)
    filtered_df = filtered_df.sort_values(['행정구역', '연도'], ascending=[True, False])
    filtered_df['연도'] = filtered_df['연도'].astype(str)  # 시각화용 문자열
    filtered_df['연도'] = filtered_df['연도'].astype(str).astype(int)

    filtered_df.reset_index(drop=True, inplace=True)
    
    return filtered_df
'''

def get_low_extinction_regions(df, n=None, thresh=None):
    year = 2024
    year_df = df[df['연도'] == year]

    if year_df.empty:
        raise ValueError(f"{year}년 데이터가 존재하지 않습니다.")
    if n is not None and thresh is not None:
        raise ValueError("n과 thresh 중 하나만 지정하세요.")
    
    # 2024년 기준 소멸지수 낮은 지역 선택
    if n is not None:
        selected_df = year_df.nsmallest(n, '지방소멸지수').copy()
    elif thresh is not None:
        selected_df = year_df[year_df['지방소멸지수'] <= thresh].sort_values('지방소멸지수').copy()
    else:
        raise ValueError("n 또는 thresh 중 하나는 반드시 지정해야 합니다.")
    
    # 지방소멸지수 낮을수록 동일한 값은 동일한 순위 부여
    selected_df['소멸위험순위'] = selected_df['지방소멸지수'].rank(method='dense', ascending=True).astype(int)

    # 행정구역 정렬 순서 확보 (소멸위험순위 기준 정렬)
    selected_df = selected_df.sort_values(['소멸위험순위', '행정구역'])
    selected_regions = selected_df['행정구역'].tolist()

    # 전체 연도 데이터 중 해당 지역만 필터링
    filtered_df = df[df['행정구역'].isin(selected_regions)].copy()

    # 소멸위험순위 병합
    filtered_df = filtered_df.merge(
        selected_df[['행정구역', '소멸위험순위']],
        on='행정구역',
        how='left'
    )

    # 연도 숫자형 → 문자열 및 정렬 가능하게 변환
    filtered_df['연도'] = filtered_df['연도'].astype(int)

    # 카테고리형으로 행정구역 순서 지정
    filtered_df['행정구역'] = pd.Categorical(
        filtered_df['행정구역'],
        categories=selected_regions,
        ordered=True
    )

    # 정렬: 행정구역(소멸지수 낮은 순), 연도(내림차순)
    filtered_df = filtered_df.sort_values(['행정구역', '연도'], ascending=[True, False])
    filtered_df.reset_index(drop=True, inplace=True)
    
    return filtered_df


def plot_extinction_trend(filtered_df, title="decline_index_trend", save = True,  path='./plot'):
    """
    지방소멸지수 시계열 추이를 Plotly로 시각화합니다.
    x축은 연도(int형 오름차순), y축은 지방소멸지수,
    hover에는 20~39세 여성 인구 수와 65세 이상 인구 수를 함께 표시합니다.
    """
    # 연도 정렬 (오름차순 보장)
    filtered_df = filtered_df.sort_values(['연도'])

    fig = px.line(
        filtered_df,
        x='연도',               # x축: int형 연도
        y='지방소멸지수',
        color='행정구역',
        markers=True,
        hover_data={
            '지방소멸지수': ':.3f',
            '20~39세_여성': True,
            '65세_이상_전체': True,
            '연도': False  # 연도는 x축에 있으므로 hover에서는 생략
        },
        title=title
    )

    fig.update_layout(
        xaxis_title="연도",
        yaxis_title="지방소멸지수",
        hoverlabel=dict(bgcolor="white", font_size=12),
        legend_title_text="행정구역"
    )

    if save:
        save_fig_to_html(fig, output_path=f'{path}/{title}.html')



    return fig

