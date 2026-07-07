# v1.7.6-alpha — Holdout Output Structure and Handoff Contract

**Version:** `v1.7.6-alpha`  
**Native witness:** `C_Z = min(D, P, R, B)`

This note records the output structure required after the `v1.7.6-alpha` fresh holdout contract and before `v1.7.7-alpha` audit, `v1.7.8-alpha` cleanup, and `v1.7.9-alpha` reviewer packaging.

No run result is promoted into repo evidence by this note. Local `runs/` artifacts remain local evidence until a later patch deliberately promotes a bounded summary.

## Pressure fixed

Some debt-evidence report builders are historical modules and may retain historical internal report-version labels when they are reused inside a `v1.7.6-alpha` holdout workflow.

Required wording for reviewer packaging:

```text
Some included debt-evidence report modules may retain historical internal report-version labels;
the active package/evaluator boundary remains v1.7.6-alpha.
```

This is a witness-translation repair. It prevents a cold reader from thinking a v1.6 internal report label overrides the active v1.7.6 holdout boundary.

## Testing rhythm

Do not run the full holdout ladder as one giant block until the smallest rung proves the pipeline.

Required run rhythm:

```text
1. Run triad27 only.
2. Build triad27 report.
3. Build triad27 compressed summary.
4. Run v1.7.6 evaluator on the triad27 row.
5. Build triad27 assistant handoff.
6. Inspect.
7. Run deep81 only.
8. Inspect.
9. Run wide243 only.
10. Package all three after each rung has a valid report/evaluator/handoff.
```

A one-shot runner is allowed only after the rung-level pipeline is already proven. Big blocks are allowed to be efficient only after small blocks have earned trust. Efficiency without witness is just a fast shovel.

## Output layers

Future holdout output should separate four layers.

| layer | purpose | handoff role |
|---|---|---|
| full output report | complete system output, full report, decision JSON, CSV evidence, bundles | `--full-output-report` |
| compressed summary | short state card: rung, lane counts, false crowns, boundary, next action | `--compressed-summary` |
| visual outputs | SVG / PNG / HTML / card outputs for human-facing review | `--visual-output` |
| report label note | boundary notes for historical internal report labels and active package version | `--report-label-note` |

The compressed summary must point back to the full output report. It is a reader door, not a replacement for evidence.

## Assistant handoff state

The assistant handoff should be able to carry:

```text
full output report(s)
compressed summary report(s)
visual output(s)
machine decision files
report label notes
strict include audit
```

This supports two needs at once:

```text
system out = full output report and machine-readable evidence
handoff state = compressed reviewer surface plus pointers to the full output
```

The future human-friendly display layer can read the same handoff and render a dashboard/card view without changing the evidence contract.

## Forbidden moves

```text
Do not commit generated runs/ output as repo truth.
Do not let a compressed summary replace full evidence.
Do not build a passed handoff after missing required includes.
Do not print COMPLETE after an earlier required gate failed.
Do not treat visuals as claim upgrades.
Do not treat controlled holdout output as role-blind discovery.
```

## v1.7.7 dependency

`v1.7.7-alpha` should audit the clean rung-level output before reviewer/reproduction guidance. `v1.7.8-alpha` should clean the repo surface after the audit passes. `v1.7.9-alpha` should package reviewer/reproduction guidance only after cleanup passes. It should include this structure:

```text
full_output/
compressed_summary/
visuals/
machine/
handoff/
```

That structure is future-facing. It prepares the software for a more universal and human-friendly output display later, without making the display layer part of the scientific claim.
