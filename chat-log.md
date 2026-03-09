# Chat Log - 3dpuzzle

Data: 2026-03-09

## Contesto iniziale
- Problema: `--save-all` sembrava non salvare nulla.
- File principale: `soluzione_puzzle_depth1_ultimo_v2.py`

## Interventi eseguiti

### 1. Fix `--save-all`
- Causa trovata: il file veniva scritto solo quando veniva trovata almeno una soluzione.
- Modifica: introdotta funzione `persist_results(save_all, results)`.
- Effetto: ora il JSON viene salvato anche quando non ci sono soluzioni (`[]`) o in uscita anticipata (`--max-iter`, altri return).

### 2. Salvataggio di tutte le soluzioni valide con `--check-assembly`
- Richiesta: includere nel JSON anche le soluzioni valide non assemblabili.
- Modifica: rimosso il filtro che scartava le non-assemblabili quando `--check-assembly` e attivo.
- Effetto: `result.json` contiene sia `classification: "assembleable"` sia `classification: "valid"`.

### 3. Diagnostica montaggio fisico (blocco su V2)
- Osservazione utente: con sequenza `H0 V0 H1 V1 H2 V2 ...` il puzzle reale si blocca su `V2`.
- Modifica importante: aggiunta modalita `--assembly-mode sequence` con simulazione esplicita della sequenza alternata.
- Aggiunti campi diagnostici nel JSON:
  - `assembly_mode`
  - `assembly_details.blocked_step`
  - `assembly_details.blocked_piece_type`
  - `assembly_details.blocked_piece_index`
  - `assembly_details.reason`
  - eventuali `required_movement`, `available_slack`

### 4. Taratura vincoli di slack
- Nuovi parametri:
  - `--assembly-movement-credit`
  - `--assembly-min-locked-cols`
- Configurazione che replica il caso utente (blocco su `V2`):
  - `--assembly-mode sequence --assembly-movement-credit 0 --assembly-min-locked-cols 2`

## Comando di riferimento (blocco su V2)
```powershell
python .\soluzione_puzzle_depth1_ultimo_v2.py --check-assembly --assembly-mode sequence --assembly-movement-credit 0 --assembly-min-locked-cols 2 --max-solutions 1 --save-all result_sequence_v2like.json
```

## Esito osservato
Nel file `result_sequence_v2like.json`:
- `classification: "valid"`
- `assembly_details.blocked_step: 6`
- `assembly_details.blocked_piece_type: "V"`
- `assembly_details.blocked_piece_index: 2`

Interpretazione: blocco su `V2` coerente con prova fisica.

## File toccati
- `soluzione_puzzle_depth1_ultimo_v2.py`
- `result.json`
- `result_sequence_strict.json`
- `result_sequence_credit1.json`
- `result_sequence_v2like.json`
- `chat-log.md`
