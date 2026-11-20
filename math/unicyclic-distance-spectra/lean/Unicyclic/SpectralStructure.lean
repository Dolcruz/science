import Unicyclic.Statement
import Unicyclic.Perron

namespace Unicyclic

open Matrix

variable {V : Type} [Fintype V] [DecidableEq V] (G : SimpleGraph V)

/-- The number of vertices equidistant from two given vertices. -/
noncomputable def tieCount (x y : V) : ℕ :=
  (Finset.univ.filter fun z => G.dist z x = G.dist z y).card

/-- Evaluation on differences of coordinate vectors on the two sides of a matrix. -/
def edgePairing {R : Type*} [Ring R] (A : Matrix V V R) (x y u v : V) : R :=
  A x u - A x v - A y u + A y v

omit [Fintype V] [DecidableEq V] in
theorem distMatrix_isHermitian : (distMatrix G).IsHermitian := by
  ext i j
  simpa [distMatrix, Matrix.conjTranspose_apply] using (G.dist_comm (u := j) (v := i))

omit [Fintype V] in
private theorem diagonal_sub_smul_one (f : V → ℝ) (r : ℝ) :
    Matrix.diagonal f - r • 1 = Matrix.diagonal (fun i => f i - r) := by
  ext i j
  by_cases h : i = j <;> simp [h]

theorem dist_cubic_of_spectrum {r s t : ℝ} (hspec : spectrum ℝ (distMatrix G) = {r,s,t}) :
    (distMatrix G - r • 1) * (distMatrix G - s • 1) * (distMatrix G - t • 1) = 0 := by
  classical
  let hA := distMatrix_isHermitian G
  let E := Unitary.conjStarAlgAut ℝ _ (star hA.eigenvectorUnitary)
  have hdiag : E (distMatrix G) = Matrix.diagonal hA.eigenvalues :=
    hA.conjStarAlgAut_star_eigenvectorUnitary
  apply E.injective
  change E _ = E 0
  simp only [map_mul, map_sub, map_smul, map_one, map_zero, hdiag, diagonal_sub_smul_one,
    Matrix.diagonal_mul_diagonal]
  have hz (i : V) : (hA.eigenvalues i - r) * (hA.eigenvalues i - s) *
      (hA.eigenvalues i - t) = 0 := by
    have hmem := hA.eigenvalues_mem_spectrum_real i
    rw [hspec] at hmem
    simp only [Set.mem_insert_iff, Set.mem_singleton_iff] at hmem
    rcases hmem with hi | hi | hi <;> simp [hi]
  simp [hz]

/-- Three distinct distance eigenvalues give a cubic matrix identity without multiplicities. -/
theorem exists_cubic_annihilator (h : numDistanceEigenvalues G = 3) :
    ∃ r s t : ℝ, r ≠ s ∧ r ≠ t ∧ s ≠ t ∧ spectrum ℝ (distMatrix G) = {r,s,t} ∧
      (distMatrix G - r • 1) * (distMatrix G - s • 1) * (distMatrix G - t • 1) = 0 := by
  classical
  obtain ⟨r,s,t,hrs,hrt,hst,hspec⟩ := Set.ncard_eq_three.mp h
  exact ⟨r,s,t,hrs,hrt,hst,hspec,dist_cubic_of_spectrum G hspec⟩

theorem exists_ordered_three_spectrum (h : numDistanceEigenvalues G = 3) :
    ∃ ρ s t : ℝ, t < s ∧ s < ρ ∧ spectrum ℝ (distMatrix G) = {ρ,s,t} := by
  obtain ⟨r,s,t,hrs,hrt,hst,hspec⟩ := Set.ncard_eq_three.mp h
  rw [hspec]
  rcases lt_or_gt_of_ne hrs with h | h <;> rcases lt_or_gt_of_ne hrt with k | k <;>
    rcases lt_or_gt_of_ne hst with l | l <;> first
    | exact ⟨r,s,t,by linarith,by linarith,rfl⟩
    | exact ⟨r,t,s,by linarith,by linarith,by ext; simp; tauto⟩
    | exact ⟨s,r,t,by linarith,by linarith,by ext; simp; tauto⟩
    | exact ⟨s,t,r,by linarith,by linarith,by ext; simp; tauto⟩
    | exact ⟨t,r,s,by linarith,by linarith,by ext; simp; tauto⟩
    | exact ⟨t,s,r,by linarith,by linarith,by ext; simp; tauto⟩

private theorem quadratic_factor (A : Matrix V V ℝ) (s t : ℝ) :
    (A-s • 1) * (A-t • 1) = A*A + (-(s+t)) • A + (s*t) • 1 := by
  simp [sub_mul, mul_sub, smul_sub, smul_smul, add_smul, mul_comm t s]
  abel

/-- A monic cubic in powers of the distance matrix when there are three distinct eigenvalues. -/
theorem exists_cubic_powers (h : numDistanceEigenvalues G = 3) :
    ∃ a b c : ℝ, distMatrix G ^ 3 + a • (distMatrix G ^ 2) + b • distMatrix G + c • 1 = 0 := by
  obtain ⟨r,s,t,_,_,_,_,hc⟩ := exists_cubic_annihilator G h
  refine ⟨-(r+s+t), r*s+r*t+s*t, -(r*s*t), ?_⟩
  rw [← hc, quadratic_factor]
  simp [pow_succ, add_mul, mul_sub, smul_add, smul_sub, smul_smul, add_smul, mul_add]
  module

/-- For a connected graph, the quadratic vanishing on its two smaller spectral values is the
outer product of a strictly positive Perron vector with itself. -/
theorem exists_rankOne_of_three_spectrum {ρ s t : ℝ} (hconn : G.Connected)
    (hs : s < ρ) (ht : t < ρ) (hspec : spectrum ℝ (distMatrix G) = {ρ,s,t}) :
    ∃ a : V → ℝ, (∀ i, 0 < a i) ∧ (distMatrix G) *ᵥ a = ρ • a ∧
      distMatrix G * distMatrix G + (-(s+t)) • distMatrix G + (s*t) • 1 = Matrix.vecMulVec a a := by
  classical
  let A := distMatrix G
  have hmax : IsGreatest (spectrum ℝ A) ρ := by
    change IsGreatest (spectrum ℝ (distMatrix G)) ρ
    rw [hspec]
    refine ⟨by simp, ?_⟩
    intro v hv
    simp only [Set.mem_insert_iff, Set.mem_singleton_iff] at hv
    rcases hv with rfl | rfl | rfl <;> linarith
  have hn (i j : V) : 0 ≤ A i j := by dsimp [A, distMatrix]; positivity
  have hpos (i j : V) (hij : i ≠ j) : 0 < A i j := by
    change 0 < (G.dist i j : ℝ)
    exact_mod_cast hconn.pos_dist_of_ne hij
  obtain ⟨p,hpp,hp,hsimple⟩ := exists_pos_top_eigenvector (distMatrix_isHermitian G) hn hpos hmax
  change A *ᵥ p = ρ • p at hp
  let Q := (A-s • 1)*(A-t • 1)
  have hQzero : (A-ρ • 1)*Q = 0 := by
    simpa only [Q, A, mul_assoc] using dist_cubic_of_spectrum G hspec
  have hAQ : A*Q = ρ • Q := by
    simpa [sub_mul, smul_mul_assoc, sub_eq_zero] using hQzero
  have hcol (j : V) : A *ᵥ (fun i => Q i j) = ρ • (fun i => Q i j) := by
    funext i
    exact congrFun (congrFun hAQ i) j
  choose c hc using fun j => hsimple _ (hcol j)
  have hentry (i j : V) : Q i j = c j * p i := congrFun (hc j) i
  have hAT : Aᵀ = A := by
    ext i j
    change (G.dist j i : ℝ) = (G.dist i j : ℝ)
    exact_mod_cast (G.dist_comm (u := j) (v := i))
  have hQT : Qᵀ = Q := by
    simp [Q, Matrix.transpose_mul, hAT, quadratic_factor, add_comm s t, mul_comm s t]
  let j₀ : V := Classical.choice hconn.nonempty
  let b := c j₀ / p j₀
  have hcoef (j : V) : c j = b * p j := by
    have hsym : Q j₀ j = Q j j₀ := congrFun (congrFun hQT j) j₀
    rw [hentry, hentry] at hsym
    dsimp [b]
    field_simp [ne_of_gt (hpp j₀)]
    linarith
  have hQp : Q *ᵥ p = ((ρ-s)*(ρ-t)) • p := by
    have hshift (u : ℝ) : (A-u • 1) *ᵥ p = (ρ-u) • p := by
      simp [Matrix.sub_mulVec, Matrix.smul_mulVec, hp, sub_smul]
    rw [show Q = (A-s • 1)*(A-t • 1) from rfl, ← Matrix.mulVec_mulVec,
      hshift, Matrix.mulVec_smul, hshift, smul_smul, mul_comm]
  have hb : 0 < b := by
    by_contra! h
    have hsum : (Q *ᵥ p) j₀ ≤ 0 := Finset.sum_nonpos fun j _ => by
      change Q j₀ j * p j ≤ 0
      rw [hentry, hcoef]
      exact mul_nonpos_of_nonpos_of_nonneg
        (mul_nonpos_of_nonpos_of_nonneg (mul_nonpos_of_nonpos_of_nonneg h (hpp j).le) (hpp j₀).le) (hpp j).le
    have hgt := mul_pos (mul_pos (sub_pos.mpr hs) (sub_pos.mpr ht)) (hpp j₀)
    rw [hQp] at hsum
    exact (not_lt_of_ge hsum) hgt
  let a := Real.sqrt b • p
  refine ⟨a, fun i => mul_pos (Real.sqrt_pos.mpr hb) (hpp i), ?_, ?_⟩
  · change A *ᵥ (Real.sqrt b • p) = ρ • (Real.sqrt b • p)
    rw [Matrix.mulVec_smul, hp, smul_comm]
  · rw [← quadratic_factor]
    change Q = Matrix.vecMulVec a a
    ext i j
    rw [hentry, hcoef]
    change b * p j * p i = (Real.sqrt b * p i) * (Real.sqrt b * p j)
    calc
      _ = (Real.sqrt b)^2 * p j * p i := by rw [Real.sq_sqrt hb.le]
      _ = _ := by ring

/-- Constant transmission makes the square of a three-eigenvalue distance matrix an affine
function of distance away from its diagonal. -/
theorem exists_affine_square_offdiag (hconn : G.Connected) (hthree : numDistanceEigenvalues G = 3)
    (hrows : ∀ x y : V, (∑ z, distMatrix G x z) = ∑ z, distMatrix G y z) :
    ∃ s t : ℝ, ∀ x y : V, x ≠ y → (distMatrix G ^ 2) x y = s * distMatrix G x y + t := by
  classical
  let j₀ : V := Classical.choice hconn.nonempty
  let R : ℝ := ∑ z, distMatrix G j₀ z
  obtain ⟨ρ,s,t,hst,hs,hspec⟩ := exists_ordered_three_spectrum G hthree
  obtain ⟨a,hpos,_,hQ⟩ := exists_rankOne_of_three_spectrum G hconn hs (hst.trans hs) hspec
  have hrows' : distMatrix G *ᵥ (1 : V → ℝ) = R • 1 := by
    funext i
    simpa [Matrix.mulVec, dotProduct, R] using hrows i j₀
  have hshift (u : ℝ) : (distMatrix G-u • 1) *ᵥ (1 : V → ℝ) = (R-u) • 1 := by
    rw [Matrix.sub_mulVec, hrows', Matrix.smul_mulVec, Matrix.one_mulVec, sub_smul]
  have hQ1 : Matrix.vecMulVec a a *ᵥ (1 : V → ℝ) = ((R-s)*(R-t)) • 1 := by
    rw [← hQ, ← quadratic_factor, ← Matrix.mulVec_mulVec, hshift, Matrix.mulVec_smul,
      hshift, smul_smul, mul_comm]
  have hsum : 0 < ∑ i, a i := Finset.sum_pos' (fun i _ => (hpos i).le)
    ⟨j₀, Finset.mem_univ _, hpos j₀⟩
  have ha (i : V) : a i = a j₀ := by
    have hi := congrFun hQ1 i
    have hj := congrFun hQ1 j₀
    simp [Matrix.mulVec, dotProduct, Matrix.vecMulVec_apply, ← Finset.mul_sum] at hi hj
    exact (mul_left_inj' hsum.ne').mp (hi.trans hj.symm)
  refine ⟨s+t,a j₀*a j₀,?_⟩
  intro i j hij
  have h := congrFun (congrFun hQ i) j
  simp [Matrix.vecMulVec_apply, hij, ha i, ha j, pow_two] at h ⊢
  linarith

omit [Fintype V] [DecidableEq V] in
private theorem sq_dist_sub_of_adj {x y : V} (h : G.Adj x y) (z : V) :
    (distMatrix G z x - distMatrix G z y) ^ 2 =
      1 - (if G.dist z x = G.dist z y then 1 else 0 : ℝ) := by
  by_cases he : G.dist z x = G.dist z y
  · simp [distMatrix, he]
  rw [ite_eq_right he]
  have hd := h.diff_dist_adj (u := z)
  rcases hd with hd | hd | hd
  · exact (he hd.symm).elim
  · simp [distMatrix, hd]
  · have heq : G.dist z x = G.dist z y + 1 := by omega
    simp [distMatrix, heq]

omit [DecidableEq V] in
theorem edgePairing_sq_of_adj {x y : V} (h : G.Adj x y) :
    edgePairing (distMatrix G * distMatrix G) x y x y =
      (Fintype.card V : ℝ) - (tieCount G x y : ℝ) := by
  classical
  calc
    _ = ∑ z, (distMatrix G z x - distMatrix G z y) ^ 2 := by
      simp only [edgePairing, Matrix.mul_apply, ← Finset.sum_sub_distrib, ← Finset.sum_add_distrib]
      apply Finset.sum_congr rfl
      intro z _
      dsimp [distMatrix]
      rw [G.dist_comm (u := x) (v := z), G.dist_comm (u := y) (v := z)]
      ring
    _ = _ := by
      simp_rw [sq_dist_sub_of_adj G h]
      rw [Finset.sum_sub_distrib]
      simp [tieCount]

/-- The adjacent-vertex case of the two-vertex identity for shortest-path distances. -/
theorem edgePairing_quadratic_of_adj {x y : V} (h : G.Adj x y) (s t : ℝ) :
    edgePairing (distMatrix G * distMatrix G + s • distMatrix G + t • 1) x y x y =
      (Fintype.card V : ℝ) - (tieCount G x y : ℝ) - 2 * s + 2 * t := by
  have hxy : x ≠ y := h.ne
  have hyx : y ≠ x := hxy.symm
  have ha : G.dist x y = 1 := SimpleGraph.dist_eq_one_iff_adj.mpr h
  have hb : G.dist y x = 1 := SimpleGraph.dist_eq_one_iff_adj.mpr h.symm
  have he := edgePairing_sq_of_adj G h
  unfold edgePairing at he ⊢
  simp [Matrix.add_apply, Matrix.smul_apply, distMatrix, hxy, hyx, ha, hb] at he ⊢
  linarith

/-- A rank-one quadratic in the distance matrix gives the edge identity. -/
theorem sq_perron_sub_of_rankOne {s t : ℝ} {a : V → ℝ}
    (hQ : distMatrix G * distMatrix G + s • distMatrix G + t • 1 = Matrix.vecMulVec a a)
    {x y : V} (h : G.Adj x y) :
    (a x - a y)^2 = (Fintype.card V : ℝ) - (tieCount G x y : ℝ) - 2*s + 2*t := by
  have he := edgePairing_quadratic_of_adj G h s t
  rw [hQ] at he
  calc
    _ = edgePairing (Matrix.vecMulVec a a) x y x y := by
      simp only [edgePairing, Matrix.vecMulVec_apply]
      ring
    _ = _ := he

/-- No product of consecutive integers with both factors positive is a square. -/
theorem consecutive_product_ne_square {H : ℤ} (hH : 2 ≤ H) (z : ℤ) :
    z^2 ≠ H*(H-1) := by
  intro hz
  have hsq : |z| * |z| = z^2 := by rw [← abs_mul, abs_of_nonneg (mul_self_nonneg z), pow_two]
  by_cases h : |z| < H
  · have hle : |z| ≤ H-1 := by omega
    nlinarith [mul_self_le_mul_self (abs_nonneg z) hle]
  · have hle : H ≤ |z| := by omega
    nlinarith [mul_self_le_mul_self (by omega : 0 ≤ H) hle]

private theorem quadratic_integral_entry (s t : ℤ) (x y : V) :
    ∃ k : ℤ, (distMatrix G * distMatrix G + (s:ℝ) • distMatrix G + (t:ℝ) • 1) x y = k := by
  refine ⟨(∑ z, (G.dist x z : ℤ) * (G.dist z y : ℤ)) +
    s * (G.dist x y : ℤ) + t * (if x = y then 1 else 0), ?_⟩
  by_cases h : x = y <;> simp [distMatrix, Matrix.mul_apply, h]

/-- An integral rank-one quadratic in the distance matrix rules out the three edge tie counts
zero, one and two occurring together in the same graph. -/
theorem no_three_tie_counts_of_rankOne {s t : ℤ} {a : V → ℝ}
    (hQ : distMatrix G * distMatrix G + (s:ℝ) • distMatrix G + (t:ℝ) • 1 = Matrix.vecMulVec a a)
    {x₀ y₀ x₁ y₁ x₂ y₂ : V}
    (h₀ : G.Adj x₀ y₀) (h₁ : G.Adj x₁ y₁) (h₂ : G.Adj x₂ y₂)
    (t₀ : tieCount G x₀ y₀ = 0) (t₁ : tieCount G x₁ y₁ = 1) (t₂ : tieCount G x₂ y₂ = 2) :
    False := by
  let H : ℤ := (Fintype.card V : ℤ) - 2*s + 2*t
  have hH : (H:ℝ) = (Fintype.card V : ℝ) - 2*(s:ℝ) + 2*(t:ℝ) := by simp [H]
  have e₀ := sq_perron_sub_of_rankOne G hQ h₀
  have e₁ := sq_perron_sub_of_rankOne G hQ h₁
  have e₂ := sq_perron_sub_of_rankOne G hQ h₂
  rw [t₀] at e₀
  rw [t₁] at e₁
  rw [t₂] at e₂
  norm_num at e₀ e₁ e₂
  have H₂ : 2 ≤ H := by
    have : (2:ℝ) ≤ H := by nlinarith [sq_nonneg (a x₂ - a y₂)]
    exact_mod_cast this
  have integral (x y : V) : ∃ k : ℤ, a x * a y = k := by
    obtain ⟨k, hk⟩ := quadratic_integral_entry G s t x y
    rw [hQ] at hk
    exact ⟨k, hk⟩
  obtain ⟨b, hb⟩ := integral x₀ x₁
  obtain ⟨c, hc⟩ := integral x₀ y₁
  obtain ⟨d, hd⟩ := integral y₀ x₁
  obtain ⟨e, he⟩ := integral y₀ y₁
  let z : ℤ := b-c-d+e
  have cross : (z:ℝ) = (a x₀-a y₀)*(a x₁-a y₁) := by
    simp only [z, Int.cast_add, Int.cast_sub, ← hb, ← hc, ← hd, ← he]
    ring
  have hz : (z:ℝ)^2 = (H:ℝ) * ((H:ℝ) - 1) := by
    rw [cross, mul_pow, e₀, e₁, hH]
    ring
  exact consecutive_product_ne_square H₂ z (by exact_mod_cast hz)

end Unicyclic
