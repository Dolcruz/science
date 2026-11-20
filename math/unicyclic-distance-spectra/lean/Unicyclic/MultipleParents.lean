import Unicyclic.LeafBalance
import Unicyclic.LeafSpectral

namespace Unicyclic

open SimpleGraph
open scoped Fin.CommRing

/-- Two distinct vertices on a cycle of length at least five can be distinguished
by adjacency to a third vertex. -/
theorem cycle_distinguishes {k : ℕ} {p q : Fin (k+5)} (hpq : p ≠ q) :
    ∃ z, z ≠ p ∧ z ≠ q ∧ (cycleGraph (k+5)).dist z p ≠ (cycleGraph (k+5)).dist z q := by
  by_contra! hall
  have hn {i : ℕ} (hi : 0 < i) (hj : i ≤ 4) : (i : Fin (k+5)) ≠ 0 := by
    intro h
    have hv := congrArg Fin.val h
    simp [Fin.val_natCast, Nat.mod_eq_of_lt (show i < k+5 by omega)] at hv
    omega
  have h₂ : (2 : Fin (k+5)) ≠ 0 := hn (i := 2) (by decide) (by decide)
  have h₃ : (3 : Fin (k+5)) ≠ 0 := hn (i := 3) (by decide) (by decide)
  have h₄ : (4 : Fin (k+5)) ≠ 0 := hn (i := 4) (by decide) (by decide)
  have next {z : Fin (k+5)} (hz : z ≠ p) (h : (cycleGraph (k+5)).Adj z p) :
      z = q ∨ (cycleGraph (k+5)).Adj z q := by
    by_cases hzq : z = q
    · exact Or.inl hzq
    · exact Or.inr (dist_eq_one_iff_adj.mp ((hall z hz hzq).symm.trans (dist_eq_one_iff_adj.mpr h)))
  have plus : q = p+1 ∨ q = p+2 := by
    rcases next (z := p+1) (by simp) (cycleGraph_adj.mpr (Or.inl (by abel))) with h | h
    · exact Or.inl h.symm
    · rcases cycleGraph_adj.mp h with h | h
      · exact (hpq (by linear_combination h)).elim
      · right; linear_combination h
  have minus : q = p-1 ∨ q = p-2 := by
    rcases next (z := p-1) (by simp) (cycleGraph_adj.mpr (Or.inr (by abel))) with h | h
    · exact Or.inl h.symm
    · rcases cycleGraph_adj.mp h with h | h
      · right; linear_combination -h
      · exact (hpq (by linear_combination -h)).elim
  rcases plus with h | h <;> rcases minus with h' | h'
  · exact h₂ (by linear_combination h'-h)
  · exact h₃ (by linear_combination h'-h)
  · exact h₃ (by linear_combination h'-h)
  · exact h₄ (by linear_combination h'-h)

/-- On a core of length at least five, all pendant vertices must share a parent
if there are only three distance eigenvalues. -/
theorem single_parent_of_long_cycle {V : Type} [Fintype V] [DecidableEq V] {G : SimpleGraph V}
    [DecidableRel G.Adj] (h : IsUnicyclic G) (hthree : numDistanceEigenvalues G = 3)
    {k : ℕ} (f : Copy (cycleGraph (k+5)) G)
    (hr : ∀ v, v ∈ Set.range f ↔ G.degree v ≠ 1)
    (hi : ∀ i j, G.dist (f i) (f j) = (cycleGraph (k+5)).dist i j)
    (hl : ∃ l, l ∉ Set.range f) :
    ∃ p : Fin (k+5), ∀ z, z ∉ Set.range f → G.degree z = 1 ∧ G.Adj z (f p) := by
  have hn' := Fintype.card_le_of_injective _ f.injective
  rw [Fintype.card_fin] at hn'
  have hn : 2 < Fintype.card V := by omega
  have hs : GraphStructure.LeafSideCondition G := leafSideCondition_of_three h.1 hthree
  have parent (l : V) (hl : l ∉ Set.range f) :
      ∃ p : Fin (k+5), G.degree l = 1 ∧ G.Adj l (f p) ∧ ∀ j, G.Adj l j → j = f p := by
    have hd : G.degree l = 1 := not_not.mp (fun hh => hl ((hr l).mpr hh))
    obtain ⟨v,hv,hu⟩ := degree_eq_one_iff_existsUnique_adj.mp hd
    obtain ⟨p,rfl⟩ := GraphStructure.leaf_parent_on_cycle h hs f hd hv
    exact ⟨p,hd,hv,hu⟩
  obtain ⟨l,hl⟩ := hl
  obtain ⟨p,_,hlp,hu⟩ := parent l hl
  obtain ⟨ρ,s,t,hts,hsρ,hspec⟩ := exists_ordered_three_spectrum G hthree
  obtain ⟨a,ha,he,hQ⟩ := exists_rankOne_of_three_spectrum G h.1 hsρ (hts.trans hsρ) hspec
  refine ⟨p, fun m hm => ?_⟩
  obtain ⟨q,hd,hmq,hv⟩ := parent m hm
  refine ⟨hd, ?_⟩
  suffices p = q by simpa [this] using hmq
  by_contra hpq
  obtain ⟨z,hzp,hzq,hz⟩ := cycle_distinguishes hpq
  have hg := leaf_gap_eq h.1 hn hlp hu hmq hv ha he hQ
  have hdist := dist_parents_eq_of_leaf_gap_eq h.1 hlp hu hmq hv hQ hg
    (z := f z) (fun e => hl ⟨z,e⟩) (fun e => hzp (f.injective e))
    (fun e => hm ⟨z,e⟩) (fun e => hzq (f.injective e))
  exact hz (by simpa only [hi] using hdist)

end Unicyclic
