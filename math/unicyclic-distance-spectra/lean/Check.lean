/-
FROZEN FILE. Do not edit.

The project is finished exactly when `lake build` succeeds with this file unchanged:
every target statement is proved, with no `sorry` and no axioms beyond the three
standard ones.
-/
import Unicyclic.Proof

example : Unicyclic.MainStatement := Unicyclic.main
example : Unicyclic.SanityC4 := Unicyclic.sanityC4
example : Unicyclic.SanityC5 := Unicyclic.sanityC5
example : Unicyclic.SanityCycle := Unicyclic.sanityCycle
example : Unicyclic.SanityPath := Unicyclic.sanityPath
example : Unicyclic.SanityC6 := Unicyclic.sanityC6

/-- info: 'Unicyclic.main' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Unicyclic.main

/-- info: 'Unicyclic.sanityC4' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Unicyclic.sanityC4

/-- info: 'Unicyclic.sanityC5' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Unicyclic.sanityC5

/-- info: 'Unicyclic.sanityC6' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Unicyclic.sanityC6
