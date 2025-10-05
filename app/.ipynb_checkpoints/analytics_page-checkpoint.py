import pandas as pd
import streamlit as st
from media import render_img_html
import plotly.express as px
import plotly.graph_objects as go
from sktime.performance_metrics.forecasting import mean_absolute_error

def analytics_page():
    cols = st.columns([1, 1, 15])
    with cols[0]:
        render_img_html("imgs/client_logo.png", 125)
    
    st.header('Controle de Estações', divider='blue')

    # Ler aqruivos
    arquivos = {
        'swaps': 'data/processed/merged_data.parquet',
        'stations': 'data/processed/stations_processed.parquet',
        'preds_cabinets_hourly': 'data/model/pred_cabinets_hourly.parquet',
        'preds_cabinets_daily': 'data/model/pred_cabinets_daily.parquet',
        'preds_stations_hourly': 'data/model/pred_stations_hourly.parquet',
        'preds_stations_daily': 'data/model/pred_stations_daily.parquet',
    }

    for key, path in arquivos.items():
        if key not in st.session_state:
            st.session_state[key] = pd.read_parquet(path, engine='pyarrow')

    df_cabs_h = st.session_state['preds_cabinets_hourly']
    df_cabs_d = st.session_state['preds_cabinets_daily']
    df_sta_h = st.session_state['preds_stations_hourly']
    df_sta_d = st.session_state['preds_stations_daily']
    df_all = st.session_state['swaps']
    df_sta_all = st.session_state['stations']
    
    df = df_all[df_all['swap_station_id'].isin(df_sta_h.swap_station_id.unique())][:].reset_index(drop=True)
    df_sta = df_sta_all[df_sta_all['swap_station_id'].isin(df_sta_h.swap_station_id.unique())][:].reset_index(drop=True)

    # ------------ Seleções ------------
    cols = st.columns([2,3,4])

    cols[0].selectbox('Selecione a cidade', ['São Paulo'])

    nomes = df_sta.swap_station_name.unique()
    nome = cols[1].selectbox('Selecione a estação', nomes)

    sta_select = df_sta[df_sta['swap_station_name']==nome][:].reset_index(drop=True)
    id = sta_select.swap_station_id[0]
    swaps_select = df[df['swap_station_id']==id][:].reset_index(drop=True)

    st.write(f'## {nome} - ID {sta_select.swap_station_id[0]}')
    st.caption(f'{sta_select.address[0]}')

    # ------------ Métricas da estação ------------
    st.subheader('Métricas da Estação')
    cols = st.columns(8)

    mean = df_sta_all.cabinet_number.mean()
    diff = round(sta_select.cabinet_number[0] - mean) 
    cols[0].metric('Qtd. de Cabinets', sta_select.cabinet_number[0], diff)

    mean = df_sta_all.swaps_per_day_mean.mean()
    diff = round(sta_select.swaps_per_day_mean[0] - mean) 
    cols[1].metric('Média de Swaps/Dia', round(sta_select.swaps_per_day_mean[0]), diff)

    mean = df_sta_all.swaps_per_hour_mean.mean()
    diff = round(sta_select.swaps_per_hour_mean[0] - mean) 
    cols[2].metric('Média de Swaps/Hora', round(sta_select.swaps_per_hour_mean[0]), diff)
    
    mean = df_sta_all.swaps_per_cabinet.mean()
    diff = round(sta_select.swaps_per_cabinet[0] - mean) 
    cols[3].metric('Média de Swaps/Cabinet', round(sta_select.swaps_per_cabinet[0]), diff)

    mean = df_sta_all.swaps_per_observation.mean()*100
    diff = round(sta_select.swaps_per_observation[0]*100 - mean, 2) 
    cols[4].metric('Swaps/Tráfego', f'{round(sta_select.swaps_per_observation[0]*100, 2)}%', diff)
    cols[4].markdown(
        "<span style='font-size:14px; color:gray;'>*Conversão de demanda*</span>",
        unsafe_allow_html=True
    )

    mean = df_sta_all.observations_per_swaps.mean()*100
    diff = round(abs((sta_select.observations_per_swaps[0]*100 - mean)), 2) 
    cols[5].metric('Tráfego/Swaps', f'{round(sta_select.observations_per_swaps[0]*100, 2)}%', diff)
    cols[5].markdown(
        "<span style='font-size:14px; color:gray;'>*Demanda reprimida*</span>",
        unsafe_allow_html=True
    )

    mean = df_sta_all.nearest_station_distance_km.mean()
    diff = round((sta_select.nearest_station_distance_km[0] - mean), 3) 
    cols[6].metric('Estação Mais Próxima', f'{round(sta_select.nearest_station_distance_km[0], 3)} km', diff)
    cols[6].markdown(
        f"<span style='font-size:14px; color:gray;'>*{sta_select.nearest_station_name[0]}*</span>",
        unsafe_allow_html=True
    )

    temp = swaps_select.dropna(subset=['status']).status.value_counts()
    completed = temp.get('completed', 0)
    swap_success = temp.get('swap_success_door_left_opened', 0)
    success = round(((completed + swap_success) / temp.sum()) * 100, 2)     
    cols[7].metric('Swaps Bem-Sucedidos', f'{success}%')
    
    # ------------ Previsões ------------
    st.write('### Previsão de Swaps')
    
    cols = st.columns(5)
    grain = cols[0].radio('Selecione a granularidade', ['Horária', 'Diária'],horizontal=True)

    if grain == 'Horária':
        df_preds = df_sta_h[df_sta_h['swap_station_id']==id][:].reset_index()
    else: 
        df_preds = df_sta_d[df_sta_d['swap_station_id']==id][:].reset_index()
        
    df_preds['ds'] = pd.to_datetime(df_preds['ds'])
    #df_preds = df_preds[df_preds['ds'].dt.month>=df_preds.dropna()['ds'].dt.month.max()]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_preds['ds'],
        y=df_preds['counts'],
        name='Real',
        mode='lines',
        line=dict(color='black', width=1.5)
    ))
    fig.add_trace(go.Scatter(
        x=df_preds['ds'],
        y=df_preds['predicted'],
        name='Previsões',
        mode='lines',
        line=dict(color='#2EC2FF', width=2, shape='spline')
    ))
    fig.add_trace(go.Scatter(
        x=df_preds['ds'],
        y=df_preds['upper_interval'],
        name='Intervalo Superior',
        mode='lines',
        line=dict(color='#2EC2FF', width=1, shape='spline', dash='dash'),
        opacity=0.6
    ))
    fig.add_trace(go.Scatter(
        x=df_preds['ds'],
        y=df_preds['lower_interval'],
        name='Intervalo Inferior',
        mode='lines',
        line=dict(color='#2EC2FF', width=1, shape='spline', dash='dash'),
        opacity=0.6
    ))
    fig.update_layout(
        template='plotly_white',
        title=f'Previsão de Swaps - {nome}',
        xaxis_title='Data',
        yaxis_title='Swaps',
        height=500, width=1200
    )

    fig.add_vline(x=df_preds.dropna()['ds'].max(), line_width=3, line_dash="dash", line_color="#8c00ff", )
    tile = st.container(border=True)
    tile.plotly_chart(fig, usecontainer_width=True)

    df_eval = df_preds.dropna(subset='counts')
    mae = round(mean_absolute_error(df_eval['counts'], df_eval['predicted']))
    tile.write(f'- Erro absoluto médio do modelo: **{mae}**')
    
    st.divider()
    
    # ------------ Cabinets ------------
    st.write('## Análise de Cabinets')

    cabinets = swaps_select.cabinet_id.unique().astype(int)
    cols = st.columns(4)
    cabinet_id = cols[0].selectbox('Selecione o cabinet', cabinets)

    df_cabinet = swaps_select[swaps_select['cabinet_id']==cabinet_id][:].reset_index(drop=True)
    df_cabinet_h = df_cabs_h[df_cabs_h['cabinet_id']==cabinet_id][:].reset_index(drop=True)
    df_cabinet_d = df_cabs_d[df_cabs_d['cabinet_id']==cabinet_id][:].reset_index(drop=True)

    cols = st.columns(3)
    mean = df_cabs_h.counts.mean()
    diff = round(df_cabinet_h.counts[0].mean() - mean) 
    tile = cols[0].container(border=True)
    tile.metric('Média de Swaps/Hora', df_cabinet_h.counts[0].mean(), diff)

    mean = df_cabs_d.counts.mean()
    diff = round(df_cabinet_d.counts[0].mean() - mean)
    tile = cols[1].container(border=True)
    tile.metric('Média de Swaps/Dia', df_cabinet_d.counts[0].mean(), diff)
 
    temp = df_cabinet.dropna(subset=['status']).status.value_counts()
    completed = temp.get('completed', 0)
    swap_success = temp.get('swap_success_door_left_opened', 0)
    success = round(((completed + swap_success) / temp.sum()) * 100, 2) 
    with cols[2].container(border=True):
        st.metric('Swaps Bem-Sucedidos', f'{success}%')
        with st.expander(f'Contagens'):
            st.write(temp)
    
    st.write('### Previsão de Swaps (Cabinet)')

    cols = st.columns(5)
    grain = cols[0].radio('Selecione a granularidade', ['Horária', 'Diária'], horizontal=True, key=200)

    if grain == 'Horária':
        df_preds = df_cabinet_h[df_cabinet_h['cabinet_id']==cabinet_id][:].reset_index()
    else: 
        df_preds = df_cabinet_d[df_cabinet_d['cabinet_id']==cabinet_id][:].reset_index()
        
    df_preds['ds'] = pd.to_datetime(df_preds['ds'])
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_preds['ds'],
        y=df_preds['counts'],
        name='Real',
        mode='lines',
        line=dict(color='black', width=1.5)
    ))
    fig.add_trace(go.Scatter(
        x=df_preds['ds'],
        y=df_preds['predicted'],
        name='Previsões',
        mode='lines',
        line=dict(color='#2EC2FF', width=2, shape='spline')
    ))
    fig.add_trace(go.Scatter(
        x=df_preds['ds'],
        y=df_preds['upper_interval'],
        name='Intervalo Superior',
        mode='lines',
        line=dict(color='#2EC2FF', width=1, shape='spline', dash='dash'),
        opacity=0.6
    ))
    fig.add_trace(go.Scatter(
        x=df_preds['ds'],
        y=df_preds['lower_interval'],
        name='Intervalo Inferior',
        mode='lines',
        line=dict(color='#2EC2FF', width=1, shape='spline', dash='dash'),
        opacity=0.6
    ))
    fig.update_layout(
        template='plotly_white',
        title=f'Previsão de Swaps - Cabinet {cabinet_id}',
        xaxis_title='Data',
        yaxis_title='Swaps',
        height=500, width=1200
    )

    fig.add_vline(x=df_preds.dropna()['ds'].max(), line_width=3, line_dash="dash", line_color="#8c00ff", )
    tile = st.container(border=True)
    tile.plotly_chart(fig, usecontainer_width=True)

    df_eval = df_preds.dropna(subset='counts')
    mae = round(mean_absolute_error(df_eval['counts'], df_eval['predicted']))
    tile.write(f'- Erro absoluto médio do modelo: **{mae}**')
    



