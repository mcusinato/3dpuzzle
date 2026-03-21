# Conversazione Compatta — 2026-03-21

## Obiettivo
Risolvere puzzle 3D: 8 pezzi rettangolari (4×9) con 4 tacche ciascuno in posizione 2,4,6,8.
4 pezzi vanno in orizzontale, 4 in verticale → griglia 4×4 di incroci.

## Definizione pezzi
Ogni tacca = (profondità 1-3, direzione U=dall'alto / D=dal basso).
```
Pezzo 1: [3U  3D  2D  2D]
Pezzo 2: [1D  2U  1U  3U]
Pezzo 3: [3U  2D  2D  2D]  (identico al 7)
Pezzo 4: [2U  2D  3U  3D]
Pezzo 5: [3D  2D  3U  2U]
Pezzo 6: [2U  3U  2D  3D]
Pezzo 7: [3U  2D  2D  2D]  (identico al 3)
Pezzo 8: [2D  2U  3D  3U]
```

## Regole incastro
Ad ogni incrocio (Hi, Vj): direzioni opposte + somma profondità ≥ 4.
Slack = somma - 4 (0 = perfetto, >0 = gioco).

## Varianti per pezzo
4 orientamenti: originale, specchiato (dx↔sx), capovolto (U↔D), specch+capov.

## Solver (puzzle_solver.py)
- Scritto da zero, ignora codice precedente.
- Enumera tutte le C(8,4)=70 suddivisioni H/V × permutazioni × varianti.
- Backtracking per assegnare V alle colonne.
- **Risultati**: 24.064 soluzioni geometriche, 3.008 uniche (dedup 3↔7), 20 split H/V.
- Tutte le soluzioni hanno slack totale = 11 (costante) e 5 incroci a slack=0.

## Verifica montaggio
### Tentativo 1: DAG "dall'alto"
Ogni croce definisce un ordine (chi deve essere piazzato prima).
→ 0 soluzioni: ci sono sempre cicli (i pezzi hanno tacche U e D miste).

### Tentativo 2: DAG flessibile (ogni pezzo sceglie alto/basso)
256 combinazioni di direzione di ingresso per gli 8 pezzi.
→ 0 soluzioni: cicli inevitabili comunque.

### Stato attuale
Assembly check rimosso. Output mostra solo soluzioni geometriche con metriche di slack.
**L'utente conferma che la soluzione 1 NON è assemblabile** → serve modello corretto.

## Output attuale
- Pezzi mostrati direttamente come tacche posizionate (es. `[1D 2U 1U 3U]`), non come "Pezzo X variante Y".
- Griglia compatta: `1D▼3U(0)` = tacca H=1D, V sotto H (▼), tacca V=3U, slack=0.
- JSON: `puzzle_solutions_new.json` con tutte le 3008 soluzioni.

## Prossimi passi
- Trovare un modello di assemblabilità corretto che filtri le soluzioni impossibili.
- Possibilmente verificare i dati dei pezzi sulla foto originale.
