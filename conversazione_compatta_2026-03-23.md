# Conversazione Compatta — 2026-03-23

## Obiettivo
Integrare una regola di assemblabilita' basata sullo shift necessario per inserire un pezzo, per filtrare le soluzioni geometriche non montabili.

## Dati chiave forniti dall'utente
- Lo shift e' vincolato solo tra pezzi paralleli (H con H, V con V), non tra H e V.
- Per una coppia di pezzi paralleli gia' agganciati, lo shift massimo ammesso in una direzione e' il minimo tra tutti gli incroci gia' fatti in quella direzione.
- Il gioco di un incrocio e' $slack = d_h + d_v - 4$.

## Regola di inserimento (nuovo pezzo)
- Se i buchi da incastrare sono tutti nella stessa direzione, l'inserimento e' sempre possibile (si entra dal lato libero).
- Se ci sono direzioni opposte, lo spostamento richiesto dipende dalla coppia di profondita' e si prende il massimo:
  - 3+3 -> 2
  - 3+2 -> 3
  - 2+2 -> 4
  - 3+1 -> 5
  - 2+1 -> 6
  - 1+1 -> 7

## Implementazione (puzzle_solver.py)
- Aggiunto controllo di assemblabilita' per sequenza di default: H0 V0 H1 V1 H2 V2 H3 V3.
- Calcolo del minimo slack per direzione sui pezzi gia' posati.
- Inserimento valido se esiste una direzione (U o D) in cui tutti i pezzi gia' posati possono shiftare almeno quanto richiesto.
- La metrica `sequence_ok` viene salvata nei risultati.

## Stato
- Solver aggiornato, non eseguito dopo la modifica.
- Da verificare quante soluzioni passano la sequenza di default.
