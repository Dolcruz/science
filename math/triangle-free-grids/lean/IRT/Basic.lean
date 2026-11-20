/-
The digit method of Károlyi and Solymosi for sets without isosceles right triangles,
for an arbitrary digit alphabet in a Gaussian-integer base.
-/
import Mathlib

open Finset GaussianInt

local notation "ℤ[i]" => GaussianInt

namespace IRT

/-- The Gaussian integer `i`. -/
def I : ℤ[i] := ⟨0, 1⟩

theorem I_mul_I : I * I = -1 := by decide

/-- A digit alphabet with `q` digits for the base `β`, listed in peeling order.
`a + i c = (1 + i) b` says that `a, b, c` form an isosceles right triangle with the
right angle at `b` (or that `a = b = c`). -/
structure Alphabet (β : ℤ[i]) (q : ℕ) where
  /-- the digits -/
  P : Fin q → ℤ[i]
  /-- no carries -/
  nocarry : ∀ a b c : Fin q,
    β ∣ (P a + I * P c - (1 + I) * P b) → P a + I * P c = (1 + I) * P b
  /-- peeling order: in a non-constant solution an endpoint precedes the centre -/
  peel : ∀ a b c : Fin q,
    P a + I * P c = (1 + I) * P b → (a = b ∧ c = b) ∨ a < b ∨ c < b

namespace Alphabet

variable {β : ℤ[i]} {q : ℕ} (𝒜 : Alphabet β q)

theorem P_injective : Function.Injective 𝒜.P := by
  intro a b hab
  have h1 := 𝒜.peel a b b (by rw [hab]; ring)
  have h2 := 𝒜.peel b a a (by rw [hab]; ring)
  rcases h1 with h | h | h
  · exact h.1
  · rcases h2 with h' | h' | h'
    · exact h'.1.symm
    · exact absurd h (lt_asymm h')
    · exact absurd h' (lt_irrefl _)
  · exact absurd h (lt_irrefl _)

/-- The value `w₀ + w₁ β + w₂ β² + ⋯` of a word. -/
def Φ {m : ℕ} (w : Fin m → Fin q) : ℤ[i] := ∑ j : Fin m, 𝒜.P (w j) * β ^ (j : ℕ)

theorem Φ_succ {m : ℕ} (w : Fin (m + 1) → Fin q) :
    𝒜.Φ w = 𝒜.P (w 0) + β * 𝒜.Φ (fun j => w j.succ) := by
  simp only [Φ, Fin.sum_univ_succ, Fin.val_zero, pow_zero, mul_one, Fin.val_succ,
    Finset.mul_sum]
  congr 1
  apply Finset.sum_congr rfl
  intro j _
  ring

/-- A triangle equation between word values holds in every digit position. -/
theorem digitwise (hβ : β ≠ 0) : ∀ {m : ℕ} (A B C : Fin m → Fin q),
    𝒜.Φ A + I * 𝒜.Φ C = (1 + I) * 𝒜.Φ B →
    ∀ j, 𝒜.P (A j) + I * 𝒜.P (C j) = (1 + I) * 𝒜.P (B j) := by
  intro m
  induction m with
  | zero => intro A B C _ j; exact j.elim0
  | succ m ih =>
    intro A B C h j
    rw [Φ_succ, Φ_succ, Φ_succ] at h
    have hd : β ∣ (𝒜.P (A 0) + I * 𝒜.P (C 0) - (1 + I) * 𝒜.P (B 0)) :=
      ⟨(1 + I) * 𝒜.Φ (fun j => B j.succ) - 𝒜.Φ (fun j => A j.succ)
        - I * 𝒜.Φ (fun j => C j.succ), by linear_combination h⟩
    have h0 := 𝒜.nocarry _ _ _ hd
    have h' : β * (𝒜.Φ (fun j => A j.succ) + I * 𝒜.Φ (fun j => C j.succ)
        - (1 + I) * 𝒜.Φ (fun j => B j.succ)) = 0 := by
      linear_combination h - h0
    have h'' : 𝒜.Φ (fun j => A j.succ) + I * 𝒜.Φ (fun j => C j.succ)
        = (1 + I) * 𝒜.Φ (fun j => B j.succ) := by
      have := (mul_eq_zero.mp h').resolve_left hβ
      linear_combination this
    exact Fin.cases h0 (fun j => ih _ _ _ h'' j) j

theorem Φ_injective (hβ : β ≠ 0) {m : ℕ} :
    Function.Injective (𝒜.Φ : (Fin m → Fin q) → ℤ[i]) := by
  intro A B hAB
  have hd := 𝒜.digitwise hβ A B B (by rw [hAB]; ring)
  funext j
  apply 𝒜.P_injective
  linear_combination hd j

/-! ### Weights and levels -/

/-- The weight of the `t`-th digit: earlier digits are heavier. -/
def wt (q : ℕ) (t : Fin q) : ℕ := 2 ^ (q - 1 - (t : ℕ))

theorem wt_pos (t : Fin q) : 0 < wt q t := by unfold wt; positivity

theorem wt_le (t : Fin q) : wt q t ≤ 2 ^ (q - 1) :=
  Nat.pow_le_pow_right (by norm_num) (by omega)

theorem two_wt_le {a b : Fin q} (hab : a < b) : 2 * wt q b ≤ wt q a := by
  unfold wt
  have h1 : (a : ℕ) < b := hab
  have h2 := b.isLt
  calc 2 * 2 ^ (q - 1 - (b : ℕ)) = 2 ^ (q - 1 - (b : ℕ) + 1) := by ring
    _ ≤ 2 ^ (q - 1 - (a : ℕ)) := Nat.pow_le_pow_right (by norm_num) (by omega)

theorem weight {a b c : Fin q} (h : 𝒜.P a + I * 𝒜.P c = (1 + I) * 𝒜.P b) :
    2 * wt q b ≤ wt q a + wt q c ∧ (2 * wt q b = wt q a + wt q c → a = b ∧ c = b) := by
  rcases 𝒜.peel a b c h with ⟨h1, h2⟩ | hlt | hlt
  · subst h1; subst h2
    exact ⟨by omega, fun _ => ⟨rfl, rfl⟩⟩
  · have := two_wt_le hlt
    have := wt_pos c
    exact ⟨by omega, fun _ => by omega⟩
  · have := two_wt_le hlt
    have := wt_pos a
    exact ⟨by omega, fun _ => by omega⟩

/-- The level of a word: the sum of the weights of its digits. -/
def L {m : ℕ} (w : Fin m → Fin q) : ℕ := ∑ j : Fin m, wt q (w j)

/-- Three words of the same level whose values satisfy the triangle equation are equal. -/
theorem words_eq (hβ : β ≠ 0) {m : ℕ} (A B C : Fin m → Fin q)
    (heq : 𝒜.Φ A + I * 𝒜.Φ C = (1 + I) * 𝒜.Φ B) (hA : L A = L B) (hC : L C = L B) :
    A = B ∧ C = B := by
  have hd := 𝒜.digitwise hβ A B C heq
  have hle : ∀ j ∈ (univ : Finset (Fin m)),
      2 * wt q (B j) ≤ wt q (A j) + wt q (C j) := fun j _ => (𝒜.weight (hd j)).1
  have hsum : ∑ j, 2 * wt q (B j) = ∑ j, (wt q (A j) + wt q (C j)) := by
    rw [Finset.sum_add_distrib, ← Finset.mul_sum]
    simp only [L] at hA hC
    omega
  have hall := (Finset.sum_eq_sum_iff_of_le hle).mp hsum
  constructor
  · funext j; exact ((𝒜.weight (hd j)).2 (hall j (mem_univ j))).1
  · funext j; exact ((𝒜.weight (hd j)).2 (hall j (mem_univ j))).2

/-- The points whose words have level `ℓ`. -/
def levelSet (m ℓ : ℕ) : Finset ℤ[i] :=
  (univ.filter fun w : Fin m → Fin q => L w = ℓ).image 𝒜.Φ

/-- A level set contains no isosceles right triangle. -/
theorem levelSet_free (hβ : β ≠ 0) (m ℓ : ℕ) :
    ∀ x ∈ 𝒜.levelSet m ℓ, ∀ y ∈ 𝒜.levelSet m ℓ, ∀ z ∈ 𝒜.levelSet m ℓ,
      x + I * z = (1 + I) * y → x = y ∧ z = y := by
  simp only [levelSet, mem_image, mem_filter, mem_univ, true_and]
  rintro _ ⟨A, hA, rfl⟩ _ ⟨B, hB, rfl⟩ _ ⟨C, hC, rfl⟩ h
  obtain ⟨h1, h2⟩ := 𝒜.words_eq hβ A B C h (hA.trans hB.symm) (hC.trans hB.symm)
  subst h1; subst h2
  exact ⟨rfl, rfl⟩

theorem L_le {m : ℕ} (w : Fin m → Fin q) : L w ≤ m * 2 ^ (q - 1) := by
  calc L w ≤ ∑ _j : Fin m, 2 ^ (q - 1) := Finset.sum_le_sum fun j _ => wt_le (w j)
    _ = m * 2 ^ (q - 1) := by simp

/-- Some level set is large. -/
theorem exists_large_level (hβ : β ≠ 0) (m : ℕ) :
    ∃ ℓ, q ^ m / (m * 2 ^ (q - 1) + 1) ≤ (𝒜.levelSet m ℓ).card := by
  have hmaps : ∀ w ∈ (univ : Finset (Fin m → Fin q)),
      L w ∈ range (m * 2 ^ (q - 1) + 1) := fun w _ =>
    mem_range.mpr (Nat.lt_succ_of_le (L_le w))
  obtain ⟨ℓ, -, hℓ⟩ := exists_le_card_fiber_of_mul_le_card_of_maps_to hmaps
    (nonempty_range_add_one) (n := q ^ m / (m * 2 ^ (q - 1) + 1)) (by
      rw [card_range, card_univ, Fintype.card_fun, Fintype.card_fin, Fintype.card_fin]
      exact Nat.mul_div_le _ _)
  refine ⟨ℓ, ?_⟩
  rw [levelSet, card_image_of_injective _ (𝒜.Φ_injective hβ)]
  exact hℓ

/-! ### Size of the points -/

theorem norm_Φ_le (hP : ∀ a, ‖(𝒜.P a : ℂ)‖ ≤ (‖(β : ℂ)‖ - 1) / 2) :
    ∀ {m : ℕ} (w : Fin m → Fin q), ‖(𝒜.Φ w : ℂ)‖ ≤ (‖(β : ℂ)‖ ^ m - 1) / 2 := by
  intro m
  induction m with
  | zero => intro w; simp [Φ]
  | succ m ih =>
    intro w
    rw [Φ_succ, toComplex_add, toComplex_mul]
    calc ‖(𝒜.P (w 0) : ℂ) + (β : ℂ) * (𝒜.Φ (fun j => w j.succ) : ℂ)‖
        ≤ ‖(𝒜.P (w 0) : ℂ)‖ + ‖(β : ℂ)‖ * ‖(𝒜.Φ (fun j => w j.succ) : ℂ)‖ := by
          rw [← norm_mul]; exact norm_add_le _ _
      _ ≤ (‖(β : ℂ)‖ - 1) / 2 + ‖(β : ℂ)‖ * ((‖(β : ℂ)‖ ^ m - 1) / 2) :=
          add_le_add (hP _) (mul_le_mul_of_nonneg_left (ih _) (norm_nonneg _))
      _ = (‖(β : ℂ)‖ ^ (m + 1) - 1) / 2 := by ring

/-- Coordinates of the value of a word of length `m`: `2 |x| + 1 ≤ |β|^m`. -/
theorem coord_bound (hP : ∀ a, ‖(𝒜.P a : ℂ)‖ ≤ (‖(β : ℂ)‖ - 1) / 2)
    {m : ℕ} (w : Fin m → Fin q) :
    2 * |((𝒜.Φ w).re : ℝ)| + 1 ≤ ‖(β : ℂ)‖ ^ m ∧
    2 * |((𝒜.Φ w).im : ℝ)| + 1 ≤ ‖(β : ℂ)‖ ^ m := by
  have h := 𝒜.norm_Φ_le hP w
  have h1 := Complex.abs_re_le_norm (𝒜.Φ w : ℂ)
  have h2 := Complex.abs_im_le_norm (𝒜.Φ w : ℂ)
  rw [← intCast_re] at h1
  rw [← intCast_im] at h2
  constructor <;> linarith

end Alphabet

end IRT
