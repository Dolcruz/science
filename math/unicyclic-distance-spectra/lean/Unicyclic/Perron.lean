import Unicyclic.Statement

namespace Unicyclic

open Matrix

variable {V : Type} [Fintype V] [DecidableEq V]

omit [DecidableEq V] in
private theorem quadratic_le_abs (A : Matrix V V ℝ) (hn : ∀ i j, 0 ≤ A i j)
    (p : V → ℝ) :
    p ⬝ᵥ (A *ᵥ p) ≤ (fun i => |p i|) ⬝ᵥ (A *ᵥ (fun i => |p i|)) := by
  unfold dotProduct Matrix.mulVec
  dsimp [dotProduct]
  apply Finset.sum_le_sum
  intro i _
  rw [Finset.mul_sum, Finset.mul_sum]
  apply Finset.sum_le_sum
  intro j _
  simpa only [abs_mul, abs_of_nonneg (hn i j)] using le_abs_self (p i * (A i j * p j))

private theorem shifted_posSemidef {A : Matrix V V ℝ} (hA : A.IsHermitian)
    {ρ : ℝ} (ht : ∀ r ∈ spectrum ℝ A, r ≤ ρ) :
    (algebraMap ℝ (Matrix V V ℝ) ρ - A).PosSemidef := by
  apply Matrix.posSemidef_iff_isHermitian_and_spectrum_nonneg.mpr
  constructor
  · refine IsHermitian.sub ?_ hA
    simp [Matrix.IsHermitian, Algebra.algebraMap_eq_smul_one]
  · intro r hr
    have hmem : ρ - r ∈ spectrum ℝ A := by
      rw [spectrum.mem_iff] at hr ⊢
      intro hu
      apply hr
      rw [map_sub] at hu
      have he : algebraMap ℝ (Matrix V V ℝ) r - (algebraMap ℝ _ ρ - A) =
          -(algebraMap ℝ _ ρ - algebraMap ℝ _ r - A) := by abel
      rw [he]
      exact hu.neg
    have := ht _ hmem
    change 0 ≤ r
    linarith

private theorem abs_top_eigenvector {A : Matrix V V ℝ} (hn : ∀ i j, 0 ≤ A i j)
    {ρ : ℝ} (hps : (algebraMap ℝ (Matrix V V ℝ) ρ - A).PosSemidef)
    {p : V → ℝ} (hp : A *ᵥ p = ρ • p) :
    A *ᵥ (fun i => |p i|) = ρ • (fun i => |p i|) := by
  let q : V → ℝ := fun i => |p i|
  have hnorm : q ⬝ᵥ (ρ • q) = p ⬝ᵥ (ρ • p) := by
    apply Finset.sum_congr rfl
    intro i _
    change |p i| * (ρ * |p i|) = p i * (ρ * p i)
    rcases le_total 0 (p i) with h | h
    · simp [abs_of_nonneg h]
    · simp [abs_of_nonpos h]
  have hle := quadratic_le_abs A hn p
  rw [hp, ← hnorm] at hle
  have hn0 := hps.dotProduct_mulVec_nonneg q
  have hz : star q ⬝ᵥ ((algebraMap ℝ (Matrix V V ℝ) ρ - A) *ᵥ q) = 0 := by
    refine le_antisymm ?_ hn0
    simpa [Algebra.algebraMap_eq_smul_one, sub_mulVec, smul_mulVec, dotProduct_sub]
      using sub_nonpos.mpr hle
  have hz' := hps.dotProduct_mulVec_zero_iff.mp hz
  simpa [Algebra.algebraMap_eq_smul_one, sub_mulVec, smul_mulVec, sub_eq_zero, eq_comm]
    using hz'

private theorem top_eigenvector_ne_zero_at {A : Matrix V V ℝ}
    (hn : ∀ i j, 0 ≤ A i j) (hpos : ∀ i j, i ≠ j → 0 < A i j)
    {ρ : ℝ} (hps : (algebraMap ℝ (Matrix V V ℝ) ρ - A).PosSemidef)
    {p : V → ℝ} (hp : A *ᵥ p = ρ • p) (hne : p ≠ 0) (i : V) : p i ≠ 0 := by
  intro hi
  obtain ⟨j, hj⟩ : ∃ j, p j ≠ 0 := by
    by_contra! h
    exact hne (funext h)
  have hij : i ≠ j := fun e => hj (e ▸ hi)
  have h : 0 < ∑ k, A i k * |p k| := Finset.sum_pos'
    (fun k _ => mul_nonneg (hn i k) (abs_nonneg _))
    ⟨j, Finset.mem_univ _, mul_pos (hpos i j hij) (abs_pos.mpr hj)⟩
  have hi' := congrFun (abs_top_eigenvector hn hps hp) i
  simp [Matrix.mulVec, dotProduct, hi] at hi'
  linarith

/-- At the largest spectral value of a real symmetric matrix with positive off-diagonal
entries and nonnegative diagonal, the eigenspace is spanned by a strictly positive vector. -/
theorem exists_pos_top_eigenvector {A : Matrix V V ℝ} (hA : A.IsHermitian)
    (hn : ∀ i j, 0 ≤ A i j) (hpos : ∀ i j, i ≠ j → 0 < A i j)
    {ρ : ℝ} (ht : IsGreatest (spectrum ℝ A) ρ) :
    ∃ p : V → ℝ, (∀ i, 0 < p i) ∧ A *ᵥ p = ρ • p ∧
      ∀ w : V → ℝ, A *ᵥ w = ρ • w → ∃ c : ℝ, w = c • p := by
  have hρ := ht.1
  rw [hA.spectrum_real_eq_range_eigenvalues] at hρ
  obtain ⟨j, hj⟩ := hρ
  let v : V → ℝ := ⇑(hA.eigenvectorBasis j)
  have hv : A *ᵥ v = ρ • v := hj ▸ hA.mulVec_eigenvectorBasis j
  have hne : v ≠ 0 := by
    intro h
    apply hA.eigenvectorBasis.toBasis.ne_zero j
    ext i
    exact congrFun h i
  have hs := shifted_posSemidef hA (fun r hr => ht.2 hr)
  let p : V → ℝ := fun i => |v i|
  have hp : A *ᵥ p = ρ • p := abs_top_eigenvector hn hs hv
  have hpp : ∀ i, 0 < p i := fun i =>
    abs_pos.mpr (top_eigenvector_ne_zero_at hn hpos hs hv hne i)
  refine ⟨p, hpp, hp, ?_⟩
  intro w hw
  let c := w j / p j
  refine ⟨c, sub_eq_zero.mp ?_⟩
  by_contra h
  have heig : A *ᵥ (w - c • p) = ρ • (w - c • p) := by
    rw [mulVec_sub, mulVec_smul, hw, hp, smul_sub, smul_comm c ρ]
  apply top_eigenvector_ne_zero_at hn hpos hs heig h j
  change w j - (w j / p j) * p j = 0
  rw [div_mul_cancel₀ _ (hpp j).ne', sub_self]

end Unicyclic
