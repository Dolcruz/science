import Unicyclic.Statement

namespace Unicyclic.GraphStructure

open SimpleGraph

/-- No finite tree can have the same number of edges and vertices. -/
theorem not_unicyclic_of_isTree {V : Type} [Fintype V] {G : SimpleGraph V}
    (hT : G.IsTree) : ¬ IsUnicyclic G := by
  intro h
  have hcount := hT.ncard_edgeSet_add_one
  rw [Nat.card_eq_fintype_card, h.2] at hcount
  omega

theorem sanityPath : SanityPath := by
  exact not_unicyclic_of_isTree (isTree_pathGraph_add_one 2)

/-- In a unicyclic graph the degree sum is twice the number of vertices. -/
theorem sum_degrees_of_unicyclic {V : Type} [Fintype V] (G : SimpleGraph V)
    [DecidableRel G.Adj] (h : IsUnicyclic G) :
    ∑ v, G.degree v = 2 * Fintype.card V := by
  classical
  have he : G.edgeFinset.card = G.edgeSet.ncard := by
    rw [← G.coe_edgeFinset, Set.ncard_coe_finset]
  rw [G.sum_degrees_eq_twice_card_edges, he, h.2]

theorem sanityCycle : SanityCycle := by
  intro n hn
  obtain ⟨m, rfl⟩ : ∃ m, n = m + 3 := ⟨n - 3, by omega⟩
  refine ⟨connected_cycleGraph_add_one, ?_⟩
  have hsum := (cycleGraph (m + 3)).sum_degrees_eq_twice_card_edges
  simp only [cycleGraph_degree_three_le, Finset.sum_const, Finset.card_univ, Fintype.card_fin,
    smul_eq_mul] at hsum
  rw [← (cycleGraph (m + 3)).coe_edgeFinset, Set.ncard_coe_finset, Fintype.card_fin]
  omega

/-- A graph satisfying the numerical definition contains a simple cycle. -/
theorem exists_cycle_of_unicyclic {V : Type} [Fintype V] {G : SimpleGraph V}
    (h : IsUnicyclic G) : ∃ (v : V) (p : G.Walk v v), p.IsCycle := by
  apply not_isAcyclic_iff_exists_isCycle.mp
  exact fun hA => not_unicyclic_of_isTree ⟨h.1, hA⟩ h

/-- If a connected unicyclic graph has no leaves, all its degrees are exactly two. -/
theorem degree_eq_two_of_no_leaf {V : Type} [Fintype V] [Nontrivial V]
    {G : SimpleGraph V} [DecidableRel G.Adj] (h : IsUnicyclic G)
    (hn : ∀ v, G.degree v ≠ 1) (v : V) : G.degree v = 2 := by
  have htwo (w : V) : 2 ≤ G.degree w := by
    have hp := h.1.preconnected.degree_pos_of_nontrivial w
    have hne := hn w
    omega
  have hsum : (∑ _w : V, (2 : ℕ)) = ∑ w, G.degree w := by
    rw [sum_degrees_of_unicyclic G h]
    simp [Nat.mul_comm]
  exact ((Finset.sum_eq_sum_iff_of_le (fun w _ => htwo w)).mp hsum v (Finset.mem_univ v)).symm

/-- Removing a leaf from a unicyclic graph preserves unicyclicity. -/
theorem unicyclic_induce_compl_leaf {V : Type} [Fintype V] [DecidableEq V]
    {G : SimpleGraph V} [DecidableRel G.Adj] (h : IsUnicyclic G) {l : V}
    (hl : G.degree l = 1) : IsUnicyclic (G.induce ({l}ᶜ : Set V)) := by
  refine ⟨h.1.induce_compl_singleton_of_degree_eq_one hl, ?_⟩
  classical
  rw [← (G.induce ({l}ᶜ : Set V)).coe_edgeFinset, Set.ncard_coe_finset,
    G.card_edgeFinset_induce_compl_singleton, G.card_edgeFinset_deleteIncidenceSet, hl,
    Fintype.card_compl_set, @Fintype.card_unique ({l} : Set V)]
  have he : G.edgeFinset.card = G.edgeSet.ncard := by
    rw [← G.coe_edgeFinset, Set.ncard_coe_finset]
  rw [he, h.2]

/-- Every shortest path leaving a leaf starts with its unique incident edge. -/
theorem dist_from_leaf {V : Type} {G : SimpleGraph V} (hc : G.Connected) {l u z : V}
    (hadj : G.Adj l u) (huniq : ∀ w, G.Adj l w → w = u) (hz : l ≠ z) :
    G.dist l z = G.dist u z + 1 := by
  obtain ⟨p, hp⟩ := hc.exists_walk_length_eq_dist l z
  have hnil : ¬ p.Nil := Walk.not_nil_of_ne hz
  have hlen : 0 < p.length := Walk.not_nil_iff_lt_length.mp hnil
  have hs : p.snd = u := huniq _ (Walk.adj_snd hnil)
  have hlo := dist_le p.tail
  rw [Walk.length_tail, hp, hs] at hlo
  have hhi := hc.dist_triangle (u := l) (v := u) (w := z)
  rw [dist_eq_one_iff_adj.mpr hadj] at hhi
  omega

/-- Removing any edge of a cycle in a unicyclic graph leaves a spanning tree. -/
theorem isTree_delete_cycle_edge {V : Type} [Fintype V] {G : SimpleGraph V}
    (h : IsUnicyclic G) {v : V} {p : G.Walk v v} (hp : p.IsCycle)
    {e : Sym2 V} (he : e ∈ p.edges) : (G.deleteEdges {e}).IsTree := by
  have hem := p.edges_subset_edgeSet he
  apply isTree_iff_connected_and_card.mpr
  refine ⟨h.1.preconnected.connected_deleteEdges_of_not_isBridge
    (fun hb => hb.notMem_edges_of_isCycle hp he), ?_⟩
  rw [Nat.card_coe_set_eq, edgeSet_deleteEdges, Set.ncard_sdiff_singleton_add_one hem,
    Nat.card_eq_fintype_card, h.2]

/-- All simple cycles in a unicyclic graph have the same edge set. -/
theorem mem_cycle_edges_iff {V : Type} [Fintype V] {G : SimpleGraph V} (h : IsUnicyclic G)
    {v w : V} {p : G.Walk v v} {q : G.Walk w w} (hp : p.IsCycle) (hq : q.IsCycle)
    (e : Sym2 V) : e ∈ p.edges ↔ e ∈ q.edges := by
  suffices transfer_mem : ∀ {a b : V} {P : G.Walk a a} {Q : G.Walk b b},
      P.IsCycle → Q.IsCycle → e ∈ P.edges → e ∈ Q.edges from
    ⟨transfer_mem hp hq, transfer_mem hq hp⟩
  intro a b P Q hP hQ he
  by_contra hmissing
  have hsub (f : Sym2 V) (hf : f ∈ Q.edges) : f ∈ (G.deleteEdges {e}).edgeSet := by
    rw [edgeSet_deleteEdges]
    exact ⟨Q.edges_subset_edgeSet hf, fun hfe => hmissing (Set.mem_singleton_iff.mp hfe ▸ hf)⟩
  exact (isTree_delete_cycle_edge h hP he).isAcyclic (Q.transfer _ hsub) (hQ.transfer _)

/-- A copy that preserves every vertex degree exhausts a connected target. -/
private theorem iso_of_copy_preserving_degree {W V : Type} [Fintype W] [Fintype V] [Nonempty W]
    {H : SimpleGraph W} {G : SimpleGraph V} [DecidableRel H.Adj] [DecidableRel G.Adj]
    (f : Copy H G) (hc : G.Connected) (hd : ∀ w, H.degree w = G.degree (f w)) :
    Nonempty (H ≃g G) := by
  classical
  have lift (w : W) (z : V) (ha : G.Adj (f w) z) : ∃ b, H.Adj w b ∧ f b = z := by
    have hh : Fintype.card (H.neighborSet w) = Fintype.card (G.neighborSet (f w)) := by
      simpa only [card_neighborSet_eq_degree] using hd w
    have honto := ((Fintype.bijective_iff_injective_and_card (f.mapNeighborSet w)).mpr
      ⟨(f.mapNeighborSet w).injective, hh⟩).2
    obtain ⟨⟨b, hb⟩, hfb⟩ := honto ⟨z, ha⟩
    exact ⟨b, hb, congrArg Subtype.val hfb⟩
  have walk {v w : V} (p : G.Walk v w) : (∃ a, f a = v) → ∃ b, f b = w := by
    induction p with
    | nil => exact id
    | cons h _ ih =>
      rintro ⟨a, rfl⟩
      obtain ⟨b, _, hb⟩ := lift a _ h
      exact ih ⟨b,hb⟩
  let a : W := Classical.choice inferInstance
  have onto (z : V) : ∃ b, f b = z := (hc.preconnected (f a) z).elim fun p => walk p ⟨a, rfl⟩
  refine ⟨⟨Equiv.ofBijective f ⟨f.injective, onto⟩, ?_⟩⟩
  intro x y
  change G.Adj (f x) (f y) ↔ H.Adj x y
  refine ⟨fun ha => ?_, f.toHom.map_rel'⟩
  obtain ⟨b, hb, he⟩ := lift x _ ha
  exact f.injective he ▸ hb

/-- A unicyclic graph with no leaves is isomorphic to a bare cycle. -/
theorem iso_cycle_of_no_leaf {V : Type} [Fintype V] [Nontrivial V]
    {G : SimpleGraph V} [DecidableRel G.Adj] (h : IsUnicyclic G)
    (hn : ∀ v, G.degree v ≠ 1) :
    ∃ n, 3 ≤ n ∧ Nonempty (G ≃g cycleGraph n) := by
  classical
  obtain ⟨v, p, hp⟩ := exists_cycle_of_unicyclic h
  have hlen : 3 ≤ p.length := hp.three_le_length
  obtain ⟨m, hm⟩ : ∃ m, p.length = m + 3 := ⟨p.length - 3, by omega⟩
  obtain ⟨f⟩ := (cycleGraph_isContained_iff (n := m + 3) (by omega)).mpr ⟨v,p,hp,hm⟩
  obtain ⟨e⟩ := iso_of_copy_preserving_degree f h.1 fun w => by
    rw [cycleGraph_degree_three_le, degree_eq_two_of_no_leaf h hn]
  exact ⟨m + 3, by omega, ⟨e.symm⟩⟩

/-- Every edge outside a specified cycle is a bridge. -/
theorem isBridge_of_notMem_cycle {V : Type} [Fintype V] {G : SimpleGraph V}
    (h : IsUnicyclic G) {a : V} {p : G.Walk a a} (hp : p.IsCycle) {e : Sym2 V}
    (hmem : e ∈ G.edgeSet) (he : e ∉ p.edges) : G.IsBridge e :=
  (isBridge_iff_forall_cycle_notMem hmem).mpr fun _ _ hq =>
    fun hqe => he ((mem_cycle_edges_iff h hq hp e).mp hqe)

/-- A bridge has no equidistant vertex. -/
theorem dist_ne_of_isBridge {V : Type} {G : SimpleGraph V} (hc : G.Connected) {u v : V}
    (hb : G.IsBridge s(u,v)) (z : V) : G.dist z u ≠ G.dist z v := by
  intro h
  have avoid {a b : V} (heq : G.dist a z = G.dist b z) :
      (G.deleteEdges {s(a,b)}).Reachable a z := by
    obtain ⟨p, hp, hlen⟩ := hc.exists_path_of_dist a z
    apply reachable_deleteEdges_iff_exists_walk.mpr
    refine ⟨p, fun hmem => ?_⟩
    obtain ⟨hbs,hn⟩ := hp.mk_start_mem_edges_iff.mp hmem
    have hpos := Walk.not_nil_iff_lt_length.mp hn
    have hh := dist_le p.tail
    rw [Walk.length_tail, ← hbs, hlen] at hh
    omega
  have heq : G.dist u z = G.dist v z := by simpa only [dist_comm (u := z)] using h
  have h₁ := avoid heq
  have h₂ := avoid heq.symm
  rw [Sym2.eq_swap] at h₂
  exact (isBridge_iff.mp hb) (h₁.trans h₂.symm)

/-- In a bipartite graph, distances from a fixed vertex to adjacent endpoints differ. -/
theorem dist_ne_of_bipartite {V : Type} {G : SimpleGraph V} (hc : G.Connected) (hb : G.IsBipartite)
    {u v : V} (ha : G.Adj u v) (z : V) : G.dist z u ≠ G.dist z v := by
  intro heq
  obtain ⟨p,hp⟩ := hc.exists_walk_length_eq_dist z u
  obtain ⟨q,hq⟩ := hc.exists_walk_length_eq_dist z v
  obtain ⟨r,hr⟩ := isBipartite_iff_forall_walk_even_length.mp hb z ((p.concat ha).append q.reverse)
  simp only [Walk.length_append, Walk.length_concat, Walk.length_reverse, hp, hq, heq] at hr
  omega

/-- A connected subgraph containing a cycle inherits unicyclicity. -/
theorem unicyclic_of_containing_cycle {W V : Type} [Fintype W] [Fintype V]
    {H : SimpleGraph W} {G : SimpleGraph V} (f : Copy H G) (h : IsUnicyclic G)
    (hH : H.Connected) {w : W} {p : H.Walk w w} (hp : p.IsCycle) : IsUnicyclic H := by
  let e := s(w,p.snd)
  have hep : e ∈ p.edges := Walk.mk_start_snd_mem_edges hp.not_nil
  have he' : Sym2.map f e ∈ (p.map f.toHom).edges := by
    rw [Walk.edges_map]
    exact List.mem_map.mpr ⟨e,hep,rfl⟩
  have hT := isTree_delete_cycle_edge h (hp.map f.injective) he'
  let g : H.deleteEdges {e} →g G.deleteEdges {Sym2.map f e} :=
    ⟨f, fun {x y} hxy => by
      obtain ⟨ha,hn⟩ := deleteEdges_adj.mp hxy
      refine deleteEdges_adj.mpr ⟨f.toHom.map_rel' ha, fun heq => hn ?_⟩
      exact (Sym2.map.injective f.injective) heq⟩
  have ht : (H.deleteEdges {e}).IsTree :=
    ⟨hH.preconnected.connected_deleteEdges_of_not_isBridge (fun hb => hb.notMem_edges_of_isCycle hp hep),
      hT.isAcyclic.comap g f.injective⟩
  refine ⟨hH, ?_⟩
  have hc := ht.ncard_edgeSet_add_one
  rwa [edgeSet_deleteEdges, Set.ncard_sdiff_singleton_add_one (p.edges_subset_edgeSet hep),
    Nat.card_eq_fintype_card] at hc

/-- Every vertex reachable from a vertex in an adjacency-closed set stays in the set. -/
private theorem forall_of_adj_closed {V : Type} {G : SimpleGraph V} (hc : G.Connected)
    (P : V → Prop) {a : V} (ha : P a) (hstep : ∀ {v w}, P v → G.Adj v w → P w) (v : V) : P v := by
  have hw {i j : V} (p : G.Walk i j) : P i → P j := by
    induction p with
    | nil => exact id
    | cons hadj _ ih => exact fun h => ih (hstep h hadj)
  exact (hc.preconnected a v).elim fun p => hw p ha

/-- Off the image of a cycle copy, every incident edge is a bridge. -/
private theorem bridge_off_cycle {V : Type} [Fintype V] {G : SimpleGraph V} (h : IsUnicyclic G)
    {m : ℕ} (f : Copy (cycleGraph (m+3)) G) {u x : V} (hu : u ∉ Set.range f) (hx : G.Adj u x) :
    G.IsBridge s(u,x) := by
  let c := (cycleGraph.cycle m).map f.toHom
  have hc : c.IsCycle := cycleGraph.isCycle_cycle.map f.injective
  refine isBridge_of_notMem_cycle h hc hx (fun he => hu ?_)
  have hv := c.fst_mem_support_of_mem_edges he
  obtain ⟨i,_,hi⟩ := List.mem_map.mp (Walk.support_map .. ▸ hv)
  exact ⟨i,hi⟩

/-- The metric obstruction obtained at a leaf and its neighbor. -/
def LeafSideCondition {V : Type} [Fintype V] (G : SimpleGraph V) [DecidableRel G.Adj] : Prop :=
  ∀ {l u x z : V}, G.degree l = 1 → G.Adj l u → G.Adj u x → x ≠ l →
    (∀ w, G.dist w u ≠ G.dist w x) → G.dist z x < G.dist z u → z = x

private theorem two_le_degree_of_cycle_copy {V : Type} [Fintype V] {G : SimpleGraph V}
    [DecidableRel G.Adj] {m : ℕ} (f : Copy (cycleGraph (m+3)) G) (i : Fin (m+3)) :
    2 ≤ G.degree (f i) := by
  have hh := Fintype.card_le_of_injective _ (f.mapNeighborSet i).injective
  simpa only [card_neighborSet_eq_degree, cycleGraph_degree_three_le] using hh


/-- In a unicyclic graph satisfying the leaf metric obstruction, some edge incident to a
leaf's parent must have an equidistant vertex. -/
theorem exists_tied_edge_at_leaf_parent {V : Type} [Fintype V] {G : SimpleGraph V}
    [DecidableRel G.Adj] (h : IsUnicyclic G) (hs : LeafSideCondition G) {m : ℕ}
    (f : Copy (cycleGraph (m+3)) G) {l u : V} (hl : G.degree l = 1) (hlu : G.Adj l u) :
    ∃ x, G.Adj u x ∧ ∃ z, G.dist z u = G.dist z x := by
  by_contra! hn
  have leaf {x : V} (hx : G.Adj u x) : G.degree x = 1 := by
    by_cases heq : x = l
    · exact heq ▸ hl
    have hd := hn x hx
    apply degree_eq_one_iff_existsUnique_adj.mpr
    refine ⟨u, hx.symm, fun z hz => ?_⟩
    by_contra hzu
    have hpos : G.dist z u ≠ 0 := dist_ne_zero_iff_ne_and_reachable.mpr ⟨hzu,h.1.preconnected _ _⟩
    have hone : G.dist z x = 1 := dist_eq_one_iff_adj.mpr hz.symm
    have hdiff := hd z
    have hlt : G.dist z x < G.dist z u := by omega
    exact hz.ne (hs hl hlu hx heq hd hlt).symm
  have hclose {a b : V} (ha : a = u ∨ G.Adj u a) (hab : G.Adj a b) :
      b = u ∨ G.Adj u b := by
    obtain rfl | ha := ha
    · exact Or.inr hab
    · exact Or.inl ((degree_eq_one_iff_existsUnique_adj.mp (leaf ha)).unique hab ha.symm)
  have hsingle (i : Fin (m+3)) : f i = u := by
    have hr := forall_of_adj_closed h.1 (fun z => z = u ∨ G.Adj u z) (Or.inl rfl) hclose (f i)
    obtain heq | hadj := hr
    · exact heq
    · have hh := leaf hadj
      have hd := two_le_degree_of_cycle_copy f i
      omega
  have he := f.injective ((hsingle 0).trans (hsingle 1).symm)
  exact (Fin.zero_ne_one (n := m+1)) he

/-- Under the metric obstruction, the parent of every leaf lies on the cycle. -/
theorem leaf_parent_on_cycle {V : Type} [Fintype V] {G : SimpleGraph V} [DecidableRel G.Adj]
    (h : IsUnicyclic G) (hs : LeafSideCondition G) {m : ℕ} (f : Copy (cycleGraph (m+3)) G)
    {l u : V} (hl : G.degree l = 1) (hlu : G.Adj l u) : u ∈ Set.range f := by
  by_contra hu
  obtain ⟨x,hx,z,hz⟩ := exists_tied_edge_at_leaf_parent h hs f hl hlu
  exact dist_ne_of_isBridge h.1 (bridge_off_cycle h f hu hx) z hz

/-- A bipartite unicyclic graph satisfying the leaf metric condition has no leaves. -/
theorem no_bipartite_leaf {V : Type} [Fintype V] {G : SimpleGraph V} [DecidableRel G.Adj]
    (h : IsUnicyclic G) (hs : LeafSideCondition G) (hbi : G.IsBipartite) (l : V) :
    G.degree l ≠ 1 := by
  intro hl
  obtain ⟨u,hu,_⟩ := degree_eq_one_iff_existsUnique_adj.mp hl
  obtain ⟨a,p,hp⟩ := exists_cycle_of_unicyclic h
  have hlen := hp.three_le_length
  obtain ⟨m,hm⟩ : ∃ m, p.length = m+3 := ⟨p.length-3, by omega⟩
  obtain ⟨f⟩ := (cycleGraph_isContained_iff (n := m+3) (by omega)).mpr ⟨a,p,hp,hm⟩
  obtain ⟨x,hx,z,hz⟩ := exists_tied_edge_at_leaf_parent h hs f hl hu
  exact dist_ne_of_bipartite h.1 hbi hx z hz

/-- Removing vertices with at most one neighbor preserves distances between retained vertices. -/
theorem dist_induce_of_omitted_leaves {V : Type} {G : SimpleGraph V} (hc : G.Connected)
    (s : Set V) (hs : ∀ v ∉ s, (G.neighborSet v).Subsingleton) (x y : s) :
    G.dist x.val y.val = (G.induce s).dist x y := by
  have hpconn := hc.preconnected.induce_of_degree_eq_one hs
  refine le_antisymm ((Copy.induce G s).toHom.dist_le (hpconn x y)) ?_
  obtain ⟨p,hp,hlen⟩ := hc.exists_path_of_dist x.val y.val
  have hstay : ∀ z ∈ p.support, z ∈ s := by
    intro z hz
    by_contra hzs
    exact hp.isTrail.notMem_support_of_subsingleton_neighborSet (x := z)
      (fun he => hzs (he.symm ▸ x.property)) (fun he => hzs (he.symm ▸ y.property)) (hs z hzs) hz
  have hdist := dist_le (p.induce s hstay)
  simpa only [Walk.length_induce, hlen] using hdist

/-- The vertices of degree different from one induce an isometric cycle, provided that
every leaf's parent satisfies the metric condition. -/
theorem cycle_leaves_decomposition {V : Type} [Fintype V] {G : SimpleGraph V} [DecidableRel G.Adj]
    (h : IsUnicyclic G) (hs : LeafSideCondition G) :
    ∃ (m : ℕ) (f : Copy (cycleGraph (m+3)) G),
      (∀ v, v ∈ Set.range f ↔ G.degree v ≠ 1) ∧
      (∀ i j, G.dist (f i) (f j) = (cycleGraph (m+3)).dist i j) := by
  classical
  obtain ⟨a,p,hp⟩ := exists_cycle_of_unicyclic h
  have hlen : 3 ≤ p.length := hp.three_le_length
  obtain ⟨m,hm⟩ : ∃ m, p.length = m + 3 := ⟨p.length - 3, by omega⟩
  obtain ⟨f⟩ := (cycleGraph_isContained_iff (n := m+3) (by omega)).mpr ⟨a,p,hp,hm⟩
  let s : Set V := {v | G.degree v ≠ 1}
  have hsub (i : Fin (m+3)) : f i ∈ s := by
    have hh := two_le_degree_of_cycle_copy f i
    change G.degree (f i) ≠ 1
    omega
  let F : Copy (cycleGraph (m+3)) (G.induce s) :=
    ⟨⟨fun i => ⟨f i, hsub i⟩, fun hij => f.toHom.map_rel' hij⟩,
      fun _ _ he => f.injective (congrArg Subtype.val he)⟩
  let : Nonempty s := ⟨F 0⟩
  have hremoved (v : V) (hv : v ∉ s) : (G.neighborSet v).Subsingleton := by
    have hh : G.degree v = 1 := Classical.not_not.mp hv
    simp [← Set.ncard_le_one_iff_subsingleton, hh]
  have hc : (G.induce s).Connected := ⟨h.1.preconnected.induce_of_degree_eq_one hremoved⟩
  have hU : IsUnicyclic (G.induce s) := unicyclic_of_containing_cycle (Copy.induce G s) h hc
    (cycleGraph.isCycle_cycle.map (f := F.toHom) F.injective)
  have hmin (y : s) : (G.induce s).degree y ≠ 1 := by
    by_cases hy : y.val ∈ Set.range f
    · obtain ⟨i,hi⟩ := hy
      have he : F i = y := Subtype.ext hi
      have hh := two_le_degree_of_cycle_copy F i
      rw [he] at hh
      omega
    · have hneigh : G.neighborSet y ⊆ s := by
        intro z hz
        exact fun hleaf => hy (leaf_parent_on_cycle h hs f hleaf (show G.Adj y z from hz).symm)
      rw [degree_induce_of_neighborSet_subset hneigh]
      exact y.property
  have := two_le_degree_of_cycle_copy F 0
  let : Nontrivial s := nontrivial_of_degree_ne_zero (G := G.induce s) (v := F 0) (by omega)
  obtain ⟨e⟩ := iso_of_copy_preserving_degree F hc fun i => by
    rw [cycleGraph_degree_three_le, degree_eq_two_of_no_leaf hU hmin]
  let C := (Copy.induce G s).comp e.toCopy
  refine ⟨m,C, fun v => ⟨?_, ?_⟩, fun i j => ?_⟩
  · rintro ⟨i,rfl⟩
    exact (e i).property
  · intro hv
    obtain ⟨i,hi⟩ := e.surjective ⟨v,hv⟩
    exact ⟨i,congrArg Subtype.val hi⟩
  · exact (dist_induce_of_omitted_leaves h.1 s hremoved (e i) (e j)).trans (e.dist_eq i j)


/-- The colors at the endpoints of a walk in a two-coloring agree exactly at even length. -/
private theorem same_color_iff_even_length {V : Type} {G : SimpleGraph V}
    (c : G.Coloring (Fin 2)) {v w : V} (p : G.Walk v w) : c v = c w ↔ Even p.length := by
  induction p with
  | nil => simp
  | @cons v u w ha p ih =>
    have hdiff := c.valid ha
    have htwo : c v = c w ↔ c u ≠ c w := by
      constructor
      · intro he he'
        exact hdiff (he.trans he'.symm)
      · intro he
        apply Fin.ext
        have hd : (c v).val ≠ (c u).val := fun hh => hdiff (Fin.ext hh)
        have he' : (c u).val ≠ (c w).val := fun hh => he (Fin.ext hh)
        have hv := (c v).isLt
        have hu := (c u).isLt
        have hw := (c w).isLt
        omega
    rw [htwo, ne_eq, ih, Walk.length_cons, Nat.even_add_one]

/-- A unicyclic graph with an even cycle is bipartite. -/
theorem bipartite_of_even_cycle {V : Type} [Fintype V] {G : SimpleGraph V}
    (h : IsUnicyclic G) {v : V} {p : G.Walk v v} (hp : p.IsCycle) (he : Even p.length) :
    G.IsBipartite := by
  classical
  cases p with
  | nil => exact (hp.not_nil Walk.nil_nil).elim
  | @cons v w _ hv q =>
    let T := G.deleteEdges {s(v,w)}
    have hT : T.IsTree := isTree_delete_cycle_edge h hp (List.mem_cons_self ..)
    obtain ⟨c⟩ := hT.isAcyclic.isBipartite
    have hsub (e : Sym2 V) (heq : e ∈ q.edges) : e ∈ T.edgeSet := by
      change e ∈ (G.deleteEdges {s(v,w)}).edgeSet
      rw [edgeSet_deleteEdges]
      refine ⟨q.edges_subset_edgeSet heq, ?_⟩
      intro hsame
      have hmiss := (List.nodup_cons.mp hp.edges_nodup).1
      obtain rfl : e = s(v,w) := Set.mem_singleton_iff.mp hsame
      exact hmiss heq
    have hdiff : c w ≠ c v := by
      intro hsame
      have hpar := (same_color_iff_even_length c (q.transfer T hsub)).mp hsame
      rw [Walk.length_transfer] at hpar
      rw [Walk.length_cons, Nat.even_add_one] at he
      exact he hpar
    refine ⟨Coloring.mk c fun {x y} hxy => ?_⟩
    by_cases hexy : s(x,y) = s(v,w)
    · obtain ⟨rfl,rfl⟩ | ⟨rfl,rfl⟩ := Sym2.eq_iff.mp hexy
      · exact hdiff.symm
      · exact hdiff
    · exact c.valid (deleteEdges_adj.mpr ⟨hxy,hexy⟩)

/-- A finite unicyclic graph containing a copy of an even cycle is bipartite. -/
theorem bipartite_of_even_core {V : Type} [Fintype V] {G : SimpleGraph V}
    (h : IsUnicyclic G) {m : ℕ} (f : Copy (cycleGraph (m+3)) G) (he : Even (m+3)) :
    G.IsBipartite := by
  apply bipartite_of_even_cycle h (cycleGraph.isCycle_cycle.map (f := f.toHom) f.injective)
  simpa only [Walk.length_map, cycleGraph.length_cycle] using he

end Unicyclic.GraphStructure
