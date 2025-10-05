import pandas as pd
import streamlit as st
from media import render_img_html
import numpy as np

# Função auxiliar para normalizar valores
def normalize(series):
    return (series - series.min()) / (series.max() - series.min() + 1e-9)

def suggest_cabinets_allocation(df, cabinets_to_add=10, max_cabinets=8, exponent=5, w_swaps_cabinet=0.35, w_swaps_per_obs=0.15, w_obs_per_swaps=0.3, w_distance=0.1, w_cabinet_number=0.1):
    df_alloc = df[df['cabinet_number']<max_cabinets].reset_index(drop=True).copy()

    # Normalização dos scores
    df_alloc['score_swaps_cabinet'] = normalize(df_alloc['swaps_per_cabinet'])
    df_alloc['score_swaps_per_obs'] = normalize(df_alloc['swaps_per_observation'])
    df_alloc['score_obs_per_swaps'] = normalize(df_alloc['observations_per_swaps'])
    df_alloc['score_distance'] = normalize(df_alloc['nearest_station_distance_km'])
    df_alloc['score_cabinet_number'] = 1 / (1 + df_alloc['cabinet_number'])

    # Score de prioridade final
    df_alloc['priority_score_raw'] = (
          w_swaps_cabinet * df_alloc['score_swaps_cabinet']
        + w_swaps_per_obs * df_alloc['score_swaps_per_obs']
        + w_obs_per_swaps * df_alloc['score_obs_per_swaps']
        + w_distance * df_alloc['score_distance']
        + w_cabinet_number * df_alloc['score_cabinet_number']
    )

    # Aplicação de potência para maior diferenciação
    df_alloc['priority_score'] = df_alloc['priority_score_raw'] ** exponent
    
    # Alocação dos novos gabinetes
    df_alloc['allocation_float'] = (df_alloc['priority_score'] / df_alloc['priority_score'].sum()) * cabinets_to_add
    df_alloc['allocation'] = np.floor(df_alloc['allocation_float'])
    
    # Distribuir o restante (depois do floor)
    remaining = cabinets_to_add - int(df_alloc['allocation'].sum())
    if remaining > 0:
        top_up = df_alloc.sort_values('allocation_float', ascending=False).head(remaining).index
        df_alloc.loc[top_up, 'allocation'] += 1

    # Estimativa de ganho
    df_alloc['new_swaps_per_day_mean'] = df_alloc['swaps_per_day_mean'] + \
        df_alloc['swaps_per_cabinet'] * np.log1p(df_alloc['allocation']) / np.log1p(df_alloc['cabinet_number'] + 1)
    
    df_alloc['gain'] = df_alloc['new_swaps_per_day_mean'] - df_alloc['swaps_per_day_mean']

    # Organização do dataframe com os resultados
    cols = [
        'swap_station_id', 'allocation', 'cabinet_number', 
        'swaps_per_day_mean', 'new_swaps_per_day_mean', 'gain',
        'swaps_per_cabinet', 'swaps_per_observation', 
        'observations_per_swaps', 'nearest_station_distance_km']
    df_alloc = (
        df_alloc[df_alloc['allocation']>0][cols]
        .sort_values('allocation', ascending=False)
        .round(3)
        .reset_index(drop=True)
    )

    return df_alloc

def suggest_cabinets_removal(df, cabinets_to_remove=10, min_cabinets=1, min_cabinets_remaining=0, w_swaps_cabinet=0.35, w_swaps_per_obs=0.15, w_obs_per_swaps=0.3, w_distance=0.1, w_cabinet_number=0.1):
    df_rem = df[df['cabinet_number'] > min_cabinets].copy()

    # Normalizações
    df_rem['score_swaps_cabinet'] = normalize(df_rem['swaps_per_cabinet'])
    df_rem['score_swaps_per_obs'] = normalize(df_rem['swaps_per_observation'])
    df_rem['score_obs_per_swaps'] = normalize(df_rem['observations_per_swaps'])
    df_rem['score_distance'] = normalize(df_rem['nearest_station_distance_km'])
    df_rem['score_cabinet_number'] = 1 / (1 + df_rem['cabinet_number'])

    # Priority score “menos eficiente”
    df_rem['priority_score_raw'] = (
          w_swaps_cabinet * df_rem['score_swaps_cabinet']
        + w_swaps_per_obs * df_rem['score_swaps_per_obs']
        + w_obs_per_swaps * df_rem['score_obs_per_swaps']
        + w_distance * df_rem['score_distance']
        + w_cabinet_number * df_rem['score_cabinet_number']
    )
    df_rem['priority_score'] = df_rem['priority_score_raw'] ** 5

    # Score invertido para remoção
    df_rem['inverse_score'] = 1 / (df_rem['priority_score'] + 1e-9)

    # Distribuição inicial proporcional
    df_rem['removal_float'] = (df_rem['inverse_score'] / df_rem['inverse_score'].sum()) * cabinets_to_remove
    df_rem['removal'] = np.floor(df_rem['removal_float']).astype(int)

    # -------- Redistribuição iterativa para respeitar min_cabinets --------
    while df_rem['removal'].sum() < cabinets_to_remove:
        remaining = cabinets_to_remove - df_rem['removal'].sum()
        # Estaçoes que ainda podem perder cabinets
        df_rem['max_removable'] = df_rem['cabinet_number'] - min_cabinets - df_rem['removal']
        candidates = df_rem[df_rem['max_removable'] > 0]
        if candidates.empty:
            break  # não há mais onde remover
        # Ordenar por inverso do score (menos eficiente primeiro)
        candidates = candidates.sort_values('inverse_score', ascending=False)
        for idx in candidates.index:
            if remaining == 0:
                break
            df_rem.at[idx, 'removal'] += 1
            remaining -= 1

    # Garantir que não violamos min_cabinets
    df_rem['removal'] = df_rem.apply(
        lambda row: min(row['removal'], max(row['cabinet_number'] - min_cabinets_remaining, 0)), axis=1
    )

    # Estimativa de perda
    df_rem['new_swaps_per_day_mean'] = df_rem['swaps_per_day_mean'] - \
        df_rem['swaps_per_cabinet'] * np.log1p(df_rem['removal'].abs()) / np.log1p(df_rem['cabinet_number'])
    df_rem['loss'] = df_rem['swaps_per_day_mean'] - df_rem['new_swaps_per_day_mean']

    # Organização final
    cols = [
        'swap_station_id', 'removal', 'cabinet_number', 
        'swaps_per_day_mean', 'new_swaps_per_day_mean', 'loss',
        'swaps_per_cabinet', 'swaps_per_observation', 
        'observations_per_swaps', 'nearest_station_distance_km']
    
    df_rem = (
        df_rem[df_rem['removal']>0][cols]
        .sort_values('removal', ascending=False)
        .round(3)
        .reset_index(drop=True)
    )
    
    return df_rem

def cabinet_allocation_page():
    cols = st.columns([1, 1, 15])
    with cols[0]:
        render_img_html("imgs/client_logo.png", 125)
    
    st.header('Alocação Inteligente de Cabinets', divider='blue')
    
    # Ler aqruivos
    arquivos = {
        'stations': '../data/processed/stations_processed.parquet',
        'allocation_md': 'allocation.md',
    }

    # Carregar CSV normalmente
    if 'stations' not in st.session_state:
        st.session_state['stations'] = pd.read_parquet(arquivos['stations'], engine='pyarrow')
    
    # Carregar Markdown como string
    if 'allocation_md' not in st.session_state:
        with open(arquivos['allocation_md'], 'r', encoding='utf-8') as f:
            st.session_state['allocation_md'] = f.read()

    df = st.session_state['stations']
    allocation_md = st.session_state['allocation_md']

    st.markdown(allocation_md)

    st.divider()
    
    st.write('**Seleções**')
    cols = st.columns(4)
    cabinets_to_add = cols[0].number_input('Qtd. de cabinets a adicionar', min_value=1, max_value=100, value=10, step=1)
    cabinets_to_remove = cols[1].number_input('Qtd. de cabinets a remover', min_value=1, max_value=50, value=3, step=1)
    max_cabinets = cols[2].number_input('Selecionar estações com qtd. de cabinets abaixo de', min_value=1, max_value=15, value=8, step=1)

    st.write('**Pesos**')
    cols = st.columns(5)
    w_swaps_cabinet = cols[0].number_input('Peso: swaps/cabinet', min_value=0.01, max_value=1.0, value=0.35, step=0.05)
    w_swaps_per_obs = cols[1].number_input('Peso: obs/swaps', min_value=0.01, max_value=1.0, value=0.3, step=0.05)
    w_obs_per_swaps = cols[2].number_input('Peso: swaps/obs', min_value=0.01, max_value=1.0, value=0.15, step=0.05)
    w_distance = cols[3].number_input('Peso: distância', min_value=0.01, max_value=1.0, value=0.1, step=0.05)
    w_cabinet_number = cols[4].number_input('Peso: nº cabinets', min_value=0.01, max_value=1.0, value=0.1, step=0.05)

    st.write('#### Alocação de Cabinets')
    df_alloc = suggest_cabinets_allocation(
        df, cabinets_to_add=cabinets_to_add, max_cabinets=max_cabinets, w_swaps_cabinet=w_swaps_cabinet, 
        w_swaps_per_obs=w_swaps_per_obs, w_obs_per_swaps=w_obs_per_swaps, w_distance=w_distance, 
        w_cabinet_number=w_cabinet_number
    )
    st.dataframe(df_alloc)

    gain_sum = df_alloc.gain.sum().round(2)
    gain_mean = df_alloc.gain.mean().round(2)
    st.write(f'Com a alocação configurada acima, estima-se:')
    st.write(f'- Ganho total de **{gain_sum}** swaps diários;') 
    st.write(f'- Média de ganho de **{gain_mean}** swaps diários por estação.')

    st.write('#### Remoção de cabinets')
    df_remove = suggest_cabinets_removal(
        df, cabinets_to_remove=cabinets_to_remove, w_swaps_cabinet=w_swaps_cabinet, 
        w_swaps_per_obs=w_swaps_per_obs, w_obs_per_swaps=w_obs_per_swaps, w_distance=w_distance, 
        w_cabinet_number=w_cabinet_number
    )
    st.dataframe(df_remove)
    loss_sum = df_remove.loss.sum().round(2)
    loss_mean = df_remove.loss.mean().round(2)
    st.write(f'Com a alocação configurada acima, estima-se:')
    st.write(f'- Perda total de **{loss_sum}** swaps diários;') 
    st.write(f'- Média de perda de **{loss_mean}** swaps diários por estação.')
