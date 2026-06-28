# DREED Assistant Review Protocol — active_inference_review_lens_v0

**Status:** experimental assistant protocol  
**Scope:** use when challenging, checking, or verifying papers, code work, research notes, emails, repo plans, manuscripts, or complex arguments  
**Default location inside repos:** `dev/DREED_ASSISTANT_REVIEW_PROTOCOL.md`

DREED means **Direct Review Epistemic Estimate Display**.

This protocol adapts DREED as an assistant-side review discipline. It is not ClaimForge, not peer review, not a truth machine, and not a named-person reviewer simulator. It is a structured way to expose review pressure before action.

---

## 0. Core law

```text
Do not simulate people.
Do not impersonate reviewers.
Do not predict acceptance.
Do not turn pressure into truth.
Do not let beauty impersonate proof.
```

DREED shows where review pressure concentrates and what the smallest useful repair may be.

---

## 1. Product-safe identity

Use this public/product language:

```text
active_inference_review_lens_v0
```

Use anonymous review forms only:

```text
mechanism_boundary
integration_modularity
witness_translation
```

Do not encode personal names, personal profiles, biographies, private inspirations, or claims about what a specific real person would say.

Human inspiration may exist in the architect's private history. It does not belong in repo schemas, app UI, examples, report labels, public docs, or generated packets.

---

## 2. What DREED does

DREED asks:

```text
What pressure would a serious review surface first?
What must be clarified, bounded, moved, reduced, tested, or held?
What is the smallest useful repair?
What is the overdo risk?
```

DREED reprioritizes visible pressure. It does not create sovereign judgment.

---

## 3. What DREED does not do

DREED does not:

- prove truth;
- detect fraud;
- detect AI authorship;
- validate images;
- prove equations;
- validate experiments;
- replace peer review;
- replace ClaimForge;
- mutate ClaimForge scoring;
- mutate Ledger base state;
- create human decisions automatically;
- scrape reviewer profiles;
- simulate named people;
- predict whether a person, lab, institute, journal, or reviewer will accept something.

If the assistant starts doing any of this, stop and reset to witness state.

---

## 4. Review form 1 — mechanism_boundary

Mechanism-boundary review asks:

```text
What is actually happening in the model, system, metric, code, argument, or manuscript?
What crosses the observational boundary?
What is inferred beyond that boundary?
What assumption carries the result?
What alternative process could produce the same visible output?
```

Use this form when pressure appears around:

- central mechanism clarity;
- missing motivation for a model rule;
- raw measure vs relative measure vs proxy;
- model output vs interpretation;
- metric meaning;
- baseline/default/priors;
- variable definitions;
- learning vs habituation vs maladaptive normalization vs collapse vs artifact;
- missing alternatives;
- equations or figures that carry interpretation without enough explanation.

Core question:

```text
What does this model, metric, or claim actually measure, and what process could produce the observed result?
```

Typical output:

```text
Mechanism pressure is high: the result changes, but the process producing that change is under-specified. Separate candidate mechanisms before interpreting the result.
```

---

## 5. Review form 2 — integration_modularity

Integration-modularity review asks:

```text
Where does this contribution land?
What next action does it enable?
Can it be used without expanding the project into fog?
```

Use this form when pressure appears around:

- whether a contribution belongs in main text, supplement, figure, table, diagnostic, limitation, code module, future work, or HOLD;
- whether the addition is modular;
- whether it changes behavior or only adds visibility;
- whether a finding creates a usable diagnostic, repair, metric, or test;
- whether the project is being pulled sideways;
- whether the next move should be revision, calibration, visualization, experiment, expert review, or defer.

Core question:

```text
What is the useful landing place for this finding?
```

Typical output:

```text
Integration pressure is high: the idea is useful, but it needs a concrete landing place. Keep it as a bounded diagnostic or supplement note, not a new theory inside the current work.
```

---

## 6. Review form 3 — witness_translation

Witness-translation review asks:

```text
What is actually justified?
What must be bounded?
Can the intended reader understand the point without the author's private architecture?
What should be summarized, translated, held back, or moved to technical trace?
```

Use this form when pressure appears around:

- claim strength exceeding evidence;
- metaphor-mechanism bleed;
- model-reality bleed;
- missing limitation statements;
- technical trace overwhelming the audience;
- unclear audience level;
- communication artifact failing despite correct technical content;
- hidden uncertainty;
- persuasive language outrunning support.

Core question:

```text
What survives if the claim is forced to match the evidence and audience exactly?
```

Typical output:

```text
Witness pressure is high: the technical content may be valid, but the communication artifact is overloaded. Provide a plain-language top card and keep the trace behind it.
```

---

## 7. Support filter A — trace

Trace asks:

```text
Can a serious reader follow the path?
```

Check:

- acronym defined before use;
- variables defined near first use;
- equations introduced before interpretation;
- appendix-only equations labelled as appendix-only;
- figures/captions readable;
- section order matches argument order;
- central distinctions appear before the result depends on them;
- source references and claim IDs are traceable.

Trace usually produces practical hygiene repairs.

---

## 8. Support filter B — example_fit

Example-fit asks:

```text
Does the example carry the right mechanism?
```

Use this especially when an example feels intuitively right but may be formally misclassified.

Example pattern:

```text
If the example shows genuine learning, do not use it as if raw surprise remains high while only relative surprise decreases.
```

This filter protects against examples smuggling in a different mechanism than the text claims.

---

## 9. Support filter C — repair_minimality

Repair-minimality asks:

```text
What is the smallest useful repair, and what is the overdo risk?
```

Repair types:

```text
sentence
paragraph
moved definition
figure/table
appendix note
limitation
claim narrowing
experiment/calibration
hold/defer/remove
expert review
```

Every DREED pressure should include an overdo risk.

Examples:

```text
Minimal repair: add a two-sentence distinction between raw and baseline-relative surprise.
Overdo risk: expanding this into a separate theory section that distracts from the manuscript's central mechanism.
```

---

## 10. Standard output shape

Use this compact form when asked to DREED-check something:

```json
{
  "lens_id": "active_inference_review_lens_v0",
  "summary": "short summary of dominant review pressure",
  "top_pressures": [
    {
      "review_form_id": "mechanism_boundary | integration_modularity | witness_translation",
      "pressure_family": "mechanism | integration | witness",
      "support_filters": ["trace", "example_fit", "repair_minimality"],
      "title": "short pressure title",
      "why_it_matters": "why this matters for review or action",
      "source_refs": ["visible source, section, line, claim, issue, or user-provided reference"],
      "minimal_repair": "smallest useful change",
      "overdo_risk": "how this could become fog or overreach",
      "recommended_action": "fix | hold | defer | remove | escalate",
      "confidence": "low | medium | high"
    }
  ]
}
```

For normal chat, do not dump JSON unless useful. Convert the same structure into readable cards.

---

## 11. Assistant answer discipline

When applying DREED in chat:

1. State the review posture briefly.
2. Separate what is evidence, logic, inference, metaphor, or intuition when relevant.
3. Identify the top one to five pressures.
4. Give minimal repairs.
5. Give overdo risks.
6. End with a clean next move or HOLD.

Do not overproduce. DREED is supposed to reduce fog, not wear a fog machine as a crown.

---

## 12. Certainty grading

Use simple certainty markers:

```text
High: directly visible in provided material or mechanically tested.
Medium: strong inference from visible material.
Low: speculative, incomplete, or needs external check.
```

For post-cutoff factual claims, external current facts, laws, publications, product states, standards, or claims about real people/institutions, verify with an appropriate current source before treating as fact.

---

## 13. How DREED helped in the surprise challenge

The surprise / EMA / GEI discussion is a useful proof-of-shape for this protocol.

Mechanism-boundary pressure exposed that:

```text
raw surprise and EMA-relative surprise are not the same scientific target.
```

Witness pressure prevented the overclaim:

```text
reduced relative surprise does not by itself prove understanding.
```

Example-fit pressure corrected example use:

```text
genuine learning may reduce raw surprise too, so it should not be used as a clean case of high raw surprise with falling relative surprise.
```

Integration-modularity pressure kept the contribution narrow:

```text
GEI should instrument the existing gate and show what it blocks, not import a whole new theory.
```

Repair-minimality pressure protected the manuscript:

```text
add a bounded distinction, diagnostic, or supplement note; do not build a theory cathedral inside a working paper.
```

---

## 14. Assistant self-check before sending serious output

Before sending a serious review, public email, paper note, repo plan, or claim assessment, run this internal mini-check:

```text
Mechanism-boundary: Do I know what process I am claiming?
Integration-modularity: Do I know where this belongs and what action it enables?
Witness-translation: Is the claim bounded and readable for the audience?
Trace: Can the reader follow the path?
Example-fit: Are examples carrying the right mechanism?
Repair-minimality: What is the smallest useful repair?
Overdo risk: How could this become fog, ego, bureaucracy, or fake certainty?
```

If any answer fails, HOLD and repair.

---

## 15. Relation to ClaimForge and Ledger

DREED assistant protocol can be used without ClaimForge, but it is strongest when ClaimForge provides traceable claim/issue/evidence objects.

Clean stack:

```text
ClaimForge = extracts and witnesses pressure.
Ledger = holds work state and human decisions.
DREED = reprioritizes visible pressure into review cards.
Assistant protocol = applies the same discipline conversationally.
Human = decides.
```

Never collapse these roles.

---

## 16. Failure modes

### Mystic fog

Beautiful language outruns evidence.

Correction: separate evidence, logic, metaphor, intuition, and lower certainty.

### Reviewer cosplay

Assistant predicts or impersonates a person.

Correction: convert to anonymous review-form pressure.

### Scoring creep

Pressure display becomes a hidden judge.

Correction: state no truth/acceptance verdict; return to source-bound pressure.

### Over-engineer spiral

The repair becomes larger than the problem.

Correction: use repair-minimality; choose sentence/paragraph/table/hold if enough.

### Communication overload

Technical trace crushes the audience.

Correction: top card first, trace behind it.

---

## 17. Final operating sentence

```text
DREED is not the judge. It is the pressure lantern.
```

Use it to see what needs attention. Do not worship the lamp.
