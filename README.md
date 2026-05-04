# Simulador de Redes de Filas (G/G/n/K)

Este projeto consiste em um simulador de eventos discretos genérico para redes de filas, permitindo a modelagem de topologias complexas com múltiplas filas, roteamento baseado em probabilidades e capacidades finitas ou infinitas. O simulador é configurado externamente via arquivos YAML.

## Pré-requisitos
- Python 3.x
- Biblioteca PyYAML (para processamento do arquivo de configuração)

## Instalação
Para instalar a única dependência necessária, execute o comando abaixo no seu terminal:

pip install pyyaml

## Como Executar
1. Clone o repositório
2. Instale a dependência
3. Execute o simulador através do comando:

python simulador.py --modelo modelo.yml

## Configuração do Modelo (modelo.yml)
O arquivo de configuração permite definir as chegadas externas, os parâmetros de cada fila (servidores, capacidade, tempos de serviço) e a rede de roteamento. Abaixo está o exemplo configurado para a topologia de validação:

arrivals: 
   Q1: 2.0

queues: 
   Q1: 
      servers: 1
      capacity: 999999
      minArrival: 2.0
      maxArrival: 4.0
      minService: 1.0
      maxService: 2.0
   Q2: 
      servers: 2
      capacity: 5
      minService: 4.0
      maxService: 6.0
   Q3: 
      servers: 2
      capacity: 10
      minService: 5.0
      maxService: 15.0

network: 
-  source: Q1
   target: Q2
   probability: 0.8
-  source: Q1
   target: Q3
   probability: 0.2
-  source: Q2
   target: Q1
   probability: 0.3
-  source: Q2
   target: Q3
   probability: 0.5
-  source: Q3
   target: Q2
   probability: 0.7

rndnumbersPerSeed: 100000
seeds: 
- 1
