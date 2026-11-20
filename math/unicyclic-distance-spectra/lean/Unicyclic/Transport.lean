import Unicyclic.Statement

namespace Unicyclic

open SimpleGraph

/-- Relabeling vertices preserves the entire distance spectrum. -/
theorem spectrum_distMatrix_iso {V W : Type} [Fintype V] [Fintype W]
    [DecidableEq V] [DecidableEq W] {G : SimpleGraph V} {H : SimpleGraph W}
    (e : G ≃g H) : spectrum ℝ (distMatrix G) = spectrum ℝ (distMatrix H) := by
  let f := Matrix.reindexAlgEquiv ℝ ℝ e.toEquiv
  have h : f (distMatrix G) = distMatrix H := by
    ext i j
    obtain ⟨x, rfl⟩ := e.surjective i
    obtain ⟨y, rfl⟩ := e.surjective j
    change (G.dist (e.symm (e x)) (e.symm (e y)) : ℝ) = (H.dist (e x) (e y) : ℝ)
    simp [e.dist_eq]
  rw [← h]
  exact (AlgEquiv.spectrum_eq f (distMatrix G)).symm

theorem numDistanceEigenvalues_iso {V W : Type} [Fintype V] [Fintype W]
    [DecidableEq V] [DecidableEq W] {G : SimpleGraph V} {H : SimpleGraph W}
    (e : G ≃g H) : numDistanceEigenvalues G = numDistanceEigenvalues H :=
  congrArg Set.ncard (spectrum_distMatrix_iso e)

end Unicyclic
