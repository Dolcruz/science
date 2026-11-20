import IRT.Main

/-!
The main theorem is `IRT.main`. Besides the three standard axioms of Lean and Mathlib it
depends on one further axiom, produced by `native_decide` in `IRT.certificate`: the finite
check of all `313^3` digit triples is carried out by compiled code.
-/

/-- info: 'IRT.main' depends on axioms: [propext, Classical.choice, Quot.sound, IRT.certificate._native.native_decide.ax_1_1] -/
#guard_msgs in
#print axioms IRT.main
