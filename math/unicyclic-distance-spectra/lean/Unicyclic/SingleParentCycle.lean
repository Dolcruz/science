import Unicyclic.CycleDistances
import Unicyclic.LeafBalance
import Unicyclic.LeafSpectral

namespace Unicyclic

open SimpleGraph Matrix Finset

private theorem cycle_natural_metric {n : ℕ} (i j : Fin n) :
    (cycleGraph n).dist i j =
      min (max i.val j.val - min i.val j.val) (n - (max i.val j.val - min i.val j.val)) := by
  have he := cycle_dist_int i j
  simp only [cycleRadius, abs_eq_max_neg] at he
  omega

private theorem cycle_dist_translate {n : ℕ} [NeZero n] (i j p : Fin n) :
    (cycleGraph n).dist (i+p) (j+p) = (cycleGraph n).dist i j := by
  simp [cycleGraph_dist, around]

private theorem cycle_sum_dist_sq {n : ℕ} [NeZero n] (x y : Fin n) :
    (∑ z, ((cycleGraph n).dist x z : ℝ)^2) = ∑ z, ((cycleGraph n).dist y z : ℝ)^2 := by
  apply Fintype.sum_equiv (Equiv.addRight (y-x))
  intro z
  change ((cycleGraph n).dist x z : ℝ)^2 = ((cycleGraph n).dist y (z+(y-x)) : ℝ)^2
  have hx : x+(y-x) = y := by abel
  have he := cycle_dist_translate x z (y-x)
  rw [hx] at he
  rw [he]

variable {V : Type} [Fintype V] [DecidableEq V] {G : SimpleGraph V} [DecidableRel G.Adj]
variable {n : ℕ} [NeZero n] {e : Fin n → V}
variable (hd : ∀ i j, G.dist (e i) (e j) = (cycleGraph n).dist i j)
variable (hoff : ∀ z ∉ Set.range e, G.degree z = 1 ∧ G.Adj z (e 0))

include hd hoff

omit [DecidableEq V] in
private theorem off_dist (hconn : G.Connected) {z : V} (hz : z ∉ Set.range e) (j : Fin n) :
    G.dist z (e j) = (cycleGraph n).dist 0 j + 1 := by
  obtain ⟨hdeg, ha⟩ := hoff z hz
  have hu : ∀ v, G.Adj z v → v = e 0 := fun v hv =>
    (degree_eq_one_iff_existsUnique_adj.mp hdeg).unique hv ha
  have hne : z ≠ e j := by rintro rfl; exact hz ⟨j,rfl⟩
  rw [GraphStructure.dist_from_leaf hconn ha hu hne, hd]

private theorem perron_eq_at_equal_radius (hconn : G.Connected) (hi : Function.Injective e)
    {a : V → ℝ} (ha : ∀ z, 0 < a z) {s t : ℝ}
    (hQ : distMatrix G * distMatrix G + s • distMatrix G + t • 1 = vecMulVec a a)
    (u v : Fin n) (hr : (cycleGraph n).dist 0 u = (cycleGraph n).dist 0 v) :
    a (e u) = a (e v) := by
  classical
  let core := univ.map (⟨e,hi⟩ : Fin n ↪ V)
  have hin (z : V) : z ∈ core ↔ z ∈ Set.range e := by simp [core, Set.mem_range]
  let f (i : Fin n) (z : V) := (G.dist z (e i) : ℝ)^2
  have hcore : ∑ z ∈ core, f u z = ∑ z ∈ core, f v z := by
    simpa [core, f, hd, (cycleGraph n).dist_comm (v := u),
      (cycleGraph n).dist_comm (v := v)] using cycle_sum_dist_sq u v
  have hrest : ∑ z ∈ univ \ core, f u z = ∑ z ∈ univ \ core, f v z := by
    apply sum_congr rfl
    intro z hz
    have hn := (hin z).not.mp (mem_sdiff.mp hz).2
    simp only [f, off_dist hd hoff hconn hn, hr]
  have hall : ∑ z, f u z = ∑ z, f v z := by
    rw [← Finset.sum_sdiff (f := f u) (subset_univ core), ← Finset.sum_sdiff (f := f v) (subset_univ core),
      hcore,hrest]
  have diag (i : Fin n) : (∑ z, f i z) + t = a (e i)^2 := by
    have h := congrFun (congrFun hQ (e i)) (e i)
    simpa [Matrix.mul_apply, Matrix.vecMulVec_apply, distMatrix, f, sq, G.dist_comm (u := e i)] using h
  have hu := diag u
  have hv := diag v
  rw [hall] at hu
  rcases sq_eq_sq_iff_eq_or_eq_neg.mp (hu.symm.trans hv) with h | h
  · exact h
  · linarith [ha (e u), ha (e v)]

private theorem odd_single_parent_zero (hconn : G.Connected) (hi : Function.Injective e)
    (hn : 4 ≤ n) (ho : Odd n) {leaf : V} (hout : leaf ∉ Set.range e)
    (hthree : numDistanceEigenvalues G = 3) : False := by
  classical
  obtain ⟨k,hk⟩ := ho
  let x : Fin n := ⟨1,by omega⟩
  let y : Fin n := ⟨2,by omega⟩
  let u : Fin n := ⟨k,by omega⟩
  let v : Fin n := ⟨k+1,by omega⟩
  let q : Fin n := ⟨k+2,by omega⟩
  have hxy : G.Adj (e x) (e y) := by
    apply dist_eq_one_iff_adj.mp
    rw [hd, cycle_natural_metric]; dsimp [x,y]; omega
  have huv : G.Adj (e u) (e v) := by
    apply dist_eq_one_iff_adj.mp
    rw [hd, cycle_natural_metric]; dsimp [u,v]; omega
  have hr : (cycleGraph n).dist 0 u = (cycleGraph n).dist 0 v := by
    rw [cycle_natural_metric, cycle_natural_metric]; dsimp [u,v]; omega
  have ht₁ : tieCount G (e x) (e y) = 1 := by
    have hs : univ.filter (fun z => G.dist z (e x) = G.dist z (e y)) = {e q} := by
      ext z
      simp only [mem_filter, mem_univ, true_and, mem_singleton]
      by_cases hz : z ∈ Set.range e
      · obtain ⟨i,rfl⟩ := hz
        rw [hd, hd, hi.eq_iff, Fin.ext_iff, cycle_natural_metric, cycle_natural_metric]
        dsimp [x,y,q]
        omega
      · have hne : z ≠ e q := fun he => hz ⟨q,he.symm⟩
        simp only [hne, iff_false]
        rw [off_dist hd hoff hconn hz, off_dist hd hoff hconn hz,
          cycle_natural_metric, cycle_natural_metric]
        dsimp [x,y]
        omega
    simp [tieCount, hs]
  have ht₂ : 2 ≤ tieCount G (e u) (e v) := by
    have hne : leaf ≠ e 0 := fun he => hout ⟨0,he.symm⟩
    have hsub : ({leaf,e 0} : Finset V) ⊆
        univ.filter (fun z => G.dist z (e u) = G.dist z (e v)) := by
      intro z hz
      simp only [mem_insert, mem_singleton] at hz
      rcases hz with rfl | rfl
      · simp [off_dist hd hoff hconn hout, hr]
      · simp [hd, hr]
    simpa [tieCount, hne] using card_le_card hsub
  obtain ⟨hdeg,hadj⟩ := hoff leaf hout
  have hu : ∀ w, G.Adj leaf w → w = e 0 := fun w hw =>
    (degree_eq_one_iff_existsUnique_adj.mp hdeg).unique hw hadj
  obtain ⟨ρ,s,t,ht,hs,hsp⟩ := exists_ordered_three_spectrum G hthree
  obtain ⟨a,ha,_,hQ⟩ := exists_rankOne_of_three_spectrum G hconn hs (ht.trans hs) hsp
  exact no_one_tie_disjoint_leaf_of_equal_perron_edge hconn hadj hu hxy huv
    (fun he => hout ⟨x,he.symm⟩) (fun he => hout ⟨y,he.symm⟩)
    (hi.ne (by simp [x, Fin.ext_iff])) (hi.ne (by simp [y, Fin.ext_iff]))
    hQ (tieCount_of_untied (leaf_untied hconn hadj hu)) ht₁ ht₂
    (perron_eq_at_equal_radius hd hoff hconn hi ha hQ u v hr)

omit hd hoff in
/-- On an odd cycle of length at least five, attaching one or more leaves
at a single vertex rules out a three-element distance spectrum. -/
theorem not_single_parent_cycle (hconn : G.Connected) (hn : 4 ≤ n) (ho : Odd n)
    (f : Copy (cycleGraph n) G) (p : Fin n)
    (hiso : ∀ i j, G.dist (f i) (f j) = (cycleGraph n).dist i j)
    (hl : ∀ z ∉ Set.range f, G.degree z = 1 ∧ G.Adj z (f p))
    (hout : ∃ z, z ∉ Set.range f) (hthree : numDistanceEigenvalues G = 3) : False := by
  let e : Fin n → V := fun i => f (i+p)
  have he : Function.Injective e := f.injective.comp (Equiv.addRight p).injective
  have hr : Set.range e = Set.range f := by
    exact (Equiv.addRight p).surjective.range_comp f
  have hd' (i j : Fin n) : G.dist (e i) (e j) = (cycleGraph n).dist i j := by
    rw [show G.dist (e i) (e j) = _ from hiso (i+p) (j+p), cycle_dist_translate]
  have hl' (z : V) (hz : z ∉ Set.range e) : G.degree z = 1 ∧ G.Adj z (e 0) := by
    rw [hr] at hz
    simpa [e] using hl z hz
  obtain ⟨leaf,hs⟩ := hout
  exact odd_single_parent_zero hd' hl' hconn he hn ho (hr ▸ hs) hthree
end Unicyclic
