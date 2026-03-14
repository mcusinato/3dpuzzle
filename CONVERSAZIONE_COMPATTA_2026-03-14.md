# Conversazione Compatta - 2026-03-14

## Obiettivo
Correggere e rendere piu robusto il controllo di montabilita in `soluzione_puzzle3d.py`, poi migliorare output e opzioni CLI.

## Problemi identificati
- `assembly-check` dava esiti incoerenti su casi reali discussi (blocchi attesi su `V3`).
- Nel check verticale c'era un falso confronto aggregato (`max(required)` vs `min(available)` su coppie diverse).
- La stima locale delle capacita non modellava bene i vincoli accoppiati tra pezzi gia montati.

## Correzioni tecniche applicate
- Fix del ramo inserimento verticale:
  - rimosso il confronto aggregato incoerente;
  - decisione basata sul vero esito pairwise (`worst_block`).
- Correzione direzione di movimento richiesta al pezzo opposto.
- Introduzione modello globale a vincoli di differenza tra spostamenti relativi (Floyd-Warshall) per calcolare lo shift massimo disponibile tra coppie di pezzi gia montati.

## Risultato sul caso utente
- Configurazione segnalata: ora passa `V2` e blocca `V3` con `insufficient_vertical_spread`, coerente con l'analisi manuale.

## Nuove funzionalita CLI
- Modalita di ricerca assembly:
  - `--assembly-search sequence` (default, sequenza fissa);
  - `--assembly-search dynamic` (ordine dinamico con backtracking + euristica fail-first).
- Alias compatto:
  - `--assembly-check {sequence,dynamic}` (abilita check assembly e seleziona modalita).
- Nuova opzione stampa:
  - `--print-valid` stampa ogni soluzione valida (non solo assemblabili).

## Output migliorato
- Con `dynamic`, nella riga di stampa viene indicato anche se il metodo dinamico aggiunge almeno 1 passo rispetto alla sequenza fissa:
  - `dynamic_adds_step_vs_sequence=yes/no`
  - con dettaglio `dynamic_steps` e `sequence_steps`.
- Nei dettagli assembly e stato anche `max_completed_steps` per confronti diagnostici.

## Comandi utili
- Ricerca dinamica + stampa valide:
  - `python3 .\\soluzione_puzzle3d.py --max-solutions 1000 --check-assembly --assembly-search dynamic --print-valid`
- Sintassi alias equivalente:
  - `python3 .\\soluzione_puzzle3d.py --max-solutions 1000 --assembly-check dynamic --print-valid`

## Stato
- Script eseguibile senza errori sintattici.
- Comportamento assembly piu coerente sui casi discussi.
