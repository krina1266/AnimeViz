import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="Аниме‑мероприятия 2021–2025", page_icon="🎌")
st.title("🎌 Аниме‑мероприятия 2021–2025")
st.write("Фильтруйте и анализируйте данные об аниме-мероприятиях!!!.")

@st.cache_data
def load_data():
    df = pd.read_csv("Anime.csv", encoding='utf-8')
    df['Начало'] = pd.to_datetime(df['Начало'], errors='coerce')
    df['Год'] = df['Начало'].dt.year
    for col in ['Город', 'Название фандома/фильма/аниме', 'Возрастной рейтинг', 'Активность', 'Контент', 'Музыка']:
        df[col] = df[col].fillna('Не указано').astype(str)
    return df

df = load_data()

# --- Фильтры в боковой панели (оставляем как было) ---
st.sidebar.header("Фильтры")

cities = sorted(df['Город'].unique())
selected_cities = st.sidebar.multiselect("Города", cities, default=cities[:5] if len(cities) > 5 else cities)

fandoms = sorted(df['Название фандома/фильма/аниме'].unique())
selected_fandoms = st.sidebar.multiselect("Фандом / фильм / аниме", fandoms, default=fandoms[:5] if len(fandoms) > 5 else fandoms)

age_ratings = sorted(df['Возрастной рейтинг'].unique())
selected_age = st.sidebar.multiselect("Возрастной рейтинг", age_ratings, default=age_ratings)

activities = sorted(df['Активность'].unique())
selected_activity = st.sidebar.multiselect("Активность", activities, default=activities)

contents = sorted(df['Контент'].unique())
selected_content = st.sidebar.multiselect("Контент", contents, default=contents)

musics = sorted(df['Музыка'].unique())
selected_music = st.sidebar.multiselect("Музыка", musics, default=musics)

years = sorted(df['Год'].dropna().unique())
if len(years) > 0:
    min_year, max_year = int(min(years)), int(max(years))
    selected_years = st.sidebar.slider("Годы", min_year, max_year, (min_year, max_year))
else:
    selected_years = (2021, 2025)

filtered_df = df[
    (df['Город'].isin(selected_cities)) &
    (df['Название фандома/фильма/аниме'].isin(selected_fandoms)) &
    (df['Возрастной рейтинг'].isin(selected_age)) &
    (df['Активность'].isin(selected_activity)) &
    (df['Контент'].isin(selected_content)) &
    (df['Музыка'].isin(selected_music)) &
    (df['Год'].between(selected_years[0], selected_years[1]))
]

st.header(f"📊 Найдено мероприятий: {len(filtered_df)}")

tab1, tab2, tab3 = st.tabs(["📋 Таблица", "📈 Динамика по годам", "🏙️ Топ городов"])

# --- Таблица ---
with tab1:
    st.subheader("Список мероприятий (с учётом фильтров)")
    display_cols = ['Начало', 'Конец', 'Город', 'название', 'Название фандома/фильма/аниме',
                    'Возрастной рейтинг', 'Активность', 'Контент', 'Музыка', 'Ссылка']
    display_cols = [col for col in display_cols if col in filtered_df.columns]
    table_df = filtered_df[display_cols].copy()
    if 'Начало' in table_df.columns:
        table_df['Начало'] = table_df['Начало'].dt.strftime('%d.%m.%Y')
    column_config = {"Ссылка": st.column_config.LinkColumn("Ссылка", display_text="Открыть")}
    st.dataframe(table_df, use_container_width=True, height=400, column_config=column_config)
    csv = filtered_df.drop(columns=['Год'], errors='ignore').to_csv(index=False).encode('utf-8')
    st.download_button("📥 Скачать отфильтрованные данные (CSV)", data=csv, file_name='filtered_anime_events.csv', mime='text/csv')

# --- Новый график (как в примере с фильмами) ---
with tab2:
    st.subheader("Динамика по годам (выберите фандомы)")
    # Все фандомы из данных
    all_fandoms = sorted(df['Название фандома/фильма/аниме'].unique())
    default_fandoms = all_fandoms[:5] if len(all_fandoms) > 5 else all_fandoms
    selected_fandoms_graph = st.multiselect(
        "Фандомы для графика",
        options=all_fandoms,
        default=default_fandoms
    )
    years_range = st.slider(
        "Диапазон лет",
        min_value=int(df['Год'].min()),
        max_value=int(df['Год'].max()),
        value=(int(df['Год'].min()), int(df['Год'].max()))
    )
    plot_df = df[
        (df['Название фандома/фильма/аниме'].isin(selected_fandoms_graph)) &
        (df['Год'].between(years_range[0], years_range[1]))
    ]
    yearly_counts = plot_df.groupby(['Год', 'Название фандома/фильма/аниме']).size().reset_index(name='Количество')
    if yearly_counts.empty:
        st.warning("Для выбранных фандомов и лет нет данных.")
    else:
        chart = alt.Chart(yearly_counts).mark_line(point=True).encode(
            x=alt.X('Год:Q', title='Год', axis=alt.Axis(format='d')),
            y=alt.Y('Количество:Q', title='Количество мероприятий'),
            color=alt.Color('Название фандома/фильма/аниме:N', title='Фандом'),
            tooltip=['Год', 'Название фандома/фильма/аниме', 'Количество']
        ).properties(height=400)
        st.altair_chart(chart, use_container_width=True)

# --- Топ городов ---
with tab3:
    st.subheader("Топ‑10 городов по количеству мероприятий")
    city_counts = filtered_df['Город'].value_counts().head(10).reset_index()
    city_counts.columns = ['Город', 'Количество']
    bar_chart = alt.Chart(city_counts).mark_bar().encode(
        x=alt.X('Город:N', sort='-y'),
        y=alt.Y('Количество:Q'),
        color=alt.Color('Город:N', legend=None),
        tooltip=['Город', 'Количество']
    ).properties(height=400)
    st.altair_chart(bar_chart, use_container_width=True)

st.markdown("---")
st.caption("Данные получены с сайта animeconventions.ru, парсинг выполнен в 2026 году.")