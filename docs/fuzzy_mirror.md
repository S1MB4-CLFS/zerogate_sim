# ZeroGateSim Fuzzy / Many-Valued Mirror

**Line:** `v1.3.0-alpha`
**Status:** first known-logic projection mirror

The fuzzy / many-valued mirror is the first formal comparison because ZeroGateSim already computes continuous gate scores in `[0, 1]`:

```text
D = distinction
P = polarity
R = relation
B = observed return
C_Z = min(D, P, R, B)
```

This makes fuzzy-style conjunction a natural comparison surface.

## Native rule

ZeroGateSim's native rule is weakest-gate coherence:

```text
C_Z = min(D, P, R, B)
```

The minimum matters because a candidate should not pass by averaging away a missing gate.

## Mirror rules

The v1.3.0 mirror compares the native rule against:

```text
native_min_gate      = min(D, P, R, B)
product_gate         = D * P * R * B
average_gate         = (D + P + R + B) / 4
lukasiewicz_gate     = max(0, D + P + R + B - 3)
strength_min_native  = min(strength, native_min_gate)
```

These are comparison mirrors only. They do not replace the native gate.

## Main wound: average overcrown

The key diagnostic is `average_overcrown_pressure`.

It appears when:

```text
average_gate >= threshold
native_min_gate < threshold
```

This means the softer average mirror would pass a candidate while the native weakest-gate rule refuses it.

That is exactly the wound the mirror is meant to expose.

## Product pressure

The product mirror is often stricter than native min because distributed weakness compounds.

This is useful pressure, but it is not automatically better. Product conjunction can punish broad partial weakness more strongly than the native geometry intends.

## Loss report

The fuzzy mirror sees continuous gate pressure.

It does not see the full earned-one witness stack by itself:

- return-depth;
- temporal lineage;
- echo-independence;
- truth-role witness;
- final trinary demotion.

Therefore:

> A high fuzzy score is pressure, not final +1.

## Generated outputs

When a matrix run is executed, v1.3.0 writes:

```text
matrix_fuzzy_mirror_trace.csv
matrix_fuzzy_mirror_candidate_summary.csv
matrix_fuzzy_mirror_read.md
```

These files are included in the matrix evidence bundle.

## Boundary sentence

ZeroGateSim can be compared to fuzzy / many-valued scoring because it uses continuous gate scores. It is not identical to fuzzy logic because final earned-one depends on native return, lineage, independence, and witness grammar.
