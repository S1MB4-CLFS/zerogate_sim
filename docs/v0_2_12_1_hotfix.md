# v0.2.12.1-alpha hotfix

This hotfix repairs the temporal lineage package mismatch from v0.2.12-alpha.

`matrix.py` passes `time_axis` into `build_temporal_rows`. Some local installs still had the older `endurance.py` signature, causing:

`TypeError: build_temporal_rows() got an unexpected keyword argument 'time_axis'`

The fix ships the updated `endurance.py` that accepts and records `time_axis`.

Core gate math is unchanged.
