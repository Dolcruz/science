import Unicyclic.Statement

namespace Unicyclic.TriangleAlgebra

abbrev I := Fin 2 × Fin 3

/-- Distance between vertices from two classes, before the diagonal correction. -/
def base (i j : I) : ℝ :=
  (i.1.val:ℝ) + (j.1.val:ℝ) + (if i.2 = j.2 then 0 else 1)

/-- Quotient of the distance matrix of a triangle with pendant leaves. -/
def Q (w : Fin 3 → ℝ) : Matrix I I ℝ := fun i j =>
  base i j * (if j.1 = 0 then 1 else w j.2) - (if i = j then 2*(i.1.val:ℝ) else 0)

private abbrev F (w : Fin 3 → ℝ) (a b c : ℝ) :=
  Q w ^ 3 + a • (Q w ^ 2) + b • Q w + c • 1

local macro "expand_entries" : tactic => `(tactic|
  norm_num [F, pow_succ, Matrix.mul_apply, Matrix.add_apply, Matrix.smul_apply, Matrix.one_apply,
    Fintype.sum_prod_type, Fin.sum_univ_two, Fin.sum_univ_three, Q, base, smul_eq_mul])

private lemma first_difference (w : Fin 3 → ℝ) (a b c : ℝ) :
    2 * (F w a b c (0,0) (0,0) - F w a b c (0,1) (0,1)) -
    3 * (F w a b c (0,0) (0,2) - F w a b c (0,1) (0,2)) =
      -5 * (3*w 2+1) * (w 0-w 1) := by
  expand_entries
  ring

private lemma second_difference (w : Fin 3 → ℝ) (a b c : ℝ) :
    2 * (F w a b c (0,1) (0,1) - F w a b c (0,2) (0,2)) -
    3 * (F w a b c (0,1) (0,0) - F w a b c (0,2) (0,0)) =
      -5 * (3*w 0+1) * (w 1-w 2) := by
  expand_entries
  ring

private lemma equal_weights (u a b c : ℝ) :
    5*(3*u+1)*F (fun _ => u) a b c (0,0) (0,1) -
      3*(u+1)*F (fun _ => u) a b c (1,0) (0,0) -
      (6*u+1)*F (fun _ => u) a b c (1,0) (0,1) = 5*u*(9*u^2+9*u+5) := by
  expand_entries
  ring

/-- No monic cubic can annihilate the rows corresponding to occupied classes. -/
theorem impossible (w : Fin 3 → ℝ) (hw : ∀ i, 0 ≤ w i) (hpos : ∃ i, 0 < w i)
    (a b c : ℝ)
    (hroot : ∀ i j, (Q w^3 + a • (Q w^2) + b • Q w + c • 1 : Matrix I I ℝ) (0,i) j = 0)
    (hleaf : ∀ i, 0 < w i → ∀ j, (Q w^3 + a • (Q w^2) + b • Q w + c • 1 : Matrix I I ℝ) (1,i) j = 0) :
    False := by
  change ∀ i j, F w a b c (0,i) j = 0 at hroot
  change ∀ i, 0 < w i → ∀ j, F w a b c (1,i) j = 0 at hleaf
  have h₁ := first_difference w a b c
  have h₂ := second_difference w a b c
  simp only [hroot, sub_self, mul_zero] at h₁ h₂
  have dif (x y z : ℝ) (hz : 0 ≤ z) (h : 0 = -5*(3*z+1)*(x-y)) : x = y := by
    rcases mul_eq_zero.mp h.symm with hf | he
    · linarith
    · linarith
  have h01 := dif _ _ _ (hw 2) h₁
  have h12 := dif _ _ _ (hw 0) h₂
  obtain ⟨i,hi⟩ := hpos
  have hconst : w = fun _ => w 0 := by
    funext j
    fin_cases j <;> first | rfl | exact h01.symm | exact (h01.trans h12).symm
  have hu : 0 < w 0 := (congrFun hconst i) ▸ hi
  have h := equal_weights (w 0) a b c
  rw [← hconst] at h
  simp only [hroot, hleaf 0 hu, mul_zero, sub_self] at h
  have hp : 0 < 5*w 0*(9*(w 0)^2+9*w 0+5) := by positivity
  linarith

end Unicyclic.TriangleAlgebra
