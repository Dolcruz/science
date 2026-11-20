/-
Main theorem: if `3757^m ≤ n^2`, the `n × n` grid contains a set without isosceles right
triangles with at least `313^m / (m * 2^312 + 1)` points.
-/
import IRT.Basic
import IRT.Digits

open Finset GaussianInt

local notation "ℤ[i]" => GaussianInt

namespace IRT

/-- The base `β = 61 + 6i`, of norm `3757`. -/
def β₀ : ℤ[i] := ⟨61, 6⟩

theorem β₀_ne_zero : β₀ ≠ 0 := by decide

theorem β₀_norm : β₀.norm = 3757 := by decide

/-- The digits as Gaussian integers. -/
def P₀ (a : Fin 313) : ℤ[i] := ⟨(dig a).1, (dig a).2⟩

theorem expr_eq (a b c : Fin 313) :
    P₀ a + I * P₀ c - (1 + I) * P₀ b =
      ⟨(dig a).1 - (dig c).2 - ((dig b).1 - (dig b).2),
       (dig a).2 + (dig c).1 - ((dig b).1 + (dig b).2)⟩ := by
  apply Zsqrtd.ext <;> simp [P₀, I] <;> ring

/-- If `61 + 6i` divides `z`, then `z` passes the test `divB`. -/
theorem divB_of_dvd {z : ℤ[i]} (h : β₀ ∣ z) : divB z.re z.im = true := by
  obtain ⟨w, rfl⟩ := h
  have h1 : 61 * (β₀ * w).re + 6 * (β₀ * w).im = 3757 * w.re := by
    simp [β₀]; ring
  have h2 : 61 * (β₀ * w).im - 6 * (β₀ * w).re = 3757 * w.im := by
    simp [β₀]; ring
  unfold divB
  rw [h1, h2]
  simp

/-- The 313 digits form a digit alphabet for the base `61 + 6i`. -/
def alphabet₀ : Alphabet β₀ 313 where
  P := P₀
  nocarry a b c h := by
    have hdiv := divB_of_dvd h
    rw [expr_eq] at hdiv
    obtain ⟨⟨h1, h2⟩, -⟩ := certificate a b c hdiv
    have h0 : P₀ a + I * P₀ c - (1 + I) * P₀ b = 0 := by
      rw [expr_eq]; exact Zsqrtd.ext h1 h2
    linear_combination h0
  peel a b c h := by
    have h0 : P₀ a + I * P₀ c - (1 + I) * P₀ b = 0 := by linear_combination h
    rw [expr_eq] at h0
    have h1 : (dig a).1 - (dig c).2 - ((dig b).1 - (dig b).2) = 0 := by
      have := congrArg Zsqrtd.re h0; simpa using this
    have h2 : (dig a).2 + (dig c).1 - ((dig b).1 + (dig b).2) = 0 := by
      have := congrArg Zsqrtd.im h0; simpa using this
    exact (certificate a b c (by rw [h1, h2]; simp [divB])).2

theorem hP₀ (a : Fin 313) : ‖(alphabet₀.P a : ℂ)‖ ≤ (‖(β₀ : ℂ)‖ - 1) / 2 := by
  have hβ : ‖(β₀ : ℂ)‖ ^ 2 = 3757 := by
    rw [Complex.sq_norm, ← intCast_real_norm, β₀_norm]; norm_num
  have hβ' : (61 : ℝ) ≤ ‖(β₀ : ℂ)‖ := by
    nlinarith [norm_nonneg (β₀ : ℂ)]
  have ha : ‖(P₀ a : ℂ)‖ ^ 2 ≤ 900 := by
    rw [Complex.sq_norm, ← intCast_real_norm]
    have := digits_small a
    have h : (P₀ a).norm = (dig a).1 * (dig a).1 + (dig a).2 * (dig a).2 := by
      simp [P₀, Zsqrtd.norm_def]
    rw [h]
    exact_mod_cast this
  have ha' : ‖(P₀ a : ℂ)‖ ≤ 30 := by
    nlinarith [norm_nonneg (P₀ a : ℂ)]
  show ‖(P₀ a : ℂ)‖ ≤ _
  linarith

/-- `S` contains no isosceles right triangle. If the vector from `b` to `a` is the vector
from `b` to `c` rotated by 90° (so that `a, b, c` is an isosceles right triangle with its
right angle at `b`, or all three points coincide), then the points coincide. Both
orientations are covered, because `a` and `c` range over all of `S`. -/
def IRTFree (S : Finset (ℤ × ℤ)) : Prop :=
  ∀ a ∈ S, ∀ b ∈ S, ∀ c ∈ S,
    a.1 - b.1 = -(c.2 - b.2) → a.2 - b.2 = c.1 - b.1 → a = b

theorem norm_β₀_sq : ‖(β₀ : ℂ)‖ ^ 2 = 3757 := by
  rw [Complex.sq_norm, ← intCast_real_norm, β₀_norm]; norm_num

/-- **Main theorem.** If `3757^m ≤ n^2`, then the `n × n` grid `{0, …, n-1}²` contains a
set without isosceles right triangles that has at least `313^m / (m * 2^312 + 1)` points
(integer division). -/
theorem main (m n : ℕ) (hn : 3757 ^ m ≤ n ^ 2) : ∃ S : Finset (ℤ × ℤ), IRTFree S ∧
    (∀ p ∈ S, 0 ≤ p.1 ∧ p.1 < n ∧ 0 ≤ p.2 ∧ p.2 < n) ∧
    313 ^ m / (m * 2 ^ 312 + 1) ≤ S.card := by
  obtain ⟨ℓ, hℓ⟩ := alphabet₀.exists_large_level β₀_ne_zero m
  -- translate by `t = ⌊(n - 1) / 2⌋` in both coordinates
  have hinj : Function.Injective
      (fun z : ℤ[i] => (z.re + ((n : ℤ) - 1) / 2, z.im + ((n : ℤ) - 1) / 2)) := by
    intro x y h
    simp only [Prod.mk.injEq] at h
    exact Zsqrtd.ext (by omega) (by omega)
  refine ⟨(alphabet₀.levelSet m ℓ).image
    (fun z : ℤ[i] => (z.re + ((n : ℤ) - 1) / 2, z.im + ((n : ℤ) - 1) / 2)), ?_, ?_, ?_⟩
  · intro a ha b hb c hc h1 h2
    obtain ⟨x, hx, rfl⟩ := mem_image.mp ha
    obtain ⟨y, hy, rfl⟩ := mem_image.mp hb
    obtain ⟨z, hz, rfl⟩ := mem_image.mp hc
    dsimp only at h1 h2
    have hxy : x - y = I * (z - y) := by
      apply Zsqrtd.ext <;> simp [I] <;> omega
    have key : z + I * x = (1 + I) * y := by
      linear_combination I * hxy + (z - y) * I_mul_I
    have hxy' : x = y := (alphabet₀.levelSet_free β₀_ne_zero m ℓ z hz y hy x hx key).2
    rw [hxy']
  · intro p hp
    obtain ⟨z, hz, rfl⟩ := mem_image.mp hp
    obtain ⟨w, -, rfl⟩ := mem_image.mp hz
    obtain ⟨hre, him⟩ := alphabet₀.coord_bound hP₀ w
    -- `|β|^m ≤ n`
    have hsq : (‖(β₀ : ℂ)‖ ^ m) ^ 2 ≤ (n : ℝ) ^ 2 := by
      rw [← pow_mul, mul_comm, pow_mul, norm_β₀_sq]
      exact_mod_cast hn
    have hle : ‖(β₀ : ℂ)‖ ^ m ≤ (n : ℝ) :=
      (pow_le_pow_iff_left₀ (by positivity) (by positivity) two_ne_zero).mp hsq
    have hre' : 2 * |(alphabet₀.Φ w).re| + 1 ≤ (n : ℤ) := by
      have : ((2 * |(alphabet₀.Φ w).re| + 1 : ℤ) : ℝ) ≤ ((n : ℤ) : ℝ) := by
        push_cast; linarith
      exact_mod_cast this
    have him' : 2 * |(alphabet₀.Φ w).im| + 1 ≤ (n : ℤ) := by
      have : ((2 * |(alphabet₀.Φ w).im| + 1 : ℤ) : ℝ) ≤ ((n : ℤ) : ℝ) := by
        push_cast; linarith
      exact_mod_cast this
    have a1 := le_abs_self (alphabet₀.Φ w).re
    have a2 := neg_abs_le (alphabet₀.Φ w).re
    have a3 := le_abs_self (alphabet₀.Φ w).im
    have a4 := neg_abs_le (alphabet₀.Φ w).im
    dsimp only
    refine ⟨?_, ?_, ?_, ?_⟩ <;> omega
  · rw [card_image_of_injective _ hinj]
    have e : (313 : ℕ) - 1 = 312 := rfl
    rw [e] at hℓ
    exact hℓ

end IRT
