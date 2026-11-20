import Unicyclic.GraphStructure
import Unicyclic.CycleSpectra
import Unicyclic.Transport
import Unicyclic.MultipleParents
import Unicyclic.SingleParentCycle

namespace Unicyclic

open SimpleGraph

theorem sanityPath : SanityPath := GraphStructure.sanityPath
theorem sanityCycle : SanityCycle := GraphStructure.sanityCycle
theorem sanityC4 : SanityC4 := spectrum_cycle4
theorem sanityC5 : SanityC5 := spectrum_cycle5
theorem sanityC6 : SanityC6 := num_cycle6

/-- The reverse implication of the classification, for any labeling of the vertices. -/
theorem three_of_iso_cycle {V : Type} [Fintype V] [DecidableEq V] {G : SimpleGraph V}
    (h : Nonempty (G ≃g cycleGraph 4) ∨ Nonempty (G ≃g cycleGraph 5)) :
    numDistanceEigenvalues G = 3 := by
  rcases h with h4 | h5
  · obtain ⟨e⟩ := h4
    exact (numDistanceEigenvalues_iso e).trans num_cycle4
  · obtain ⟨e⟩ := h5
    exact (numDistanceEigenvalues_iso e).trans num_cycle5

/-- A surjective isometric cycle copy identifies the graph, including all its edges. -/
theorem iso_of_full_cycle {V : Type} {G : SimpleGraph V} {n : ℕ}
    (f : Copy (cycleGraph n) G) (hf : Function.Surjective f)
    (hi : ∀ i j, G.dist (f i) (f j) = (cycleGraph n).dist i j) :
    Nonempty (G ≃g cycleGraph n) := by
  let e : cycleGraph n ≃g G :=
    { toEquiv := Equiv.ofBijective f ⟨f.injective,hf⟩
      map_rel_iff' := by
        intro i j
        change G.Adj (f i) (f j) ↔ (cycleGraph n).Adj i j
        rw [← dist_eq_one_iff_adj, ← dist_eq_one_iff_adj, hi] }
  exact ⟨e.symm⟩

theorem classification_of_full_cycle {V : Type} [Fintype V] [DecidableEq V]
    {G : SimpleGraph V} {m : ℕ} (f : Copy (cycleGraph (m+3)) G) (hf : Function.Surjective f)
    (hi : ∀ i j, G.dist (f i) (f j) = (cycleGraph (m+3)).dist i j)
    (hthree : numDistanceEigenvalues G = 3) :
    Nonempty (G ≃g cycleGraph 4) ∨ Nonempty (G ≃g cycleGraph 5) := by
  obtain ⟨e⟩ := iso_of_full_cycle f hf hi
  have hc := (numDistanceEigenvalues_iso e).symm.trans hthree
  rcases (num_cycle_iff (by omega)).mp hc with hn | hn
  · left; exact hn ▸ Nonempty.intro e
  · right; exact hn ▸ Nonempty.intro e

/-- If an isometric core of a graph with three distance eigenvalues omits a
vertex, the core is a triangle. -/
theorem triangle_of_proper_core {V : Type} [Fintype V] [DecidableEq V] {G : SimpleGraph V}
    [DecidableRel G.Adj] (h : IsUnicyclic G) (hthree : numDistanceEigenvalues G = 3)
    {m : ℕ} (f : Copy (cycleGraph (m+3)) G)
    (hr : ∀ v, v ∈ Set.range f ↔ G.degree v ≠ 1)
    (hi : ∀ i j, G.dist (f i) (f j) = (cycleGraph (m+3)).dist i j)
    (hout : ∃ z, z ∉ Set.range f) : m = 0 := by
  have hs : GraphStructure.LeafSideCondition G := leafSideCondition_of_three h.1 hthree
  have ho : Odd (m+3) := by
    apply Nat.not_even_iff_odd.mp
    intro he
    obtain ⟨l, hl⟩ := hout
    exact hl ((hr l).mpr (GraphStructure.no_bipartite_leaf h hs
      (GraphStructure.bipartite_of_even_core h f he) l))
  match m with
  | 0 => rfl
  | 1 => exact False.elim ((by decide : ¬ Odd 4) ho)
  | k+2 =>
    obtain ⟨p,hp⟩ := single_parent_of_long_cycle h hthree f hr hi hout
    exact (not_single_parent_cycle h.1 (by omega) ho f p hi hp hout hthree).elim

end Unicyclic
