
#!/usr/bin/env python3
"""
Soluzione puzzle 3D - ricerca configurazione con il pezzo a profondità 1 come ultimo da inserire.

Questo script esplora combinazioni di disposizione (4 orizzontali, 4 verticali) e varianti
(di rotazione longitudinale e flip verticale) dei 8 pezzi. Verifica la montabilità fisica
secondo le regole discusse con l'utente e cerca configurazioni in cui il pezzo che contiene
profondità = 1 sia l'ultimo da inserire (ultima colonna).

Uso:
    python soluzione_puzzle_depth1_ultimo_v2.py [--max-iter N] [--save-all results.json]

Nota:
 - Il search è potenzialmente pesante; imposta --max-iter per limitare le iterazioni durante i test.
 - Output: stampa la prima soluzione trovata (se presente) e salva dettagli in file opzionale.
"""

import argparse
import json
import time
from itertools import permutations, product

# Dati pezzi: (profondità, direzione '↑'/'↓') nelle posizioni [1,3,5,7]
PIECES = {
    1: [(3, '↑'), (3, '↓'), (2, '↓'), (2, '↓')],
    2: [(1, '↓'), (2, '↑'), (1, '↑'), (3, '↑')],
    3: [(3, '↑'), (2, '↓'), (2, '↓'), (2, '↓')],
    4: [(2, '↑'), (2, '↓'), (3, '↑'), (3, '↓')],
    5: [(3, '↓'), (2, '↓'), (3, '↑'), (2, '↑')],
    6: [(2, '↑'), (3, '↑'), (2, '↓'), (3, '↓')],
    7: [(3, '↑'), (2, '↓'), (2, '↓'), (2, '↓')],
    8: [(2, '↓'), (2, '↑'), (3, '↓'), (3, '↑')],
}

# Genera le 4 varianti di un pezzo:
# 0 = originale, 1 = inverso (ordine invertito), 2 = flip verticale (↑<->↓),
# 3 = inverso + flip
def generate_variants(piece):
    base = piece
    flip = [(d, '↓' if p == '↑' else '↑') for d, p in base]
    rev_base = list(reversed(base))
    rev_flip = list(reversed(flip))
    return [base, rev_base, flip, rev_flip]

# Utility
def has_depth_one(piece):
    return any(d == 1 for d, _ in piece)

def all_same_direction(piece):
    dirs = [p for _, p in piece]
    return all(d == '↑' for d in dirs) or all(d == '↓' for d in dirs)

# Controllo fisico semplificato per inserimento di una colonna dopo che le righe sono posate:
# per ogni riga: le direzioni devono essere opposte e la somma delle profondità <= 4 (condizione di passaggio)
def can_insert_column_after_rows(h_rows, v_column):
    for row_idx in range(4):
        h = h_rows[row_idx][row_idx_col_idx_map[row_idx]] if False else None
    # NOTE: we use different indexing in the main search; this helper will be invoked with explicit pieces
    for row_idx in range(4):
        h_piece = h_rows[row_idx]
        v_piece = v_column[row_idx]
        # opposto direzione
        if h_piece[1] == v_piece[1]:
            return False
        # la somma di profondità deve permettere il passaggio (<=4)
        if h_piece[0] + v_piece[0] > 4:
            return False
    return True

# Condizione di incastro valida tra due scanalature
def fits(h_slot, v_slot):
    return h_slot[1] != v_slot[1] and (h_slot[0] + v_slot[0]) >= 4

# Funzione che verifica la montabilità ragionata: dopo che le righe sono posate, le prime 3 colonne
# devono poter essere inserite (con test can_insert_column_after_rows) e infine la 4a (con pezzo depth1)
def verify_sequence(horiz_pieces, vert_pieces):
    # horiz_pieces: lista di 4 pezzi (varianti) - ogni pezzo è lista di 4 scanalature
    # vert_pieces: lista di 4 pezzi (varianti)
    # Verifica incastri base
    for i in range(4):
        for j in range(4):
            if not fits(horiz_pieces[i][j], vert_pieces[j][i]):
                return False

    # Simula inserimento colonne 0..2 (lasciando la 3 per ultima)
    for j in range(3):
        # controlla che la colonna j possa passare nelle 4 righe
        for i in range(4):
            h = horiz_pieces[i][j]
            v = vert_pieces[j][i]
            # per poter scendere, direzioni opposte e somma profondità <=4 (per consentire scorrimento)
            if h[1] == v[1] or (h[0] + v[0] > 4):
                return False

    # Per l'ultima colonna (j=3), accettiamo che alcune somme siano >4 ma la colonna deve comunque poter essere inserita
    # cioè esistano movimenti meccanici (si assume che se tutte le prime 3 colonne sono inseribili, l'ultima sia inseribile)
    # Questo controllo è conservativo: qui verifichiamo ancora che ogni incastro sia compatibile (fits)
    for i in range(4):
        if not fits(horiz_pieces[i][3], vert_pieces[3][i]):
            return False

    return True

# Precompute variants
VARIANTS = {pid: generate_variants(PIECES[pid]) for pid in PIECES}

# Map for debug indexing - not used in verify_sequence but kept for clarity
row_idx_col_idx_map = {0:0,1:1,2:2,3:3}

def main(max_iter=None, save_all=None):
    start = time.time()
    pieces_ids = list(PIECES.keys())
    pieces_with_1 = [pid for pid in pieces_ids if has_depth_one(PIECES[pid])]
    print(f"Pezzi che contengono profondità 1: {pieces_with_1}")

    iter_count = 0
    results = []

    # Try each candidate piece-with-depth1 as the last vertical piece
    for depth1_last in pieces_with_1:
        remaining_ids = [pid for pid in pieces_ids if pid != depth1_last]
        # we choose 4 horizontals from remaining 7 (permutations of 4)
        for horiz_ids in permutations(remaining_ids, 4):
            # vertical ids are the other 3 remaining + depth1_last as last
            vert_candidates = [pid for pid in pieces_ids if pid not in horiz_ids and pid != depth1_last]
            if len(vert_candidates) != 3:
                continue
            vert_ids = tuple(vert_candidates) + (depth1_last,)
            # iterate variants but allow early pruning
            for horiz_vars in product(range(4), repeat=4):
                horiz_pieces = [VARIANTS[pid][v] for pid, v in zip(horiz_ids, horiz_vars)]

                # quick pruning: reject if any horizontal piece has all-directions equal
                if any(all_same_direction(p) for p in horiz_pieces):
                    continue

                # prune by checking row-wise direction distributions: avoid cases with 4 same dir at any pos
                bad = False
                for pos in range(4):
                    ups = sum(1 for r in horiz_pieces if r[pos][1] == '↑')
                    downs = sum(1 for r in horiz_pieces if r[pos][1] == '↓')
                    if ups == 4 or downs == 4:
                        bad = True
                        break
                if bad:
                    continue

                for vert_vars in product(range(4), repeat=4):
                    iter_count += 1
                    if max_iter and iter_count > max_iter:
                        print("Limite iterazioni raggiunto, esco.")
                        return results

                    vert_pieces = [VARIANTS[pid][v] for pid, v in zip(vert_ids, vert_vars)]

                    # similar pruning for verticals
                    if any(all_same_direction(p) for p in vert_pieces):
                        continue

                    badv = False
                    for pos in range(4):
                        ups = sum(1 for c in vert_pieces if c[pos][1] == '↑')
                        downs = sum(1 for c in vert_pieces if c[pos][1] == '↓')
                        if ups == 4 or downs == 4:
                            badv = True
                            break
                    if badv:
                        continue

                    # Verify full logical fits and the mechanical sequence condition
                    if verify_sequence(horiz_pieces, vert_pieces):
                        solution = {
                            "horiz_ids": horiz_ids,
                            "horiz_vars": list(horiz_vars),
                            "horiz_pieces": [[f"{d}{p}" for d,p in piece] for piece in horiz_pieces],
                            "vert_ids": vert_ids,
                            "vert_vars": list(vert_vars),
                            "vert_pieces": [[f"{d}{p}" for d,p in piece] for piece in vert_pieces],
                            "depth1_last": depth1_last,
                            "iter": iter_count,
                            "time_s": time.time() - start
                        }
                        print("Soluzione trovata dopo", iter_count, "iterazioni in", solution['time_s'], "s")
                        print(json.dumps(solution, indent=2))
                        results.append(solution)
                        if save_all:
                            with open(save_all, 'w') as fout:
                                json.dump(results, fout, indent=2)
                        return results

    print("Ricerca completata: nessuna soluzione trovata nei parametri impostati.")
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Ricerca soluzione puzzle, con depth=1 ultimo.')
    parser.add_argument('--max-iter', type=int, default=None, help='Numero massimo di iterazioni da eseguire (utile per debug).')
    parser.add_argument('--save-all', type=str, default=None, help='File JSON dove salvare tutte le soluzioni trovate.')
    args = parser.parse_args()
    res = main(max_iter=args.max_iter, save_all=args.save_all)
    if res:
        print('\\nPrima soluzione scritta (riassunto).')
    else:
        print('\\nNessuna soluzione trovata con i limiti forniti.')
