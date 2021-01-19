""" 
    Monitor de leitos de UTI para pacientes com COVID-19.
    Trabalho final da disciplina de simulação discreta.

    Alunos: 
        João Marcelo Almeida
        Isabela Maués

    Lista de pendências:
    - adicionar lógica que aloca mais leitos quando eles ficam próximo do treshold de ocupação máxima (mandatory)
    - adicionar a lógica que libera leitos quando eles ficam inativos por algumas semanas (mandatory)
    - Mostra um lineplot com a ocupação média usando o pacote termplotlib (nice to have)
    - Adiciona explicações relevantes sobre a simulação nesta docstring
    - formata o código antes da entrega final
    
"""

import random
import statistics
import argparse

import simpy


# Argumentos padrões da simulação
RANDOM_SEED = 42
DEFAULT_N_WEEKS = 52 # simula por um ano
NUMBER_OF_ICU_BEDS = 9860 # Número de leitos na França
NUMBER_OF_INITIAL_PATIENTS = 100 # Pacientes iniciais
TIME_TO_CLOSE_BED = 3 # semanas para desativar leitos vazios
MAX_OCUPATION_TO_NEW_BEDS = 0.80 # limite de ocupação para a criação de novos leitoss

# armazena algumas métricas importantes da simulação
ocupation_percentage_history = []
waiting_for_bed_history = []

# Dados para a geração dos eventos aleatórios
# valores são provenientes da análise exploratória dos dados sobre a ocupação
# de leitos na França, disponível em:
# ecdc.europa.eu/en/publications-data/download-data-hospital-and-icu-admission-rates-and-current-occupancy-covid-19
EVENTS_STATISTICS = {
    'weekly_admissions':{'mean':992.38, 'stdev':758.72},
    'weekly_discharges':{'mean':985.27, 'stdev':922.06}
}


class ICUMonitor():
    """ Contém a lógica de controle do monitor de leitos que será simulado """

    def __init__(self, env, n_beds, n_initial_patients):
        """ Ao instanciar o monitor de leitos, considerar estes atributos inciais """

        self.env = env
        self.beds = simpy.Container(env, n_beds, init=n_beds)
        self.total_beds = n_beds
        self.wainting_for_bed = 0


    def weekly_admissions(self):
        """ Gera o número de novas admissões semanais a partir de uma distribuição normal """

        admissions = random.gauss(
            EVENTS_STATISTICS['weekly_admissions']['mean'],
            EVENTS_STATISTICS['weekly_admissions']['stdev']
        )
        return int(admissions)

    def weekly_dischages(self):
        """ Gera o número semanal de altas de UTI """

        discharges = random.gauss(
            EVENTS_STATISTICS['weekly_discharges']['mean'],
            EVENTS_STATISTICS['weekly_discharges']['stdev']
        )
        return int(discharges)


def run_icu_bed_monitor(env, monitor, n_weeks):
    """ Orquestra a simulação, semana a semana atualizando o
        monitor de leitos com as movimentações semanais """

    for _ in range(n_weeks):
        admissions = monitor.weekly_admissions()
        # solução temporária até gerar um número coerente de liberações
        past_held_beds = monitor.total_beds - monitor.beds.level
        real_discharges = monitor.weekly_dischages()
        discharges = real_discharges if real_discharges <= past_held_beds else past_held_beds

        #TODO: aloca mais ou libera leitos se a demanda pedir isso

        if discharges > 0:
            monitor.beds.put(discharges)
        if admissions > 0:
            monitor.beds.get(admissions)

        print(f'\nSemana {env.now}: Liberou {discharges} e admitiu {admissions} pacientes')

        curent_held_beds = monitor.total_beds - monitor.beds.level
        ocupation_percentage = monitor.beds.level/monitor.total_beds * 100
        ocupation_percentage_history.append(ocupation_percentage)
        #waiting_for_bed_history.append()

        # Apresenta na linha de comando um resumo da semana
        print(f"Semana {env.now}: {monitor.total_beds} leitos ({curent_held_beds} ocupados e {monitor.beds.level} livres). Ocupação de {int(ocupation_percentage)}%")

        yield env.timeout(1)


# ArgumentParser para coletar argumentos através da linha de comando
parser = argparse.ArgumentParser(description='Simulador de ocupação de leitos de UTI para pacientes com COVID-19.')
parser.add_argument('-t',
                    '--tempo-de-simulacao',
                    type=int,
                    default=DEFAULT_N_WEEKS,
                    dest="n_weeks",
                    help=f'(Opcional) Tempo da simulação em semanas; padrão é {DEFAULT_N_WEEKS}')
parser.add_argument('-l',
                    '--leitos',
                    type=int,
                    default=NUMBER_OF_ICU_BEDS,
                    dest="n_beds",
                    help=f'(Opcional) Número de leitos de UTI disponíveis, padrão é {NUMBER_OF_ICU_BEDS}')
parser.add_argument('-p',
                    '--pacientes-iniciais',
                    type=int,
                    default=NUMBER_OF_INITIAL_PATIENTS,
                    dest="n_initial_patients",
                    help=f'(Opcional) Número de pacientes iniciais, padrão é {NUMBER_OF_INITIAL_PATIENTS}')
                    
parser.add_argument('-s',
                    '--semente',
                    type=int,
                    default=RANDOM_SEED,
                    dest="seed",
                    help='(Opcional) Semente de aleatoriedade para obtenção de resultados reproduzíveis.')


def simulate():
    """ Executa a simulação """

    args = parser.parse_args()
    random.seed(args.seed)

    # Executa a simulação
    env = simpy.Environment()
    monitor = ICUMonitor(env, args.n_beds, args.n_initial_patients)
    env.process(run_icu_bed_monitor(env, monitor, args.n_weeks))
    env.run()
    print("\nSimulação finalziada. Algumas estatísticas abaixo:")

    # TODO: apresenta dados sobre a ocupação média    


if __name__ == "__main__":
    simulate()