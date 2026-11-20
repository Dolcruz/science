import Unicyclic.CycleDistances
import Unicyclic.SpectralStructure
import Mathlib.Tactic.NormCharpoly

namespace Unicyclic

open SimpleGraph Polynomial

private def c4 : Matrix (Fin 4) (Fin 4) ℤ :=
  !![0,1,2,1; 1,0,1,2; 2,1,0,1; 1,2,1,0]

private def c5 : Matrix (Fin 5) (Fin 5) ℤ :=
  !![0,1,2,2,1; 1,0,1,2,2; 2,1,0,1,2; 2,2,1,0,1; 1,2,2,1,0]

private def c6 : Matrix (Fin 6) (Fin 6) ℤ :=
  !![0,1,2,3,2,1; 1,0,1,2,3,2; 2,1,0,1,2,3;
     3,2,1,0,1,2; 2,3,2,1,0,1; 1,2,3,2,1,0]

private theorem matrix_eq_of_int_table {n : ℕ} (G : SimpleGraph (Fin n))
    (A : Matrix (Fin n) (Fin n) ℤ) (h : ∀ u v, (G.dist u v : ℤ) = A u v) :
    distMatrix G = A.map (Int.castRingHom ℝ) := by
  ext i j
  change (G.dist i j : ℝ) = (A i j : ℝ)
  exact_mod_cast h i j

private theorem charpoly_c4 : c4.charpoly = (X - 4) * X * (X + 2)^2 := by
  unfold c4
  eval_charpoly

private theorem charpoly_c5 : c5.charpoly = (X - 6) * (X^2 + 3*X + 1)^2 := by
  unfold c5
  eval_charpoly

private theorem charpoly_c6 : c6.charpoly = (X - 9) * (X + 4)^2 * X^2 * (X + 1) := by
  unfold c6
  eval_charpoly

theorem spectrum_cycle4 : SanityC4 := by
  have h := matrix_eq_of_int_table (cycleGraph 4) c4 (by
    intro u v
    rw [cycle4_dist]
    fin_cases u <;> fin_cases v <;> rfl)
  unfold SanityC4
  ext x
  rw [Matrix.mem_spectrum_iff_isRoot_charpoly, h, Matrix.charpoly_map, charpoly_c4]
  simp [Polynomial.IsRoot, sub_eq_zero, mul_eq_zero, add_eq_zero_iff_eq_neg, or_assoc]

theorem spectrum_cycle5 : SanityC5 := by
  have h := matrix_eq_of_int_table (cycleGraph 5) c5 (by
    intro u v
    rw [cycle5_dist]
    fin_cases u <;> fin_cases v <;> rfl)
  have quadratic (x : ℝ) : x^2 + 3*x + 1 =
      (x - ((-3 + Real.sqrt 5)/2)) * (x - ((-3 - Real.sqrt 5)/2)) := by
    nlinarith [Real.sq_sqrt (show (0:ℝ) ≤ 5 by norm_num)]
  unfold SanityC5
  ext x
  rw [Matrix.mem_spectrum_iff_isRoot_charpoly, h, Matrix.charpoly_map, charpoly_c5]
  simp [Polynomial.IsRoot, quadratic, sub_eq_zero, mul_eq_zero]

theorem spectrum_cycle6 : spectrum ℝ (distMatrix (cycleGraph 6)) = {9, -4, 0, -1} := by
  have h := matrix_eq_of_int_table (cycleGraph 6) c6 (by
    intro u v
    rw [cycle6_dist]
    fin_cases u <;> fin_cases v <;> rfl)
  ext x
  rw [Matrix.mem_spectrum_iff_isRoot_charpoly, h, Matrix.charpoly_map, charpoly_c6]
  simp [Polynomial.IsRoot, sub_eq_zero, mul_eq_zero, add_eq_zero_iff_eq_neg, or_assoc]

theorem num_cycle4 : numDistanceEigenvalues (cycleGraph 4) = 3 := by
  unfold numDistanceEigenvalues
  rw [show spectrum ℝ (distMatrix (cycleGraph 4)) = _ from spectrum_cycle4]
  norm_num [Set.ncard_insert_eq_ite]

theorem num_cycle5 : numDistanceEigenvalues (cycleGraph 5) = 3 := by
  unfold numDistanceEigenvalues
  rw [show spectrum ℝ (distMatrix (cycleGraph 5)) = _ from spectrum_cycle5]
  have hs := Real.sq_sqrt (show (0:ℝ) ≤ 5 by norm_num)
  have hp := Real.sqrt_pos.2 (show (0:ℝ) < 5 by norm_num)
  have h₁ : (6:ℝ) ≠ (-3 + Real.sqrt 5)/2 := by intro h; nlinarith
  have h₂ : (6:ℝ) ≠ (-3 - Real.sqrt 5)/2 := by intro h; nlinarith
  have h₃ : (-3 + Real.sqrt 5)/2 ≠ (-3 - Real.sqrt 5)/2 := by intro h; linarith
  simp [h₁, h₂, h₃]

theorem num_cycle6 : SanityC6 := by
  unfold SanityC6 numDistanceEigenvalues
  rw [spectrum_cycle6]
  norm_num [Set.ncard_insert_eq_ite]

/-- The discrete second difference of one column of the cycle distance
matrix has one positive spike and two negative spikes (possibly coincident). -/
private theorem radius_second {n j z : ℤ} (hz : 0 ≤ z) (hzn : z < n)
    (hj : 1 ≤ j) (hjn : j+1 ≤ n/2) :
    cycleRadius n z (j+1) - 2 * cycleRadius n z j + cycleRadius n z (j-1) =
      (if z = j then 2 else 0) - (if z = j + n/2 then 1 else 0) -
        (if z = j + (n+1)/2 then 1 else 0) := by
  simp only [cycleRadius, abs_eq_max_neg]
  split_ifs <;> omega

private theorem real_dist {n : ℕ} (a b : Fin n) :
    distMatrix (cycleGraph n) a b = (cycleRadius n a b : ℝ) := by
  unfold distMatrix
  exact_mod_cast cycle_dist_int a b

theorem cycle_rows_equal {n : ℕ} [NeZero n] (x y : Fin n) :
    (∑ z, distMatrix (cycleGraph n) x z) = ∑ z, distMatrix (cycleGraph n) y z := by
  let e : Fin n ≃ Fin n := Equiv.addRight (y-x)
  apply Fintype.sum_equiv e
  intro z
  unfold distMatrix
  rw [cycleGraph_dist, cycleGraph_dist]
  congr 1
  unfold around
  change min (x-z).val (z-x).val = min (y-(z+(y-x))).val ((z+(y-x))-y).val
  have h₁ : x-z = y-(z+(y-x)) := by abel
  have h₂ : z-x = (z+(y-x))-y := by abel
  rw [h₁, h₂]
private theorem square_second {V : Type} [Fintype V] [DecidableEq V]
    (D : Matrix V V ℝ) (o p c m l r : V)
    (h : ∀ z, D z p - 2 * D z c + D z m =
      (if z = c then 2 else 0) - (if z = l then 1 else 0) - (if z = r then 1 else 0)) :
    (D^2) o p - 2 * (D^2) o c + (D^2) o m = 2 * D o c - D o l - D o r := by
  simp only [sq, Matrix.mul_apply, Finset.mul_sum]
  calc
    _ = ∑ z, D o z * (D z p - 2 * D z c + D z m) := by
      rw [← Finset.sum_sub_distrib, ← Finset.sum_add_distrib]
      apply Finset.sum_congr rfl
      intro a ha
      ring
    _ = _ := by
      simp [h, mul_sub, mul_ite, Finset.sum_sub_distrib]
      ring

private theorem second_column {n : ℕ} {p c m l r : Fin n}
    (hp : (p.val:ℤ) = c.val + 1) (hm : (m.val:ℤ) = c.val - 1)
    (hl : (l.val:ℤ) = c.val + (n:ℤ)/2) (hr : (r.val:ℤ) = c.val + ((n:ℤ)+1)/2)
    (hc : 1 ≤ (c.val:ℤ)) (hcn : (c.val:ℤ)+1 ≤ (n:ℤ)/2) (z : Fin n) :
    distMatrix (cycleGraph n) z p - 2 * distMatrix (cycleGraph n) z c +
      distMatrix (cycleGraph n) z m =
      (if z = c then 2 else 0) - (if z = l then 1 else 0) - (if z = r then 1 else 0) := by
  have he (x : Fin n) : ((z.val:ℤ) = x.val) ↔ z = x := by
    rw [Int.natCast_inj]; exact Fin.ext_iff.symm
  have h := radius_second (n := (n:ℤ)) (j := (c.val:ℤ)) (z := (z.val:ℤ))
    (by omega) (by exact_mod_cast z.isLt) hc hcn
  rw [← hp, ← hm, ← hl, ← hr] at h
  simp only [he] at h
  simp only [real_dist]
  split_ifs at * <;> exact_mod_cast h

/-- Three consecutive interior distances yield a nonzero second difference
of the squared distance matrix unless the cycle length equals four times the
middle distance. -/
private theorem affine_forces_length {n j : ℕ} [NeZero n]
    (hj : 2 ≤ j) (hn : j+1 ≤ n/2) (s t : ℝ)
    (h : ∀ x y, x ≠ y → (distMatrix (cycleGraph n) ^ 2) x y =
      s * distMatrix (cycleGraph n) x y + t) : n = 4*j := by
  let p : Fin n := ⟨j+1, by omega⟩
  let c : Fin n := ⟨j, by omega⟩
  let m : Fin n := ⟨j-1, by omega⟩
  let l : Fin n := ⟨j+n/2, by omega⟩
  let r : Fin n := ⟨j+(n+1)/2, by omega⟩
  have hp : (p.val:ℤ) = (j:ℤ)+1 := by simp [p]
  have hc : (c.val:ℤ) = (j:ℤ) := rfl
  have hm : (m.val:ℤ) = (j:ℤ)-1 := by dsimp [m]; omega
  have hl : (l.val:ℤ) = (j:ℤ)+(n:ℤ)/2 := by simp [l]
  have hr : (r.val:ℤ) = (j:ℤ)+((n:ℤ)+1)/2 := by simp [r]
  have hs := square_second (distMatrix (cycleGraph n)) 0 p c m l r
    (second_column hp hm hl hr (by omega) (by omega))
  have neighbor (a : Fin n) (ha : a.val ≤ n/2) : distMatrix (cycleGraph n) 0 a = (a.val:ℝ) := by
    rw [real_dist]
    exact_mod_cast (show cycleRadius (n:ℤ) (0:Fin n) a = (a.val:ℤ) by
      simp only [cycleRadius, Fin.val_zero, Nat.cast_zero, abs_eq_max_neg]; omega)
  have antipode (a : Fin n) (ha : n ≤ 2*a.val) :
      distMatrix (cycleGraph n) 0 a = (n:ℝ) - (a.val:ℝ) := by
    rw [real_dist]
    exact_mod_cast (show cycleRadius (n:ℤ) (0:Fin n) a = (n:ℤ)-(a.val:ℤ) by
      simp only [cycleRadius, Fin.val_zero, Nat.cast_zero, abs_eq_max_neg]; omega)
  rw [h 0 p (by simp [p, Fin.ext_iff]), h 0 c (by simp [c, Fin.ext_iff]; omega),
    h 0 m (by simp [m, Fin.ext_iff]; omega),
    neighbor p (by dsimp [p]; omega), neighbor c (by dsimp [c]; omega),
    neighbor m (by dsimp [m]; omega), antipode l (by dsimp [l]; omega),
    antipode r (by dsimp [r]; omega)] at hs
  have hmid : (n/2 + (n+1)/2 : ℕ) = n := by omega
  have hmidR : ((n/2:ℕ):ℝ) + (((n+1)/2:ℕ):ℝ) = n := by exact_mod_cast hmid
  simp only [p, c, m, l, r, Nat.cast_add, Nat.cast_one, Nat.cast_sub (by omega : 1 ≤ j)] at hs
  exact_mod_cast (show (n:ℝ) = 4*(j:ℝ) by nlinarith only [hs, hmidR])

theorem num_cycle_ne_three {n : ℕ} (hn : 7 ≤ n) :
    numDistanceEigenvalues (cycleGraph n) ≠ 3 := by
  have : NeZero n := ⟨by omega⟩
  intro he
  have hconn : (cycleGraph n).Connected := ⟨preconnected_cycleGraph⟩
  obtain ⟨s, t, h⟩ := exists_affine_square_offdiag (cycleGraph n) hconn he cycle_rows_equal
  have e := affine_forces_length (j := 2) (by decide) (by omega) s t h
  have e' := affine_forces_length (j := 3) (by decide) (by omega) s t h
  omega
theorem num_cycle3 : numDistanceEigenvalues (cycleGraph 3) = 2 := by
  let A : Matrix (Fin 3) (Fin 3) ℤ := !![0,1,1; 1,0,1; 1,1,0]
  have h := matrix_eq_of_int_table (cycleGraph 3) A (by
    intro u v
    rw [cycleGraph_dist]
    fin_cases u <;> fin_cases v <;> rfl)
  have hc : A.charpoly = (X-2)*(X+1)^2 := by dsimp [A]; eval_charpoly
  have hs : spectrum ℝ (distMatrix (cycleGraph 3)) = {2,-1} := by
    ext x
    rw [Matrix.mem_spectrum_iff_isRoot_charpoly, h, Matrix.charpoly_map, hc]
    simp [Polynomial.IsRoot, sub_eq_zero, add_eq_zero_iff_eq_neg]
  unfold numDistanceEigenvalues
  rw [hs]
  norm_num [Set.ncard_insert_eq_ite]

/-- Classification for all simple cycles. -/
theorem num_cycle_iff {n : ℕ} (hn : 3 ≤ n) :
    numDistanceEigenvalues (cycleGraph n) = 3 ↔ n = 4 ∨ n = 5 := by
  constructor
  · intro he
    by_cases hn7 : 7 ≤ n
    · exact (num_cycle_ne_three hn7 he).elim
    have h3 : n ≠ 3 := by
      rintro rfl
      rw [num_cycle3] at he
      omega
    have h6 : n ≠ 6 := by
      rintro rfl
      have h₆ : numDistanceEigenvalues (cycleGraph 6) = 4 := num_cycle6
      omega
    omega
  · rintro (rfl | rfl)
    · exact num_cycle4
    · exact num_cycle5
end Unicyclic
