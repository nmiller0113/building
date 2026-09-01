# crosscheck

A Claude Code skill that makes Claude review what it builds, and stop reviewing when the
review is done.

Claude will happily finish a change and report it as working without anyone checking it.
Ask it to check, and the opposite failure appears: it finds a real defect, fixes it, finds
another because the fix is new code, and the loop never closes. Both are the same missing
thing, a review with defined edges. crosscheck gives it two: how wide a review may look,
and how many times it may run.

## Install

```
/plugin marketplace add nmiller0113/claude-marketplace
/plugin install crosscheck@nates-plugins
```

Then `/reload-plugins`, or restart. Update later with
`/plugin update crosscheck@nates-plugins` followed by `/reload-plugins` again.

## The method

1. **Read the real contract.** The source of the thing being called, not a memory of it.
2. **Implement.**
3. **Send it for adversarial review, unprompted, every time.** Three strikes, then the
   roles swap, three more, then stop at six and come back to you.

The reviewer is whatever independent context you have: a second model, fresh subagents
that never saw the build conversation, or you. Independence from the build is the property
that matters, not which engine provides it.

## How it fires

Three ways, in increasing order of reliability. The third is on by default once the plugin
is installed; the first two are how it reaches Claude in the moment.

**Automatically.** Claude reads the skill's description and loads it when it judges the
task matches: creating or changing anything executable or rule-bearing.

**On demand: `/crosscheck:crosscheck`.** Loads it right now. Reach for this when Claude has
already declared something done without checking it.

**Always, via the shipped hook.** A skill only enters Claude's context when it is
*invoked*, and automatic invocation is a judgment call Claude can miss. So this plugin
registers a `SessionStart` hook that runs at every fresh context, including after
compaction, and prints `skills/crosscheck/REMINDER.md`: a declarative summary of the rules.

Nothing to configure. Because the summary ships inside the plugin, it updates whenever the
plugin does, unlike a copy pasted into a hook of your own. The hook prints nothing at all
if the file is missing or unreadable, so a broken install fails quiet rather than claiming
a rule is in force when it is not.

If you write your own summary instead, write it as statements of fact, not as commands.
Claude's prompt-injection defenses surface command-shaped hook text to the user rather than
absorbing it, which leaves you with a rule that reads well and never applies.

## The work-order gate: off unless you turn it on

The skill above is text, and text is followed by judgment. The plugin also ships a
`PreToolUse` hook that removes two of its rules from judgment entirely.

**It is dormant.** Nothing happens until you set `WORKORDER_GATE=1` in your environment.
That is deliberate: a plugin that hard-blocks a stranger's first edit reads as a broken
install, not a methodology.

Armed, it enforces two things:

- **Before the first file change**, a work order must exist at
  `<project>/.claude/workorder.json` whose `quote` field is verbatim findable in something
  **you actually typed** this session. It reads the live transcript to check, which is the
  point: Claude cannot write its own permission slip.
- **A commit is blocked** while that work order says a review is owed and records none.

```json
{ "quote": "your literal words asking for this",
  "scope": "one line: what is about to change",
  "review": "required",
  "opened_at": 1788290000 }
```

Configuration, all optional environment variables: `WORKORDER_GATE_STATE` moves the file,
`WORKORDER_GATE_EXEMPT` takes colon-separated path prefixes that need no work order,
`WORKORDER_GATE_MAX_AGE_H` sets how long an order stays valid (default 12), and
`WORKORDER_GATE_IGNORE_PREFIXES` marks message prefixes that are not you, for setups that
inject scheduled prompts. Add `.claude/workorder.json` and its `.log` sibling to your `.gitignore`.

**What it can and cannot do, plainly.** It fails **open**: any error lets the call through,
because a gate that wedges a session costs more than the gap it closes. Every fail-open is
logged and surfaced to you, so a permanently broken gate cannot masquerade as a working
one. It detects writes by parsing the command, so quoted strings and heredoc bodies are never
mistaken for redirects, and it recognises a **fixed set** of writing commands: an
unrecognised tool that writes will pass, so an allowed command is not proof of anything.
Writes inside an interpreted script are caught only when the script is **inline**, as a
`-c` argument or a heredoc; a script already on disk is never read, so `python3 build.py`
is invisible to it. An inline body written deliberately to slip past the scan will slip
past it. Those limits are the design, not an oversight: the gate exists to stop
unasked-for work, not to contain an adversary. It needs `python3` on PATH.

One more thing worth knowing: the quote check proves the words are **present** in
something you typed, not that you meant them as permission for this. A fragment of a
sentence still matches the sentence.

## Pairs well with kiss

[kiss](https://github.com/nmiller0113/kiss) governs **what** to build: the boundary of the
ask, the floor beneath it, and the closing offer. crosscheck governs **how** to build it:
the contract, the review, and where the review stops.

A companion, not a dependency. crosscheck works alone, and restates the two rules the two
skills share, because a rule about writing review prompts has to live where review prompts
get written.

## License

MIT.
