#!/usr/bin/env python3
"""
Simula una sequenza di montaggio alternata: H0 -> V0 -> H1 -> V1 -> H2 -> V2 -> H3 -> V3
per vedere esattamente dove si blocca l'assemblaggio.
"""

# La soluzione trovata
horiz_ids = [1, 4, 5, 7]
vert_ids = [3, 6, 8, 2]

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

def can_interlock(slot1, slot2):
    """
    Due pezzi possono incastrarsi se:
    - Hanno direzioni opposte
    - La somma delle profondità >= 4
    
    Il "gioco" (slack) è: somma - 4
    - somma = 4 → gioco = 0 (bloccati)
    - somma = 5 → gioco = 1 (possono shiftare di 1)
    - somma = 6 → gioco = 2 (possono shiftare di 2)
    
    Returns: (can_fit, slack) dove slack è None se non possono incastrarsi
    """
    opposite_dir = slot1[1] != slot2[1]
    sum_depth = slot1[0] + slot2[0]
    if opposite_dir and sum_depth >= 4:
        return True, sum_depth - 4
    else:
        return False, None

def simulate_alternating_assembly():
    """
    Simula il montaggio alternando: H0 -> V0 -> H1 -> V1 -> H2 -> V2 -> H3 -> V3
    """
    print("="*80)
    print("SIMULAZIONE MONTAGGIO ALTERNATO")
    print("Sequenza: H0 -> V0 -> H1 -> V1 -> H2 -> V2 -> H3 -> V3")
    print("="*80)
    
    # Rappresentiamo lo stato della griglia: None = vuoto, altrimenti (h_slot, v_slot)
    grid = [[None for _ in range(4)] for _ in range(4)]
    
    # Teniamo traccia di quali pezzi sono stati inseriti
    h_placed = [False] * 4
    v_placed = [False] * 4
    
    sequence = []
    for i in range(4):
        sequence.append(('H', i))  # Orizzontale i
        sequence.append(('V', i))  # Verticale i
    
    step = 0
    for piece_type, idx in sequence:
        step += 1
        print(f"\n{'='*80}")
        print(f"PASSO {step}: Inserimento {'ORIZZONTALE' if piece_type == 'H' else 'VERTICALE'} {idx} (pezzo {horiz_ids[idx] if piece_type == 'H' else vert_ids[idx]})")
        print(f"{'='*80}")
        
        if piece_type == 'H':
            # Inseriamo il pezzo orizzontale alla riga idx
            print(f"\nInserimento RIGA {idx} - Pezzo {horiz_ids[idx]}: {[f'{d}{p}' for d, p in horiz_pieces[idx]]}")
            
            # Controlliamo se può essere inserito rispetto ai verticali già presenti
            can_insert = True
            conflicts = []
            
            for col in range(4):
                if v_placed[col]:
                    # C'è già un pezzo verticale in questa colonna
                    h_slot = horiz_pieces[idx][col]
                    v_slot = vert_pieces[col][idx]
                    
                    can_fit, slack = can_interlock(h_slot, v_slot)
                    
                    print(f"  Col {col} (V{col} già presente): h={h_slot[0]}{h_slot[1]} v={v_slot[0]}{v_slot[1]} -> ", end="")
                    
                    if can_fit:
                        sum_depth = h_slot[0] + v_slot[0]
                        status = f"bloccato" if slack == 0 else f"gioco={slack}"
                        print(f"✓ OK (somma={sum_depth}, {status})")
                    else:
                        same_dir = h_slot[1] == v_slot[1]
                        sum_depth = h_slot[0] + v_slot[0]
                        reason = "stessa direzione" if same_dir else f"somma={sum_depth} < 4"
                        print(f"✗ IMPOSSIBILE ({reason})")
                        can_insert = False
                        conflicts.append((col, h_slot, v_slot, reason))
            
            if can_insert:
                h_placed[idx] = True
                for col in range(4):
                    if v_placed[col]:
                        grid[idx][col] = (horiz_pieces[idx][col], vert_pieces[col][idx])
                print(f"\n✓ RIGA {idx} inserita con successo!")
            else:
                print(f"\n✗ IMPOSSIBILE inserire RIGA {idx}!")
                print(f"   Conflitti in {len(conflicts)} posizione/i:")
                for col, h, v, reason in conflicts:
                    print(f"     - Colonna {col}: {reason}")
                print("\n" + "="*80)
                print("❌ MONTAGGIO BLOCCATO!")
                print("="*80)
                return False, step, piece_type, idx, conflicts
                
        else:  # 'V'
            # Inseriamo il pezzo verticale alla colonna idx
            print(f"\nInserimento COLONNA {idx} - Pezzo {vert_ids[idx]}: {[f'{d}{p}' for d, p in vert_pieces[idx]]}")
            
            # Controlliamo se può essere inserito rispetto agli orizzontali già presenti
            can_insert = True
            conflicts = []
            
            for row in range(4):
                if h_placed[row]:
                    # C'è già un pezzo orizzontale in questa riga
                    h_slot = horiz_pieces[row][idx]
                    v_slot = vert_pieces[idx][row]
                    
                    can_fit, slack = can_interlock(h_slot, v_slot)
                    
                    print(f"  Riga {row} (H{row} già presente): h={h_slot[0]}{h_slot[1]} v={v_slot[0]}{v_slot[1]} -> ", end="")
                    
                    if can_fit:
                        sum_depth = h_slot[0] + v_slot[0]
                        status = f"bloccato" if slack == 0 else f"gioco={slack}"
                        print(f"✓ OK (somma={sum_depth}, {status})")
                    else:
                        same_dir = h_slot[1] == v_slot[1]
                        sum_depth = h_slot[0] + v_slot[0]
                        reason = "stessa direzione" if same_dir else f"somma={sum_depth} < 4"
                        print(f"✗ IMPOSSIBILE ({reason})")
                        can_insert = False
                        conflicts.append((row, h_slot, v_slot, reason))
            
            if can_insert:
                v_placed[idx] = True
                for row in range(4):
                    if h_placed[row]:
                        grid[row][idx] = (horiz_pieces[row][idx], vert_pieces[idx][row])
                print(f"\n✓ COLONNA {idx} inserita con successo!")
            else:
                print(f"\n✗ IMPOSSIBILE inserire COLONNA {idx}!")
                print(f"   Conflitti in {len(conflicts)} posizione/i:")
                for row, h, v, reason in conflicts:
                    print(f"     - Riga {row}: {reason}")
                print("\n" + "="*80)
                print("❌ MONTAGGIO BLOCCATO!")
                print("="*80)
                return False, step, piece_type, idx, conflicts
    
    print("\n" + "="*80)
    print("✓ MONTAGGIO COMPLETATO CON SUCCESSO!")
    print("="*80)
    return True, step, None, None, None

if __name__ == '__main__':
    success, final_step, blocked_type, blocked_idx, conflicts = simulate_alternating_assembly()
    
    print("\n" + "="*80)
    print("RIEPILOGO")
    print("="*80)
    if success:
        print("✓ La configurazione è assemblabile con questa sequenza!")
    else:
        piece_name = "ORIZZONTALE" if blocked_type == 'H' else "VERTICALE"
        piece_id = horiz_ids[blocked_idx] if blocked_type == 'H' else vert_ids[blocked_idx]
        print(f"✗ Montaggio bloccato al passo {final_step}")
        print(f"✗ Non è possibile inserire {piece_name} {blocked_idx} (pezzo {piece_id})")
        print(f"✗ La configurazione NON è assemblabile con questa sequenza!")
