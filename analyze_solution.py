#!/usr/bin/env python3
"""
Analizza una soluzione specifica per capire perché viene rifiutata dal check_assembly.
"""

import json

# La soluzione trovata
horiz_ids = [1, 4, 5, 7]
vert_ids = [3, 6, 8, 2]

# Pezzi ricostruiti dalla soluzione JSON
horiz_pieces = [
    [(2, '_'), (2, '_'), (3, '_'), (3, '^')],  # Pezzo 1 w_f
    [(2, '^'), (2, '_'), (3, '^'), (3, '_')],  # Pezzo 4 orig
    [(2, '^'), (3, '^'), (2, '_'), (3, '_')],  # Pezzo 5 w_f
    [(2, '^'), (2, '^'), (2, '^'), (3, '_')],  # Pezzo 7 wh_f
]

vert_pieces = [
    [(3, '^'), (2, '_'), (2, '_'), (2, '_')],  # Pezzo 3 orig
    [(2, '^'), (3, '^'), (2, '_'), (3, '_')],  # Pezzo 6 orig
    [(3, '^'), (3, '_'), (2, '^'), (2, '_')],  # Pezzo 8 w_f
    [(1, '_'), (2, '^'), (1, '^'), (3, '^')],  # Pezzo 2 orig (depth1_last)
]

def fits(h_slot, v_slot):
    """Incastro valido: direzioni opposte E somma >= 4"""
    return h_slot[1] != v_slot[1] and (h_slot[0] + v_slot[0]) >= 4

def can_insert_column_prelock(horiz_pieces, vert_pieces, col_idx):
    """Una colonna è inseribile durante il montaggio se scorre in tutte le righe."""
    print(f"\n  Colonna {col_idx} (pezzo verticale {vert_ids[col_idx]}):")
    can_insert = True
    for row_idx in range(4):
        h = horiz_pieces[row_idx][col_idx]
        v = vert_pieces[col_idx][row_idx]
        
        same_dir = h[1] == v[1]
        sum_depth = h[0] + v[0]
        can_slide = not same_dir and sum_depth <= 4
        
        status = "✓ OK" if can_slide else "✗ BLOCCATO"
        print(f"    Riga {row_idx} (pezzo oriz {horiz_ids[row_idx]}): h={h[0]}{h[1]} v={v[0]}{v[1]} -> ", end="")
        print(f"dir_opposta={not same_dir}, somma={sum_depth} -> {status}")
        
        if same_dir or sum_depth > 4:
            can_insert = False
    
    return can_insert

def verify_interlocks_only(horiz_pieces, vert_pieces):
    """Verifica incastri geometrici"""
    print("\n=== VERIFICA INCASTRI GEOMETRICI ===")
    all_valid = True
    for i in range(4):
        for j in range(4):
            h = horiz_pieces[i][j]
            v = vert_pieces[j][i]
            valid = fits(h, v)
            status = "✓" if valid else "✗"
            if not valid:
                print(f"{status} Riga {i}, Col {j}: h={h[0]}{h[1]} v={v[0]}{v[1]} -> dir_opposta={h[1] != v[1]}, somma={h[0] + v[0]}")
                all_valid = False
    
    if all_valid:
        print("✓ Tutti gli incastri sono geometricamente validi!")
    return all_valid

def analyze_assembly(horiz_pieces, vert_pieces):
    """Analizza montabilità secondo check_assembly"""
    print("\n=== ANALISI MONTABILITÀ ===")
    print("Regola: almeno 3 colonne devono essere inseribili in pre-lock")
    print("(cioè devono poter scorrere verticalmente: direzioni opposte E somma profondità ≤ 4)\n")
    
    insertable_columns = []
    for col_idx in range(4):
        can_insert = can_insert_column_prelock(horiz_pieces, vert_pieces, col_idx)
        insertable_columns.append(can_insert)
        result = "✓ INSERIBILE" if can_insert else "✗ NON INSERIBILE"
        print(f"  -> Colonna {col_idx}: {result}")
    
    num_insertable = sum(insertable_columns)
    print(f"\n  Totale colonne inseribili: {num_insertable}/4")
    
    if num_insertable >= 3:
        print("  ✓ OK: almeno 3 colonne sono inseribili -> ASSEMBLABILE")
        return True
    else:
        print(f"  ✗ FALLITO: solo {num_insertable} colonne inseribili (servono almeno 3) -> NON ASSEMBLABILE")
        return False

def print_grid():
    """Stampa la griglia della configurazione"""
    print("\n=== CONFIGURAZIONE ===")
    print("\nPezzi orizzontali (righe 0-3):")
    for i, pid in enumerate(horiz_ids):
        print(f"  Riga {i} - Pezzo {pid}: {[f'{d}{p}' for d, p in horiz_pieces[i]]}")
    
    print("\nPezzi verticali (colonne 0-3):")
    for i, pid in enumerate(vert_ids):
        print(f"  Colonna {i} - Pezzo {pid}: {[f'{d}{p}' for d, p in vert_pieces[i]]}")
    
    print("\nGriglia incroci (H=orizzontale, V=verticale):")
    print("     Col0         Col1         Col2         Col3")
    for i in range(4):
        row_str = f"R{i}: "
        for j in range(4):
            h = horiz_pieces[i][j]
            v = vert_pieces[j][i]
            row_str += f"H{h[0]}{h[1]}+V{v[0]}{v[1]}  "
        print(row_str)

if __name__ == '__main__':
    print("="*70)
    print("ANALISI SOLUZIONE PUZZLE 3D")
    print("="*70)
    
    print_grid()
    
    # Verifica incastri
    interlocks_ok = verify_interlocks_only(horiz_pieces, vert_pieces)
    
    # Verifica assemblaggio
    assembly_ok = analyze_assembly(horiz_pieces, vert_pieces)
    
    print("\n" + "="*70)
    print("CONCLUSIONE:")
    print(f"  Incastri geometrici: {'✓ VALIDI' if interlocks_ok else '✗ INVALIDI'}")
    print(f"  Assemblabilità fisica: {'✓ ASSEMBLABILE' if assembly_ok else '✗ NON ASSEMBLABILE'}")
    print("="*70)
