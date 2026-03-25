# Conversazione Compatta 2026-03-25

## Obiettivo

Verificare la montabilita reale delle soluzioni geometriche del puzzle, eliminando i falsi positivi del checker semplificato.

## Cosa e stato fatto

1. Analisi della soluzione 62 con descrizione fisica del montaggio passo-passo.
2. Confronto tra checker: emersa discrepanza tra logica semplificata e solver.
3. Allineamento degli script al criterio del solver principale.
4. Revisione del criterio di inserimento nel solver per gestire meglio i vincoli di shift.
5. Introduzione del vincolo di orientazione coerente con la progressione della sequenza.
6. Semplificazione output di stampa delle soluzioni montabili in ordine di sequenza valida.

## Risultati finali

- Soluzioni totali testate: 376
- Soluzioni montabili: 17
- Soluzioni non montabili: 359
- La soluzione 62 e NON montabile in tutte e 4 le sequenze standard.

## Verifiche chiave

- Caso 62: confermata non montabilita con criterio aggiornato.
- Caso 184: confermato blocco in Seq1 al passo V2, coerente con analisi manuale.

## File modificati

- check_assemblability.py
  - usa il criterio del solver
  - stampa le montabili in formato semplice, in ordine della sequenza valida (H0:[...], V0:[...], ...)
- puzzle_solver.py
  - raffinata la logica di _can_insert/_feasible_relative_shift
  - aggiunto vincolo sul verso di inserimento dedotto dalla progressione degli indici
- print_solution_62.py
  - verifica reale delle 4 sequenze invece di testo hardcoded

## Elenco montabili (indici)

208, 209, 210, 211, 212, 213, 214, 215, 240, 241, 242, 243, 246, 252, 253, 254, 255

## Note

- In working tree risulta modificato anche puzzle_solutions_unique_geometric.json.
- Nessun errore di lint/sintassi nei file Python aggiornati.
