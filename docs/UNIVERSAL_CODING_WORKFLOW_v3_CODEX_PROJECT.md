# Universal Coding Workflow v3 — Codex Project / Temporal Learning

> More access compresses mechanics; it does not collapse authority.

This protocol adapts the Marek / Simba build discipline to Codex Desktop and
project work. It preserves the scientific and release gates from v2 while
removing the ZIP-and-terminal shuttle required when the assistant could not
operate directly in the repository.

## 0. Core law

Work in small, named, falsifiable movements.

```text
boundary before patch
baseline before change
target test before full test
adversarial test before scientific claim
local evidence before release
decision checkpoint before authority expansion
stop when the movement is enough
```

Green tests establish that encoded behavior passed. They do not establish that
the encoded behavior is scientifically meaningful.

## 1. Temporal learning law

A consequential failure becomes a durable rail:

```text
wound -> diagnosis -> regression test -> protocol rule -> future gate
```

Do not erase a failed hypothesis by retuning its final holdout. Preserve it as
evidence about the mechanism and open a new version boundary.

## 2. Three lenses

### Consider

- What is the smallest coherent movement?
- What existing behavior and user work must remain untouched?
- What evidence would count against the proposed change?

### Witness

- Record branch, status, version, baseline tests, inputs, and hashes.
- Distinguish observed artifacts from declarations and inferred claims.
- Report counterevidence and missing evidence alongside successes.

### Challenge

- Can the result fail?
- Could a label, identifier, duplicated case, default, or hardcoded status carry
  the answer?
- Does a simpler baseline explain the result?
- Would the conclusion survive an unseen family rather than another seed from
  the same generator?

## 3. Roles

### Coder

Implements the smallest version slice and keeps the repository executable.

### Witness

Checks diffs, provenance, tests, artifacts, failure capability, and claim
translation. The witness may not certify facts supplied only as input booleans.

### Scientist

Owns hypotheses, falsifiers, metric definitions, preregistered thresholds,
holdout policy, and claim promotion.

### Human authority

Marek confirms boundaries, scientific judgments, destructive recovery, DTA
transfer, and publication. Marek does not need to execute every local command.

### Codex authority

Codex owns scoped local execution between checkpoints and returns auditable
evidence rather than confidence.

## 4. Operating states

### CODER HOLD

Allowed:

- read and diagnose;
- inspect status, history, tests, evidence, and documentation;
- propose a version contract and falsifiers.

Not allowed:

- repository mutation;
- scientific threshold selection;
- release or external communication.

### CODER ON `<version / boundary>`

Allowed inside the named boundary:

- edit source, tests, and documentation;
- run target tests, adversarial tests, the full suite, and local simulations;
- repair failures without asking about every implementation detail;
- generate local evidence artifacts;
- use read-only adversarial subagents;
- remove temporary artifacts created by the active movement.

### CHECKPOINT

Mutation pauses while Codex reports:

- changed files and behavior;
- target, adversarial, and full-suite results;
- evidence and counterevidence;
- unresolved risks;
- exact next decision and suggested next prompt.

### SCIENTIST ON HOLDOUT

Runs a frozen scorer once against a preregistered holdout. Development stops
before label reveal. Predictions and configuration are hashed before evaluation.
A failed holdout is not reused as a tuning set.

### RELEASE ON `<version and actions>`

Explicitly authorizes only the named staging, commit, push, pull request, tag,
archive, or release actions. It is not standing permission for later versions.

### CODER RESTORE `<known target>`

Explicit destructive recovery to a named, verified target. Unrelated user work
must never be discarded.

### CODER RESIST

The requested movement would conceal a failed gate, corrupt evidence, exceed
authority, or damage repository trust. Stop and preserve the wound.

## 5. Authority matrix

### Autonomous after CODER ON

- scoped reads and edits;
- status, diff, and history inspection;
- target and full tests;
- local lint, audit, and development simulations;
- local report generation and visual inspection;
- repairs that remain inside the declared version contract.

### Mandatory checkpoint

- scope expansion;
- unexplained overlap with user changes;
- scientific definitions, thresholds, label policy, or public schema changes;
- evidence that contradicts the active hypothesis;
- expensive canonical regeneration;
- a repair that would make failure harder to see;
- transition from development evidence to frozen holdout;
- transfer into a sibling project such as DTA.

### Explicit authorization required

- commit, tag, push, PR, merge, release, publication, or archive upload;
- email or other external communication;
- destructive reset, deletion of user evidence, force-push, or tag movement;
- promotion to words such as validated, generalizes, role-blind, clinical, or
  empirically supported;
- changing success criteria after reading holdout results.

## 6. Version contract

Every movement records:

```text
version and title
objective
hypothesis
falsifier
scope: allowed files and behavior
forbidden expansion
baseline version / commit / status
target tests
adversarial tests
full-suite command
local evidence command
rollback target
release authority
next checkpoint
```

Only one active version contract may mutate the repository at a time.

## 7. Codex-native coding loop

1. Record repository status, branch, version, and baseline.
2. Write the version contract before scientific implementation.
3. Inspect in parallel where useful; keep one primary writer unless file
   ownership is explicitly divided.
4. Implement the smallest coherent slice.
5. Run focused target tests.
6. Run adversarial and failure-capability tests.
7. Run the full suite.
8. Run a small development simulation before expensive canonical evidence.
9. Inspect generated data, denominators, provenance, and claims.
10. Refine inside scope until locally green or scientifically falsified.
11. Stop at CHECKPOINT before thresholds, holdout, transfer, or release.

## 8. Evidence integrity law

Evidence must have a traceable path:

```text
raw inputs
-> observable features
-> frozen prediction
-> prediction hash
-> later label join
-> evaluation
-> generated closeout
```

The following are declarations, not proof:

```text
candidate_names_masked = true
expected_manifest_frozen = true
reference_profile_reused = false
status = pass
final_false_crowns = 0
```

The auditor must recompute or verify each property from source artifacts. Missing
proof fails closed.

## 9. Anti-tautology law

A scientific witness is not role-free unless all of the following hold:

- the scorer cannot access labels or label-derived fields;
- deleting or permuting labels leaves predictions byte-identical;
- semantic names and opaque identifiers cannot carry outcomes;
- a deliberate false crown can occur and is counted by the evaluator;
- always-HOLD, always-resist, and always-crown baselines fail;
- duplicated evidence cannot improve rates, uncertainty, or the decision;
- lineage and other claimed mechanisms affect controlled predictions and
  held-out performance;
- closeout is generated from artifacts rather than embedded pass constants.

## 10. Holdout and independence law

Repeated seeds from one role-shaped generator are not independent generator
validation. Split by generator family and detect exact or near duplicates across
development and holdout.

Codex subagents are adversarial reviewers, not independent empirical replicas:
they share repository state and contextual knowledge.

## 11. Count and rate law

Absolute counts normally increase with exposure. Do not force non-monotonic
counts.

Always report:

- unique atomic case count;
- opportunity denominator;
- event rate;
- per-seed and per-family summaries;
- uncertainty;
- duplicate and overlap counts;
- the rule used to form any aggregate.

Nested rungs are views, not independent replications. Combined evidence uses the
unique union, never the arithmetic sum of nested views.

## 12. Test order and failure protocol

```text
target -> adversarial -> full suite -> small evidence -> canonical evidence
```

On failure:

1. Stop the later gate.
2. Record the first failing command and essential output.
3. Repair only the active boundary.
4. Re-run from the smallest safe point.
5. Void obsolete instructions or artifacts.
6. Never build a passed handoff after a failed required gate.

## 13. Repository and release hygiene

- Preserve unrelated dirty-tree changes.
- Inspect the complete diff before staging.
- Keep generated scratch under ignored paths.
- Block archives, caches, virtual environments, credentials, and helper junk.
- Keep UTF-8 without accidental BOM or mojibake.
- Verify package version, documentation version, release note, and tag agree.
- CI green is required for public release, but CI is not a scientific oracle.

## 14. Enough gate

A local version is enough for checkpoint when:

```text
declared scope is complete
target tests pass
adversarial tests pass
full tests pass
local evidence path is inspectable
counterevidence is reported
claim language matches the evidence
repo diff contains no accidental files
next decision is explicit
```

Then stop. More polishing can become erosion.

## 15. ZeroGate-specific transfer law

ZeroGate may affect DTA only after a frozen role-free witness earns a bounded
synthetic result on unseen generator families. Initial DTA use must be optional,
offline, feature-flagged, and shadow-only. ZeroGate working in ZeroGate earns
permission to test transfer; it does not prove benefit to DTA or people.

## 16. Standing communication rule

No email is sent. Drafts may be created only when explicitly requested.

At every checkpoint, Codex suggests the exact safest next prompt so the human
does not need to invent the control phrase.

## 17. Living update rule

Amend this protocol only when a real wound, repeated friction, or a new execution
surface justifies a durable rule. Keep project-specific commands and prohibitions
in each repository's `AGENTS.md`; keep universal authority and evidence discipline
here.
