# Visual Witness Polish Branch Note

Branch purpose: prepare ZeroGateSim for public sharing and paper scaffolding without mutating the core simulator or tagging a release too early.

## Current rule

No tag.

No release.

No merge to `main` until the public-facing front room is coherent enough to support the post-test paper path.

## Accepted visual format

Use the visual witness style introduced in this branch:

- off-white background;
- large readable labels;
- trinary color logic;
- thick flow arrows;
- clean boxes;
- no decorative geometry that does not carry mechanism.

## Current branch task

Make the repo understandable for readers who did not participate in the build.

The branch should leave the core software alone and polish:

- reader path;
- visual guide;
- proof card;
- claim boundary;
- reviewer guide;
- paper scaffold.

## Merge condition

Merge only when:

- tests pass;
- visuals are readable;
- README front room is coherent;
- the post-test paper scaffold is present;
- no generated runs, exports, caches, or bundles are committed.
