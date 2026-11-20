import Unicyclic.GraphStructure
import Unicyclic.SpectralStructure

namespace Unicyclic

open Matrix

variable {V : Type} [Fintype V] [DecidableEq V] {G : SimpleGraph V}

omit [Fintype V] in
theorem distMatrix_leaf_col_sub (hc : G.Connected) {l p : V}
    (ha : G.Adj l p) (hu : ∀ w, G.Adj l w → w = p) (z : V) :
    distMatrix G z l - distMatrix G z p = 1 - (if z = l then 2 else 0 : ℝ) := by
  by_cases h : z = l
  · subst z
    simp [distMatrix, SimpleGraph.dist_eq_one_iff_adj.mpr ha]
    norm_num
  · have hd := GraphStructure.dist_from_leaf hc ha hu (Ne.symm h)
    simp [distMatrix, h, G.dist_comm (u := z) (v := l), G.dist_comm (u := z) (v := p), hd]

/-- A leaf isolates one term in a difference of columns of the squared distance matrix. -/
theorem distMatrix_sq_leaf_col_sub (hc : G.Connected) {l p : V}
    (ha : G.Adj l p) (hu : ∀ w, G.Adj l w → w = p) (z : V) :
    (distMatrix G * distMatrix G) z l - (distMatrix G * distMatrix G) z p =
      (∑ w, distMatrix G z w) - 2 * distMatrix G z l := by
  classical
  calc
    _ = ∑ w, distMatrix G z w * (distMatrix G w l - distMatrix G w p) := by
      simp [Matrix.mul_apply, mul_sub, Finset.sum_sub_distrib]
    _ = ∑ w, (distMatrix G z w - if w = l then 2*distMatrix G z w else 0) := by
      apply Finset.sum_congr rfl
      intro w _
      rw [distMatrix_leaf_col_sub hc ha hu]
      by_cases h : w = l <;> simp [h]; ring
    _ = _ := by simp [Finset.sum_sub_distrib]

/-- On a disjoint pair the terms in the distance matrix and identity vanish in a mixed
leaf-edge pairing. Only the square term remains, and every one of its entries is integral. -/
theorem integral_mixed_leaf_edge {l p x y : V} (hc : G.Connected)
    (ha : G.Adj l p) (hu : ∀ w, G.Adj l w → w = p)
    (hlx : l ≠ x) (hly : l ≠ y) (hpx : p ≠ x) (hpy : p ≠ y) (s t : ℝ) :
    ∃ k : ℤ, edgePairing (distMatrix G * distMatrix G + s • distMatrix G + t • 1) x y l p = (k : ℝ) := by
  refine ⟨(∑ w, (G.dist x w : ℤ) * (G.dist w l : ℤ)) -
    (∑ w, (G.dist x w : ℤ) * (G.dist w p : ℤ)) -
    (∑ w, (G.dist y w : ℤ) * (G.dist w l : ℤ)) +
    (∑ w, (G.dist y w : ℤ) * (G.dist w p : ℤ)), ?_⟩
  have hdx := distMatrix_leaf_col_sub hc ha hu x
  have hdy := distMatrix_leaf_col_sub hc ha hu y
  simp [hlx.symm, hly.symm] at hdx hdy
  unfold edgePairing
  simp [Matrix.mul_apply, hlx.symm,hly.symm,hpx.symm,hpy.symm, distMatrix] at hdx hdy ⊢
  linear_combination s * hdx - s * hdy

/-- A tied Perron edge with at least two distance ties fixes the squared gap on the leaf edge.
An additional disjoint one-tie edge would give an impossible integral mixed pairing. -/
theorem no_one_tie_disjoint_leaf_of_equal_perron_edge {l p x y u v : V}
    {a : V → ℝ} {s t : ℝ} (hc : G.Connected)
    (hl : G.Adj l p) (hu : ∀ w, G.Adj l w → w = p)
    (hxy : G.Adj x y) (huv : G.Adj u v)
    (hlx : l ≠ x) (hly : l ≠ y) (hpx : p ≠ x) (hpy : p ≠ y)
    (hQ : distMatrix G * distMatrix G + s • distMatrix G + t • 1 = Matrix.vecMulVec a a)
    (h₀ : tieCount G l p = 0) (h₁ : tieCount G x y = 1) (h₂ : 2 ≤ tieCount G u v)
    (hgap : a u = a v) : False := by
  have e₀ := sq_perron_sub_of_rankOne G hQ hl
  have e₁ := sq_perron_sub_of_rankOne G hQ hxy
  have e₂ := sq_perron_sub_of_rankOne G hQ huv
  rw [h₀] at e₀
  rw [h₁] at e₁
  rw [hgap, sub_self] at e₂
  norm_num at e₀ e₁ e₂
  let H : ℤ := tieCount G u v
  have hf : (H:ℝ) = (tieCount G u v : ℝ) := by simp [H]
  have g₀ : (a l - a p)^2 = (H:ℝ) := by linarith
  have g₁ : (a x - a y)^2 = (H:ℝ) - 1 := by linarith
  obtain ⟨z,hz⟩ := integral_mixed_leaf_edge hc hl hu hlx hly hpx hpy s t
  rw [hQ] at hz
  simp only [edgePairing, Matrix.vecMulVec_apply] at hz
  have hprod : (z : ℝ) = (a l-a p)*(a x-a y) := by linarith only [hz]
  have hsq : (z : ℝ)^2 = (H:ℝ)*((H:ℝ)-1) := by rw [hprod, mul_pow, g₀, g₁]
  exact consecutive_product_ne_square (H := H) (by dsimp [H]; exact_mod_cast h₂) z (by exact_mod_cast hsq)

/-- If a quadratic rank-one certificate gives equal signed gaps along two leaf edges,
all vertices outside their endpoints have identical distances to the two parents. -/
theorem dist_parents_eq_of_leaf_gap_eq {l p m q z : V} {a : V → ℝ} {s t : ℝ}
    (hc : G.Connected) (hl : G.Adj l p) (hu : ∀ w, G.Adj l w → w = p)
    (hm : G.Adj m q) (hv : ∀ w, G.Adj m w → w = q)
    (hQ : distMatrix G * distMatrix G + s • distMatrix G + t • 1 = Matrix.vecMulVec a a)
    (hgap : a l-a p = a m-a q) (hzl : z ≠ l) (hzp : z ≠ p) (hzm : z ≠ m) (hzq : z ≠ q) :
    G.dist z p = G.dist z q := by
  have hcol (i : V) := congrFun (congrFun hQ z) i
  have hsame : a z * a l-a z * a p = a z * a m-a z * a q := by
    linear_combination a z * hgap
  have hl₂ := distMatrix_sq_leaf_col_sub hc hl hu z
  have hm₂ := distMatrix_sq_leaf_col_sub hc hm hv z
  have hl₁ := distMatrix_leaf_col_sub hc hl hu z
  have hm₁ := distMatrix_leaf_col_sub hc hm hv z
  simp [hzl,hzm] at hl₁ hm₁
  have hlp := hcol l
  have hpp := hcol p
  have hmq := hcol m
  have hqq := hcol q
  simp [Matrix.vecMulVec_apply,hzl,hzp,hzm,hzq] at hlp hpp hmq hqq
  have he : distMatrix G z p = distMatrix G z q := by
    linear_combination -(hlp-hpp-hmq+hqq+hsame-hl₂+hm₂-s*hl₁+s*hm₁)/2 - hl₁ + hm₁
  exact_mod_cast (show (G.dist z p : ℝ) = (G.dist z q : ℝ) from he)

end Unicyclic
