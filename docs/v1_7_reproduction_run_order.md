# v1.7.9 Reproduction Run Order

The official order is:

```text
triad27 -> inspect -> deep81 -> inspect -> wide243 -> inspect -> combined package later
```

`triad27` is the plumbing gate. If it fails, stop. Do not bury the first wound under deep81 or wide243 output.

`deep81` runs only after triad27 output is clean.

`wide243` runs only after deep81 output is clean.

The combined package is a navigation layer. It must not replace the three separate records.

Boundary: this is controlled synthetic-field evidence only. It is not role-blind discovery, not independent generator validation, and not physical/cosmological proof.
