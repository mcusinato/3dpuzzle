
#!/usr/bin/env python3
"""
Soluzione puzzle 3D - ricerca configurazione con il pezzo a profondità 1 come ultimo da inserire.

Questo script esplora combinazioni di disposizione (4 orizzontali, 4 verticali) e varianti
(di rotazione longitudinale e flip verticale) degli 8 pezzi. Di default verifica solo
la compatibilità degli incastri geometrici; opzionalmente può verificare anche
la montabilità fisica secondo le regole discusse con l'utente.

Uso:
    python soluzione_puzzle_depth1_ultimo_v2.py [--max-iter N] [--max-solutions K] [--save-all results.json] [--check-assembly] [--allow-any-last]

Nota:
 - Il search è potenzialmente pesante; imposta --max-iter per limitare le iterazioni durante i test.
 - Output: stampa le soluzioni trovate fino a --max-solutions e salva dettagli in file opzionale.
"""

import argparse
import json
import time
from itertools import permutations, product

# Dati pezzi: (profondita, direzione '^'/'_') nelle posizioni [1,3,5,7]
PIECES = {
    1: [(3, '^'), (3, '_'), (2, '_'), (2, '_')],
    2: [(1, '_'), (2, '^'), (1, '^'), (3, '^')],
    3: [(3, '^'), (2, '_'), (2, '_'), (2, '_')],
    4: [(2, '^'), (2, '_'), (3, '^'), (3, '_')],
    5: [(3, '_'), (2, '_'), (3, '^'), (2, '^')],
    6: [(2, '^'), (3, '^'), (2, '_'), (3, '_')],
    7: [(3, '^'), (2, '_'), (2, '_'), (2, '_')],
    8: [(2, '_'), (2, '^'), (3, '_'), (3, '^')],
}

# Genera le 4 varianti di un pezzo:
# 0 = originale, 1 = inverso (ordine invertito), 2 = flip verticale (^<->_),
# 3 = inverso + flip
def generate_variants(piece):
    base = piece
    flip = [(d, '_' if p == '^' else '^') for d, p in base]
    rev_base = list(reversed(base))
    rev_flip = list(reversed(flip))
    return [base, rev_base, flip, rev_flip]

# Utility
def has_depth_one(piece):
    return any(d == 1 for d, _ in piece)

def all_same_direction(piece):
    dirs = [p for _, p in piece]
    return all(d == '^' for d in dirs) or all(d == '_' for d in dirs)

# Condizione di incastro valida tra due scanalature
def fits(h_slot, v_slot):
    return h_slot[1] != v_slot[1] and (h_slot[0] + v_slot[0]) >= 4


def output_dir_symbol(direction):
    return direction


def format_slot_for_output(slot):
    depth, direction = slot
    return f"{depth}{output_dir_symbol(direction)}"


def variant_label(variant_idx):
    labels = {
        0: 'orig',
        1: 'w_f',
        2: 'h_p',
        3: 'wh_f',
    }
    return labels[variant_idx]

# Verifica solo la compatibilità degli incastri (senza vincoli di sequenza di montaggio)
def verify_interlocks_only(horiz_pieces, vert_pieces):
    for i in range(4):
        for j in range(4):
            if not fits(horiz_pieces[i][j], vert_pieces[j][i]):
                return False
    return True


# Verifica opzionale della montabilità (temporaneamente permissiva):
# qualunque configurazione valida per incastro viene considerata assemblabile.
def verify_with_assembly(horiz_pieces, vert_pieces):
    return verify_interlocks_only(horiz_pieces, vert_pieces)

# Precompute variants
VARIANTS = {pid: generate_variants(PIECES[pid]) for pid in PIECES}


def print_summary(valid_count, assembleable_count, returned_count):
    assembleable_text = 'na' if assembleable_count is None else str(assembleable_count)
    print(f"Summary: valid={valid_count}, assembleable={assembleable_text}, returned={returned_count}")

def main(max_iter=None, save_all=None, check_assembly=False, max_solutions=1, force_depth1_last=True):
    start = time.time()
    pieces_ids = list(PIECES.keys())
    pieces_with_1 = [pid for pid in pieces_ids if has_depth_one(PIECES[pid])]
    last_vertical_candidates = pieces_with_1 if force_depth1_last else pieces_ids
    # print(f"Pieces containing depth 1: {pieces_with_1}")

    iter_count = 0
    results = []
    valid_count = 0
    assembleable_count = 0 if check_assembly else None

    # Try each candidate as the last vertical piece.
    # By default this is limited to pieces containing depth=1, unless --allow-any-last is used.
    for last_vertical_id in last_vertical_candidates:
        remaining_ids = [pid for pid in pieces_ids if pid != last_vertical_id]
        # we choose 4 horizontals from remaining 7 (permutations of 4)
        for horiz_ids in permutations(remaining_ids, 4):
            # vertical ids are the other 3 remaining + depth1_last as last
            vert_candidates = [pid for pid in pieces_ids if pid not in horiz_ids and pid != last_vertical_id]
            if len(vert_candidates) != 3:
                continue
            vert_ids = tuple(vert_candidates) + (last_vertical_id,)
            # iterate variants but allow early pruning
            for horiz_vars in product(range(4), repeat=4):
                horiz_pieces = [VARIANTS[pid][v] for pid, v in zip(horiz_ids, horiz_vars)]

                # quick pruning: reject if any horizontal piece has all-directions equal
                if any(all_same_direction(p) for p in horiz_pieces):
                    continue

                # prune by checking row-wise direction distributions: avoid cases with 4 same dir at any pos
                bad = False
                for pos in range(4):
                    ups = sum(1 for r in horiz_pieces if r[pos][1] == '^')
                    downs = sum(1 for r in horiz_pieces if r[pos][1] == '_')
                    if ups == 4 or downs == 4:
                        bad = True
                        break
                if bad:
                    continue

                for vert_vars in product(range(4), repeat=4):
                    iter_count += 1
                    if max_iter and iter_count > max_iter:
                        print("Max iterations reached, exiting.")
                        print_summary(valid_count, assembleable_count, len(results))
                        return results

                    vert_pieces = [VARIANTS[pid][v] for pid, v in zip(vert_ids, vert_vars)]

                    # similar pruning for verticals
                    if any(all_same_direction(p) for p in vert_pieces):
                        continue

                    badv = False
                    for pos in range(4):
                        ups = sum(1 for c in vert_pieces if c[pos][1] == '^')
                        downs = sum(1 for c in vert_pieces if c[pos][1] == '_')
                        if ups == 4 or downs == 4:
                            badv = True
                            break
                    if badv:
                        continue

                    is_valid = verify_interlocks_only(horiz_pieces, vert_pieces)
                    if not is_valid:
                        continue

                    valid_count += 1
                    reached_valid_limit = max_solutions is not None and valid_count >= max_solutions

                    if check_assembly:
                        is_assembleable = verify_with_assembly(horiz_pieces, vert_pieces)
                        if is_assembleable:
                            assembleable_count += 1
                    else:
                        is_assembleable = False

                    if check_assembly and not is_assembleable:
                        if reached_valid_limit:
                            print(f"Reached max-solutions={max_solutions}.")
                            print_summary(valid_count, assembleable_count, len(results))
                            return results
                        continue

                    solution = {
                        "horiz_ids": horiz_ids,
                        "horiz_vars": [variant_label(v) for v in horiz_vars],
                        "horiz_pieces": [[format_slot_for_output(slot) for slot in piece] for piece in horiz_pieces],
                        "vert_ids": vert_ids,
                        "vert_vars": [variant_label(v) for v in vert_vars],
                        "vert_pieces": [[format_slot_for_output(slot) for slot in piece] for piece in vert_pieces],
                        "classification": "assembleable" if is_assembleable else "valid",
                        "depth1_last": last_vertical_id if has_depth_one(PIECES[last_vertical_id]) else None,
                        "last_vertical_id": last_vertical_id,
                        "iter": iter_count,
                        "time_s": time.time() - start
                    }
                    # print(f"Solution found after {iter_count} iterations in {solution['time_s']:.3f}s")
                    # print(json.dumps(solution, indent=2))
                    results.append(solution)
                    if save_all:
                        with open(save_all, 'w') as fout:
                            json.dump(results, fout, indent=2)
                    if reached_valid_limit:
                        print(f"Reached max-solutions={max_solutions}.")
                        print_summary(valid_count, assembleable_count, len(results))
                        return results

    print("Search completed: no solution found with the current limits.")
    print_summary(valid_count, assembleable_count, len(results))
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Ricerca soluzione puzzle, con depth=1 ultimo.')
    parser.add_argument('--max-iter', type=int, default=None, help='Numero massimo di iterazioni da eseguire (utile per debug).')
    parser.add_argument('--save-all', type=str, default=None, help='File JSON dove salvare tutte le soluzioni trovate.')
    parser.add_argument('--check-assembly', action='store_true', help='Attiva anche il controllo di montabilità fisica (piu restrittivo).')
    parser.add_argument('--max-solutions', type=int, default=1, help='Numero massimo di soluzioni da trovare prima di fermarsi (usa valori >1 per cercare piu combinazioni).')
    parser.add_argument('--force-depth1-last', dest='force_depth1_last', action='store_true', default=True, help='Forza un pezzo con depth=1 come ultimo verticale (default).')
    parser.add_argument('--allow-any-last', dest='force_depth1_last', action='store_false', help='Non forzare depth=1 ultimo; prova qualunque pezzo come ultimo verticale.')
    args = parser.parse_args()
    res = main(
        max_iter=args.max_iter,
        save_all=args.save_all,
        check_assembly=args.check_assembly,
        max_solutions=args.max_solutions,
        force_depth1_last=args.force_depth1_last,
    )
    #if res:
    #    print(f"Found {len(res)} valid solution(s).")
    #else:
    #    print("No solution found with the provided limits.")
