import Unicyclic.SpectralStructure
import Unicyclic.LeafBalance
import Unicyclic.TriangleAlgebra
import Unicyclic.TriangleGeometry

namespace Unicyclic

open Matrix

namespace TriangleLeaves

variable {V K : Type} [Fintype V] [DecidableEq V] [Fintype K] [DecidableEq K]

private def indicator (classOf : V → K) : Matrix V K ℝ :=
  fun v i => if classOf v = i then 1 else 0

private def countClass (classOf : V → K) (j : K) : ℕ :=
  (Finset.univ.filter (fun v => classOf v = j)).card

omit [Fintype V] [DecidableEq V] in
private theorem indicator_mul_apply (classOf : V → K) (B : Matrix K K ℝ) (v : V) (j : K) :
    (indicator classOf * B) v j = B (classOf v) j := by
  simp [Matrix.mul_apply, indicator, ite_mul]

/-- Row sums into each fiber give the matrix on functions constant within every fiber. -/
private theorem lift_class_matrix (classOf : V → K) (base : K → K → ℝ) (corr : K → ℝ)
    (D : Matrix V V ℝ) (B : Matrix K K ℝ)
    (hd : ∀ v w, D v w = base (classOf v) (classOf w) - if v = w then corr (classOf v) else 0)
    (hb : ∀ i j, B i j = base i j * (countClass classOf j : ℝ) - if i=j then corr i else 0) :
    D * indicator classOf = indicator classOf * B := by
  ext v j
  rw [indicator_mul_apply, hb, Matrix.mul_apply]
  have splitTerm (w : V) : D v w * indicator classOf w j =
      (if classOf w = j then base (classOf v) j else 0) -
      (if v=w then (if classOf v=j then corr (classOf v) else 0) else 0) := by
    rw [hd]
    by_cases h : v=w
    · subst w
      by_cases hj : classOf v = j <;> simp [indicator, hj]
    · by_cases hj : classOf w = j <;> simp [indicator, hj, h]
  simp_rw [splitTerm]
  simp [Finset.sum_sub_distrib, Finset.sum_ite, countClass, mul_comm]

private theorem transfer_cubic {D : Matrix V V ℝ} {P : Matrix V K ℝ} {B : Matrix K K ℝ}
    (h : D*P = P*B) (a b c : ℝ) (hc : D^3 + a • (D^2) + b • D + c • 1 = 0) :
    P * (B^3 + a • (B^2) + b • B + c • 1) = 0 := by
  have hp (n : ℕ) : D^n * P = P * B^n := by
    induction n with
    | zero => simp
    | succ n ih =>
      rw [pow_succ, Matrix.mul_assoc, h, ← Matrix.mul_assoc, ih, Matrix.mul_assoc, ← pow_succ]
  have h' := congrArg (fun M : Matrix V V ℝ => M*P) hc
  simpa [Matrix.add_mul, Matrix.mul_add, hp, h] using h'

end TriangleLeaves

open SimpleGraph TriangleLeaves TriangleAlgebra in
/-- A unicyclic graph with triangular core and at least one pendant vertex cannot have three
distinct distance eigenvalues. The six classes of vertices permit empty leaf classes. -/
theorem triangle_leaves_excluded {V : Type} [Fintype V] [DecidableEq V] {G : SimpleGraph V}
    [DecidableRel G.Adj] (h : IsUnicyclic G) (f : Copy (cycleGraph 3) G)
    (hrange : ∀ v, v ∈ Set.range f ↔ G.degree v ≠ 1) (hl : ∃ v, G.degree v = 1) :
    numDistanceEigenvalues G ≠ 3 := by
  classical
  intro hthree
  obtain ⟨cl, hroot, honly, ⟨v₁,hv₁⟩, hmetric⟩ := TriangleGeometry.triangle_coordinates h
    (leafSideCondition_of_three h.1 hthree) f hrange hl
  let w : Fin 3 → ℝ := fun i => (countClass cl (1,i) : ℝ)
  have hrootCount (i : Fin 3) : countClass cl (0,i) = 1 := by
    have heq (v : V) : cl v = (0,i) ↔ v=f i := ⟨honly v i, fun e => e ▸ hroot i⟩
    apply Finset.card_eq_one.mpr
    refine ⟨f i,?_⟩
    ext v
    simp [heq]
  have hweight (i : Fin 3) : 0 < w i ↔ ∃ v, cl v = (1,i) := by
    change 0 < ((Finset.univ.filter (fun v => cl v = (1,i))).card : ℝ) ↔ _
    rw [Nat.cast_pos, Finset.card_pos]
    simp [Finset.Nonempty]
  have hB (i j : I) : Q w i j = base i j * (countClass cl j : ℝ) -
      (if i=j then 2*(i.1.val:ℝ) else 0) := by
    obtain ⟨k,j⟩ := j
    fin_cases k <;> simp [Q, w, hrootCount]
  have hinter := lift_class_matrix cl base (fun i => 2*(i.1.val:ℝ)) (distMatrix G) (Q w) hmetric hB
  obtain ⟨a,b,c,hcubic⟩ := exists_cubic_powers G hthree
  have htransfer := transfer_cubic hinter a b c hcubic
  have hat (v : V) (j : I) : (Q w ^ 3 + a • (Q w^2) + b • Q w + c • 1 : Matrix I I ℝ) (cl v) j = 0 := by
    simpa only [indicator_mul_apply, Matrix.zero_apply] using congrFun (congrFun htransfer v) j
  apply impossible w (fun i => Nat.cast_nonneg _) ?_ a b c ?_ ?_
  · refine ⟨(cl v₁).2, (hweight _).mpr ⟨v₁, ?_⟩⟩
    exact Prod.ext hv₁ rfl
  · intro i j
    simpa only [hroot] using hat (f i) j
  · intro i hi j
    obtain ⟨v,hv⟩ := (hweight i).mp hi
    simpa only [hv] using hat v j

end Unicyclic
