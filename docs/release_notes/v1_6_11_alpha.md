# ZeroGateSim v1.6.11-alpha Release Notes

## Purpose

`v1.6.11-alpha` combines the planned roadmap truth audit and shadow feature-design proposal into one compressed gate.

It repairs the release spine after roadmap drift, names the current shadow wound, and defines the next several gates before new feature implementation begins.

## Added

- `zerogate-shadow-route-audit`
- `src/zerogate_sim/shadow_route_audit_report.py`
- `docs/shadow_route_audit_and_feature_design.md`
- `tests/test_shadow_route_audit_report.py`

## Changed

- README current version and shadow route wording now point to `v1.6.11-alpha`.
- ROADMAP current line and language boundary now include `v1.6.10-alpha` and `v1.6.11-alpha`.
- ROADMAP now states the next bounded route before deeper weather is allowed.

## Scientific boundary

`v1.6.11-alpha` does not implement new shadow features and does not retune the score.

It records the current state:

```text
native four-gate witness: standing
shadow density pressure: candidate signal
shadow relation / return / demotion specificity: not earned
```

Native witness remains:

```text
C_Z = min(D, P, R, B)
```

## Next allowed gate

`v1.6.12-alpha` may implement observable, role-stripped feature columns for relation ownership, return integrity, demotion trajectory, zero-hold ambiguity, and density residual pressure.

Blocked until triad27 specificity is earned:

```text
deep81 / wide243 shadow trust
role-blind discovery language
detector closeout
native witness mutation
```
