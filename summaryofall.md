# Summary of All Conversations — 3D Lattice Puzzle Project

## The Puzzle

8 rectangular pieces (4×9) each with 4 notches at positions 2, 4, 6, 8.
4 pieces go horizontal (H0–H3), 4 vertical (V0–V3) → 4×4 grid of interlocking crosses.
Each notch has a depth (1–3) and direction (U=up, D=down).
At each crossing: directions must be opposite and depth sum ≥ 4 (slack = sum − 4).

### Piece Definitions
```
Piece 1: [3U  3D  2D  2D]
Piece 2: [1D  2U  1U  3U]
Piece 3: [3U  2D  2D  2D]  (identical to 7)
Piece 4: [2U  2D  3U  3D]
Piece 5: [3D  2D  3U  2U]
Piece 6: [2U  3U  2D  3D]
Piece 7: [3U  2D  2D  2D]  (identical to 3)
Piece 8: [2D  2U  3D  3U]
```

Each piece has 4 orientation variants: original, mirrored, flipped (U↔D), mirrored+flipped.

---

## Timeline of Work

### 2026-03-13 — Assembly Trace & Mobility Model
- Improved printing and assembly checking in `soluzione_puzzle3d.py`.
- Added directional mobility model replacing simple slack check.
- Added per-hole spread control during V and H insertion.
- Assembly trace shows movement limits, required spread, available spread, and block reasons.
- **Result**: Model improved but not definitive — false positives remained (solutions marked assemblable that are not).

### 2026-03-14 — Global Constraint Model & CLI
- Fixed vertical insertion branch (removed incoherent aggregate comparison).
- Introduced global constraint model using Floyd-Warshall for maximum relative shift between already-placed parallel pieces.
- Added dynamic assembly search with backtracking + fail-first heuristic (`--assembly-search dynamic`).
- Added `--print-valid` and improved output with `dynamic_adds_step_vs_sequence` diagnostics.
- **Result**: Assembly check more coherent on discussed cases.

### 2026-03-19 — Subset Assembly Filter
- Added subset verification for H1, H2, V1, V2 positions only.
- Tests all 24 orderings of the 4 target pieces ignoring others.
- New CLI flag: `--check-subset-h1h2-v1v2`.
- Results saved to `results_subset_h1h2_v1v2.json`.
- Committed and pushed: `Add subset assembly filter for H1 H2 V1 V2`.

### 2026-03-21 — Clean Solver Rewrite
- Rewrote solver from scratch as `puzzle_solver.py`.
- Enumerates all C(8,4)=70 H/V splits × permutations × variants with backtracking.
- **Results**: 24,064 raw geometric solutions, 3,008 unique (dedup pieces 3↔7), across 20 H/V splits.
- All solutions have constant total slack = 11 with exactly 5 zero-slack crossings.
- Assembly check attempts (DAG from-above, flexible DAG with 256 direction combos) → **0 assemblable solutions** (always cyclic dependencies).
- Assembly check removed from output; focus shifted to geometric solutions only.

### 2026-03-23 — Shift-Based Assembly Rule
- Defined shift constraints: only between parallel pieces (H↔H, V↔V).
- Max allowed shift = minimum slack across all crossings in that direction for a pair.
- Required shift for mixed-direction insertion depends on notch depth pairs:
  - 3+3→2, 3+2→3, 2+2→4, 3+1→5, 2+1→6, 1+1→7
- Implemented in `puzzle_solver.py` for default sequence H0 V0 H1 V1 H2 V2 H3 V3.
- **Status**: Updated but not yet executed to verify results.

### 2026-03-24 — Unique Geometric Solutions & Symmetry Dedup
- Created `find_unique_geometric_solutions.py`.
- Canonical signature from 8 symmetry transformations: reverse positions, swap H↔V, flip all U↔D.
- **Results**:
  - 24,064 raw → 752 (dedup 3/7) → **376 unique** (all symmetries)
  - 32 with H0-unique filter (piece 2 with depth-1 notch at first crossing)
- Output saved to `puzzle_solutions_unique_geometric.json`.

### 2026-03-25 — Assembly Verification & False Positive Elimination
- Detailed step-by-step physical analysis of solution 62.
- Aligned checker scripts to solver criteria; eliminated discrepancies.
- Refined `_can_insert` / `_feasible_relative_shift` logic in solver.
- Added insertion direction constraint based on sequence index progression.
- **Results out of 376 unique solutions**:
  - **17 assemblable** (by shift-only model)
  - **359 not assemblable**
  - Solution 62 confirmed NOT assemblable.
- Assemblable solution indices: 208–215, 240–243, 246, 252–255.

### 2026-03-30 — Conclusion
- After physical verification, it was determined that **the puzzle is NOT solvable using shift-only insertion**.
- The shift-based assembly model, while refined across multiple iterations, cannot produce a valid real-world assembly sequence.
- The lattice puzzle likely requires a different assembly technique (e.g., rotational insertion, flex, or a specific non-obvious sequence) that is not captured by the linear shift model explored here.

---

## Files in the Project

| File | Description |
|------|-------------|
| `puzzle_solver.py` | Main solver: geometric search + shift-based assembly check |
| `find_unique_geometric_solutions.py` | Dedup solver with 8 symmetry transformations |
| `check_assemblability.py` | Standalone assembly verifier using solver criteria |
| `simulate_assembly_sequence.py` | Assembly sequence simulation |
| `simulate_assembly_with_slack.py` | Assembly simulation with slack modeling |
| `analyze_solution.py` | Solution analysis utilities |
| `print_solution_62.py` | Detailed verification of solution 62 |
| `soluzione_puzzle3d.py` | Original solver (superseded by puzzle_solver.py) |
| `puzzle_solutions_new.json` | All 3,008 geometric solutions |
| `puzzle_solutions_unique_geometric.json` | 376 unique geometric solutions |
| `results.json` | Raw solver results |
| `results_subset_h1h2_v1v2.json` | Subset filter results |

## Conclusion

**The puzzle is not solvable with shift-only insertion.** All geometric solutions were found and verified, but none can be physically assembled using only linear shifts of parallel pieces. A different assembly approach is needed — check the web for known solutions to this type of lattice/burr puzzle.
