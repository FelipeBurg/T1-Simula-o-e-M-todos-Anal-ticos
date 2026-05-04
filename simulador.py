import argparse
import heapq
import random
import yaml
from collections import defaultdict

class GeradorAleatorio:
    def __init__(self, limite, lista_fixa=None, seed=42):
        self.rng = random.Random(seed)
        self.limite = limite
        self.usados = 0
        self.lista_fixa = lista_fixa if lista_fixa else []


    #Aqui pedi pro Gemini ajustar o código, eu tava errando a lógica de usar os números fixos e depois os aleatórios, ele arrumou pra mim.
    def get_random(self):
        if self.usados >= self.limite:
            return None
        if self.usados < len(self.lista_fixa):
            r = self.lista_fixa[self.usados]
        else:
            r = self.rng.random()
        self.usados += 1
        return r

    def get_uniform(self, a, b):
        r = self.get_random()
        if r is None:
            return None
        return a + (b - a) * r

class Evento:
    def __init__(self, tempo, tipo, fila):
        self.tempo = tempo
        self.tipo = tipo
        self.fila = fila

    def __lt__(self, other):
        return self.tempo < other.tempo

class Fila:
    def __init__(self, nome, servers, capacity, minArrival=None, maxArrival=None, minService=1.0, maxService=2.0):
        self.nome = nome
        self.servidores = servers
        self.capacidade = capacity
        self.min_chegada = minArrival
        self.max_chegada = maxArrival
        self.min_servico = minService
        self.max_servico = maxService
        self.status = 0
        self.em_atendimento = 0
        self.perdas = 0
        self.tempos = defaultdict(float)
        self.roteamento = []

    def add_rota(self, probabilidade, fila_destino):
        self.roteamento.append((probabilidade, fila_destino))

    def proximo_destino(self, gerador):
        if not self.roteamento:
            return None
        # Ajuste para lidar com o caso de uma única rota com probabilidade 1.0, evitando chamadas desnecessárias ao gerador de números aleatórios.
        #Aqui depois de mandar pro Gemini avaliar se tava de acordo com o enunciado, ele colocou isso, o meu tava mais simples, tratava nada, só ia
        if len(self.roteamento) == 1 and self.roteamento[0][0] == 1.0:
            return self.roteamento[0][1]
        r = gerador.get_random()
        if r is None:
            return "FIM_SIMULACAO"
        acumulado = 0.0
        for prob, dest in self.roteamento:
            acumulado += prob
            if r <= acumulado:
                return dest
        return None

class Simulador:
    def __init__(self, gerador):
        self.filas = {}
        self.gerador = gerador
        self.eventos = []
        self.tempo_global = 0.0

    def agendar_evento(self, tempo, tipo, fila):
        heapq.heappush(self.eventos, Evento(tempo, tipo, fila))

    def executar(self, agendamentos_iniciais):
        for nome_fila, tempo_chegada in agendamentos_iniciais.items():
            if nome_fila in self.filas:
                self.agendar_evento(tempo_chegada, 'CHEGADA', self.filas[nome_fila])
        while self.eventos:
            evento = heapq.heappop(self.eventos)
            if self.gerador.usados >= self.gerador.limite:
                break
            delta_t = evento.tempo - self.tempo_global
            self.tempo_global = evento.tempo
            for fila in self.filas.values():
                fila.tempos[fila.status] += delta_t
            if evento.tipo == 'CHEGADA':
                self.trata_chegada(evento.fila)
            elif evento.tipo == 'SAIDA':
                self.trata_saida(evento.fila)

    def trata_chegada(self, fila):
        if fila.min_chegada is not None:
            tempo_interchegada = self.gerador.get_uniform(fila.min_chegada, fila.max_chegada)
            if tempo_interchegada is not None:
                self.agendar_evento(self.tempo_global + tempo_interchegada, 'CHEGADA', fila)
        self.entrar_na_fila(fila)

    def entrar_na_fila(self, fila):
        if fila.status < fila.capacidade:
            fila.status += 1
            if fila.em_atendimento < fila.servidores:
                fila.em_atendimento += 1
                tempo_servico = self.gerador.get_uniform(fila.min_servico, fila.max_servico)
                if tempo_servico is not None:
                    self.agendar_evento(self.tempo_global + tempo_servico, 'SAIDA', fila)
        else:
            fila.perdas += 1

    def trata_saida(self, fila):
        fila.status -= 1
        fila.em_atendimento -= 1
        if fila.status >= fila.servidores:
            fila.em_atendimento += 1
            tempo_servico = self.gerador.get_uniform(fila.min_servico, fila.max_servico)
            if tempo_servico is not None:
                self.agendar_evento(self.tempo_global + tempo_servico, 'SAIDA', fila)
        destino = fila.proximo_destino(self.gerador)
        if destino == "FIM_SIMULACAO":
            return
        elif destino is not None:
            self.entrar_na_fila(destino)

    def imprimir_relatorio(self):
        print("\n" + "="*50)
        print("RESULTADOS DA SIMULACAO")
        print("="*50)
        print(f"Tempo global da simulacao: {self.tempo_global:.4f}")
        print(f"Numeros aleatorios consumidos: {self.gerador.usados}\n")
        for nome in sorted(self.filas.keys()):
            f = self.filas[nome]
            print(f"--- {f.nome} ---")
            print(f"Servidores: {f.servidores} | Capacidade: {'Infinita' if f.capacidade > 99999 else f.capacidade}")
            print(f"Total de Perdas: {f.perdas}")
            print("\n Estado | Tempo Acumulado | Probabilidade")
            print("-" * 43)
            estados = sorted(f.tempos.keys())
            for estado in estados:
                tempo = f.tempos[estado]
                probabilidade = (tempo / self.tempo_global) if self.tempo_global > 0 else 0.0
                print(f"   {estado:>4} | {tempo:>15.4f} | {probabilidade:>12.2%}")
            print("\n")

def carregar_e_simular(arquivo_yml):
    with open(arquivo_yml, 'r') as file:
        config = yaml.safe_load(file)
    aleatorios_lista = config.get('rndnumbers', [])
    limite = config.get('rndnumbersPerSeed', len(aleatorios_lista) if aleatorios_lista else 100000)
    seeds = config.get('seeds', [1])
    gerador = GeradorAleatorio(limite=limite, lista_fixa=aleatorios_lista, seed=seeds[0])
    sim = Simulador(gerador)
    for q_nome, q_dados in config.get('queues', {}).items():
        fila = Fila(
            nome=q_nome,
            servers=q_dados.get('servers', 1),
            capacity=q_dados.get('capacity', float('inf')),
            minArrival=q_dados.get('minArrival'),
            maxArrival=q_dados.get('maxArrival'),
            minService=q_dados.get('minService', 1.0),
            maxService=q_dados.get('maxService', 2.0)
        )
        sim.filas[q_nome] = fila
    for rota in config.get('network', []):
        origem = sim.filas.get(rota['source'])
        destino = sim.filas.get(rota['target'])
        if origem and destino:
            origem.add_rota(rota['probability'], destino)
    agendamentos = config.get('arrivals', {})
    sim.executar(agendamentos)
    sim.imprimir_relatorio()

# Ponto de entrada do script: pega o nome do arquivo do terminal e roda
def main():
    parser = argparse.ArgumentParser(description="Simulador de Redes de Filas")
    parser.add_argument("--modelo", type=str, default="modelo.yml", help="Caminho para o arquivo YAML")
    args = parser.parse_args()
    
    print(f"Carregando o modelo: {args.modelo}")
    carregar_e_simular(args.modelo)

if __name__ == "__main__":
    main()

    #Não esquecer de apagar comentários antes de entregar.