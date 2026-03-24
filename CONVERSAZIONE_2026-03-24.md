# Conversazione 2026-03-24: Soluzioni Geometriche Uniche Puzzle 3D

## Obiettivo
Creare uno script Python che enumeri **tutte le soluzioni geometricamente compatibili** del puzzle 3D, ignorando la montabilità, e deduplichi quelle equivalenti secondo specifiche regole di simmetria.

## Problema Affrontato

### Input
- 8 pezzi rettangolari ad incastro (4 alti, 4 larghi)
- Griglia 4×4 di incroci (4 orizzontali H0-H3, 4 verticali V0-V3)
- 4 varianti orientamento per pezzo (originale, specchiato, capovolto, entrambi)

### Richieste Equivalenze
1. **Pezzi uguali (3, 7)**: indistinguibili
2. **Inversione posizionale**: `H0 H1 H2 H3 V0 V1 V2 V3` ≡ `H3 H2 H1 H0 V3 V2 V1 V0`
3. **Scambio blocchi**: `H0...V0...` ≡ `V0...H0...`
4. **Capovolgimento totale**: tutti pezzi con U↔D equivalenti

## Soluzione Implementata

### Nuovo Script: `find_unique_geometric_solutions.py`
- **Motore di ricerca**: basato su `puzzle_solver.py` (compatibilità geometrica)
- **Canonizzazione**: griglia 4×4 indipendente da ID pezzi
- **Dedup**: 8 combinazioni di trasformazioni (2³: reverse, swap_hv, flip_directions)
- **Firma canonica**: min() tra tutte le 8 varianti di ogni soluzione

### Funzionalità CLI
```bash
# Tutte le 376 soluzioni uniche
python find_unique_geometric_solutions.py

# Solo le 32 con H0 primo buco da 1 unico
python find_unique_geometric_solutions.py --filter-h0-unique

# Formato compatto ID/variante
python find_unique_geometric_solutions.py --show-compact

# Salva solo filtrate nel JSON
python find_unique_geometric_solutions.py --filter-h0-unique
```

## Risultati

### Conteggi Finali
| Metrica | Valore |
|---------|--------|
| Configurazioni H testate | 430,080 |
| Soluzioni geometriche raw | 24,064 |
| Con equivalenza 3/7 | 752 |
| Dopo inversione posizionale | 752 |
| Dopo scambio H/V | 752 |
| Dopo capovolgimento U↔D | **376** |
| Filtro H0-unico | **32** |

### Esempio Soluzione (H0-unico)
```
H0:[1D 2U 1U 3U] | V0:[3U 2U 3D 2D] | 
H1:[2D 2D 3D 3U] | V1:[3D 2U 2U 2U] | 
H2:[2U 2D 3U 3D] | V2:[3D 3U 2D 2U] | 
H3:[3U 2D 2D 2D] | V3:[3D 2D 3U 2U]
```
Formato: tacche `{profondità}{direzione}` es. `1D`=profondità 1 verso il basso

## Implementazione Chiave

### Canonizzazione (8 trasformazioni)
```python
def canonical_signature(sol):
    candidates = [
        grid_signature(sol, reverse=r, swap_hv=s, flip_all=f)
        for r in (False, True)
        for s in (False, True)
        for f in (False, True)
    ]
    return min(candidates)  # firma lessicograficamente minima
```

### Firma Geometrica
- Indipendente da ID pezzi (usa solo tacche)
- Griglia 4×4 degli incroci
- Tuple di notch (depth, direction)

### Filtro H0-Unico
- Pezzo 2 con pattern 3+1 (tre buchi in un verso, uno l'opposto)
- Primo buco (incrocio H0-V0) da 1 nella direzione unica
- Risultato: 32 configurazioni validate

## File Generati
- **Script**: `find_unique_geometric_solutions.py`
- **Output JSON**: `puzzle_solutions_unique_geometric.json` (32 o 376 soluzioni)

## Performance
- **Tempo ricerca completa**: 1.4s → 2.3s (con tutte equivalenze)
- **Progressione**: stampa ogni 100k config testate

## Equivalenze Verificate
- ✅ Pezzi 3 e 7 indistinguibili
- ✅ Inversione totale (H0-3 + V0-3)
- ✅ Scambio blocchi H↔V
- ✅ Capovolgimento U↔D su tutti i pezzi

## Note Tecniche
- Firma geometrica robusta a rappresentazione:
  - Invariante sotto scambio 3↔7
  - Invariante sotto 8 transformazioni simmetriche
- Dedup garantisce non-equivalenza secondo regole specificate
- JSON contiene metadata di equivalenze applicate

## Commit
```
Aggiunte soluzioni geometriche uniche con equivalenze (376 totali, 32 con H0 unico)
```
