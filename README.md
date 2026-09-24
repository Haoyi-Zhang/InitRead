# Initialization State Safety

A self-contained bounded invariant-checking experiment, with an untrusted certificate producer, a separately implemented stateful checker, an exact small oracle, ordered witness fixtures, and passive observations of locally authored Java graphs.

**Scientific status: research checkpoint, not a completed deserialization defense.** The handwritten arguments are conditional mathematical proofs for the specified model. Implementation evidence consists of finite tests and replay, not a proof-assistant verification. Dynamic read-dependency monitoring and certifying computation are established prior techniques; this repository does not establish a novel combination. The accompanying paper is not required to run any command here.

## Reproduce

Requirements are a Linux environment, Python with its standard library, and an available local JDK (`java` and `javac`). No package download, external API, network connection, third-party application, or private data is used. The runner uses one experiment worker and sequential bounded Java child processes; it does not launch an external service.

From this repository's root:

```sh
python reproduce.py --out replay-output --verify-against results/campaign
```

`replay-output` must be absent or empty. The program refuses to overwrite archived results. It runs all 17 directed test methods, the original redundant-predicate control, both full small-domain checker audits, six ordered witness programs and their negative controls, the 128-object capacity fixture, and 24 owned Java round trips. Exit zero means those commands and comparisons passed; it is not a claim of general implementation correctness or scientific novelty. An exception, timeout, or resource cutoff is a failure/unknown outcome, never evidence of safety.

The replay comparison includes seven scientific JSON files and five deterministic data files. CPU/RSS/time fields are excluded. Generated Java callback data are compared byte-for-byte to the recorded data on the tested environment. Exact agreement on another JDK is not assumed: a changed callback order must be investigated, not silently normalized into agreement. No cross-machine or cross-JDK reproducibility result is claimed.

To regenerate the tables used in the paper from the archived canonical measurements:

```sh
python export_paper_data.py --results results/campaign --out table-output
```

This command needs no LaTeX installation or paper directory. It writes five source fragments, including the measurement macros. Exporting from a new run instead intentionally changes its timing/RSS macros; deterministic scientific counts should still agree. The paper's build instructions are delivered with the full project, not required by this standalone repository.

The delivered source and inputs were exercised from a clean standalone-archive extraction. All seven scientific JSON comparisons and all five exact data comparisons matched; the 17 directed tests passed. `results/replay-verification.json`, `results/replay-measurements.json`, and `results/replay-unit-tests.txt` retain that verification. The replay used 29.0210 aggregate process CPU seconds; this repeated run is not additional workload breadth.

## What was measured

| Quantity | Recorded result |
|---|---:|
| Heap/root states at two and three objects | 33,344 |
| Safely admitted pre-states | 10,438 |
| Value-changing write/root-addition candidates | 615,984 |
| Candidates replayed in the full checker | 615,984 |
| Frontier / dense-oracle disagreements | 0 |
| Checker / dense-oracle disagreements | 0 |
| Unsafe candidates accepted by written-object control | 4,296 |
| Full predicate obligations | 1,068,056 |
| Selected frontier predicate obligations | 681,696 |
| Full-census checker steps | 4,458,364 |
| Directed test methods | 17 passed |
| Deliberately malformed certificate cases | 18 rejected without semantic commit |
| Violating witness fixtures agreeing with whole-path oracle | 5 |
| Safe witness fixture closed by semantic search | 1 |
| Owned Java round trips / callback snapshots | 24 / 66 |
| Callback snapshots with a reachable unready object | 18 across 9 cases |
| Java final valid / invalid snapshots | 18 / 6 |
| Java input-to-final invariant validity changes | 0 |
| Constructor calls during owned Serializable restoration | 0 |
| Specified 128-object certificate | 613 UTF-8 bytes, including newline |

These are census counts or named fixture observations, not independent real-world workloads, error-rate estimates, or attack-prevention measurements. Some event labels have the same resulting state. No 304-program benchmark, 40-public-example corpus, or production-tool baseline was completed. The written-object, stale-cache, root-only, phase-only, and well-formedness-only controls are deliberately restricted original implementations, not runs of published typestate or annotation tools.

The recorded full campaign took 29.1980 aggregate process CPU seconds. The sum of Linux parent and child maximum resident-set measurements is 190,560 KiB (186.09 MiB), a conservative aggregate upper bound, not a synchronized memory profile. Its maxima can arise at different times. There is no measured monitor speedup or deployed JVM overhead comparison. Preliminary interactive smoke tests were not all individually metered, so this timing is not an exact total for all research activity. `results/resource-accounting.json` distinguishes retained campaign measurements from this accounting limitation.

## Exact scope and trust boundary

A heap contains 1–128 fixed objects, each with `(ready, value, next)`. The first two fields are bits; `next` is null (`-1`) or an object identity. The declared invariant is

```
ready(o) and (next(o) is null or value(o) <= value(next(o)))
```

It must hold for every object in the exact closure of all retained external roots. Events are four integers `(object, field, value, added_root)`; field identifiers are 0, 1, 2, and `added_root=-1` means no addition. Same-value assignments are admitted and can encode a pure root addition. Objects and roots are not deallocated; an external reference that remains retained must remain rooted. The census covers every changing-value write and optional root addition from every safe pre-state at sizes two and three. Same-value and root-only events are separately covered by directed fixtures.

The producer emits exact closure, ordered predicate-read transcripts for a sufficient revalidation frontier, and an `ALLOW` or `DENY_UNSAFE` proposal. The checker reconstructs the candidate from authentic input, checks exact coverage and read values, then either commits atomically or leaves heap, roots and cache unchanged. `INVALID_CERT` does not mean the underlying candidate is unsafe. Diagnostic step counts may change on rejection. The checker trusts the initial state, policy, complete event/root observation, its own protected memory, and the atomic gate. The ordinary Python object boundary is not isolation from arbitrary hostile Python code or a network parser.

The ready bit is metadata, not attestation of a constructor chain. There is no bytecode interpretation, allocation, class hierarchy, factory semantics, exception unwinding, handle replacement, unrestricted reflection, native code, or concurrency model. The Java program passively snapshots its own graphs; it is not connected to the abstract atomic enforcement gate. Callback snapshots cannot prove complete event coverage. Omitted external retention is explicitly demonstrated as an observation-contract failure.

The witness search is limited to the owned finite transition systems in `inputs/witness-programs.json`. It returns the least abstract edge sequence in length/lexicographic order. It does not search third-party code or construct serialized gadgets, and the transition checker does not independently certify global shortest-path optimality.

## Repository map and evidence

`src/model.py` specifies heap updates, reachability, and the short-circuit predicate evaluator. `src/producer.py` emits read certificates. `src/checker.py` imports neither the model, producer, nor oracle and uses separate closure/predicate code. `src/oracle.py` uses dense transitive closure and an eager predicate. This is implementation diversity within one research execution, not independent external review.

`src/exhaustive.py` deterministically enumerates the exact small domain. `src/witness.py` contains semantic breadth-first search, a whole-path oracle, and deliberately wrong-key controls. `src/redundant_control.py` reproduces the first predicate that failed to discriminate cross-object revalidation. Its historical `safe_preconditions` counter counts events, not distinct pre-states; do not reinterpret it as a state count.

`java/BenignGraphs.java` creates its own input graphs and serializes them only to in-memory byte arrays. It accepts no external stream or application class. The six invalid final snapshots are already invalid before serialization; no corruption of initially valid objects is claimed.

`proofs/argument.md` contains the complete mathematical arguments. `tests/` contains directed unit fixtures. `inputs/` fixes finite domains and ordered program edges. `results/campaign/` is the canonical measured campaign, with per-safe-state CSV aggregates, first counterexamples for the restricted controls, raw Java snapshot JSON lines, and summaries. Per-state aggregates preserve exact inclusion keys; event-level observations can be reconstructed deterministically rather than storing 615,984 duplicate traces.

`results/pilot-stride127/` preserves a pilot that evaluated the entire frontier but sampled the checker at a fixed stride. It is not added to workload breadth. `results/redundant-predicate-pilot.json` preserves the logically redundant design control. `results/replay-verification.json` and `results/replay-measurements.json` record clean-extraction replay when present. `claim_evidence_ledger.csv` maps claims to proofs, code, and results; `external_resources.csv` records source access and redistribution boundaries.

## Attribution and permitted reuse

Original code, fixtures, generated data, and repository documentation are supplied under `LICENSE`. No implementation of MUSTI, InvCOP, Seneca, or another external tool is bundled or executed. Literature attribution is retained in the proof document and external-resource ledger. Scholarly PDFs are not redistributed under an invented license. The IEEE publication template belongs only to the paper package and retains its own upstream notices.

Substantive problem analysis, proof text, implementation, experiments, and documentation were generated with ChatGPT (GPT-6 Astra Pro) and require human verification before external use. The producer, checker and oracle were not independently authored or externally reviewed. An offline replay does not resolve authorship, publication, novelty, or JVM-refinement obligations.
