This summary ships with the crosscheck skill. Where the plugin is installed, the full
text loads through the Skill tool under this plugin's crosscheck skill, and where that
text is not loaded, the statements below are the rule in effect.

- Anything executable or rule-bearing that gets created or changed goes for an
  independent adversarial review before it is called done. That covers scripts, hooks,
  skills and prompt templates, service units, permission rules, and the behavioural rules
  written into always-loaded instruction files. All means all, not only the parts that
  looked risky, and the characteristic failure is narrowing the rule until the thing in
  hand falls just outside it.
- The reviewer is the most independent capable context available: a different model,
  otherwise fresh agents sharing none of the build conversation, otherwise a person.
  Independence from the build context is the property that matters rather than the engine.
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
  work, where a cycle is one build-or-fix attempt plus one review of it. The builder holds
  cycles one to three and the reviewer holds four to six. A cycle fails on a confirmed
  critical or high finding; mediums and lows are a sentence to the requester rather than
  another cycle. The same defect re-attempted under a new name is the same defect.
- The terminator fires on six FAILURES rather than on six cycles elapsed. A cycle that
  comes back clean, or with only mediums and lows, is a loop that converged: those fixes
  still get reviewed, and the work is then done. Converged has never meant unreviewed, and
  describing finished work as stopped by a rule reports a wall that was never hit.
  The severity call at that last cycle belongs to the reviewer rather than the
  builder, and an ambiguity at the terminator is never resolved toward convergence.
- Cycle counts are stated as they happen, in the message where each one lands. A count
  reassembled afterwards is the count that gets talked down.
- Before a reading is believed, the instrument that produced it is checked: an empty
  result, a zero, or a conveniently confirming answer each get one proof that the
  instrument can produce a different answer.
