import Unicyclic.Statement

namespace Unicyclic

open SimpleGraph

/-- A distance table is certified by its diagonal, one-step lower bounds,
and a descending edge toward every distinct target. -/
theorem dist_eq_table {V : Type} {G : SimpleGraph V} (hc : G.Connected)
    (d : V → V → ℕ)
    (hz : ∀ u v, d u v = 0 ↔ u = v)
    (hlip : ∀ u w v, G.Adj u w → d u v ≤ d w v + 1)
    (hdesc : ∀ u v, u ≠ v → ∃ w, G.Adj u w ∧ d u v = d w v + 1)
    (u v : V) : G.dist u v = d u v := by
  have lower {a b : V} (p : G.Walk a b) : d a b ≤ p.length := by
    induction p with
    | nil => simpa using (hz _ _).2 rfl |>.le
    | cons ha p ih => exact (hlip _ _ _ ha).trans (Nat.succ_le_succ ih)
  apply le_antisymm
  · generalize hd : d u v = k
    induction k generalizing u with
    | zero =>
      obtain rfl := (hz _ _).1 hd
      simp
    | succ k ih =>
      have hne : u ≠ v := by
        intro he
        have := (hz _ _).2 he
        omega
      obtain ⟨w, hw, hdec⟩ := hdesc u v hne
      have hwk : d w v = k := by omega
      have hup := ih w hwk
      have htri := hc.dist_triangle (u := u) (v := w) (w := v)
      rw [dist_eq_one_iff_adj.mpr hw] at htri
      omega
  · obtain ⟨p, hp⟩ := hc.exists_walk_length_eq_dist u v
    exact hp ▸ lower p

/-- Shorter of the two distances around the numbered cycle. -/
def around {n : ℕ} (u v : Fin n) : ℕ := min (u-v).val (v-u).val

private theorem cycle_adj_val_le {n : ℕ} {a b : Fin (n+2)}
    (hab : (cycleGraph (n+2)).Adj a b) (hb : b ≠ 0) : a.val ≤ b.val+1 := by
  rcases cycleGraph_adj.mp hab with h | h
  · have ha : a = b + 1 := by rw [← h]; abel
    rw [ha, Fin.val_add_one]
    split <;> simp_all
  · have ha : a = b - 1 := by rw [← h]; abel
    rw [ha, Fin.val_sub_one_of_ne_zero hb]
    omega

private theorem around_step {n : ℕ} {i k : Fin (n+2)} (j : Fin (n+2))
    (h : (cycleGraph (n+2)).Adj i k) : around i j ≤ around k j + 1 := by
  by_cases hkj : k = j
  · subst k
    rcases cycleGraph_adj.mp h with h | h
    · exact le_trans (min_le_left _ _) (by rw [h]; simp [around])
    · exact le_trans (min_le_right _ _) (by rw [h]; simp [around])
  · have h₁ : (cycleGraph (n+2)).Adj (i-j) (k-j) := by
      apply cycleGraph_adj.mpr
      simpa only [sub_sub_sub_cancel_right] using cycleGraph_adj.mp h
    have h₂ : (cycleGraph (n+2)).Adj (j-i) (j-k) := by
      apply cycleGraph_adj.mpr
      simpa only [sub_sub_sub_cancel_left] using cycleGraph_adj.mp h.symm
    have f := cycle_adj_val_le h₁ (sub_ne_zero.mpr hkj)
    have b := cycle_adj_val_le h₂ (sub_ne_zero.mpr (Ne.symm hkj))
    unfold around
    omega

/-- Distance in a cycle is the minimum of the clockwise and counterclockwise
arc lengths. The finite subtraction in each term wraps around the cycle. -/
theorem cycleGraph_dist {n : ℕ} (u v : Fin n) : (cycleGraph n).dist u v = around u v := by
  match n with
  | 0 => exact Fin.elim0 u
  | 1 => obtain rfl : u = v := Subsingleton.elim _ _; simp [around]
  | n+2 =>
    apply dist_eq_table connected_cycleGraph_add_one around
    · intro i j
      by_cases h : i = j
      · subst j; simp [around]
      · have l := Fin.val_ne_zero_iff.mpr (sub_ne_zero.mpr h)
        have r := Fin.val_ne_zero_iff.mpr (sub_ne_zero.mpr (Ne.symm h))
        unfold around; omega
    · intro i k j h
      exact around_step j h
    · intro i j hij
      have decr (a b : Fin (n+2)) (h : a ≠ b) :
          ((a-b)-1).val < (a-b).val := by
        have h₀ : a-b ≠ 0 := sub_ne_zero.mpr h
        rw [Fin.val_sub_one_of_ne_zero h₀]
        have hp : 0 < (a-b).val := by
          exact Nat.pos_of_ne_zero (Fin.val_ne_zero_iff.mpr h₀)
        omega
      by_cases hl : (i-j).val ≤ (j-i).val
      · have he : (cycleGraph (n+2)).Adj i (i-1) := cycleGraph_adj.mpr (Or.inl (by abel))
        refine ⟨i-1, he, ?_⟩
        have upper := around_step j he
        have hs := decr i j hij
        have he' : i-1-j = (i-j)-1 := by abel
        unfold around at *
        rw [he'] at upper ⊢
        omega
      · have he : (cycleGraph (n+2)).Adj i (i+1) := cycleGraph_adj.mpr (Or.inr (by abel))
        refine ⟨i+1, he, ?_⟩
        have upper := around_step j he
        have hs := decr j i (Ne.symm hij)
        have he' : j-(i+1) = (j-i)-1 := by abel
        unfold around at *
        rw [he'] at upper ⊢
        omega
theorem cycle4_dist (u v : Fin 4) : (cycleGraph 4).dist u v = around u v :=
  cycleGraph_dist u v

theorem cycle5_dist (u v : Fin 5) : (cycleGraph 5).dist u v = around u v :=
  cycleGraph_dist u v

theorem cycle6_dist (u v : Fin 6) : (cycleGraph 6).dist u v = around u v :=
  cycleGraph_dist u v

/-- Distance between two labels on a circle of circumference n. -/
def cycleRadius (n a b : ℤ) : ℤ := min |a-b| (n - |a-b|)

theorem cycle_dist_int {n : ℕ} (a b : Fin n) :
    ((cycleGraph n).dist a b : ℤ) = cycleRadius n a b := by
  rw [cycleGraph_dist, around, Nat.cast_min]
  simp only [Fin.coe_int_sub_eq_ite, cycleRadius, Fin.le_iff_val_le_val, abs_eq_max_neg]
  split_ifs <;> omega

end Unicyclic
