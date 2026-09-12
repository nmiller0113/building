This summary ships with the crosscheck skill. Where the plugin is installed, the full
text loads through the Skill tool under this plugin's crosscheck skill, and where that
text is not loaded, the statements below are the rule in effect.

- Anything executable or rule-bearing that gets created or changed goes for an
  independent adversarial review before it is called done. That covers scripts, hooks,
  skills and prompt templates, service units, permission rules, and the behavioural rules
  written into always-loaded instruction files. All means all, not only the parts that
  looked risky, and the characteristic failure is narrowing the rule until the thing in
  hand falls just outside it.
- The reviewer is whichever model the requester designated as their always-reviewer, named
  once in their instruction file rather than chosen per task, and it reviews every cycle
  whoever built. The designation is not a rank and need not be the most capable model
  available. Independence is the fresh context rather than a different engine: where the
  designated reviewer and the builder are the same model, that is two separate fresh
  contexts, one building and one reviewing, and the review is not thereby compromised.
  Where no reviewer has been designated yet, which is the state of every fresh install, the
  designation is ASKED FOR before the first review rather than chosen by the assistant or
  skipped, and the requester is the one who records it in their instruction file. Where the
  requester has no second model to name, fresh agents sharing none of the build
  conversation, or a person, is a valid answer FROM THEM to that designation question.
- A designated reviewer that is unavailable, out of quota or erroring is a STOP and a
  question to the requester. It is never grounds to substitute another model, to stand in
  fresh agents of some other model, or to proceed unreviewed. The stand-in above is an
  answer the requester gives when designating, never one the assistant reaches for mid-loop.
- A constraint on APPLYING the result is not an ending. A maintenance window, a live host or a
  deploy freeze is a reason to wait before applying a change and never a reason to stop
  reviewing one, since the review reaches nothing and changes nothing: a build that has been
  made but not reviewed is the middle of a cycle. The reviewed artifact and the constraint go to
  the requester together, as one decision. This does not touch the stops that are real: the
  unavailable reviewer and the missing designation above, and scope that grows mid-build, each
  stop the loop on their own terms.
- A review's aperture is the change and nothing wider. It asks two questions only: does
  this change do what it claims, and did it break what already worked. A prompt that asks
  what else is wrong, names a surface the change did not touch, or asks for further
  instances of a defect class commissions findings rather than checking work. Those
  findings are real and still manufactured, and a limit on review rounds does not bound
  them, because it constrains how many times the work is looked at rather than how widely.
  Findings outside the change are recorded for the requester rather than acted on, and
  never handed over as discoveries. The narrow exception is a change to a shared contract,
  whose reviewer may follow that contract to its call sites.
- A finding is bounded by what it is about rather than only by how bad it is. A finding
  about the delivered work is a result to act on. A finding about the check the builder
  wrote, that the check can be circumvented by an input built to match it, is a report: it
  obliges no rebuild and advances no counter, whatever severity the reviewer assigned. The
  test is whether an accidental change produces that shape, and where closing it needs an
  input hand-crafted against the check, it does not.
- The loop is bounded at six cycles, counted per distinct change rather than per body of
  work, where a cycle is one build-or-fix attempt plus one review of it. The builder is
  whatever model the build was triggered from, and it holds cycles one to three; after three
  failures it steps up exactly one tier and that next tier builds four to six from the
  reviewer's findings, while the designated reviewer reviews all six. Where there is no tier
  above the builder, that is said out loud and the loop keeps building to six on the same
  model rather than inventing a tier or stopping at three. Three failures
  are evidence the builder is the wrong instrument rather than the review, which is why the
  builder moves and the reviewer does not. A cycle fails on a confirmed
  critical or high finding; mediums and lows are a sentence to the requester rather than
  another cycle. The same defect re-attempted under a new name is the same defect.
- The terminator fires on six FAILURES rather than on six cycles elapsed. A cycle that
  comes back clean, or with only mediums and lows, is a loop that CONVERGED, and
  convergence is a stop. Describing finished work as halted by a rule reports a wall that
  was never hit. The severity call at that last cycle belongs to the reviewer rather than
  the builder, and an ambiguity at the terminator is never resolved toward convergence.
- The mediums and lows left at convergence are a REPORT, not a queue. They are not work
  that has yet to be done; they are what the loop decided not to do. Acting on them is new
  scope, and new scope is the requester's to authorise, in one line, with a recommendation
  attached whose default is to fix none of them.
- A severity word travels with its trigger condition or it is an inflated claim. "Can
  report success while the state is wrong" is true of most checks and tells the requester
  nothing; the same finding qualified with what must coincide for it to happen, and how
  briefly, is one they can price in seconds. A reviewer grades the artifact in isolation
  and cannot know the deployment reality that makes a finding rare, so its label is an
  input to that judgment rather than a verdict to pass along. Relaying an unweighted
  severity is how a narrow race arrives sounding like a fire, and consent obtained that
  way was manufactured rather than given.
- When the findings start landing only in machinery added after convergence, rather than
  in the work that was asked for, the loop is eating itself: stop and hand it back. That
  boundary is visible while it is happening.
- Cycle counts are stated as they happen, in the message where each one lands. A count
  reassembled afterwards is the count that gets talked down.
- Before a reading is believed, the instrument that produced it is checked: an empty
  result, a zero, or a conveniently confirming answer each get one proof that the
  instrument can produce a different answer.
