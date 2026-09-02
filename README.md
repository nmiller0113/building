# building

Two Claude Code skills for building something and actually finishing it.

Claude will finish a change, report it as working, and leave. What is missing is not
effort, it is the two things that come after the part that felt like the work: an
independent check on what was just done, and making the result findable. So a version
number ends up in a manifest with no tag behind it, a release nobody can read, and a
comment describing what the code used to do.

## Install

```
/plugin marketplace add nmiller0113/claude-marketplace
/plugin install building@nates-plugins
```

Then `/reload-plugins`, or restart. Update later with
`/plugin update building@nates-plugins` followed by `/reload-plugins` again.

## The two skills

**`building`** is the spine: read the real contract rather than a memory of it,
implement, review, then make it findable. It carries what makes a version real (one
source of truth, an annotated tag on the commit that declares it, a release carrying the
same text as the changelog), what a release note is actually for, the repository
conventions that are cheap at setup and expensive to retrofit, and a definition of
finished that is not "it runs".

**`crosscheck`** is the review discipline it hands off to, and it is bounded at both
ends. **How wide:** a review looks at what changed and nothing else, asking two questions
only. Ask it what else is wrong and it will tell you, forever, because an uncovered
codebase plus a reviewer told to hunt is an unbounded list. **How many times:** the
builder gets three cycles, then the roles swap and the reviewer builds, then it stops at
six and comes back to you. Six failed cycles means the problem is misunderstood rather
than unfinished, and that is a conversation.

They ship together because they are one practice. Use `building` and it will reach for
`crosscheck` at step three.

## How they fire

Three ways, in increasing order of reliability. The third is on by default.

**Automatically.** Claude reads a skill's description and loads it when it judges the
task matches.

**On demand: `/building:building` or `/building:crosscheck`.** Reach for the second when
Claude has already declared something done without checking it.

**Always, via the shipped hook.** A skill only enters Claude's context when it is
*invoked*, and automatic invocation is a judgment call Claude can miss. So this plugin
registers a `SessionStart` hook that runs at every fresh context, including after
compaction, and prints a declarative summary of **every** skill it ships.

Nothing to configure. The summaries live inside the plugin, so they update when it does,
and the hook discovers them rather than naming them, so adding a skill cannot silently
leave its rules unshipped. If a file is missing or unreadable the hook prints nothing at
all, so a broken install fails quiet rather than claiming a rule is in force when it is
not.

If you write your own summary instead, write it as statements of fact, not as commands.
Claude's prompt-injection defenses surface command-shaped hook text to the user rather
than absorbing it, which leaves you with a rule that reads well and never applies.

## The work-order gate: off unless you turn it on

The skills above are text, and text is followed by judgment. The plugin also ships a
`PreToolUse` hook that takes two of those rules out of judgment entirely.

**It is dormant.** Nothing happens until you set `WORKORDER_GATE=1` in your environment.
A plugin that hard-blocks a stranger's first edit reads as a broken install, not a
methodology.

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

Optional environment variables: `WORKORDER_GATE_STATE` moves the file,
`WORKORDER_GATE_EXEMPT` takes path prefixes needing no work order, separated by your
platform's path separator (`:` on macOS and Linux, `;` on Windows, because a Windows path
already contains a colon),
`WORKORDER_GATE_MAX_AGE_H` sets how long an order stays valid (default 12), and
`WORKORDER_GATE_IGNORE_PREFIXES` marks message prefixes that are not you, for setups that
inject scheduled prompts. Add `.claude/workorder.json` and its `.log` sibling to your
`.gitignore`.

**How it decides, and what it cannot do.** It parses the command rather than pattern
matching it, so quoted strings, comments, arithmetic and heredoc bodies are never mistaken
for redirects. Then it asks whether the command is one **known to only read**. Anything
else needs a work order.

That direction is deliberate. A list of commands known to *write* can only ever be
incomplete, and every gap in it is silent; a list of known readers is incomplete too, but
its gaps are visible and cost one work order. An unfamiliar tool is stopped, not waved
through.

The bounded part is the shell. An interpreter's **inline** script is scanned for write
calls as a best effort, and a script already on disk is never read at all, so
`python3 build.py` passes. An inline body written deliberately to slip past that scan will
slip past it. The gate exists to stop unasked-for work, not to contain an adversary.

It fails **open**: any error lets the call through, logged and surfaced to you, so a
permanently broken gate cannot quietly masquerade as a working one.

One more thing worth knowing: the quote check proves the words are **present** in
something you typed, not that you meant them as permission for this. A fragment of a
sentence still matches the sentence.

## Requirements

Python 3 on PATH, as `python3` or `python`. Both hooks probe for both spellings and do
nothing at all if neither is there, so the plugin degrades to plain skills rather than
erroring.

A POSIX shell for the hooks themselves. Claude Code runs a hook's command string through a
shell (`sh` on macOS and Linux, Git Bash on Windows), and the two command strings this
plugin registers are POSIX shell, so they need one of those.

**On Windows without Git Bash, install Git Bash before relying on the gate.** Claude Code
falls back to PowerShell there, which cannot parse either command string, and the two hooks
degrade differently:

- **The skills still load and work normally.** They are text and need no shell.
- **The `SessionStart` reminder** reports one non-blocking hook error at boot and prints
  nothing. You lose the always-on summary, not the skills.
- **The work-order gate enforces nothing.** It is a `PreToolUse` hook, so the failure is not
  a one-off at start-up: it reports a non-blocking hook error on *every* file-changing and
  Bash call, and because a non-zero exit that is not 2 does not block, every one of those
  calls proceeds ungated. Setting `WORKORDER_GATE=1` on such a box gives you the errors
  without the gate.

No distro is assumed, no package manager, and no path layout.

## Pairs well with kiss

[kiss](https://github.com/nmiller0113/kiss) governs **what** to build: the boundary of the
ask, the floor beneath it, and the closing offer. This governs **how** to build it and
when it is done.

A companion, not a dependency. Neither needs the other.

## License

MIT.
