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
  python3 icu_bed_monitor.py 
  
  # Cenário 1: lockdowns rigorosos
  python3 icu_bed_monitor.py --scenario-1
  
  # Cenário 2: extensão do lockdown de final de ano
  python3 icu_bed_monitor.py --scenario-2
```
