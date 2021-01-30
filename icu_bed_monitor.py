""" 
    Monitor de leitos de UTI para pacientes com COVID-19.
    Trabalho final da disciplina de simulação discreta.

    Alunos: 
        João Marcelo Almeida
        Isabela Maués

    Lista de pendências:
    - adicionar lógica que aloca mais leitos quando eles ficam próximo do treshold de ocupação máxima (mandatory)
    - adicionar a lógica que libera leitos quando eles ficam inativos por algumas semanas (mandatory)
    - (FEITO) Mostra um lineplot com a ocupação média usando o pacote termplotlib (nice to have)
    - Adiciona explicações relevantes sobre a simulação nesta docstring
    - formata o código antes da entrega final
    
    Dados relevantes sobre a pandemia na França:
    - data de início do primeiro lockdown nacional na França: 17 de março, semana 12, ocupação era de 14%, 1700 novas admissões
    - primeiro pico de admissões em UTIs: semana 14, duas semanas após o ínicio do lockdown

    - segundo lockdown na França: 28 de outubro a 14 de dezembro, semana 44, ocupação era de 30%, 2571 novas admissões
    - segundo pico de admissões em UTIS: semana 45, uma semana após o ínicio do lockdown

    (essa datas de pico de admissões fazem bastante sentido considerando o tempo médio de incubação do vírus
    e o tempo médio de ínicio da fase mais violenta da doença nos acometidos por ela)
"""

import argparse
from typing import List
import os
from shutil import which
import statistics

import numpy
import termplotlib as tpl
import simpy


# Argumentos padrões da simulação
DEFAULT_N_WEEKS = 52 # simula por um ano
NUMBER_OF_ICU_BEDS = 9860 # Número de leitos na França
NUMBER_OF_INITIAL_PATIENTS = 0 # Pacientes iniciais

# arguementos relacionados ao cenário de simulação 1: lockdown de dezembro extendido
SCENARIO_1_N_WEEKS = 10
SCENARIO_1_LOCKDOWN = list(range(5)) # lockdown vai da 1° a 4° semana de simulação
SCENARIO_1_PACIENTS = 2896 # Número de leitos ocupados em 14 de dezembro de 2020

# Arguemntos relacionados ao 2° cenário de simulação
SCENARIO_2_N_BEDS = 5054
SCENARIO_2_OCUPATION_TO_LOCKDOWN = 70.0 # pocentagem de ocupação limite (passou disso é lockdown)

# armazena algumas métricas importantes da simulação
ocupation_percentage_history = []
absolute_ocupation_history = []

# Dados para a geração dos eventos aleatórios
# valores são provenientes da análise exploratória dos dados sobre a ocupação
# de leitos na França, disponível em:
# ecdc.europa.eu/en/publications-data/download-data-hospital-and-icu-admission-rates-and-current-occupancy-covid-19
EVENTS_STATISTICS = {
    'admissions':{'mean':992.38, 'stdev':758.72, 'weeks':52},
    'discharges':{'mean':985.27, 'stdev':922.06, 'weeks':52}
}


class ICUMonitor():
    """ Contém a lógica de controle do monitor de leitos que será simulado """

    def __init__(self, env, n_weeks: int, n_beds: int, n_patients: int, ocupation_to_lockdown: float, adm_pdf: str, disc_pdf: str):
        """ Ao instanciar o monitor de leitos, considerar estes atributos inciais """

        self.env = env
        # o número de leitos inicialmente disponíveis é o total menos o inicialmente alocado
        self.beds = simpy.Container(env, n_beds, init=n_beds-n_patients)
        self.total_beds = n_beds

        self.ocupation_to_lockdown = ocupation_to_lockdown
        self.n_weeks = n_weeks
    
        # define qual função densidade de probabilidade é usada para gerar os
        # números de admissões e liberações semanais dosleitos
        self.admissions_pdf = adm_pdf
        self.discharges_pdf = disc_pdf
    
        # amostra os valores antes de iniciar a simulação
        self.admissions = self.generate_weekly_transit(kind="admissions")
        self.discharges = self.generate_weekly_transit(kind="discharges")


    def generate_weekly_transit(self, kind:str, n_weeks=None):
        """ Amostra o número de novas admissões semanais a partir de uma distribuição normal 
            kind: pode ser 'admissions' ou 'discharges' """

        #  obtém a função densidade de probabilidade desejada
        pdf = self.admissions_pdf if kind == "admissions" else self.discharges_pdf
        density_function = getattr(numpy.random, pdf)
        transit = None

        n_weeks = n_weeks or self.n_weeks

        if pdf == "exponential":
            # caveat: amostrar de uma exponencial não requer os desvio padrão da distribuição
            transit = density_function(
                EVENTS_STATISTICS[kind]['mean'],
                size=n_weeks
            )

        elif pdf == "lognormal" or pdf == "normal":            
            transit = density_function(
                EVENTS_STATISTICS[kind]['mean'],
                EVENTS_STATISTICS[kind]['stdev'],
                size=n_weeks
            )

        return sorted([int(i) for i in transit])


    def record_ocupation_percentage(self, week):
        """ Calcula e armazena estatísticas sobre a ocupação de leitos da semana """

        current_held_beds = self.total_beds - self.beds.level
        ocupation_percentage = current_held_beds / self.total_beds * 100
        
        absolute_ocupation_history.append(current_held_beds)
        ocupation_percentage_history.append(ocupation_percentage)
        print(f"Semana {week}: {self.total_beds} leitos: {current_held_beds}/{self.beds.level} (ocupados/livres). {round(ocupation_percentage)}% ocupado")

        return ocupation_percentage


def set_lockdown(curr_week: int, n_weeks: int):
    """ Configura o cenário de lockdown por 4 semanas """

    lockdown_interval = list(range(
        curr_week+1, # começa o lockdown na semana seguinte
        curr_week+5 # faz ele durar 4 semanas
        ))

    return lockdown_interval


def manage_lockdown(monitor, week: int, lockdown_interval: List, last_transmissibility: float):
    """ Altera os parametros da simulação simulando as alterações que ocorreriam
    na pandemia em caso de lockdown """

    if lockdown_interval == []:
        return last_transmissibility, lockdown_interval

    in_lockdown = week in lockdown_interval
    lockdown_start_week = lockdown_interval[0]
    lockdown_end_week = lockdown_interval[-1]
    
    # determina se precisa limpar os dados do último lockdown
    ended = False 
    if week > lockdown_end_week + 2:
        lockdown_interval = []
        ended = True

    recent_start = lockdown_start_week <= week <= lockdown_start_week +2
    recent_end = lockdown_end_week <= week <= lockdown_end_week + 2
    print('recent start', recent_start,'recent end', recent_end)
    
    if recent_start:
        transmissibility = 0.75
    elif in_lockdown:
        # O período de duas semanas após o ínicio do lockdown ainda não apresenta diminuição drástica no número de casos
        transmissibility = 0.25
    elif recent_end:
        # o período de duas semanas após o término do lockdown é marcado por um contágio brando
        transmissibility = 0.50
    elif ended:
        transmissibility = 1.00
    
    # determina se acabou o cooldown do lockdown por completo para reamostrar os dados
    if ended:
        print("Reamostrando!")
        remaining_weeks = monitor.n_weeks - week
        monitor.generate_weekly_transit('admissions', n_weeks=remaining_weeks)
        monitor.generate_weekly_transit('discharges', n_weeks=remaining_weeks)

    return transmissibility, lockdown_interval


def run_icu_bed_monitor(env, monitor, lockdown_interval: List[int]):
    """ Orquestra a simulação, semana a semana atualizando o
        monitor de leitos com as movimentações semanais.

        Argumentos:
        lockdown_interval: lista de inteiro com as semanas onde há lockdown
    """
    transmissibility = 1.0

    for week in range(1, monitor.n_weeks+1):

        transmissibility, lockdown_interval = manage_lockdown(monitor, week, lockdown_interval, transmissibility)

        admissions = int( monitor.admissions[week-1] * transmissibility )
        
        past_held_beds = monitor.total_beds - monitor.beds.level
        real_discharges = monitor.discharges[week-1]
        # Para garantir que não vamos liberar mais leitos do que os que estão ocupados
        discharges = real_discharges if real_discharges <= past_held_beds else past_held_beds
        print(f'\nSemana {env.now}: Liberou {discharges} e admitiu {admissions} pacientes')
        print(f'Em lockdown: {lockdown_interval != []}. Taxa de transmissão: {transmissibility*100}%')
        print(f'lockdown_interval: {lockdown_interval}')

        if discharges > 0:
            monitor.beds.put(discharges)
        if admissions > 0:
            monitor.beds.get(admissions)

        # calcual a ocupação percentual, se estiver acima do limite, decreta um lockdown (se não já estivermos em um)
        curr_ocupation = monitor.record_ocupation_percentage(env.now)
        if curr_ocupation > monitor.ocupation_to_lockdown and lockdown_interval == []:
            print('Ocupação suiperior ao limite: Decretando lockdown nacional!')
            lockdown_interval = set_lockdown(env.now, monitor.n_weeks)

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
                    dest="n_init_patients",
                    help=f'(Opcional) Número de pacientes iniciais, padrão é {NUMBER_OF_INITIAL_PATIENTS}')

parser.add_argument('-1',
                    '--cenario-1',
                    action='store_true',                    
                    default=False,
                    dest="scenario_1",
                    help='(Opcional) Define que o cenário de simulação 1 será executado.')

parser.add_argument('-2',
                    '--cenario-2',
                    action='store_true',                    
                    default=False,
                    dest="scenario_2",
                    help='(Opcional) Define que o cenário de simulação 2 será executado.')

parser.add_argument('-s',
                    '--semente',
                    type=int,
                    default=numpy.random.randint(1000),
                    dest="seed",
                    help='(Opcional) Semente de aleatoriedade para obtenção de resultados reproduzíveis.')


def plot_results():
    """ desenha na linha de comando gráficos com alguns resultado relevantes da simulação """
    
    # obtem as dimensões atuais do terminal
    term_height, term_width = os.popen('stty size', 'r').read().split()

    fig1 = tpl.figure()
    fig2 = tpl.figure()
    x = range(len(ocupation_percentage_history))
    
    print("\nOcupação percentual dos leitos ao longo das semanas:")
    fig1.plot(
        x=x,
        y=ocupation_percentage_history,
        width=int(term_width),
        height=int(term_height)//2
    )

    fig1.show()

    print("\nN° de leitos ocupados:")
    fig2.plot(
        x=x,
        y=absolute_ocupation_history,
        width=int(term_width),
        height=int(term_height)//2
    )

    fig2.show()


def simulate():
    """ Executa a simulação """

    args = parser.parse_args()

    numpy.random.seed(args.seed)
    # seed=918 dá bons resultados para o cenário geral
    # seed=273 dá bons resultados para o cenário 1
    # seed=226 dá bons resultados para o cenário 2

    # Executa a simulação
    env = simpy.Environment()
    monitor = ICUMonitor(
        env,
        n_weeks=SCENARIO_1_N_WEEKS if args.scenario_1 else args.n_weeks,
        n_patients=SCENARIO_1_PACIENTS if args.scenario_1 else args.n_init_patients,
        n_beds=SCENARIO_2_N_BEDS if args.scenario_2 else args.n_beds,
        ocupation_to_lockdown=SCENARIO_2_OCUPATION_TO_LOCKDOWN if args.scenario_2 else float('inf'),
        adm_pdf='normal',
        disc_pdf='normal' 
    )

    env.process(run_icu_bed_monitor(
        env=env, 
        monitor=monitor,
        lockdown_interval=SCENARIO_1_LOCKDOWN if args.scenario_1 else []
        ))
    
    print("Simulação iniciada. os parametros são\n:", args)
    env.run()
    print("\nSimulação finalizada.")

    # Apresenta gráficos sobre a ocupação média (se o cliente tiver gnuplot instalado)
    if which('gnuplot') is not None:
        plot_results()

    # salva os resultados em um .csv
    numpy.savetxt("results.csv", numpy.round(ocupation_percentage_history), delimiter =",", fmt='%1.1f')


if __name__ == "__main__":
    simulate()