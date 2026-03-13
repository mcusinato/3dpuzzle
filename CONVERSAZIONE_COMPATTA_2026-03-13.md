# Conversazione Compatta - 2026-03-13

## Obiettivo
Migliorare la stampa e il controllo di montabilita di `soluzione_puzzle3d.py` per il puzzle 3D, con focus su sequenza di montaggio `H0,V0,H1,V1,H2,V2,H3,V3`.

## Modifiche principali fatte
- Stampa soluzione orientata su una sola riga:
  - formato: `H0: [...] | H1: [...] | H2: [...] | H3: [...] | V0: [...] | V1: [...] | V2: [...] | V3: [...]`
  - rimossi `piece=...`, `variant=...`, e intestazione `Systematic solution`.
- Aggiunto trace di assembly opzionale con flag `--assembly-trace`.
- Il trace ora mostra limiti di movimento per ogni step:
  - `Hk(u=...,d=...)`
  - `Vk(u=...,d=...)`
  - `req_spread`, `avail_spread`, `status`, `reason`.
- Il trace include anche lo step bloccato (non solo quelli completati).

## Evoluzione della logica assembly
- Sostituito check slack semplice con modello di mobilita direzionale.
- Aggiunto controllo spread per-buco durante inserimento sia di `V` che di `H`.
- Regola per domanda di movimento per buco aggiornata a:
  - `depth=1 -> 3`, `depth=2 -> 2`, `depth=3 -> 1` (`4 - depth`).

## Stato attuale
- Il modello e migliorato ma non ancora definitivo: restano casi segnalati dall'utente dove una soluzione viene ancora classificata come assemblabile quando nella realta non lo e.
- Punto da riprendere:
  - affinare il calcolo dello spread combinato su piu buchi e vincoli accoppiati tra pezzi gia montati, con priorita ai casi di blocco sull'ultimo pezzo (`V3`).

## Esempi discussi
- Caso non assemblabile segnalato su `V2` perche i primi due buchi richiedono shift tra `H0` e `H1` maggiore di quello disponibile.
- Caso non assemblabile segnalato su `V3` con richiesta di shift elevata sui primi due buchi, non catturata pienamente dal modello corrente.

## Prossimo step suggerito
- Introdurre una verifica di fattibilita globale del tentativo di inserimento come sistema di vincoli (non solo check a coppie), mantenendo il trace dettagliato per spiegare il primo vincolo violato.
