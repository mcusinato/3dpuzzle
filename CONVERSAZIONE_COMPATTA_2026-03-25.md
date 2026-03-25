# Conversazione 2026-03-25: Montabilità delle Soluzioni Geometriche

## Riassunto Esecutivo

Abbiamo verificato la montabilità delle **376 soluzioni geometriche uniche** del puzzle 3D.

### Risultati Principali

**Delle 376 soluzioni geometriche uniche: 82 sono montabili (21.8%)**

| Metrica | Valore |
|---------|--------|
| Soluzioni totali | 376 |
| Soluzioni montabili | **82** |
| Soluzioni non montabili | 294 |
| Percentuale montabili | **21.8%** |

## Metodologia di Verifica

### Sequenze di Montaggio Testate

Per ogni soluzione sono state testate 4 sequenze di montaggio:
1. **Seq1**: H0 V0 H1 V1 H2 V2 H3 V3
2. **Seq2**: V0 H0 V1 H1 V2 H2 V3 H3
3. **Seq3**: H3 V3 H2 V2 H1 V1 H0 V0 (inversa della 1)
4. **Seq4**: V3 H3 V2 H2 V1 H1 V0 H0 (inversa della 2)

### Logica di Montabilità

- **Primi 3 pezzi**: sempre montabili (geometricamente compatibili)
- **Da 4° pezzo in poi**: si inserisce nel 2° buco dei pezzi ortogonali
  - **Stessa direzione**: inseribile dal lato libero ✓
  - **Direzioni opposte**: richiede shift uniformi (profondità uguali)
    - Se profondità incoerenti: **NON montabile** ✗

### Cause di Non Montabilità

Le 294 soluzioni non montabili falliscono tipicamente al 3°-6° pezzo perché:
- Pezzi ortogonali hanno profondità del 2° buco incompatibili per lo shift
- Esempio: H0 ha profondità 3, H1 ha profondità 2 → scorrimento impossibile

## Risultati Dettagliati per Sequenza

| Sequenza | Soluzioni che funzionano |
|----------|--------------------------|
| Seq1 (H-first) | ~60+ soluzioni |
| Seq2 (V-first) | ~50+ soluzioni |
| Seq3 (H-reverse) | ~50+ soluzioni |
| Seq4 (V-reverse) | ~40+ soluzioni |

**Nota**: Numeri approssimativi; alcune soluzioni funzionano con multiple sequenze.

## Soluzioni "Super-Montabili"

Alcune soluzioni funzionano con **TUTTE 4 sequenze**:
- Soluzione 62
- Soluzione 91
- Soluzione 93
- Soluzione 106
- Soluzione 108
- Soluzione 263
- Soluzione 286

Totale: **7 soluzioni super-montabili**

### Esempio: Soluzione 62

```
H0=P1/v1:[2D 2D 3D 3U] | H1=P5/v2:[3U 2U 3D 2D] | H2=P2/v0:[1D 2U 1U 3U] | H3=P3/v3:[2U 2U 2U 3D] | 
V0=P4/v0:[2U 2D 3U 3D] | V1=P7/v0:[3U 2D 2D 2D] | V2=P6/v3:[3U 2U 3D 2D] | V3=P8/v0:[2D 2U 3D 3U]
```

- ✅ Seq1, ✅ Seq2, ✅ Seq3, ✅ Seq4

## File Generati/Modificati

1. **check_assemblability.py** - Script di verifica montabilità
2. **print_solution_62.py** - Script per stampare soluzione dettagliata
3. **puzzle_solutions_unique_geometric.json** - Soluzioni (invariato)

## Conclusioni

1. ✅ **Esiste almeno una soluzione montabile** (82 in totale)
2. ✅ **Esistono soluzioni "super-montabili"** (7 con tutte le sequenze)
3. ✅ **La logica di shift** è robusta e spiega i fallimenti
4. ⚠️ **78.2% delle soluzioni** non è montabile con alcuna sequenza

## Prossimi Passi Possibili

- [ ] Cercare sequenze di montaggio alternative (non solo H/V first)
- [ ] Verificare se lo shift parziale è possibile
- [ ] Analizzare i pattern comuni nelle 82 soluzioni montabili
- [ ] Validare fisicamente la soluzione 62 (o altre super-montabili)
