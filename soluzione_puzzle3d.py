
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
import os
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


def format_oriented_piece(piece):
    return ' '.join(format_slot_for_output(slot) for slot in piece)


def print_systematic_solution(horiz_ids, horiz_vars, horiz_pieces, vert_ids, vert_vars, vert_pieces):
    h_parts = [f"H{idx}: [{format_oriented_piece(piece)}]" for idx, piece in enumerate(horiz_pieces)]
    v_parts = [f"V{idx}: [{format_oriented_piece(piece)}]" for idx, piece in enumerate(vert_pieces)]
    print(' | '.join(h_parts + v_parts))


def _fmt_limit(value):
    return 'inf' if value == float('inf') else str(value)


def print_assembly_trace(trace_steps):
    print("Assembly trace:")
    for step in trace_steps:
        h_limits = ' '.join(
            f"H{i}(u={_fmt_limit(lim['up'])},d={_fmt_limit(lim['down'])})"
            for i, lim in enumerate(step['h_limits'])
        )
        v_limits = ' '.join(
            f"V{i}(u={_fmt_limit(lim['up'])},d={_fmt_limit(lim['down'])})"
            for i, lim in enumerate(step['v_limits'])
        )
        req = step.get('required_spread', 0)
        avail = step.get('available_spread', 'na')
        status = step.get('status', 'ok')
        reason = step.get('reason', '')
        suffix = f" status={status}" + (f" reason={reason}" if reason else "")
        print(
            f"  step={step['step']} piece={step['piece']} "
            f"req_spread={req} avail_spread={avail}{suffix} | {h_limits} | {v_limits}"
        )

# Verifica solo la compatibilità degli incastri (senza vincoli di sequenza di montaggio)
def verify_interlocks_only(horiz_pieces, vert_pieces):
    for i in range(4):
        for j in range(4):
            if not fits(horiz_pieces[i][j], vert_pieces[j][i]):
                return False
    return True


def can_insert_column_prelock(horiz_pieces, vert_pieces, col_idx):
    """Una colonna e inseribile durante il montaggio se scorre in tutte le righe."""
    for row_idx in range(4):
        h = horiz_pieces[row_idx][col_idx]
        v = vert_pieces[col_idx][row_idx]
        # Direzioni opposte e somma <= 4 per consentire scorrimento verticale.
        if h[1] == v[1] or (h[0] + v[0] > 4):
            return False
    return True


# Verifica opzionale della montabilità (v1):
# una configurazione e assemblabile se gli incastri sono validi e almeno 3 colonne
# risultano inseribili in pre-lock. La colonna rimanente viene considerata la colonna di chiusura.
def verify_with_assembly(horiz_pieces, vert_pieces):
    if not verify_interlocks_only(horiz_pieces, vert_pieces):
        return False

    prelock_insertable = [
        can_insert_column_prelock(horiz_pieces, vert_pieces, col_idx)
        for col_idx in range(4)
    ]
    return sum(prelock_insertable) >= 3


def _simulate_alternating_sequence(
    horiz_pieces,
    vert_pieces,
    movement_credit=0,
    min_locked_cols_for_slack_check=2,
    capture_trace=False,
):
    """
    Simula la sequenza H0->V0->H1->V1->H2->V2->H3->V3 con un modello
    di mobilita direzionale:
    - ogni contatto H/V limita il movimento solo in una direzione per H e in
      una direzione per V;
    - i limiti disponibili vengono aggiornati dopo ogni inserimento;
    - quando si inserisce una nuova V, si richiede uno spread minimo tra le V
      gia montate proporzionale ai contatti con depth=3 della nuova V.

    movement_credit e min_locked_cols_for_slack_check sono mantenuti per
    compatibilita della firma ma non usati nel nuovo modello.
    """
    h_placed = [False] * 4
    v_placed = [False] * 4
    trace_steps = []

    def directional_mobility_limits():
        """
        Restituisce i limiti di movimento per ciascun pezzo gia montato.
        Per ogni pezzo:
        - up: quanto puo muoversi verso l'alto (inf = libero)
        - down: quanto puo muoversi verso il basso (inf = libero)
        """
        inf = float('inf')
        h_limits = [{'up': inf, 'down': inf} for _ in range(4)]
        v_limits = [{'up': inf, 'down': inf} for _ in range(4)]

        for row in range(4):
            if not h_placed[row]:
                continue
            for col in range(4):
                if not v_placed[col]:
                    continue

                h_slot = horiz_pieces[row][col]
                v_slot = vert_pieces[col][row]
                depth_slack = h_slot[0] + v_slot[0] - 4

                # Caso 1: H '_' vs V '^' -> limita H down e V up.
                if h_slot[1] == '_' and v_slot[1] == '^':
                    h_limits[row]['down'] = min(h_limits[row]['down'], depth_slack)
                    v_limits[col]['up'] = min(v_limits[col]['up'], depth_slack)
                # Caso 2: H '^' vs V '_' -> limita H up e V down.
                elif h_slot[1] == '^' and v_slot[1] == '_':
                    h_limits[row]['up'] = min(h_limits[row]['up'], depth_slack)
                    v_limits[col]['down'] = min(v_limits[col]['down'], depth_slack)

        return h_limits, v_limits

    def depth_movement_demand(depth):
        """
        Domanda di spostamento introdotta dal buco del pezzo in inserimento.

        Modello fisico per-buco: la richiesta e inversa alla profondita,
        quindi depth=1 richiede 3, depth=2 richiede 2, depth=3 richiede 1.
        """
        return max(0, 4 - depth)

    def opposite_piece_motion_dir(slot_direction):
        """Direzione richiesta al pezzo opposto per facilitare l'inserimento."""
        return 'down' if slot_direction == '^' else 'up'

    def pairwise_shift_check_for_insertion(piece_type, idx, h_limits, v_limits):
        """
        Check spread per-buco:
        - raccoglie per ogni contatto la domanda di movimento del pezzo opposto;
        - per ogni coppia con direzioni opposte verifica che la capacita combinata
          sia almeno la domanda combinata.

        Restituisce (ok, details).
        """
        demands = []

        if piece_type == 'V':
            for row in range(4):
                if not h_placed[row]:
                    continue
                v_slot = vert_pieces[idx][row]
                demand = depth_movement_demand(v_slot[0])
                motion_dir = opposite_piece_motion_dir(v_slot[1])
                capacity = h_limits[row][motion_dir]
                demands.append({
                    'opp_type': 'H',
                    'opp_idx': row,
                    'demand': demand,
                    'motion_dir': motion_dir,
                    'capacity': capacity,
                })
        else:
            for col in range(4):
                if not v_placed[col]:
                    continue
                h_slot = horiz_pieces[idx][col]
                demand = depth_movement_demand(h_slot[0])
                motion_dir = opposite_piece_motion_dir(h_slot[1])
                capacity = v_limits[col][motion_dir]
                demands.append({
                    'opp_type': 'V',
                    'opp_idx': col,
                    'demand': demand,
                    'motion_dir': motion_dir,
                    'capacity': capacity,
                })

        pair_required_values = []
        pair_available_values = []
        worst_block = None

        for i in range(len(demands)):
            for j in range(i + 1, len(demands)):
                a = demands[i]
                b = demands[j]

                # Vincolo rilevante quando i due contatti chiedono mosse opposte.
                if a['motion_dir'] == b['motion_dir']:
                    continue

                required = a['demand'] + b['demand']
                available = a['capacity'] + b['capacity']

                pair_required_values.append(required)
                pair_available_values.append(available)

                if available < required:
                    if worst_block is None or (required - available) > worst_block['gap']:
                        worst_block = {
                            'gap': required - available,
                            'a': a,
                            'b': b,
                            'required': required,
                            'available': available,
                        }

        summary_required = max(pair_required_values) if pair_required_values else 0
        summary_available = min(pair_available_values) if pair_available_values else 'na'

        return worst_block is None, {
            'required_spread': summary_required,
            'available_spread': summary_available,
            'demands': demands,
            'worst_block': worst_block,
        }

    sequence = []
    for i in range(4):
        sequence.append(('H', i))
        sequence.append(('V', i))

    for step_idx, (piece_type, idx) in enumerate(sequence, start=1):
        if piece_type == 'H':
            h_limits_before, v_limits_before = directional_mobility_limits()
            # Inserimento riga: deve interlockare con tutte le colonne gia presenti.
            for col in range(4):
                if not v_placed[col]:
                    continue
                h_slot = horiz_pieces[idx][col]
                v_slot = vert_pieces[col][idx]
                can_fit = fits(h_slot, v_slot)
                if not can_fit:
                    if capture_trace:
                        trace_steps.append({
                            'step': step_idx,
                            'piece': f'H{idx}',
                            'required_spread': 'na',
                            'available_spread': 'na',
                            'status': 'blocked',
                            'reason': 'interlock_invalid',
                            'h_limits': h_limits_before,
                            'v_limits': v_limits_before,
                        })
                    return False, {
                        'blocked_step': step_idx,
                        'blocked_piece_type': 'H',
                        'blocked_piece_index': idx,
                        'blocked_at_row': idx,
                        'blocked_at_col': col,
                        'reason': 'interlock_invalid',
                        'trace_steps': trace_steps if capture_trace else None,
                    }

            pairwise_ok, pairwise_details = pairwise_shift_check_for_insertion(
                'H', idx, h_limits_before, v_limits_before
            )
            if not pairwise_ok:
                if capture_trace:
                    trace_steps.append({
                        'step': step_idx,
                        'piece': f'H{idx}',
                        'required_spread': pairwise_details['required_spread'],
                        'available_spread': pairwise_details['available_spread'],
                        'status': 'blocked',
                        'reason': 'insufficient_pair_shift',
                        'h_limits': h_limits_before,
                        'v_limits': v_limits_before,
                    })
                return False, {
                    'blocked_step': step_idx,
                    'blocked_piece_type': 'H',
                    'blocked_piece_index': idx,
                    'reason': 'insufficient_pair_shift',
                    'required_spread': pairwise_details['required_spread'],
                    'available_spread': pairwise_details['available_spread'],
                    'pair_block': pairwise_details['worst_block'],
                    'trace_steps': trace_steps if capture_trace else None,
                }

            h_placed[idx] = True
            h_limits, v_limits = directional_mobility_limits()

            if capture_trace:
                trace_steps.append({
                    'step': step_idx,
                    'piece': f'H{idx}',
                    'required_spread': pairwise_details['required_spread'],
                    'available_spread': pairwise_details['available_spread'],
                    'status': 'ok',
                    'h_limits': h_limits,
                    'v_limits': v_limits,
                })

        else:
            # Inserimento colonna: interlock valido + check spread per-buco
            # sui pezzi orizzontali gia montati.
            h_limits_before, v_limits_before = directional_mobility_limits()
            for row in range(4):
                if not h_placed[row]:
                    continue
                h_slot = horiz_pieces[row][idx]
                v_slot = vert_pieces[idx][row]
                can_fit = fits(h_slot, v_slot)
                if not can_fit:
                    if capture_trace:
                        trace_steps.append({
                            'step': step_idx,
                            'piece': f'V{idx}',
                            'required_spread': 'na',
                            'available_spread': 'na',
                            'status': 'blocked',
                            'reason': 'interlock_invalid',
                            'h_limits': h_limits_before,
                            'v_limits': v_limits_before,
                        })
                    return False, {
                        'blocked_step': step_idx,
                        'blocked_piece_type': 'V',
                        'blocked_piece_index': idx,
                        'blocked_at_row': row,
                        'blocked_at_col': idx,
                        'reason': 'interlock_invalid',
                        'trace_steps': trace_steps if capture_trace else None,
                    }

            pairwise_ok, pairwise_details = pairwise_shift_check_for_insertion(
                'V', idx, h_limits_before, v_limits_before
            )
            required_spread = max(0, pairwise_details['required_spread'] - movement_credit)
            available_spread = pairwise_details['available_spread']

            if available_spread != 'na' and available_spread < required_spread:
                if capture_trace:
                    trace_steps.append({
                        'step': step_idx,
                        'piece': f'V{idx}',
                        'required_spread': required_spread,
                        'available_spread': available_spread,
                        'status': 'blocked',
                        'reason': 'insufficient_vertical_spread',
                        'h_limits': h_limits_before,
                        'v_limits': v_limits_before,
                    })
                return False, {
                    'blocked_step': step_idx,
                    'blocked_piece_type': 'V',
                    'blocked_piece_index': idx,
                    'reason': 'insufficient_vertical_spread',
                    'required_spread': required_spread,
                    'available_spread': available_spread,
                    'pair_block': pairwise_details['worst_block'],
                    'trace_steps': trace_steps if capture_trace else None,
                }

            v_placed[idx] = True
            h_limits, v_limits = directional_mobility_limits()

            if capture_trace:
                trace_steps.append({
                    'step': step_idx,
                    'piece': f'V{idx}',
                    'required_spread': required_spread,
                    'available_spread': available_spread,
                    'status': 'ok',
                    'h_limits': h_limits,
                    'v_limits': v_limits,
                })

    return (True, {'trace_steps': trace_steps}) if capture_trace else (True, None)


def verify_with_assembly_sequence(horiz_pieces, vert_pieces, capture_trace=False):
    return _simulate_alternating_sequence(
        horiz_pieces,
        vert_pieces,
        movement_credit=0,
        min_locked_cols_for_slack_check=2,
        capture_trace=capture_trace,
    )

# Precompute variants
VARIANTS = {pid: generate_variants(PIECES[pid]) for pid in PIECES}


def print_summary(valid_count, assembleable_count, returned_count):
    assembleable_text = 'na' if assembleable_count is None else str(assembleable_count)
    print(f"Summary: valid={valid_count}, assembleable={assembleable_text}, returned={returned_count}")


def persist_results(save_all, results):
    """Write results JSON whenever --save-all is provided (also when empty)."""
    if not save_all:
        return

    out_dir = os.path.dirname(save_all)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    with open(save_all, 'w', encoding='utf-8') as fout:
        json.dump(results, fout, indent=2)

def main(
    max_iter=None,
    save_all=None,
    check_assembly=False,
    assembly_trace=False,
    max_solutions=1,
    force_depth1_last=True,
):
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
                        persist_results(save_all, results)
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
                    elapsed_s = time.time() - start

                    if check_assembly:
                        is_assembleable, assembly_details = verify_with_assembly_sequence(
                            horiz_pieces,
                            vert_pieces,
                            capture_trace=assembly_trace,
                        )
                        if is_assembleable:
                            assembleable_count += 1
                        assembleable_text = 'yes' if is_assembleable else 'no'
                    else:
                        is_assembleable = False
                        assembly_details = None
                        assembleable_text = 'na'

                    print(
                        f"Valid solution found: iter={iter_count}, time={elapsed_s:.3f}s, "
                        f"assembleable={assembleable_text}"
                    )
                    print_systematic_solution(
                        horiz_ids,
                        horiz_vars,
                        horiz_pieces,
                        vert_ids,
                        vert_vars,
                        vert_pieces,
                    )
                    if check_assembly and assembly_trace and assembly_details and assembly_details.get('trace_steps'):
                        print_assembly_trace(assembly_details['trace_steps'])

                    reached_valid_limit = max_solutions is not None and valid_count >= max_solutions

                    solution = {
                        "horiz_ids": horiz_ids,
                        "horiz_vars": [variant_label(v) for v in horiz_vars],
                        "horiz_pieces": [[format_slot_for_output(slot) for slot in piece] for piece in horiz_pieces],
                        "vert_ids": vert_ids,
                        "vert_vars": [variant_label(v) for v in vert_vars],
                        "vert_pieces": [[format_slot_for_output(slot) for slot in piece] for piece in vert_pieces],
                        "classification": "assembleable" if is_assembleable else "valid",
                        "assembly_mode": "sequence" if check_assembly else None,
                        "assembly_details": assembly_details,
                        "depth1_last": last_vertical_id if has_depth_one(PIECES[last_vertical_id]) else None,
                        "last_vertical_id": last_vertical_id,
                        "iter": iter_count,
                        "time_s": elapsed_s
                    }
                    # print(f"Solution found after {iter_count} iterations in {solution['time_s']:.3f}s")
                    # print(json.dumps(solution, indent=2))
                    results.append(solution)
                    persist_results(save_all, results)
                    if reached_valid_limit:
                        print(f"Reached max-solutions={max_solutions}.")
                        persist_results(save_all, results)
                        print_summary(valid_count, assembleable_count, len(results))
                        return results

    print("Search completed: no solution found with the current limits.")
    persist_results(save_all, results)
    print_summary(valid_count, assembleable_count, len(results))
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Ricerca soluzione puzzle, con depth=1 ultimo.')
    parser.add_argument('--max-iter', type=int, default=None, help='Numero massimo di iterazioni da eseguire (utile per debug).')
    parser.add_argument('--save-all', type=str, default=None, help='File JSON dove salvare tutte le soluzioni trovate.')
    parser.add_argument('--check-assembly', action='store_true', help='Attiva il controllo di montabilità fisica con simulazione sequence (H0,V0,H1,V1,...).')
    parser.add_argument('--assembly-trace', action='store_true', help='Stampa i limiti di movimento up/down passo-passo durante --check-assembly.')
    parser.add_argument('--max-solutions', type=int, default=1, help='Numero massimo di soluzioni da trovare prima di fermarsi (usa valori >1 per cercare piu combinazioni).')
    parser.add_argument('--force-depth1-last', dest='force_depth1_last', action='store_true', default=True, help='Forza un pezzo con depth=1 come ultimo verticale (default).')
    parser.add_argument('--allow-any-last', dest='force_depth1_last', action='store_false', help='Non forzare depth=1 ultimo; prova qualunque pezzo come ultimo verticale.')
    args = parser.parse_args()
    res = main(
        max_iter=args.max_iter,
        save_all=args.save_all,
        check_assembly=args.check_assembly,
        assembly_trace=args.assembly_trace,
        max_solutions=args.max_solutions,
        force_depth1_last=args.force_depth1_last,
    )
    #if res:
    #    print(f"Found {len(res)} valid solution(s).")
    #else:
    #    print("No solution found with the provided limits.")
