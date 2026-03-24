#!/usr/bin/env python3
"""
Trova tutte le soluzioni geometricamente compatibili del puzzle 3D,
ignorando la montabilità, e rimuove le soluzioni equivalenti.

Equivalenze considerate:
1) I due pezzi uguali (3 e 7) sono indistinguibili.
2) Simmetria di inversione completa:
   H0 H1 H2 H3 V0 V1 V2 V3
   ≡
   H3 H2 H1 H0 V3 V2 V1 V0
3) Scambio blocchi orizzontali/verticali:
    H0 H1 H2 H3 V0 V1 V2 V3
    ≡
    V0 V1 V2 V3 H0 H1 H2 H3

Output in ordine: H0 H1 H2 H3 V0 V1 V2 V3.
"""

from __future__ import annotations

import argparse
import json
import time
from typing import Dict, Iterable, List, Tuple

from puzzle_solver import PIECES, VARIANTS_RAW, solve

Solution = Dict[str, Tuple[Tuple[int, int], ...]]
GridSignature = Tuple[Tuple[Tuple[int, str], Tuple[int, str]], ...]


def fmt_notch(notch: Tuple[int, str]) -> str:
    depth, direction = notch
    return f"{depth}{direction}"


def fmt_piece(oriented_piece: Tuple[Tuple[int, str], ...]) -> str:
    return " ".join(fmt_notch(n) for n in oriented_piece)


def get_oriented_pieces(sol: Solution):
    h_pieces = [VARIANTS_RAW[pid][variant] for pid, variant in sol["h"]]
    v_pieces = [VARIANTS_RAW[pid][variant] for pid, variant in sol["v"]]
    return h_pieces, v_pieces


def grid_signature(
    sol: Solution,
    reverse_positions: bool = False,
    swap_hv: bool = False,
    flip_all_directions: bool = False,
) -> GridSignature:
    """
    Firma geometrica della griglia 4x4, indipendente dagli ID dei pezzi.

    - reverse_positions: applica H3..H0 e V3..V0.
    - swap_hv: applica scambio blocchi H..V <-> V..H.
    - flip_all_directions: inverte tutte le direzioni U <-> D su tutti i pezzi.
    """
    h_pieces, v_pieces = get_oriented_pieces(sol)

    if swap_hv:
        base_h, base_v = v_pieces, h_pieces
    else:
        base_h, base_v = h_pieces, v_pieces

    sig: List[Tuple[Tuple[int, str], Tuple[int, str]]] = []
    for i in range(4):
        for j in range(4):
            if not reverse_positions:
                h_notch = base_h[i][j]
                v_notch = base_v[j][i]
            else:
                h_notch = base_h[3 - i][3 - j]
                v_notch = base_v[3 - j][3 - i]

            if flip_all_directions:
                h_depth, h_dir = h_notch
                v_depth, v_dir = v_notch
                h_notch = (h_depth, 'D' if h_dir == 'U' else 'U')
                v_notch = (v_depth, 'D' if v_dir == 'U' else 'U')

            sig.append((h_notch, v_notch))

    return tuple(sig)


def canonical_signature(sol: Solution) -> GridSignature:
    candidates = [
        grid_signature(sol, reverse_positions=reverse, swap_hv=swap, flip_all_directions=flip)
        for reverse in (False, True)
        for swap in (False, True)
        for flip in (False, True)
    ]
    return min(candidates)


def deduplicate_equivalent_solutions(solutions: Iterable[Solution]) -> List[Solution]:
    seen = set()
    unique: List[Solution] = []

    for sol in solutions:
        sig = canonical_signature(sol)
        if sig in seen:
            continue
        seen.add(sig)
        unique.append(sol)

    return unique


def compact_solution(sol: Solution) -> str:
    h_parts = []
    for idx, (pid, var) in enumerate(sol["h"]):
        piece = VARIANTS_RAW[pid][var]
        h_parts.append(f"H{idx}=P{pid}/v{var}:[{fmt_piece(piece)}]")

    v_parts = []
    for idx, (pid, var) in enumerate(sol["v"]):
        piece = VARIANTS_RAW[pid][var]
        v_parts.append(f"V{idx}=P{pid}/v{var}:[{fmt_piece(piece)}]")

    return " | ".join(h_parts + v_parts)


def compact_ids_solution(sol: Solution) -> str:
    h_ids = " ".join(f"(P{pid},v{var})" for pid, var in sol["h"])
    v_ids = " ".join(f"(P{pid},v{var})" for pid, var in sol["v"])
    return f"H:[{h_ids}] V:[{v_ids}]"


def dir_counts(piece):
    c = {'U': 0, 'D': 0}
    for _, d in piece:
        c[d] += 1
    return c


def has_3_plus_1(piece):
    c = dir_counts(piece)
    return sorted(c.values()) == [1, 3]


def unique_direction(piece):
    c = dir_counts(piece)
    return 'U' if c['U'] == 1 else 'D'


def has_h0_unique_first(sol: Solution) -> bool:
    """Verifica se H0 ha primo buco da 1 e direzione unica."""
    h0_pid, h0_var = sol["h"][0]
    h0_piece = VARIANTS_RAW[h0_pid][h0_var]
    h0_first = h0_piece[0]
    h0_unique_dir = unique_direction(h0_piece)
    return (
        h0_first[0] == 1 and
        has_3_plus_1(h0_piece) and
        h0_first[1] == h0_unique_dir
    )



def export_json(path: str, all_count: int, unique_solutions: List[Solution], filtered_count: int = None) -> None:
    payload = {
        "piece_count": len(PIECES),
        "total_geometric_compatible": all_count,
        "total_unique_non_equivalent": len(unique_solutions),
        "equivalences": {
            "identical_pieces": [3, 7],
            "full_reverse": "H0 H1 H2 H3 V0 V1 V2 V3 == H3 H2 H1 H0 V3 V2 V1 V0",
            "swap_hv_blocks": "H0 H1 H2 H3 V0 V1 V2 V3 == V0 V1 V2 V3 H0 H1 H2 H3",
            "flip_all_directions": "tutti i pezzi capovolti (U↔D su tutti i notch) equivalenti",
        },
        "solutions": [
            {
                "h": [{"pid": pid, "variant": var} for pid, var in sol["h"]],
                "v": [{"pid": pid, "variant": var} for pid, var in sol["v"]],
                "text": compact_solution(sol),
            }
            for sol in unique_solutions
        ],
    }
    
    if filtered_count is not None:
        payload["filtered_count"] = filtered_count

    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Trova tutte le soluzioni geometriche uniche (non equivalenti)."
    )
    parser.add_argument(
        "--progress-every",
        type=int,
        default=50000,
        help="Mostra progresso ogni N configurazioni H testate (default: 50000).",
    )
    parser.add_argument(
        "--show",
        type=int,
        default=10,
        help="Numero di soluzioni uniche da stampare (default: 10).",
    )
    parser.add_argument(
        "--json-out",
        default="puzzle_solutions_unique_geometric.json",
        help="File JSON di output (default: puzzle_solutions_unique_geometric.json).",
    )
    parser.add_argument(
        "--show-compact",
        action="store_true",
        help="Stampa le soluzioni mostrate in formato compatto ID/variante.",
    )
    parser.add_argument(
        "--filter-h0-unique",
        action="store_true",
        help="Filtra e stampa solo le soluzioni con H0 che ha primo buco da 1 come unico.",
    )

    args = parser.parse_args()

    print("=" * 72)
    print(" Ricerca soluzioni geometriche compatibili (senza check montaggio)")
    print("=" * 72)
    print("Equivalenze:")
    print(" - pezzi uguali 3 e 7 indistinguibili")
    print(" - H0 H1 H2 H3 V0 V1 V2 V3 == H3 H2 H1 H0 V3 V2 V1 V0")
    print(" - H0 H1 H2 H3 V0 V1 V2 V3 == V0 V1 V2 V3 H0 H1 H2 H3")
    print(" - tutti i pezzi capovolti (U↔D): tutti equivalenti")

    t0 = time.time()
    all_solutions, total_checked = solve(progress_every=args.progress_every)
    unique = deduplicate_equivalent_solutions(all_solutions)
    dt = time.time() - t0

    print(f"\nConfigurazioni H testate: {total_checked:,}")
    print(f"Soluzioni geometriche compatibili (raw): {len(all_solutions):,}")
    print(f"Soluzioni uniche non equivalenti: {len(unique):,}")
    print(f"Tempo totale: {dt:.1f}s")

    n_show = min(args.show, len(unique))
    if n_show > 0:
        print(f"\nPrime {n_show} soluzioni uniche in ordine H0..H3 V0..V3:")
        for idx, sol in enumerate(unique[:n_show], 1):
            if args.show_compact:
                print(f"{idx:>3}. {compact_ids_solution(sol)}")
            else:
                print(f"{idx:>3}. {compact_solution(sol)}")

    if args.filter_h0_unique:
        filtered = [s for s in unique if has_h0_unique_first(s)]
        print(f"\nSoluzioni con H0 che ha primo buco da 1 come unico: {len(filtered)}")
        for idx, sol in enumerate(filtered, 1):
            h_pieces = [VARIANTS_RAW[pid][var] for pid, var in sol["h"]]
            v_pieces = [VARIANTS_RAW[pid][var] for pid, var in sol["v"]]
            line_parts = []
            for i in range(4):
                line_parts.append(f"H{i}:[{fmt_piece(h_pieces[i])}]")
                line_parts.append(f"V{i}:[{fmt_piece(v_pieces[i])}]")
            print(f"{idx:>2}. {' | '.join(line_parts)}")
        export_json(args.json_out, len(all_solutions), filtered, filtered_count=len(filtered))
        print(f"\nOutput JSON scritto in: {args.json_out} (solo {len(filtered)} filtrate)")
    else:
        export_json(args.json_out, len(all_solutions), unique)
        print(f"\nOutput JSON scritto in: {args.json_out}")


if __name__ == "__main__":
    main()
