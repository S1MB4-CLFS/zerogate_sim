# ZeroGateSim Belnap Evidence-State Mirror

**Line:** `v1.3.1-alpha`  
**Status:** projection mirror / comparison witness  
**Boundary:** ZeroGateSim is not Belnap-Dunn logic.

This mirror asks how ZeroGateSim final-output evidence appears when projected into a four-state evidence grammar:

| Mirror value | Meaning in this repo |
|---|---|
| `T` / `true_only` | Evidence for final +1 without current contrary pressure. |
| `F` / `false_only` | Evidence against final +1 without current positive expression pressure. |
| `B` / `both` | Positive-looking expression pressure and contrary witness are both present. |
| `N` / `neither` | No decisive evidence-for or evidence-against final +1 in this mirror. |

## Why this follows the fuzzy mirror

The fuzzy / many-valued mirror compares continuous gate scoring. The Belnap mirror compares evidence posture.

ZeroGateSim already separates:

- raw expression pressure;
- final earned-one;
- false-one demotion;
- latent overcrown hold;
- relation debt;
- containment / rejection.

That makes a four-state evidence mirror useful, but not identical to the native system.

## Native boundary

A Belnap `B` state is not permission to crown. It means the candidate carries positive-looking pressure and contrary witness at the same time.

In ZeroGate terms:

```text
raw +1 pressure + false-one / latent / relation-debt witness = conflict pressure, not final +1
```

## Matrix outputs

Matrix runs now write:

```text
matrix_belnap_mirror_summary.csv
matrix_belnap_mirror_read.md
```

The read file is meant to show whether conflict-pressure is visible and local instead of hidden inside a final score.

## Overclaim boundary

Allowed:

> ZeroGateSim can project final-output evidence into a Belnap-style mirror to see where evidence-for and evidence-against final +1 coexist.

Forbidden:

> ZeroGateSim is Belnap-Dunn logic.

Also forbidden:

> A `B` state means the candidate is both truly final +1 and truly final -1 in the native engine.

The native engine still decides final output through ZeroGateSim's earned-one witness stack.
