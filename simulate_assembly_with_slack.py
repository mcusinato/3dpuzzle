#!/usr/bin/env python3
"""
Simula montaggio con controllo dello "slack disponibile".

Quando inserisci un pezzo, gli altri pezzi devono avere abbastanza gioco
per essere spostati e permettere l'inserimento.
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
    """Due pezzi si incastrano se direzioni opposte E somma >= 4"""
    opposite_dir = slot1[1] != slot2[1]
    sum_depth = slot1[0] + slot2[0]
    if opposite_dir and sum_depth >= 4:
        return True, sum_depth - 4  # (can_fit, slack)
    else:
        return False, None

class AssemblyState:
    """Tiene traccia dello stato corrente del montaggio"""
    
    def __init__(self):
        # Quali pezzi sono stati inseriti
        self.h_placed = [False] * 4
        self.v_placed = [False] * 4
        
        # Matrice degli incastri: [row][col] = (can_fit, slack) or None
        self.grid = [[None for _ in range(4)] for _ in range(4)]
    
    def get_horizontal_slack_at_col(self, row_idx, col_idx):
        """
        Quanto può muoversi H[row_idx] alla colonna col_idx?
        Ritorna lo slack se quella colonna è già occupata da un verticale,
        altrimenti ritorna None (libero).
        """
        if not self.v_placed[col_idx]:
            return None  # Colonna libera, nessun vincolo
        
        if self.grid[row_idx][col_idx]:
            return self.grid[row_idx][col_idx][1]  # slack esistente
        else:
            # Calcola il potenziale slack
            h_slot = horiz_pieces[row_idx][col_idx]
            v_slot = vert_pieces[col_idx][row_idx]
            can_fit, slack = can_interlock(h_slot, v_slot)
            return slack if can_fit else 0
    
    def get_vertical_slack_at_row(self, col_idx, row_idx):
        """
        Quanto può muoversi V[col_idx] alla riga row_idx?
        """
        if not self.h_placed[row_idx]:
            return None  # Riga libera, nessun vincolo
        
        if self.grid[row_idx][col_idx]:
            return self.grid[row_idx][col_idx][1]  # slack esistente
        else:
            h_slot = horiz_pieces[row_idx][col_idx]
            v_slot = vert_pieces[col_idx][row_idx]
            can_fit, slack = can_interlock(h_slot, v_slot)
            return slack if can_fit else 0
    
    def can_insert_horizontal(self, row_idx):
        """
        Può inserire H[row_idx]?
        Per ogni colonna occupata, verifica che l'incastro sia valido.
        """
        print(f"\nInserimento RIGA {row_idx} - Pezzo {horiz_ids[row_idx]}: {[f'{d}{p}' for d, p in horiz_pieces[row_idx]]}")
        
        conflicts = []
        for col in range(4):
            if self.v_placed[col]:
                h_slot = horiz_pieces[row_idx][col]
                v_slot = vert_pieces[col][row_idx]
                can_fit, slack = can_interlock(h_slot, v_slot)
                
                print(f"  Col {col} (V{col} già presente): h={h_slot[0]}{h_slot[1]} v={v_slot[0]}{v_slot[1]} -> ", end="")
                
                if can_fit:
                    status = f"bloccato" if slack == 0 else f"gioco={slack}"
                    print(f"✓ OK (somma={h_slot[0] + v_slot[0]}, {status})")
                else:
                    same_dir = h_slot[1] == v_slot[1]
                    sum_depth = h_slot[0] + v_slot[0]
                    reason = "stessa direzione" if same_dir else f"somma={sum_depth} < 4"
                    print(f"✗ IMPOSSIBILE ({reason})")
                    conflicts.append((col, reason))
        
        return len(conflicts) == 0, conflicts
    
    def can_insert_vertical(self, col_idx):
        """
        Può inserire V[col_idx]?
        Per ogni riga occupata, verifica:
        1. Che l'incastro sia valido
        2. Che gli H già presenti abbiano abbastanza slack per spostarsi
        """
        print(f"\nInserimento COLONNA {col_idx} - Pezzo {vert_ids[col_idx]}: {[f'{d}{p}' for d, p in vert_pieces[col_idx]]}")
        
        conflicts = []
        max_required_slack = 0
        
        for row in range(4):
            if self.h_placed[row]:
                h_slot = horiz_pieces[row][col_idx]
                v_slot = vert_pieces[col_idx][row]
                can_fit, slack_at_intersection = can_interlock(h_slot, v_slot)
                
                print(f"  Riga {row} (H{row} già presente): h={h_slot[0]}{h_slot[1]} v={v_slot[0]}{v_slot[1]} -> ", end="")
                
                if not can_fit:
                    same_dir = h_slot[1] == v_slot[1]
                    sum_depth = h_slot[0] + v_slot[0]
                    reason = "stessa direzione" if same_dir else f"somma={sum_depth} < 4"
                    print(f"✗ IMPOSSIBILE ({reason})")
                    conflicts.append((row, reason))
                    continue
                
                # L'incastro è valido, ma H[row] deve potersi spostare per permettere l'inserimento
                # Se v_slot ha profondità > 2, richiede spazio
                required_movement = v_slot[0] - 2  # Approssimazione: depth 3 richiede 1 di movimento
                if required_movement > 0:
                    # Verifica che H[row] possa muoversi alle altre colonne
                    available_slack = float('inf')
                    for other_col in range(4):
                        if other_col != col_idx and self.v_placed[other_col]:
                            col_slack = self.get_horizontal_slack_at_col(row, other_col)
                            if col_slack is not None:
                                available_slack = min(available_slack, col_slack)
                    
                    if available_slack == float('inf'):
                        available_slack = required_movement  # Nessun vincolo
                    
                    status = f"bloccato" if slack_at_intersection == 0 else f"gioco={slack_at_intersection}"
                    print(f"OK (somma={h_slot[0] + v_slot[0]}, {status}), ", end="")
                    
                    if required_movement > available_slack:
                        reason = f"H{row} richiede movimento={required_movement} ma slack disponibile={available_slack}"
                        print(f"✗ {reason}")
                        conflicts.append((row, reason))
                    else:
                        print(f"✓ H{row} può spostarsi (richiesto={required_movement}, disponibile={available_slack})")
                else:
                    status = f"bloccato" if slack_at_intersection == 0 else f"gioco={slack_at_intersection}"
                    print(f"✓ OK (somma={h_slot[0] + v_slot[0]}, {status})")
        
        return len(conflicts) == 0, conflicts
    
    def place_horizontal(self, row_idx):
        """Inserisce H[row_idx]"""
        self.h_placed[row_idx] = True
        for col in range(4):
            if self.v_placed[col]:
                h_slot = horiz_pieces[row_idx][col]
                v_slot = vert_pieces[col][row_idx]
                can_fit, slack = can_interlock(h_slot, v_slot)
                self.grid[row_idx][col] = (can_fit, slack)
    
    def place_vertical(self, col_idx):
        """Inserisce V[col_idx]"""
        self.v_placed[col_idx] = True
        for row in range(4):
            if self.h_placed[row]:
                h_slot = horiz_pieces[row][col_idx]
                v_slot = vert_pieces[col_idx][row]
                can_fit, slack = can_interlock(h_slot, v_slot)
                self.grid[row][col_idx] = (can_fit, slack)

def simulate_alternating_assembly():
    print("="*80)
    print("SIMULAZIONE MONTAGGIO CON CONTROLLO SLACK")
    print("Sequenza: H0 -> V0 -> H1 -> V1 -> H2 -> V2 -> H3 -> V3")
    print("="*80)
    
    state = AssemblyState()
    
    sequence = []
    for i in range(4):
        sequence.append(('H', i))
        sequence.append(('V', i))
    
    step = 0
    for piece_type, idx in sequence:
        step += 1
        print(f"\n{'='*80}")
        print(f"PASSO {step}: Inserimento {'ORIZZONTALE' if piece_type == 'H' else 'VERTICALE'} {idx} (pezzo {horiz_ids[idx] if piece_type == 'H' else vert_ids[idx]})")
        print(f"{'='*80}")
        
        if piece_type == 'H':
            can_insert, conflicts = state.can_insert_horizontal(idx)
            if can_insert:
                state.place_horizontal(idx)
                print(f"\n✓ RIGA {idx} inserita con successo!")
            else:
                print(f"\n✗ IMPOSSIBILE inserire RIGA {idx}!")
                print(f"   Conflitti: {conflicts}")
                print("\n" + "="*80)
                print("❌ MONTAGGIO BLOCCATO!")
                print("="*80)
                return False, step, piece_type, idx, conflicts
        else:
            can_insert, conflicts = state.can_insert_vertical(idx)
            if can_insert:
                state.place_vertical(idx)
                print(f"\n✓ COLONNA {idx} inserita con successo!")
            else:
                print(f"\n✗ IMPOSSIBILE inserire COLONNA {idx}!")
                print(f"   Conflitti: {conflicts}")
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
