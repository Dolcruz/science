import Unicyclic.GraphStructure
import Unicyclic.SpectralStructure

namespace Unicyclic

open SimpleGraph Matrix Finset

variable {V : Type} [Fintype V] [DecidableEq V] {G : SimpleGraph V}

omit [Fintype V] in
private theorem pair_le_mass {s : Finset V} {a : V → ℝ} (ha : ∀ i, 0 < a i)
    {x y : V} (hx : x ∈ s) (hy : y ∈ s) (hne : x ≠ y) :
    a x + a y ≤ ∑ i ∈ s, a i := by
  calc
    _ = ∑ i ∈ ({x,y} : Finset V), a i := by simp [hne]
    _ ≤ _ := Finset.sum_le_sum_of_subset_of_nonneg (by
        intro i hi
        rcases Finset.mem_insert.mp hi with rfl | hi
        · exact hx
        · exact Finset.mem_singleton.mp hi ▸ hy)
      (fun i _ _ => (ha i).le)

private theorem dist_mul_lt {a : V → ℝ} {ρ : ℝ} (hn : 2 < Fintype.card V)
    (hc : G.Connected) (ha : ∀ i, 0 < a i) (he : distMatrix G *ᵥ a = ρ • a)
    {x y : V} (hxy : x ≠ y) : distMatrix G x y * a y < ρ * a x := by
  have hcard : ({x,y} : Finset V).card < (Finset.univ : Finset V).card := by simpa [hxy]
  obtain ⟨k, _, hk⟩ := Finset.exists_mem_notMem_of_card_lt_card hcard
  simp only [Finset.mem_insert, Finset.mem_singleton, not_or] at hk
  let f := fun j => distMatrix G x j * a j
  have hfk : 0 < f k := mul_pos (by
    change (0 : ℝ) < (G.dist x k : ℝ)
    exact_mod_cast hc.pos_dist_of_ne (Ne.symm hk.1)) (ha k)
  have hsum : 0 < ∑ j ∈ Finset.univ.erase y, f j :=
    Finset.sum_pos' (fun j _ => mul_nonneg (Nat.cast_nonneg _) (ha j).le)
      ⟨k, by simp [hk.2], hfk⟩
  have heq : ∑ j, f j = ρ * a x := congrFun he x
  have herm := Finset.sum_erase_add (s := Finset.univ) f (Finset.mem_univ y)
  change f y < ρ * a x
  linarith

/-- A single entry of the positive Perron vector has less than half of its total mass. -/
theorem perron_entry_lt_half {a : V → ℝ} {ρ : ℝ} (hn : 2 < Fintype.card V)
    (hc : G.Connected) (ha : ∀ i, 0 < a i) (he : distMatrix G *ᵥ a = ρ • a)
    (x : V) : 2 * a x < ∑ i, a i := by
  have hsmall (i j : V) (hij : i ≠ j) : distMatrix G i j < ρ := by
    have h₁ := dist_mul_lt hn hc ha he hij
    have h₂ := dist_mul_lt hn hc ha he hij.symm
    rw [show distMatrix G j i = distMatrix G i j by simp only [distMatrix, G.dist_comm (u := j)]] at h₂
    by_contra! hh
    nlinarith [mul_le_mul_of_nonneg_right hh (ha i).le, mul_le_mul_of_nonneg_right hh (ha j).le]
  have hne : (Finset.univ.erase x : Finset V).Nonempty := by
    rw [← Finset.card_pos, Finset.card_erase_of_mem (Finset.mem_univ _), Finset.card_univ]
    omega
  have hlt := Finset.sum_lt_sum_of_nonempty hne (fun i hi =>
    mul_lt_mul_of_pos_right (hsmall x i (Finset.ne_of_mem_erase hi).symm) (ha i))
  have hx : ∑ i ∈ univ.erase x, distMatrix G x i * a i = ρ * a x := by
    rw [Finset.sum_erase_eq_sub (Finset.mem_univ x)]
    simpa [distMatrix, Matrix.mulVec, dotProduct] using congrFun he x
  rw [hx, ← Finset.mul_sum] at hlt
  obtain ⟨y,hy⟩ := hne
  have hρ : 0 < ρ := lt_of_le_of_lt (Nat.cast_nonneg _)
    (hsmall x y (Finset.ne_of_mem_erase hy).symm)
  have hs := (mul_lt_mul_iff_right₀ hρ).mp hlt
  linarith [Finset.sum_erase_add (s := univ) a (Finset.mem_univ x)]

omit [DecidableEq V] in
private theorem balance {a : V → ℝ} {ρ : ℝ} (he : distMatrix G *ᵥ a = ρ • a)
    {x y : V} (hxy : G.Adj x y) (ht : ∀ z, G.dist z x ≠ G.dist z y) :
    ρ * (a x - a y) = (∑ z, a z) - 2 * ∑ z ∈ univ.filter (fun z => G.dist z x < G.dist z y), a z := by
  have hx : ∑ z, (G.dist z x : ℝ) * a z = ρ * a x := by
    simpa [distMatrix, Matrix.mulVec, dotProduct, G.dist_comm (u := x)] using congrFun he x
  have hy : ∑ z, (G.dist z y : ℝ) * a z = ρ * a y := by
    simpa [distMatrix, Matrix.mulVec, dotProduct, G.dist_comm (u := y)] using congrFun he y
  rw [mul_sub, ← hx, ← hy, Finset.sum_filter, Finset.mul_sum, ← Finset.sum_sub_distrib,
    ← Finset.sum_sub_distrib]
  apply Finset.sum_congr rfl
  intro z _
  rcases hxy.diff_dist_adj (u := z) with h | h | h
  · exact (ht z h.symm).elim
  · rw [h]
    simp
    ring
  · have hn := ht z
    have h' : G.dist z x = G.dist z y + 1 := by omega
    rw [h']
    simp
    ring

omit [Fintype V] [DecidableEq V] in
private theorem leaf_dist_away {l p : V} (hc : G.Connected) (hl : G.Adj l p)
    (hu : ∀ z, G.Adj l z → z = p) {z : V} (hz : z ≠ l) :
    G.dist z l = G.dist z p + 1 := by
  simpa only [G.dist_comm (u := l), G.dist_comm (u := p)] using
    GraphStructure.dist_from_leaf hc hl hu hz.symm

omit [Fintype V] [DecidableEq V] in
theorem leaf_untied {l p : V} (hc : G.Connected) (hl : G.Adj l p)
    (hu : ∀ z, G.Adj l z → z = p) (z : V) : G.dist z l ≠ G.dist z p := by
  by_cases h : z = l
  · subst z
    simp [dist_eq_one_iff_adj.mpr hl]
  · rw [leaf_dist_away hc hl hu h]
    omega

theorem leaf_balance {l p : V} (hc : G.Connected) (hl : G.Adj l p)
    (hu : ∀ z, G.Adj l z → z = p) {a : V → ℝ} {ρ : ℝ}
    (he : distMatrix G *ᵥ a = ρ • a) :
    ρ * (a l - a p) = (∑ z, a z) - 2 * a l := by
  have hf : univ.filter (fun z => G.dist z l < G.dist z p) = {l} := by
    ext z
    by_cases h : z = l
    · subst z
      simp [dist_eq_one_iff_adj.mpr hl]
    · simp [h, leaf_dist_away hc hl hu h]
  simpa [hf] using balance he hl (leaf_untied hc hl hu)

omit [DecidableEq V] in
theorem tieCount_of_untied {x y : V} (h : ∀ z, G.dist z x ≠ G.dist z y) :
    tieCount G x y = 0 := by simp [tieCount, h]

/-- At a leaf's neighbor, any other incident edge without ties has a singleton
Voronoi side away from the leaf. -/
theorem leaf_side_singleton {l p x : V} (hc : G.Connected) (hl : G.Adj l p)
    (hu : ∀ z, G.Adj l z → z = p) (hpx : G.Adj p x) (hxl : x ≠ l)
    (ht : ∀ z, G.dist z x ≠ G.dist z p)
    {a : V → ℝ} {ρ s t : ℝ} (ha : ∀ i, 0 < a i) (he : distMatrix G *ᵥ a = ρ • a)
    (hQ : distMatrix G * distMatrix G + s • distMatrix G + t • 1 = vecMulVec a a)
    (z : V) (hz : G.dist z x < G.dist z p) : z = x := by
  let P := univ.filter fun j => G.dist j p < G.dist j x
  let X := univ.filter fun j => G.dist j x < G.dist j p
  have hlp := dist_eq_one_iff_adj.mpr hl
  have hxp := dist_eq_one_iff_adj.mpr hpx.symm
  have hpP : p ∈ P := by simp [P, dist_eq_one_iff_adj.mpr hpx]
  have hlP : l ∈ P := by
    have := leaf_dist_away hc hl hu hxl
    rw [G.dist_comm (u := x) (v := l)] at this
    simp [P, hlp, this, hxp]
  have hxX : x ∈ X := by simp [X, hxp]
  have hzX : z ∈ X := by simpa [X] using hz
  have hP := pair_le_mass ha hlP hpP hl.ne
  have hL := leaf_balance hc hl hu he
  have hB := balance he hpx (fun j h => ht j h.symm)
  have hX := balance he hpx.symm ht
  change _ = _ - 2 * ∑ j ∈ P, a j at hB
  change _ = _ - 2 * ∑ j ∈ X, a j at hX
  have h₁ := sq_perron_sub_of_rankOne G hQ hl
  have h₂ := sq_perron_sub_of_rankOne G hQ hpx
  rw [tieCount_of_untied (leaf_untied hc hl hu)] at h₁
  rw [tieCount_of_untied (fun z h => ht z h.symm)] at h₂
  have hd : a l - a p = a p - a x ∨ a l - a p = -(a p - a x) :=
    sq_eq_sq_iff_eq_or_eq_neg.mp (h₁.trans h₂.symm)
  rcases hd with hd | hd
  · rw [hd] at hL
    linarith [ha p]
  · have heq : a l - a p = a x - a p := by linarith
    rw [heq] at hL
    have hmass : (∑ j ∈ X, a j) = a x := by linarith
    by_contra hh
    have hsum := pair_le_mass ha hzX hxX hh
    linarith [ha z]

/-- All leaf-to-parent differences of the positive vector have the same sign and value. -/
theorem leaf_gap_eq {l p m q : V} (hc : G.Connected) (hn : 2 < Fintype.card V)
    (hl : G.Adj l p) (hul : ∀ z, G.Adj l z → z = p)
    (hm : G.Adj m q) (hum : ∀ z, G.Adj m z → z = q)
    {a : V → ℝ} {ρ s t : ℝ} (ha : ∀ i, 0 < a i) (he : distMatrix G *ᵥ a = ρ • a)
    (hQ : distMatrix G * distMatrix G + s • distMatrix G + t • 1 = vecMulVec a a) :
    a l - a p = a m - a q := by
  have h₁ := sq_perron_sub_of_rankOne G hQ hl
  have h₂ := sq_perron_sub_of_rankOne G hQ hm
  rw [tieCount_of_untied (leaf_untied hc hl hul)] at h₁
  rw [tieCount_of_untied (leaf_untied hc hm hum)] at h₂
  rcases sq_eq_sq_iff_eq_or_eq_neg.mp (h₁.trans h₂.symm) with h | h
  · exact h
  · have b₁ := leaf_balance hc hl hul he
    have b₂ := leaf_balance hc hm hum he
    rw [h, mul_neg] at b₁
    linarith [perron_entry_lt_half hn hc ha he l, perron_entry_lt_half hn hc ha he m]

theorem leafSideCondition_of_three [DecidableRel G.Adj] (hc : G.Connected)
    (hthree : numDistanceEigenvalues G = 3) : GraphStructure.LeafSideCondition G := by
  obtain ⟨ρ, s, t, hts, hsρ, hspec⟩ := exists_ordered_three_spectrum G hthree
  obtain ⟨a, ha, he, hQ⟩ := exists_rankOne_of_three_spectrum G hc hsρ (hts.trans hsρ) hspec
  intro l p x z hdeg hl hpx hxl ht hz
  obtain ⟨q,hq,hu⟩ := degree_eq_one_iff_existsUnique_adj.mp hdeg
  exact leaf_side_singleton hc hl (fun j hj => (hu _ hj).trans (hu _ hl).symm) hpx hxl
    (fun w h => ht w h.symm) ha he hQ z hz

end Unicyclic
