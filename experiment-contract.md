# Finite experiment contract

## Status and ordering

This is the exact contract of the bounded verification experiment, not a frozen claim of research novelty. The relational predicate and domain were examined by a pilot before the complete checker census. The full-census decision to replace fixed-stride checker sampling by stride one was recorded before that full replay. Directed tests were refined during development; this is not a held-out statistical benchmark or a preregistered prevalence study. No seed, training split, or learned parameter is involved.

## Enumeration and inclusion

For each `n` in `[2,3]`, a record domain is the lexicographic product of ready in `[0,1]`, value in `[0,1]`, and next in `[-1,0,...,n-1]`. Heap order is the lexicographic product of this domain repeated `n` times. Root masks increase from zero to `2**n-1`. The unique state key is `(heap_index, root_mask)`, recorded in the per-state CSV. All states count toward the census. Only states satisfying the exact boundary invariant are eligible pre-states for candidate transitions, because checker admission requires them.

From each eligible state, object IDs, field IDs, values, and optional root additions are enumerated in ascending order. Unchanged field assignments are omitted from this particular census, not from the semantics. Every non-null root addition is retained even when it was already reachable; distinct labels with identical successors still count separately. Every candidate is re-evaluated by the independent dense oracle, by the selected frontier, and, at stride one, through a fresh checker receiving the producer certificate. A denial is checked not to mutate semantic state.

There are `[4(n+1)]^n * 2^n` states and `n(n+2)(n+1)` labeled changing-write candidates per safe pre-state. At sizes two and three these give respectively 576 and 32,768 states; 286 and 10,152 safe pre-states; and 6,864 and 609,120 candidate transitions. No failed or unfavorable case is removed.

## Intended falsifiers and controls

The primary finite falsifier is any frontier/oracle or checker/oracle decision disagreement, or any denied candidate that changes the protected heap, roots, or cache. Such a disagreement aborts reproduction. Targeted certificate corruption must return `INVALID_CERT` without semantic commit; invalid evidence is not treated as proof that a candidate is unsafe.

Five original restricted controls check (a) newly reachable plus the written object, (b) newly reachable objects only, (c) roots only, (d) readiness bits only over the closure, and (e) field-domain well-formedness only. They are meaningful omission controls, not faithful implementations of published static typestate, annotation, or dynamic invariant systems. All are evaluated on the same exact candidates; no runtime ranking is derived from them.

The original negative-design predicate requires every reachable value to be one and then redundantly requires successor values to be one. Closure implies the latter. Its two-object experiment is retained to show a pilot design that did not distinguish the intended phenomenon, rather than silently dropping the unfavorable methodological finding.

## Witnesses and owned Java graphs

Six owned ordered transition systems are exact JSON input files. The correct search key is `(pc, heap, roots)`; a monotonically increasing diagnostic epoch is irrelevant. Erasing ready is a deliberately unsound control. Keeping the epoch is a deliberately nonclosing control. Breadth-first search uses a default 8,192-node cap; caps yield `UNKNOWN`. The independent whole-path oracle has depth eight and a 100,000-edge cap. Absence of a path within the depth bound is not a safety proof. Five returned violations are compared by their complete edge sequences; the one safe semantic graph closes two states.

Eight fixed Java topologies crossed with three value patterns generate exactly 24 owned cases. Inputs are made by the source itself. Each round trip records the input predicate, constructor counter, all restoration-callback snapshots, and final snapshot. There are no downloaded objects, external byte streams, serialized payload files, reflective writes, network services, third-party vulnerability reproductions, or attack-effect measurements. Python checks every callback and final snapshot with the dense oracle. Event/root-observer completeness and JVM enforcement are outside this observation experiment.

## Budgets, steps, and reproduction equality

One experiment worker is used. Java compilation and execution are sequential children, each limited to 30 seconds, one active processor for JVM ergonomics, Serial GC, and 256 MiB Java heap. Each whole two-/three-object enumeration has a 120-second watchdog and two-million-candidate cap; an individual enumerated pre-state is much smaller than that whole-run chunk. The capacities are not promises that arbitrary 128-object state spaces are tractable. The enclosing project remains limited to four cores, 4 GiB RAM without swap, 7 CPU-hours of experiments, 4,000,000 total counted candidate transitions, and 16,000,000 checker steps.

The implemented checker counts closure memberships, frontier coverage iterations, validated read records, and one decision-validation step. This is an operation convention, not a count of all Python operations or processor instructions. Predicate-obligation counts are separate. Parent and child maximum resident-set values are added conservatively and are not interpreted as simultaneous RSS.

Replay compares the scientific content of seven JSON files and the exact bytes of five deterministic data files. It excludes timing and resident-set measurement fields. A clean same-environment extraction is the executed reproduction scope; it is not independently blinded review or cross-platform compatibility evidence. Exact consumed scientific inputs are the original source and JSON delivered here, so reproduction does not depend on a mutable public download or omitted cache.
