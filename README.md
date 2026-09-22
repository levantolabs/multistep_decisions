# multistep_decisions

**A multistep decisions benchmark for decision models.**

100 typed decisions that each need several dependent steps to reach. Every one is the kind of
decision software already delegates to a model: is this SLA met, can this user still write to
this dataset, does this rota break the rest rule, is this wire approved on the record, which
vendor does the procurement rule select.

What they share is that the answer is not written anywhere in the text. It has to be
constructed: a total carried across nine stock movements, a rule chain where one buried
condition flips the outcome, an account balance after a sequence of holds and releases, three
constraints checked at once, business hours counted across two time zones.

A model that answers in a single forward pass has no scratchpad for that. This set measures
whether a decision model reaches these answers anyway.

## An example

```json
{
  "id": "msd-state-05",
  "family": "state_tracking",
  "state": "Ticket workflow. Allowed transitions: new->triaged, triaged->in_progress, in_progress->review, review->in_progress, review->done, and any state except done -> cancelled. Invalid transitions are ignored.\nEvents: new; triaged; in_progress; review; in_progress; cancelled; review; done.",
  "question": { "type": "choice", "instructions": "Final state?" },
  "labels": ["done", "in_progress", "cancelled", "review"],
  "expected": "cancelled"
}
```

Once the ticket is cancelled, the last two events are invalid transitions and are ignored. The
last word in the text is a distractor.

## What is in it

| Family | n | What has to be constructed |
|---|---|---|
| `arithmetic_chain` | 17 | 3 to 5 dependent operations: tiers, compounding, fees, prorations, credits, affordability ratios |
| `calendar_time` | 11 | Business days, month-end arithmetic, time zones with DST, rolling windows, dated eligibility |
| `counting_quantifiers` | 9 | Counts with a condition over a list; "at least k of n", "every", "exactly one", weighted votes |
| `state_tracking` | 12 | The state after 6 to 12 ordered events: permissions, stock, contract amendments, holds, workflows, escalations, escrow |
| `input_validation` | 2 | Whether an input satisfies a stated format or calendar rule |
| `ranking_derived` | 6 | Order by a derived key (price per unit, pace, tie-breaks) and pick a position |
| `constraint_verification` | 10 | A proposed rota, itinerary, plan or roster checked against several constraints at once |
| `long_policy` | 15 | A 4 to 8 rule policy applied to one case, with exceptions, exceptions to exceptions, and routing |
| `optimization` | 7 | Hard constraints, then an objective: expected value, discounted cost, consolidation rules |
| `cross_reference` | 11 | Whether a field matches its counterpart elsewhere, or a claim is supported by the record |

28 yes/no questions (15 yes, 13 no) and 72 multiple-choice questions with 2 to 7 options. Every
item is its own scenario; no policy text, rubric or template is reused.

## Quick start

No dependencies beyond Python 3.10.

```bash
git clone https://github.com/levantolabs/multistep_decisions && cd multistep_decisions
python3 evaluate.py examples/predictions_random.jsonl
```

Run your model on `data/multistep_decisions.jsonl` and write one line per item:

```json
{"id": "msd-state-05", "answer": "cancelled"}
{"id": "msd-cal-02", "answer": "yes", "probs": {"yes": 0.91, "no": 0.09}}
```

`answer` must be one of the item's `labels`. `probs` is optional: if every line has one, the
report adds Brier score and expected calibration error. A missing or invalid answer counts as
wrong. `--json` prints the report as JSON.

## Data format

Each line of `data/multistep_decisions.jsonl` is one item:

| Field | Meaning |
|---|---|
| `id` | Stable identifier, `msd-<family>-<nn>`. Numbers keep their draft order, so there are gaps |
| `family` | One of the ten families above |
| `state` | The document the decision is about. Plain text in all 100 items |
| `question.type` | `choice` (pick one of `labels`) or `noul` (a yes/no question; `labels` is `["no", "yes"]`) |
| `question.instructions` | The question |
| `question.criteria` | For `choice`, a description per option; for `noul`, what makes the answer yes or no |
| `labels` | The exact answer set |
| `expected` | The correct label |

`data/manifest.json` carries the family and type counts and the sha256 of the data file.

## How the labels were made

- **Computed, not annotated.** Every arithmetic, calendar, counting, state, ranking,
  constraint, optimisation and reconciliation label was computed programmatically from the same
  parameters that render the text, so the label cannot disagree with the scenario. Where the
  answer is a band, the band edges were checked against the computed value.
- **Rubric in the item.** Every policy, validation and cross-reference item states its full
  rubric in `state`, so the label follows from the item alone.
- **How the 100 were chosen.** 85 items come from an earlier internal draft that had already
  been run against models. 15 draft items were dropped because they were pure computations
  (checksums, puzzles, calendar lookups) rather than decisions, a criterion set without
  reference to scores, and 15 new decision items replaced them. One carried-over item had its
  wording clarified (a stock correction whose sign was not stated); its label did not change.
  No label was changed because of a model's output.
- **Checksummed.** `data/manifest.json` carries the sha256 of the data file, so you can check
  you are scoring the released version.
- **Fixes go into new versions.** A wording problem found later is fixed in a new version with
  a changelog entry, never silently.

## Scope

It measures whether a decision model reaches answers that need a scratchpad. It does not
measure judgement on answers that are present in the text.

It contains no checksums, puzzles or calendar trivia. A decision that a deterministic function
should make is out of scope: the question is not whether a model can replace a for-loop.

## Results

| Model | Accuracy | Correct | p50 | p90 |
|---|---|---|---|---|
| **Sage v1.1 (auto)** | **92.0%** | **92 / 100** | 910 ms | 1.51 s |
| Jev 1.13.0 | 71.0% | 71 / 100 | 240 ms | 290 ms |
| Uniform random over `labels` (expected value) | 35.8% | | | |

Measured 2026-09-22 from one machine in AWS us-east-2, one request at a time, both models
through the same harness; latency is client wall clock. Repeat runs: Sage v1.1 (auto) 91, 92,
93 and 92; Jev 1.13.0 69, 71 and 71. Sage decides per question whether to reason, which is
where its extra latency goes.

Submit results for other systems by pull request, with the predictions file and how it was
produced.

## Changelog

- **1.0** (2026-09-22): first public release, 100 items.

## License and citation

MIT. See `LICENSE`, and `CITATION.cff` for citation metadata.
