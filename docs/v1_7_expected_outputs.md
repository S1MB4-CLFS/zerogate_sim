# v1.7 Expected Outputs

**Introduced:** `v1.7.9-alpha`  
**Purpose:** define the output layers expected by the reviewer package and future human-friendly display work.

**Native witness:** `C_Z = min(D, P, R, B)`

## Output layers

```text
full_output/
compressed_summary/
visuals/
machine/
handoff/
```

### full_output

Full system reports, evaluator reads, machine CSV/JSON, and matrix bundle references. This layer is for audit and trace.

### compressed_summary

Short markdown/card summaries for triad27, deep81, wide243, and combined witness state. This layer orients the reader; it does not replace the evidence.

### visuals

SVG/HTML/cards that make the evidence legible after the mechanism is understood. Visuals are witness aids, not proof by decoration.

### machine

CSV/JSON rows with lane counts, false crowns, manifest flags, evaluator decisions, and package metadata.

### handoff

Strict assistant handoff ZIPs carrying full output, compressed summary, visual output, and report-label notes. Missing includes are red. A false handoff is a false crown.

## Current visual evidence cards

The current README displays the latest local v1.7 holdout snapshot as visual cards after the mechanism and native math witness. The detailed snapshot remains in [`v1_7_latest_holdout_snapshot.md`](v1_7_latest_holdout_snapshot.md).
