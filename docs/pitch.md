# Pitch do projeto Rota Inteligente

O vídeo local é silencioso e traz legendas em português do Brasil na imagem. O texto das legendas acompanha o roteiro abaixo. Na demonstração, execute o comando na raiz e abra o grafo gerado.

## Rota Inteligente

Em horários de pico, a Sabor Express precisa decidir quais pedidos cada entregador leva e em que ordem deve atendê-los. No protótipo Rota Inteligente, simulamos esse problema para medir quanto uma estratégia de roteirização pode reduzir o custo de deslocamento.

## Da cidade ao grafo

O mapa tem quinze pontos. Cada rua é representada por um arco dirigido com dois pesos, distância e tempo. Uma rua de mão única aparece apenas no sentido permitido. Para representar um bloqueio total, retiramos os arcos nos dois sentidos. Todos os entregadores saem da base e voltam a ela.

## Como a rota é calculada

O A estrela combina o custo percorrido com uma estimativa do custo restante. A estimativa usa a distância em linha reta multiplicada pelo menor custo por unidade de distância na rede. O K-Means agrupa os pedidos em zonas, com um grupo por entregador. Finalmente, a programação dinâmica encontra a melhor sequência dentro de cada grupo pequeno. Para grupos com mais de dez paradas, usamos a heurística do vizinho mais próximo.

## Demonstração

Para rodar o cenário principal, execute python -m src no terminal. O programa compara três estratégias: atender na ordem de chegada, otimizar a ordem mantendo os grupos iniciais, e otimizar a ordem depois do K-Means. O JSON contém as paradas e as ruas percorridas. O grafo mostra as zonas de entrega e os caminhos dos dois entregadores.

## O que os números mostram

No pico, a reordenação por si só reduziu o tempo somado de duzentos e dez para cento e trinta minutos. Com K-Means, o tempo caiu para cento e oito, uma redução de quarenta e oito vírgula seis por cento em relação à referência. Para calcular caminhos entre cento e cinquenta e seis pares, o A estrela realizou novecentas e oitenta e nove expansões, contra mil trezentas e oitenta e nove do Dijkstra.

## Quando agrupar ajuda

No cenário normal, a estratégia agrupada levou noventa e oito minutos, contra oitenta e oito da referência. Agrupar pela proximidade no mapa pode piorar o resultado quando as ruas têm tempos e sentidos diferentes. A simulação é reproduzível. Para avaliar o ganho em operação, o próximo passo seria testar com dados reais e incluir capacidade, prazos e trânsito.
