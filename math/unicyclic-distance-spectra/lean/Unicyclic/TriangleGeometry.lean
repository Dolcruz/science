import Unicyclic.GraphStructure

namespace Unicyclic.TriangleGeometry

open SimpleGraph

/-- A triangle with pendant leaves has a two-coordinate distance formula. The first
coordinate is zero on the triangle and one on its leaves. The second gives the triangle
vertex itself, or the parent of a leaf. -/
theorem triangle_coordinates {V : Type} [Fintype V] [DecidableEq V] {G : SimpleGraph V}
    [DecidableRel G.Adj] (h : IsUnicyclic G) (hs : GraphStructure.LeafSideCondition G)
    (f : Copy (cycleGraph 3) G) (hrange : ∀ v, v ∈ Set.range f ↔ G.degree v ≠ 1)
    (hl : ∃ v, G.degree v = 1) :
    ∃ c : V → Fin 2 × Fin 3,
      (∀ i, c (f i) = (0,i)) ∧ (∀ v i, c v = (0,i) → v = f i) ∧
      (∃ v, (c v).1 = 1) ∧
      (∀ v w, distMatrix G v w =
        ((c v).1.val : ℝ) + ((c w).1.val : ℝ) + (if (c v).2 = (c w).2 then 0 else 1) -
          (if v = w then 2 * ((c v).1.val : ℝ) else 0)) := by
  classical
  have hassign (v : V) : ∃ i, if G.degree v = 1 then G.Adj v (f i) else v = f i := by
    by_cases hv : G.degree v = 1
    · obtain ⟨u,hu,_⟩ := degree_eq_one_iff_existsUnique_adj.mp hv
      obtain ⟨i,hi⟩ := GraphStructure.leaf_parent_on_cycle h hs (m := 0) f hv hu
      exact ⟨i, by simpa [hv,hi] using hu⟩
    · obtain ⟨i,hi⟩ := (hrange v).mpr hv
      exact ⟨i, by simpa [hv] using hi.symm⟩
  choose idx hidx using hassign
  let tag (v : V) : Fin 2 := if G.degree v = 1 then 1 else 0
  let c (v : V) := (tag v, idx v)
  have hcore (i : Fin 3) : G.degree (f i) ≠ 1 := (hrange _).mp ⟨i,rfl⟩
  have hparent {v : V} (hv : G.degree v = 1) : G.Adj v (f (idx v)) := by simpa [hv] using hidx v
  have hvertex {v : V} (hv : G.degree v ≠ 1) : v = f (idx v) := by simpa [hv] using hidx v
  have huniq {v : V} (hv : G.degree v = 1) (z : V) (hz : G.Adj v z) : z = f (idx v) :=
    (degree_eq_one_iff_existsUnique_adj.mp hv).unique hz (hparent hv)
  have htag (v w : V) (hne : v ≠ w) : G.dist v w = G.dist (f (idx v)) w + (tag v).val := by
    by_cases hv : G.degree v = 1
    · simpa [tag,hv] using GraphStructure.dist_from_leaf h.1 (hparent hv) (huniq hv) hne
    · simpa only [tag,ite_eq_right hv,Fin.val_zero,Nat.add_zero] using
        congrArg (fun z => G.dist z w) (hvertex hv)
  have hright (i : Fin 3) (w : V) :
      G.dist (f i) w = G.dist (f i) (f (idx w)) + (tag w).val := by
    by_cases hw : G.degree w = 1
    · have hne : w ≠ f i := fun he => hcore i (he ▸ hw)
      simpa only [dist_comm (u := w) (v := f i), dist_comm (u := f (idx w)) (v := f i)]
        using htag w (f i) hne
    · simpa only [tag,ite_eq_right hw,Fin.val_zero,Nat.add_zero] using
        congrArg (fun z => G.dist (f i) z) (hvertex hw)
  have htriangle (i j : Fin 3) : G.dist (f i) (f j) = (if i = j then 0 else 1) := by
    by_cases hij : i = j
    · simp [hij]
    · rw [ite_eq_right hij, dist_eq_one_iff_adj]
      apply f.toHom.map_rel'
      simpa only [cycleGraph_three_eq_top, top_adj] using hij
  refine ⟨c, fun i => ?_, fun v i hv => ?_, ?_, fun v w => ?_⟩
  · have hi := f.injective (hvertex (hcore i))
    exact Prod.ext (by simp [c, tag, hcore i]) hi.symm
  · have hv₀ : tag v = 0 := congrArg Prod.fst hv
    have hvᵢ : idx v = i := congrArg Prod.snd hv
    have hdeg : G.degree v ≠ 1 := by
      intro he
      simp [tag,he] at hv₀
    exact (hvertex hdeg).trans (congrArg f hvᵢ)
  · obtain ⟨l,hl⟩ := hl
    exact ⟨l, by simp [c,tag,hl]⟩
  · by_cases he : v = w
    · subst w
      simp [distMatrix]
      ring
    · have hd := htag v w he
      rw [hright, htriangle] at hd
      change (G.dist v w : ℝ) = ((tag v).val : ℝ) + ((tag w).val : ℝ) +
        (if idx v = idx w then 0 else 1) - (if v = w then 2 * ((tag v).val : ℝ) else 0)
      rw [hd, ite_eq_right he]
      push_cast
      split_ifs <;> ring

end Unicyclic.TriangleGeometry
