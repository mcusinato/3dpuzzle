#!/usr/bin/env python3
"""
Verifica montabilità delle soluzioni geometriche uniche.

Per ogni soluzione, prova 4 sequenze di montaggio:
1. H0 V0 H1 V1 H2 V2 H3 V3
2. V0 H0 V1 H1 V2 H2 V3 H3
3. H3 V3 H2 V2 H1 V1 H0 V0 (inversa della 1)
4. V3 H3 V2 H2 V1 H1 V0 H0 (inversa della 2)

Logica montabilità:
- Primi 3 pezzi: sempre montabili
- 4° pezzo in poi: si inserisce nel 2° buco dei pezzi precedenti
  - Se i due buchi sono nella stessa direzione: inseribile dal lato libero
  - Se i due buchi sono in direzioni opposte: servono spazi uguali per shiftare
"""

import json
from typing import List, Tuple, Optional
import puzzle_solver as ps

# Definizione pezzi (da puzzle_solver.py)
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

def _flip(d):
    """Capovolgi direzione U<->D"""
    return 'D' if d == 'U' else 'U'

def get_piece_notches(piece_id: int, variant: int) -> List[Tuple[int, str]]:
    """Restituisce i 4 notches di un pezzo per un dato variant."""
    orig = PIECES[piece_id]
    mirror = tuple(reversed(orig))
    
    # v0: originale, v1: specchiato, v2: capovolto, v3: specchiato+capovolto
    variants = [
        orig,  # v0
        mirror,  # v1: specchiato
        tuple((d, _flip(dir)) for d, dir in orig),  # v2: capovolto
        tuple((d, _flip(dir)) for d, dir in mirror),  # v3: specchiato+capovolto
    ]
    
    return list(variants[variant])


def load_solutions():
    """Carica le 376 soluzioni dal JSON."""
    with open('puzzle_solutions_unique_geometric.json', 'r') as f:
        data = json.load(f)
    return data.get('solutions', [])


def parse_solution(sol_dict):
    """Converte una soluzione dal JSON in dizionario {posizione: dati_pezzo}."""
    grid = {}
    
    # Leggi blocco H (H0-H3)
    if 'h' in sol_dict:
        for i, piece_data in enumerate(sol_dict['h']):
            pid = piece_data['pid']
            var = piece_data['variant']
            notches = get_piece_notches(pid, var)
            grid[f'H{i}'] = {
                'piece_id': pid,
                'variant': var,
                'notches': notches
            }
    
    # Leggi blocco V (V0-V3)
    if 'v' in sol_dict:
        for i, piece_data in enumerate(sol_dict['v']):
            pid = piece_data['pid']
            var = piece_data['variant']
            notches = get_piece_notches(pid, var)
            grid[f'V{i}'] = {
                'piece_id': pid,
                'variant': var,
                'notches': notches
            }
    
    return grid


def get_orthogonal_positions(position: str) -> List[str]:
    """Restituisce le posizioni ortogonali a una data posizione."""
    # Ad ogni incrocio della griglia si incontrano un pezzo H e uno V
    h_index = int(position[1])  # es. 'H2' -> 2
    v_index = int(position[1])  # es. 'V2' -> 2
    
    if position.startswith('H'):
        # Pezzo H al indice h_index si incrocia con V0, V1, V2, V3
        return [f'V{i}' for i in range(4)]
    else:
        # Pezzo V al indice v_index si incrocia con H0, H1, H2, H3
        return [f'H{i}' for i in range(4)]


def can_assemble(grid: dict, sequence: List[str]) -> Tuple[bool, str]:
    """
    Verifica se una sequenza di montaggio è valida.
    
    Restituisce: (True/False, messaggio dettaglio)
    """
    assembled = {}
    
    for step, pos in enumerate(sequence):
        if pos not in grid:
            return False, f"Passo {step}: posizione {pos} mancante nella soluzione"
        
        piece_data = grid[pos]
        notches = piece_data['notches']
        second_notch = notches[1]  # (depth, direction)
        
        if step == 0:
            # Primo pezzo: sempre montabile
            assembled[pos] = piece_data
            continue
        
        if step == 1:
            # Secondo pezzo: ortogonale al primo, sempre montabile
            # (buchi contrapposti e geometricamente compatibili)
            assembled[pos] = piece_data
            continue
        
        if step == 2:
            # Terzo pezzo: si incastra sul secondo buco del primo pezzo
            # (solo 1 pezzo prima, no vincoli)
            assembled[pos] = piece_data
            continue
        
        # Passo 3+ : il nuovo pezzo si inserisce nel 2° buco dei pezzi già inseriti
        # Verifica compatibilità con i pezzi ortogonali
        ortho_positions = get_orthogonal_positions(pos)
        
        # Raccogli i 2° buchi dei pezzi ortogonali già assemblati
        ortho_second_notches = []
        for orth_pos in ortho_positions:
            if orth_pos in assembled:
                orth_piece = assembled[orth_pos]
                orth_second_notch = orth_piece['notches'][1]
                ortho_second_notches.append((orth_pos, orth_second_notch))
        
        if not ortho_second_notches:
            # Nessun pezzo ortogonale ancora assemblato
            assembled[pos] = piece_data
            continue
        
        # Controlla compatibilità con i pezzi ortogonali
        # Se gli altri hanno il 2° buco in direzioni diverse, serve lo shift
        directions = [notch[1] for _, notch in ortho_second_notches]
        
        if len(set(directions)) > 1:
            # Direzioni diverse: serve lo shift
            # Verifica se gli spazi sono uguali
            depths = [notch[0] for _, notch in ortho_second_notches]
            
            # Per fare shift, tutti i pezzi ortogonali devono avere spazi uguali
            # e il nuovo pezzo deve potersi inserire
            if len(set(depths)) > 1:
                # Spazi diversi: non puoi shiftare in modo uniforme
                ortho_str = ', '.join([f"{pos}({d})" for pos, (d, _) in ortho_second_notches])
                return False, f"Passo {step}: {pos} non montabile. Pezzi ortogonali {ortho_str} hanno profondità incoerenti per shift."
            
            # Se siamo qui, tutti gli spazi sono uguali e le direzioni sono diverse
            # Allora lo shift è possibile (spazi simmetrici)
        
        assembled[pos] = piece_data
    
    return True, f"Sequenza valida! Tutti gli {len(sequence)} pezzi montati."


def check_all_sequences(grid: dict, solution_idx: int) -> Tuple[bool, Optional[str], List[str]]:
    """
    Prova tutte e 4 le sequenze di montaggio.
    
    Restituisce: (almeno_una_valida, primo_dettaglio, sequenze_che_funzionano)
    """
    sequences = [
        ['H0', 'V0', 'H1', 'V1', 'H2', 'V2', 'H3', 'V3'],
        ['V0', 'H0', 'V1', 'H1', 'V2', 'H2', 'V3', 'H3'],
        ['H3', 'V3', 'H2', 'V2', 'H1', 'V1', 'H0', 'V0'],
        ['V3', 'H3', 'V2', 'H2', 'V1', 'H1', 'V0', 'H0'],
    ]
    
    valid_sequences = []
    first_detail = None
    
    # Usa il criterio del solver principale per evitare discrepanze.
    solver_sol = {
        'h': tuple((grid[f'H{i}']['piece_id'], grid[f'H{i}']['variant']) for i in range(4)),
        'v': tuple((grid[f'V{i}']['piece_id'], grid[f'V{i}']['variant']) for i in range(4)),
    }

    seq_tuples = [
        [('H', 0), ('V', 0), ('H', 1), ('V', 1), ('H', 2), ('V', 2), ('H', 3), ('V', 3)],
        [('V', 0), ('H', 0), ('V', 1), ('H', 1), ('V', 2), ('H', 2), ('V', 3), ('H', 3)],
        [('H', 3), ('V', 3), ('H', 2), ('V', 2), ('H', 1), ('V', 1), ('H', 0), ('V', 0)],
        [('V', 3), ('H', 3), ('V', 2), ('H', 2), ('V', 1), ('H', 1), ('V', 0), ('H', 0)],
    ]

    for seq_idx, seq in enumerate(sequences):
        success = ps.check_assembly(solver_sol, seq_tuples[seq_idx])['sequence_ok']

        if first_detail is None:
            first_detail = f"Seq {seq_idx + 1}: {'valida' if success else 'non valida'} (criterio solver)"

        if success:
            valid_sequences.append(f"Seq{seq_idx + 1}:{' '.join(seq)}")
    
    return len(valid_sequences) > 0, first_detail, valid_sequences


def format_solution_line(sol_dict: dict) -> str:
    """Rende una soluzione in una riga compatta H/V."""
    h = ' | '.join(
        f"H{i}=P{p['pid']}/v{p['variant']}"
        for i, p in enumerate(sol_dict.get('h', []))
    )
    v = ' | '.join(
        f"V{i}=P{p['pid']}/v{p['variant']}"
        for i, p in enumerate(sol_dict.get('v', []))
    )
    return f"{h} | {v}"


SEQUENCE_ORDERS = {
    'Seq1': ['H0', 'V0', 'H1', 'V1', 'H2', 'V2', 'H3', 'V3'],
    'Seq2': ['V0', 'H0', 'V1', 'H1', 'V2', 'H2', 'V3', 'H3'],
    'Seq3': ['H3', 'V3', 'H2', 'V2', 'H1', 'V1', 'H0', 'V0'],
    'Seq4': ['V3', 'H3', 'V2', 'H2', 'V1', 'H1', 'V0', 'H0'],
}


def position_notches(sol_dict: dict, pos: str) -> str:
    """Restituisce le tacche della posizione (es. H0/V2) come stringa [3U 2D ...]."""
    axis = pos[0]
    idx = int(pos[1])
    piece = sol_dict['h'][idx] if axis == 'H' else sol_dict['v'][idx]
    notches = get_piece_notches(piece['pid'], piece['variant'])
    return ' '.join(f"{d}{s}" for d, s in notches)


def main():
    print("=" * 80)
    print(" Verifica Montabilità delle 376 Soluzioni Geometriche")
    print("=" * 80)
    
    solutions = load_solutions()
    print(f"\nCaricate {len(solutions)} soluzioni.\n")
    
    assemblable = []
    not_assemblable = []
    
    for idx, sol_dict in enumerate(solutions):
        grid = parse_solution(sol_dict)
        found_valid, detail, valid_seqs = check_all_sequences(grid, idx)
        
        if found_valid:
            assemblable.append((idx, sol_dict, valid_seqs))
            print(f"✓ Sol {idx:3d}: MONTABILE! Sequenze: {valid_seqs}")
        else:
            not_assemblable.append((idx, detail))
            if idx < 5 or idx % 50 == 0:
                print(f"✗ Sol {idx:3d}: Non montabile. {detail}")
    
    print("\n" + "=" * 80)
    print(f" RISULTATI FINALI")
    print("=" * 80)
    print(f"Soluzioni montabili: {len(assemblable)}")
    print(f"Soluzioni non montabili: {len(not_assemblable)}")
    print(f"Totale testate: {len(solutions)}")
    
    if assemblable:
        print(f"\n✓✓✓ TROVATE {len(assemblable)} SOLUZIONE(I) MONTABILE(I)! ✓✓✓")
        print("\nDettaglio semplice (ordine sequenza valida):")
        print("-" * 80)
        for sol_idx, sol, seqs in assemblable:
            print(f"Soluzione {sol_idx}:")
            for seq in seqs:
                seq_name = seq.split(':', 1)[0]
                order = SEQUENCE_ORDERS.get(seq_name, [])
                print(f"  {seq_name}:")
                for pos in order:
                    print(f"    {pos}:[{position_notches(sol, pos)}]")
            print("-" * 80)
    else:
        print("\n✗ Nessuna soluzione è montabile con le 4 sequenze testate.")
    
    print("\n" + "=" * 80)


if __name__ == '__main__':
    main()
