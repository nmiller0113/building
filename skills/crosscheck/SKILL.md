---
name: crosscheck
description: Use when creating or changing anything executable or rule-bearing: a script, a hook, a skill or agent or prompt template, a CI job or service unit, a permission rule, a shell function. Also when fixing a bug in one, and when editing a comment or log string inside one, because monitors and tests read that text. Also for a behavioural rule in an always-loaded instruction file, which runs on the model's judgment with no code behind it. Not for read-only investigation or prose carrying no behaviour.
license: MIT
---

# crosscheck

Build against the real contract, then send the change for an independent adversarial review
bounded at both ends: in how wide it looks, and in how many times it may run.

Two failures this prevents, pulling in opposite directions: shipping a build nobody checked,
and a review loop that never terminates, because every fix is itself new work to fault.

## The method

1. **Read the real contract.** The source of the thing you are calling, not your memory
   of it, and not the field names its consumer happens to use.
2. **Implement.**
3. **Send it for adversarial review. Unprompted. Every time.** Three strikes, then the
   builder tiers up, three more, then stop at six and bring it to the requester. The
   reviewer never changes.

There is no fourth step, and no step is a test file. Write tests when the work needs them
or the requester asks. This is not a testing policy.

## Who reviews

The reviewer is **whichever model the requester has designated as their always-reviewer**.
The requester names it once in their own instruction file, never per task, and it reviews
**every cycle, one through six, whoever built**.

**That designation is not a rank.** It need not be the most capable model available, and
naming a mid-tier one is a valid choice rather than a compromise. The rule is the
designation, not "whoever is strongest today".

**Independence is the fresh context, not a different engine.** What review buys is a reader
who did not write the thing, so the reviewer shares none of the build conversation. Where
the designated reviewer and the builder are the same model, that is two separate fresh
contexts, one building and one reviewing, and the review is not thereby weaker.

**Designated reviewer unavailable? Stop and ask.** Out of quota, erroring, unreachable: that
is a stop, not a licence to substitute. Say which reviewer is unavailable and wait for the
requester. Do not review with a different model because independence would technically
survive it, and do not proceed unreviewed. The sentence above is about which CONTEXT the
reviewer runs in, never about swapping the model out.

**No designation yet? Ask for one before the first review, and do not start without it.**
That is where every fresh install begins, so it is the common case, not the edge. Do not
pick a reviewer yourself, do not fall back to "whoever seems most capable", and do not skip
the review because nobody was named. Ask once; the requester records the answer in their
own instruction file, which is what stops it being asked again. Do not write it there
yourself. Fresh agents sharing none of the build conversation, or a person, is a valid
answer where they have no second model to name.

## Everything gets reviewed. All means all.

Not just the code that looked risky. Scripts and programs, hooks, service units and timers,
permission rules, prompts and templates, and **the skill files themselves**, including this one.

The characteristic failure is not skipping the review outright. It is narrowing the rule
until the thing in front of you falls just outside it. This rule has been missed three
ways inside a single hour: a finished build reported with no review at all, a first draft
of a review skill that omitted the review step, and a fix that covered code while quietly
exempting the skill file carrying the rule. **When in doubt whether something counts as a
build, it counts.**

## The review's aperture is the diff. Nothing more.

Two different things get called scope here, and confusing them is expensive. The section
above is about WHICH ARTIFACTS get reviewed: all of them, no exemptions. This one is about
HOW WIDE a single review may LOOK, and the answer is only at what the change touched.

**A review prompt asks two questions and no others:**

1. Does this change do what it claims?
2. Did it break anything that worked before?

**Banned in a review prompt:**

- "find regressions that alter X", where X names a surface the diff does not touch
- "construct a new variation of the same defect class"
- "what else is wrong in this file"
- naming a subsystem, file or behaviour that is not in the diff
- any instruction whose honest answer is a list of defects the change did not create

Give the reviewer the diff and tell it the diff is the boundary. A finding it volunteers
outside those two questions is **one line in the requester's backlog**: not a work item,
not a fix, and not something they hear about mid-flight.

**The mechanism, because knowing it is what stops the repeat.** An uncovered codebase plus
a reviewer told to hunt equals an unbounded list. The reviewer is not wrong and the findings
are not fake, which is exactly why this is seductive. Every finding is real; every one is
also manufactured by the prompt. Fix them, and the next round's prompt manufactures more,
because a fix is new development and the aperture never narrowed. **A limit on review ROUNDS
does not protect against this: it bounds how many times you look, not how widely.** And
findings from a commissioned hunt, reported as though you stumbled on them, make a codebase
look like it is falling apart when you went looking without asking.

**The one exception, and it is narrow:** a change that alters a SHARED contract, a
function signature, a data shape, a permission rule, an injected surface, may have its
reviewer look at the call sites that contract reaches. That is the diff's blast radius,
not the whole file.

## The cycle limit: six, then stop and talk

| Cycle | Builds and fixes | Reviews |
|:--|:--|:--|
| 1 to 3 | builder | the designated reviewer |
| 4 to 6 | the next tier up, from the reviewer's findings | the designated reviewer |
| 7 | does not exist | STOP. Bring it to the requester. |

A **cycle** is one build-or-fix attempt plus one review of it. Without a terminator,
"everything gets reviewed" plus "a fix is new development" is an infinite loop. Three
strikes was never a stopper; it only changes **who builds**.

**The reviewer does not move.** Three failures are evidence the BUILDER is the wrong
instrument, not that the review is, so the builder steps up and the designated reviewer
keeps reviewing. That is what preserves independence through the second phase rather than
spending it exactly when the work is going badly.

**The builder is whatever model the build was triggered from**, so there is nothing to
choose at cycle 1. At cycle 4 it steps up exactly one tier. Where there is no tier above
it, say so and **keep building to six on the same model** rather than inventing a tier or
stopping early: the loop is bounded at six either way, and three cycles are not a budget to
forfeit because the ladder ran out. Cycle 7 is the same conversation it always was, and
there is no third tier by default.

**The count is per DISTINCT CHANGE, not per body of work.** A new change starts at cycle
1 even when it lands minutes after another exhausted its three. That is the generous
reading, so it is the one not to stretch: a distinct change is a different defect or a
different feature, **never the same defect re-attempted under a new name**. Three attempts
at one thing is three, whatever you call them on the fourth. When it is genuinely unclear,
say so out loud and let the requester rule. Do not resolve an ambiguity about your own
budget in your own favour.

**A cycle FAILS when the review returns a confirmed critical or high finding.** That
definition is load-bearing: if mediums and lows counted, the loop would never converge.
Mediums and lows are a sentence to the requester, not a task list.

**That severity test answers exactly one question: does the loop CONTINUE on this defect.
It never decides whether new work gets reviewed.** Any code you write gets reviewed, full
stop, including a fix for a low, a one-line hardening, and cleanup you did on your own
initiative. The two look adjacent and are unrelated: code gets reviewed if you wrote it,
always; the loop runs another cycle only on a critical or high.

**Count the cycles out loud as they happen**, in the message where each one lands, never
reconstructed afterwards. A count you reassemble later is the count you talk yourself out
of. State it plainly: "cycle 2 of 6".

**First ask which ending happened. The terminator fires on SIX FAILURES, not six cycles
elapsed.** A cycle returning clean, or only mediums and lows, is a loop that CONVERGED and
the work is done; announcing a stopping rule over finished work describes a wall never hit.
**Convergence is a STOP, and the leftovers are a REPORT rather than a queue.** They look
like a to-do list and will be read as one if handed over as one, so they arrive with a
recommendation defaulting to fix none, each severity qualified by what must coincide for it
to bite. The reviewer graded the artifact in isolation and cannot know what makes a finding
rare in deployment; an unweighted label is how a narrow race arrives sounding like a fire,
and a yes obtained that way is manufactured. Findings landing only in machinery added AFTER
convergence mean the loop is eating itself, the last honest place to stop.

**The severity call at cycle 6 is the reviewer's, not the builder's.** A confirmed
critical or high you cannot refute on live evidence is a failure, and one you are unsure
about goes to the requester. An ambiguity at the terminator is never resolved toward
convergence: that is the same self-favouring shape the distinct-change rule already bans,
arriving at the one gate that used to need no judgment at all.

At cycle 6 WITH a failing review, stop mid-problem and say so. Not "it is nearly there",
not "this one is cheap", not a new lens. Six failed cycles is evidence the problem is
misunderstood rather than unfinished, and that is a conversation, not more agents.

## A finding about your own check is a report, not a failed cycle

The severity test asks how BAD a finding is. It never asks what the finding is ABOUT, and
that gap is expensive even with the aperture rule already in force.

| The finding is about | What it is |
|:--|:--|
| **The product**: a wrong value ships, a real regression gets through | A failed cycle. Rebuild. |
| **The detector**: your matcher can be fooled by a crafted input, your check is satisfied by a decoy | **A REPORT.** One line to the requester. It never fails a cycle and never triggers a rebuild. |

**The test: would an ACCIDENTAL change produce this shape?** If closing it requires an
input hand-written to match your own check, the answer is no, and it is a report however
the reviewer graded it. **Put that question in every review prompt**, asking the reviewer
to say whether the shape is one an accidental change could produce or only a deliberately
crafted one, so it comes back stated rather than inferred. A reviewer will happily grade
its own ingenuity high.

**And the arms race has no end by construction.** A check that compares text can always be
beaten by text written to match it. Recognising the class is the stop condition. Another
cycle is not. The strike counter only counts cycles that FAILED, so a report does not
advance it, and a build whose review returns nothing but reports has converged.

## How to run a review

- **Parallel reviewers, one distinct LENS each**, not several copies of "review this". One
  lens should always be *are the checks themselves real*, and it matters most when the
  author of the checks is also the author of the code, which is usually.
- **Frame each prompt to REFUTE.** "Try hard to break it" and "say plainly if a concern is
  not real" both belong in it. The second is what stops padded findings.
- **Ask for concrete failure scenarios** with triggering state and a file and line. A
  finding you cannot reproduce is not yet a finding.
- **Findings come back as TEXT.** Reviewers never write files, never edit, never commit.
- **Absolute paths, never relative.** A reviewer's working directory is not guaranteed.

**Put a guardrail block in every prompt, verbatim.** A reviewer with tool access can do
real damage to the environment it is inspecting, up to ending the session it runs inside.
Adapt this and add the commands that are dangerous in your environment:

> HARD GUARDRAILS. Read only: do not write, edit, or create any file anywhere. Do not run
> any command that stops, restarts or reconfigures a running service. Do not kill or signal
> any process. Do not read credential stores. Do not mutate any repository. Return findings
> as text only: do not write files or reports to disk.

**Then receive the review properly.** Verify each finding against the code before acting on
it. Findings can be wrong: a confirmed finding refuted on live evidence should have its fix
reverted before it merges. Confirmed defects get fixed; refuted ones get a sentence saying
why.

## For an instruction file, the steps map differently

A skill, an agent definition or a prompt template has no runtime, so there is nothing to
execute, but every step still applies:

- **Read the contract** means read the sibling files it must not contradict: the
  always-loaded instruction files, and any skill whose scope it touches.
- **The review** is required, using the lens below.
- **Verify it fires at all.** A skill runs only when the model reads its description and
  judges it applies. There is no hook and no regex. So check the description triggers on a
  representative task, and walk one real scenario end to end against the body. This is not
  optional: a review skill once listed artifacts inside its own scope that its description
  could not possibly fire for. A rule that cannot trigger is not a rule, and nothing else in
  the workflow would have caught it.

## Reviewing a skill or a prompt is a different lens

Code review asks "can this break?". A skill is an instruction the model acts on later,
possibly unattended, so the review asks instead:

- **Is any instruction ambiguous enough to be read two ways?** One of those ways will
  happen.
- **Does it say what to do when the rule and reality disagree?** A skill silent on that
  leaves the model improvising.
- **Does it exempt anything it should not**, or hedge a hard rule into a preference?
- **Is a stated trigger detectable?** A vague description is a rule that does not run.
- **Does it contradict another instruction file or another skill?** A conflict resolved by
  the model's judgment in the moment is not a rule.
- **Would following it literally produce the outcome it claims?** Walk one scenario.

## Read the contract, not your model of it

A producer returning one set of field names, and a consumer using different ones with the
rename happening in a third function, costs a crash on the first real run. Before calling
into existing code, open it and read the return. Before relying on a schema field, find the
line that writes it. **A field name you inferred is a guess wearing a fact's clothes.**

## Validate the instrument before you believe a reading

Three ways an instrument lies, all observed:

- A count that greps the wrong file returns zero. The zero is meaningless, not negative.
- A loop with a quoting error prints zero for every candidate. Every number is false.
- A field that reports the last detected state rather than the live one reads stale for as
  long as nobody refreshes it. An alarm has fired on exactly that.

**An empty result, a zero, or a convenient answer all get one sanity check before you act
on them.** Prove the instrument can produce a different answer.

## Designing the thing itself

- **Exemptions must be principled, not a list.** State the principle once and derive every
  waiver from it. A bare list of exceptions rots; a principle tells the next reader what to
  do about the one you did not list.
- **Fail toward not acting**, and make the failure loud rather than silent. But check which
  direction safe actually points: for a rescue mechanism, failing closed permanently and
  quietly is the worse failure.
- **One implementation.** Two copies of a contract drift. Import it, do not copy it.
- **Do not add a second actor.** If one code path starts a thing and one ends it, a feature
  needing a stop extends the existing one rather than growing a second.

## Scope

The boundary of the work is the boundary of the request: a defect outside the ask is **a
sentence to the requester, not a task**, and scope growing mid-build is the signal to stop
and check in, **never to keep going because finishing feels cheaper**. The kiss skill carries
that discipline in full and pairs well with this one: a companion, not a dependency, and
crosscheck works without it.
