/-
FROZEN FILE. Do not edit.

Definitions and target statements for:
"A connected unicyclic graph has exactly three distinct distance eigenvalues
if and only if it is the 4-cycle or the 5-cycle."
-/
import Mathlib

namespace Unicyclic

open SimpleGraph

/-- The distance matrix of a graph: the entry at `(u, v)` is the number of edges on a
shortest path from `u` to `v`. -/
noncomputable def distMatrix {V : Type} (G : SimpleGraph V) : Matrix V V ℝ :=
  fun u v => (G.dist u v : ℝ)

/-- A finite graph is unicyclic if it is connected and has exactly as many edges as
vertices. For connected graphs this is equivalent to containing exactly one cycle. -/
def IsUnicyclic {V : Type} [Fintype V] (G : SimpleGraph V) : Prop :=
  G.Connected ∧ G.edgeSet.ncard = Fintype.card V

/-- The number of distinct distance eigenvalues of `G`. The distance matrix is real and
symmetric, so all its eigenvalues are real and `spectrum ℝ` is the set of all of them. -/
noncomputable def numDistanceEigenvalues {V : Type} [Fintype V] [DecidableEq V]
    (G : SimpleGraph V) : ℕ :=
  (spectrum ℝ (distMatrix G)).ncard

/-- **Main statement.** A unicyclic graph has exactly three distinct distance eigenvalues
if and only if it is isomorphic to the 4-cycle or to the 5-cycle. -/
def MainStatement : Prop :=
  ∀ (V : Type) [Fintype V] [DecidableEq V] (G : SimpleGraph V), IsUnicyclic G →
    (numDistanceEigenvalues G = 3 ↔
      Nonempty (G ≃g cycleGraph 4) ∨ Nonempty (G ≃g cycleGraph 5))

/-! ### Sanity statements

These pin down the meaning of the definitions. If a definition above were wrong,
one of these would be false. -/

/-- The distance spectrum of the 4-cycle is `{4, 0, -2}`. -/
def SanityC4 : Prop :=
  spectrum ℝ (distMatrix (cycleGraph 4)) = {4, 0, -2}

/-- The distance spectrum of the 5-cycle is `{6, (-3 + √5) / 2, (-3 - √5) / 2}`. -/
def SanityC5 : Prop :=
  spectrum ℝ (distMatrix (cycleGraph 5)) = {6, (-3 + √5) / 2, (-3 - √5) / 2}

/-- Every cycle with at least three vertices is unicyclic. -/
def SanityCycle : Prop := ∀ n : ℕ, 3 ≤ n → IsUnicyclic (cycleGraph n)

/-- The path with three vertices is not unicyclic. -/
def SanityPath : Prop := ¬ IsUnicyclic (pathGraph 3)

/-- The 6-cycle is unicyclic but does not have three distance eigenvalues (it has four). -/
def SanityC6 : Prop := numDistanceEigenvalues (cycleGraph 6) = 4

end Unicyclic
