#!/usr/bin/env python3
"""Stampa la soluzione 62 e verifica la montabilita con il criterio del solver."""

import json
import puzzle_solver as ps

# Definizione pezzi
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
    return 'D' if d == 'U' else 'U'

def get_notches_str(piece_id, variant):
    """Converte piece_id + variant in stringa tacche."""
    orig = PIECES[piece_id]
    mirror = tuple(reversed(orig))
    variants = [
        orig,  # v0
        mirror,  # v1
        tuple((d, _flip(dir)) for d, dir in orig),  # v2
        tuple((d, _flip(dir)) for d, dir in mirror),  # v3
    ]
    notches = variants[variant]
    return ' '.join(f'{d}{dir}' for d, dir in notches)

with open('puzzle_solutions_unique_geometric.json', 'r') as f:
    data = json.load(f)

sol = data['solutions'][62]

print('=' * 90)
print(' SOLUZIONE 62 (VERIFICA MONTABILITA)')
print('=' * 90)
print()

solver_sol = {
    'h': tuple((p['pid'], p['variant']) for p in sol['h']),
    'v': tuple((p['pid'], p['variant']) for p in sol['v']),
}

sequences = [
    ('Seq1', [('H', 0), ('V', 0), ('H', 1), ('V', 1), ('H', 2), ('V', 2), ('H', 3), ('V', 3)]),
    ('Seq2', [('V', 0), ('H', 0), ('V', 1), ('H', 1), ('V', 2), ('H', 2), ('V', 3), ('H', 3)]),
    ('Seq3', [('H', 3), ('V', 3), ('H', 2), ('V', 2), ('H', 1), ('V', 1), ('H', 0), ('V', 0)]),
    ('Seq4', [('V', 3), ('H', 3), ('V', 2), ('H', 2), ('V', 1), ('H', 1), ('V', 0), ('H', 0)]),
]

print('Esito montabilita (criterio solver):')
for name, seq in sequences:
    ok = ps.check_assembly(solver_sol, seq)['sequence_ok']
    print(f'  {name}: {"MONTABILE" if ok else "NON MONTABILE"}')
print()

# Stampa il testo della soluzione se disponibile
if 'text' in sol:
    print('Rappresentazione testuale:')
    print(sol['text'])
    print()

print('BLOCCO ORIZZONTALE (H):')
for i, piece in enumerate(sol['h']):
    pid = piece['pid']
    variant = piece['variant']
    notches_str = get_notches_str(pid, variant)
    print(f'  H{i}: P{pid}/v{variant} → [{notches_str}]')

print()

print('BLOCCO VERTICALE (V):')
for i, piece in enumerate(sol['v']):
    pid = piece['pid']
    variant = piece['variant']
    notches_str = get_notches_str(pid, variant)
    print(f'  V{i}: P{pid}/v{variant} → [{notches_str}]')

print()
print('Dettaglio per posizione di montaggio:')
print()
for i in range(4):
    h_piece = sol['h'][i]
    v_piece = sol['v'][i]
    h_pid, h_var = h_piece['pid'], h_piece['variant']
    v_pid, v_var = v_piece['pid'], v_piece['variant']
    h_notches = get_notches_str(h_pid, h_var)
    v_notches = get_notches_str(v_pid, v_var)
    
    print(f'Incrocio {i}:')
    print(f'  H{i}: Pezzo {h_pid} variante {h_var:<2} → {h_notches}')
    print(f'  V{i}: Pezzo {v_pid} variante {v_var:<2} → {v_notches}')
    print()

print('=' * 90)
