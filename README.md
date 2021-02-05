### Simulando a ocupação de leitos de UTI para pacientes com COVID-19 na França
Tarefa final da disciplina de simulação discreta.

### Para executar a simulação:
```bash
 
  # obter pacotes requeridos
  pip3 install -r numpy simpy termplotlib
  
  # opcional: obter gnuplot
  sudo apt-get update -y
  sudo apt-get install -y gnuplot
  
  # Caso de simulação base:
  python3 monitor_de_leitos.py 
  
  # Cenário 1: lockdowns rigorosos
  python3 monitor_de_leitos.py --cenario-1
  
  # Cenário 2: extensão do lockdown de final de ano
  python3 monitor_de_leitos.py --cenario-2
```
A planilha com os dados de entrada e resultado da modelagem desses dados que levam à algumas estatísticas e ao resultado do teste de aderência realizado pode ser encontrada em: https://docs.google.com/spreadsheets/d/176aqE50vxrDAmuBBzOE0HoBtBPD4Z3L_j4x26tSKxpo/edit?usp=sharing
