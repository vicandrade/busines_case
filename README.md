# Previsão e Otimização de Swaps por Cabinets 🏍️🔋

Este projeto tem como objetivo prever a demanda de swaps em cabinets específicos e otimizar a alocação de cabinets entre estações, com base em métricas de eficiência operacional e demanda histórica.

---

## Estrutura do Projeto
```text
├── src/
│ ├── preprocessing/ # Scripts de limpeza e preparação de dados
│ │ ├── swaps_transform.py # Transformação dos dados de swaps
│ │ ├── stations_transform.py # Transformação dos dados das estações
│ │ ├── traffic_transform.py # Transformação dos dados de tráfego
│ │ └── merge_data.py # Agregação dos dados e cálculos interseccionais
│ ├── modeling/ # Modelagem de séries temporais horárias e diárias
│ │ ├── transform_model_data.py # Transformação dos dados para modelagem
│ │ └── make_predictions.py # Treinamento dos modelos e geração das previsões
│ ├── run_preprocessing_pipeline.py # Roda as funções de transformação e salva os dados
│ └── run_modeling_pipeline.py # Roda as funções de modelagem e salva os dados
├── notebooks/
│ ├── cabinets_allocation_report.ipynb # Estudo de alocação e remoção de cabinets
│ ├── hourly_swaps_prediction_study.ipynb # Testes de diferentes modelos de previsão
│ └── ...
├── data/
│ ├── raw/ # Dados brutos
│ ├── processed/ # Dados tratados
│ └── model/ # Predições e outputs dos modelos
├── app/
│ └── .. # Webapp
├── README.md
└── requirements.txt
```
---

## Pipeline de Pré-processamento (`src/preprocessing`)

1. **Limpeza e normalização dos dados:**  
   - Conversão de datas, remoção de duplicatas, preenchimento de valores nulos.  
   - Criação de métricas como `swaps_per_day_mean`, `swaps_per_hour_mean`, `swaps_per_observation` e `observations_per_swaps`.

2. **Agregações:**  
   - Séries horárias e diárias por `swap_station_id` e `cabinet_id`.

---

## Modelagem de Séries Temporais (`src/modeling`)

1. **Séries horárias e diárias:**  
   - Modelos probabilísticos e baseados em regressão (LightGBM, Prophet) para prever swaps futuros.  
   - Considera indisponibilidade, sazonalidade e lags das métricas.

2. **Avaliação:**  
   - Métricas como MAPE, RMSE e análise visual das predições.  
   - Intervalos de confiança e comparação entre diferentes modelos.

---

## Estudo de Alocação e Remoção de Cabinets (`notebooks/cabinets_allocation_report.ipynb`)

1. **Alocação de novos cabinets:**  
   - Calcula um `priority_score` baseado em métricas de eficiência (`swaps_per_cabinet`, `swaps_per_observation`, `observations_per_swaps`) e penalidades (`cabinet_number`, `nearest_station_distance_km`).  
   - Estima ganho potencial em `swaps_per_day_mean` para cada alocação sugerida.  

2. **Remoção de cabinets:**  
   - Identifica cabinets subutilizados ou em excesso.  
   - Calcula perda estimada ao remover cada cabinet, mantendo eficiência global.  
   - Resultado final unificado em um dataframe com alocações positivas (adição) e negativas (remoção).

---

## Notebooks de Estudo da Modelagem (`notebooks/hourly_swaps_prediction_study.ipynb`)

- Explora diferentes abordagens de séries temporais horárias e diárias.  
- Analisa correlação entre métricas operacionais e número de cabinets.  
- Testa diferentes estratégias de previsão e validação.

---

## Métricas e Estratégias de Negócio

- **swaps_per_cabinet:** eficiência individual do cabinet.  
- **swaps_per_observation / observations_per_swaps:** conversão de tráfego em swaps, indicam demanda e saturação.  
- **nearest_station_distance_km:** penaliza sobreposição de estações.  
- **cabinet_number:** penaliza excesso ou falta de cabinets.

O pipeline de alocação prioriza aumento de swaps onde há alta demanda ou subutilização, enquanto a remoção evita desperdício e realoca recursos de forma eficiente.

---

## Autor

Vic Martins - Cientista de Dados

Consultoria em ciência de dados.
