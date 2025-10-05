Para distribuir novos cabinets de maneira inteligente, trabalhamos com as 5 seguintes features:

- **swaps_per_cabinet:** média diária de swaps / nº de cabinets
- **swaps_per_observation:** swaps totais / volume de tráfego
- **observation_per_swaps:** volume de tráfego / swaps totais
- **nearest_station_distance_km:** distância da estação mais próxima
- **cabinet_number:** número de cabinets (na última semana)

Todas essas métricas podem ter seus pesos ajustados na hora de orimizar, mas antes disso, é importante entender os conceitos de negócio que as features **observation_per_swaps** e **swaps_per_observations** representam.

#### Interpretação dos Indicadores

- O indicador **swaps_per_observation** é definido como:

$$
\text{swaps\_per\_observation} = \frac{\text{swaps\_count}}{\text{observations}}
$$

Ele mede a eficiência da estação em converter o tráfego de motos próximas em swaps. Valores altos indicam que, mesmo com pouco tráfego, a estação consegue realizar muitas trocas, o que sugere alta eficiência e demanda. Valores baixos indicam que há muito tráfego passando, mas poucas trocas acontecendo, o que pode revelar um potencial de subutilização da estação. Essa variável é positivamente correlacionada com o número de cabinets.

- Por outro lado, o indicador **observations_per_swap** é definido como:

$$
\text{observations\_per\_swap} = \frac{\text{observations}}{\text{swaps\_count}}
$$

Este é essencialmente o inverso do anterior e representa quantos veículos observados passam pela estação para cada swap realizado. Valores altos indicam que, para cada troca, muitas motos passam pela estação sem utilizar o serviço, o que pode sugerir que a estação precisa de mais cabinets para atender à demanda ou está mal posicionada. Já valores baixos indicam que cada moto que passa tem alta probabilidade de realizar um swap, sugerindo que a estação é eficiente ou próxima da saturação. Esse indicador é negativamente correlacionada com o número de cabinets.

Essas duas métricas são, portanto, inversamente proporcionais: quando uma é alta, a outra tende a ser baixa. Em geral, quando o **swaps_per_observation** é baixo e o **observations_per_swap** é alto, significa que há grande tráfego mas poucas trocas, sinalizando oportunidade de melhoria com a adição de mais cabinets. Por outro lado, quando o **swaps_per_observation** é alto e o **observations_per_swap** é baixo, isso quer dizer que a estação já opera de maneira eficiente.

#### Otimização

Agora que já entedemos os conceitos envolvidos na otimização, o critério base de alocação de cabinets foi calculado a partir dos seguintes pesos atribuídos a cada variável:

- **w_swaps_cabinet = 35%**  
  Prioriza a eficiência ou saturação dos gabinetes já instalados, favorecendo estações que fazem mais swaps por gabinete.

- **w_obs_per_swaps = 30%**  
  Destaca locais com tráfego alto e poucas trocas, sugerindo potencial para crescimento com mais gabinetes.

- **w_swaps_per_obs = 15%**  
  Mede a capacidade de converter tráfego em swaps. Indica quão bem a estação atende à demanda que passa por ela.

- **w_distance = 10%**  
  Atua como leve penalização logística, desfavorecendo locais muito perto de outras estações.

- **w_cabinet_number = 10%**  
  Penaliza de forma sutil estações que já possuem muitos gabinetes, evitando subutilização.

**Estratégia Priorizada**

Essa configuração base favorece:
- **Eficiência**: dá mais valor a estações que já operam bem (ou que possuem cabinets saturados).  
- **Oportunidade de expansão**: identifica locais onde há demanda reprimida.  
- **Equilíbrio operacional**: desprioriza alocação em estações muito próxima de outras ou com excesso de cabinets.