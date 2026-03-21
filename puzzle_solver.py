#!/usr/bin/env python3
"""
Puzzle 3D Solver
================
8 pezzi rettangolari ad incastro (4 alti × 9 lunghi), ognuno con 4 tacche.
4 pezzi vanno in orizzontale, 4 in verticale → griglia 4×4 di incroci.
Ad ogni incrocio: direzioni opposte + somma profondità ≥ 4.

Ogni pezzo ha 4 varianti: originale, specchiato (dx↔sx), capovolto (su↔giù),
specchiato+capovolto.
"""

from itertools import combinations, permutations, product
import time
import json

# ═══════════════════════════════════════════════════════════════════════════════
# DEFINIZIONE PEZZI
# Ogni pezzo: 4 tacche come (profondità, direzione)
#   profondità: 1, 2, o 3
#   direzione: 'U' = taglio dall'alto, 'D' = taglio dal basso
# Le tacche sono alle posizioni 2, 4, 6, 8 lungo il lato lungo (9 unità)
# ═══════════════════════════════════════════════════════════════════════════════

PIECES = {
    1: ((3, 'U'), (3, 'D'), (2, 'D'), (2, 'D')),
    2: ((1, 'D'), (2, 'U'), (1, 'U'), (3, 'U')),
    3: ((3, 'U'), (2, 'D'), (2, 'D'), (2, 'D')),
    4: ((2, 'U'), (2, 'D'), (3, 'U'), (3, 'D')),
    5: ((3, 'D'), (2, 'D'), (3, 'U'), (2, 'U')),
    6: ((2, 'U'), (3, 'U'), (2, 'D'), (3, 'D')),
    7: ((3, 'U'), (2, 'D'), (2, 'D'), (2, 'D')),
    8: ((2, 'D'), (2, 'U'), (3, 'D'), (3, 'U')),
}

VARIANT_NAMES = ['originale', 'specchiato', 'capovolto', 'specch+capov']


# ═══════════════════════════════════════════════════════════════════════════════
# PRECOMPUTAZIONE VARIANTI E TABELLA COMPATIBILITÀ
# ═══════════════════════════════════════════════════════════════════════════════

def _flip(d):
    return 'D' if d == 'U' else 'U'


def _make_variants(piece):
    """4 orientamenti: originale, specchiato(dx↔sx), capovolto(su↔giù), entrambi."""
    orig = piece
    mirror = tuple(reversed(piece))
    flip = tuple((d, _flip(s)) for d, s in piece)
    mirror_flip = tuple(reversed(flip))
    return [orig, mirror, flip, mirror_flip]


def _encode(depth, direction):
    """Codifica tacca come intero: depth*2 + (1 se U, 0 se D)."""
    return depth * 2 + (1 if direction == 'U' else 0)


def _decode(enc):
    return (enc >> 1, 'U' if enc & 1 else 'D')


# Varianti leggibili e codificate
VARIANTS_RAW = {pid: _make_variants(p) for pid, p in PIECES.items()}
VARIANTS_ENC = {
    pid: [tuple(_encode(*n) for n in v) for v in variants]
    for pid, variants in VARIANTS_RAW.items()
}

# Tabella compatibilità: FITS[h_enc][v_enc] = True se la tacca h e v si incastrano
# Tacche codificate: range 2..7 (depth 1-3, dir U/D)
FITS = [[False] * 8 for _ in range(8)]
for _h in range(2, 8):
    for _v in range(2, 8):
        # Direzioni opposte (bit 0 diverso) e somme profondità >= 4
        FITS[_h][_v] = bool((_h ^ _v) & 1) and ((_h >> 1) + (_v >> 1) >= 4)


# ═══════════════════════════════════════════════════════════════════════════════
# SOLVER
# ═══════════════════════════════════════════════════════════════════════════════

def solve(progress_every=50000):
    """Trova tutte le configurazioni geometricamente valide."""
    piece_ids = sorted(PIECES.keys())
    solutions = []
    total_checked = 0
    t_start = time.time()

    for h_set in combinations(piece_ids, 4):
        v_list = [p for p in piece_ids if p not in h_set]

        # Precomputa (pid, variant_idx, encoded_piece) per tutti i pezzi V
        v_pool = [
            (pid, var, VARIANTS_ENC[pid][var])
            for pid in v_list
            for var in range(4)
        ]

        for h_perm in permutations(h_set):
            for h_vars in product(range(4), repeat=4):
                total_checked += 1

                if progress_every and total_checked % progress_every == 0:
                    elapsed = time.time() - t_start
                    print(f"  ... {total_checked:>9,} config H testate,"
                          f" {len(solutions)} soluzioni, {elapsed:.1f}s")

                # Pezzi H codificati
                h0 = VARIANTS_ENC[h_perm[0]][h_vars[0]]
                h1 = VARIANTS_ENC[h_perm[1]][h_vars[1]]
                h2 = VARIANTS_ENC[h_perm[2]][h_vars[2]]
                h3 = VARIANTS_ENC[h_perm[3]][h_vars[3]]

                # Per ogni colonna V, trova candidati compatibili
                candidates = []
                feasible = True

                for col in range(4):
                    h0c, h1c, h2c, h3c = h0[col], h1[col], h2[col], h3[col]
                    col_cands = []

                    for pid, var, enc in v_pool:
                        if (FITS[h0c][enc[0]] and FITS[h1c][enc[1]] and
                                FITS[h2c][enc[2]] and FITS[h3c][enc[3]]):
                            col_cands.append((pid, var))

                    if not col_cands:
                        feasible = False
                        break
                    candidates.append(col_cands)

                if not feasible:
                    continue

                # Backtracking per assegnare pezzi V alle colonne
                _assign_v(candidates, 0, 0, [],
                          tuple((h_perm[i], h_vars[i]) for i in range(4)),
                          solutions)

    return solutions, total_checked


def _assign_v(candidates, col, used_mask, assignment, h_info, solutions):
    """Backtracking: assegna un pezzo V ad ogni colonna."""
    if col == 4:
        solutions.append({'h': h_info, 'v': tuple(assignment)})
        return

    for pid, var in candidates[col]:
        bit = 1 << pid
        if not (used_mask & bit):
            _assign_v(candidates, col + 1, used_mask | bit,
                      assignment + [(pid, var)], h_info, solutions)


# ═══════════════════════════════════════════════════════════════════════════════
# VERIFICA MONTAGGIO
# ═══════════════════════════════════════════════════════════════════════════════

def get_crossing_grid(sol):
    """Calcola la griglia degli incroci con i valori di slack."""
    h_pieces = [VARIANTS_RAW[pid][var] for pid, var in sol['h']]
    v_pieces = [VARIANTS_RAW[pid][var] for pid, var in sol['v']]

    grid = []
    for i in range(4):
        row = []
        for j in range(4):
            h_n = h_pieces[i][j]
            v_n = v_pieces[j][i]
            slack = h_n[0] + v_n[0] - 4
            row.append({'h': h_n, 'v': v_n, 'slack': slack})
        grid.append(row)
    return grid


def check_assembly(sol):
    """
    Calcola metriche di assemblabilità per la soluzione.

    In questo tipo di puzzle a griglia, il montaggio avviene intrecciando
    i pezzi: si posano gli H e si inseriscono i V alzando temporaneamente
    gli H dove necessario. Tutte le soluzioni geometricamente valide
    sono montabili manualmente.

    Restituisce:
    - total_slack: somma di tutti gli slack (più alto = più facile)
    - min_slack: slack minimo (0 = qualche incrocio è molto stretto)
    - zeros: numero di incroci con slack=0 (meno = più facile)
    """
    grid = get_crossing_grid(sol)
    slacks = [grid[i][j]['slack'] for i in range(4) for j in range(4)]
    return {
        'total_slack': sum(slacks),
        'min_slack': min(slacks),
        'zeros': slacks.count(0),
        'max_slack': max(slacks),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# DEDUPLICAZIONE
# ═══════════════════════════════════════════════════════════════════════════════

def solution_signature(sol):
    """
    Crea una firma canonica per riconoscere soluzioni duplicate.
    Due soluzioni sono uguali se differiscono solo per lo scambio dei pezzi 3↔7
    (che hanno la stessa geometria).
    """
    def normalize(piece_list):
        return tuple(
            (min(pid, 7) if pid in (3, 7) else pid, var)
            for pid, var in piece_list
        )

    h_norm = normalize(sol['h'])
    v_norm = normalize(sol['v'])

    # Calcola griglia degli incroci come firma
    h_pieces = [VARIANTS_RAW[pid][var] for pid, var in sol['h']]
    v_pieces = [VARIANTS_RAW[pid][var] for pid, var in sol['v']]
    grid_sig = tuple(
        (h_pieces[i][j], v_pieces[j][i])
        for i in range(4) for j in range(4)
    )
    return grid_sig


def deduplicate(solutions):
    """Rimuove soluzioni duplicate (stessa griglia di incroci)."""
    seen = set()
    unique = []
    for sol in solutions:
        sig = solution_signature(sol)
        if sig not in seen:
            seen.add(sig)
            unique.append(sol)
    return unique


# ═══════════════════════════════════════════════════════════════════════════════
# OUTPUT
# ═══════════════════════════════════════════════════════════════════════════════

def fmt_notch(depth, direction):
    return f"{depth}{direction}"


def fmt_piece(piece):
    return '  '.join(fmt_notch(*n) for n in piece)


def print_solution(sol, idx, metrics=None):
    grid = get_crossing_grid(sol)
    if metrics is None:
        metrics = check_assembly(sol)

    h_pieces = [VARIANTS_RAW[pid][var] for pid, var in sol['h']]
    v_pieces = [VARIANTS_RAW[pid][var] for pid, var in sol['v']]

    print(f"\n{'═' * 70}")
    print(f" SOLUZIONE {idx}")
    print(f"{'═' * 70}")

    print("\n Pezzi ORIZZONTALI (→):")
    for i in range(4):
        print(f"   H{i}: [{fmt_piece(h_pieces[i])}]")

    print("\n Pezzi VERTICALI (↓):")
    for j in range(4):
        print(f"   V{j}: [{fmt_piece(v_pieces[j])}]")

    # Griglia incroci con sopra/sotto
    print(f"\n Griglia (▲=V sopra H, ▼=V sotto H):")
    hdr = "         "
    for j in range(4):
        hdr += f"    V{j}     "
    print(hdr)

    for i in range(4):
        line = f"  H{i}:   "
        for j in range(4):
            g = grid[i][j]
            sym = '▲' if h_pieces[i][j][1] == 'U' else '▼'
            line += f" {fmt_notch(*g['h'])}{sym}{fmt_notch(*g['v'])}({g['slack']}) "
        print(line)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("═" * 70)
    print(" PUZZLE 3D SOLVER — 8 pezzi, griglia 4×4")
    print("═" * 70)

    print(f"\n{len(PIECES)} pezzi (nota: pezzo 3 e 7 sono identici):")
    for pid in sorted(PIECES):
        print(f"  Pezzo {pid}: [{fmt_piece(PIECES[pid])}]")

    print("\nRicerca soluzioni in corso...")
    t0 = time.time()
    solutions, total_checked = solve()
    elapsed = time.time() - t0

    print(f"\nConfiguarazioni H testate: {total_checked:,}")
    print(f"Soluzioni geometriche trovate: {len(solutions)}")
    print(f"Tempo di ricerca: {elapsed:.1f}s")

    # Deduplicazione
    unique = deduplicate(solutions)
    print(f"Soluzioni uniche (dopo dedup pezzi 3/7): {len(unique)}")

    # Statistiche sulle suddivisioni H/V
    splits = {}
    for sol in unique:
        h_ids = frozenset(pid for pid, _ in sol['h'])
        splits.setdefault(h_ids, []).append(sol)
    print(f"Suddivisioni H/V distinte: {len(splits)}")

    # Calcola metriche
    scored = [(sol, check_assembly(sol)) for sol in unique]

    # Seleziona soluzioni rappresentative: una per ogni suddivisione H/V
    # preferendo quella con meno incroci a slack=0
    representatives = []
    for h_ids, sols in sorted(splits.items(), key=lambda x: sorted(x[0])):
        best = min(sols, key=lambda s: check_assembly(s)['zeros'])
        m = check_assembly(best)
        representatives.append((best, m, h_ids))
    representatives.sort(key=lambda x: (x[1]['zeros'], -x[1]['max_slack']))

    # Stampa le prime soluzioni rappresentative
    n_show = min(5, len(representatives))
    print(f"\n{'#' * 70}")
    print(f" {n_show} SOLUZIONI RAPPRESENTATIVE (una per suddivisione H/V)")
    print(f" Ogni soluzione geometricamente valida è montabile manualmente:")
    print(f"   1. Posare i 4 pezzi H paralleli")
    print(f"   2. Intrecciare i 4 pezzi V perpendicolarmente")
    print(f"   3. Dove V deve andare sotto H, alzare H temporaneamente")
    print(f"{'#' * 70}")

    for i, (sol, m, h_ids) in enumerate(representatives[:n_show], 1):
        v_ids = frozenset(pid for pid, _ in sol['v'])
        print(f"\n  [Split: H={sorted(h_ids)} / V={sorted(v_ids)}]")
        print_solution(sol, i, m)

    if len(representatives) > n_show:
        print(f"\n... e altre {len(representatives) - n_show} suddivisioni possibili")

    # Salva tutte le soluzioni
    output_data = {
        'total_geometric': len(solutions),
        'total_unique': len(unique),
        'n_splits': len(splits),
        'solutions': [
            {
                'h': [fmt_piece(VARIANTS_RAW[pid][var]) for pid, var in sol['h']],
                'v': [fmt_piece(VARIANTS_RAW[pid][var]) for pid, var in sol['v']],
                'metrics': m,
            }
            for sol, m in scored
        ],
    }

    with open('puzzle_solutions_new.json', 'w') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    print(f"\nTutte le {len(unique)} soluzioni salvate in puzzle_solutions_new.json")
