# Changelog

## 2.4.0

A build that has been made but not reviewed is the middle of a cycle, and this version says so
in both skills and in both shipped REMINDER files.

The skill already said that a failure is a confirmed critical or high finding, and already said
where the loop ends. What none of the four said is that a constraint on APPLYING a change has
no bearing on REVIEWING it. A maintenance window, a live host, a deploy freeze: each is a
reason to wait before applying, and none is a reason to leave a build sitting unreviewed,
because the review reaches nothing and changes nothing. Finish the cycles, then hand the
reviewed artifact and the constraint over together, as one decision for the requester.

The stops that are real are untouched, and they are now named alongside the new rule in each
place it appears, so that the two are not confused: a reviewer who is unavailable, a reviewer
who has not been designated yet, and scope that grows mid-build.

Landed in `building` and in `crosscheck`, in the skill body and in the shipped REMINDER of
each, so it reaches a session whether or not either skill is ever invoked.

## 2.3.0

The review loop spent its independence at exactly the moment it mattered most, and this
version turns that around.

It read: the builder holds cycles one to three, and after three failures the roles swap and
the reviewer builds four to six. The skill said out loud what that costs, that the reviewer
then reviews its own build, and called it a deliberate trade bounded by the three-cycle cap.
It is not a trade worth making. Three failures are evidence about the BUILDER, not about the
review, so the thing that should move is the builder.

The reviewer no longer moves. You designate one always-reviewer once, in your own instruction
file, and it reviews every cycle, one through six, whoever built. After three failures the
BUILDER steps up one tier and builds from the reviewer's findings. Cycle seven still does not
exist, and there is no third tier by default.

**If you are updating and your instruction file names a builder, that name no longer does
anything.** The previous version told you to name both. There is now nothing to choose: the
builder is whatever model the build was triggered from. Only the reviewer is designated.

**And it will ask you for that reviewer before its first review.** That is every fresh
install, and it is also any existing user who never named one, because the previous version
had an automatic fallback chain and this one does not. It will not
pick one for you, will not fall back to whichever model looks most capable, and will not skip
the review because nobody was named. Answer once and record it in your instruction file. If
you have no second model to name, fresh agents sharing none of the build conversation, or a
person, is a valid answer.

Two more rules the loop now carries where it used to be silent. **Where there is no tier
above your builder** (you triggered the build from your top model), it says so and keeps
building to six on the same one, rather than inventing a tier or quietly turning six cycles
into three. **Where your designated reviewer is unavailable**, whether out of quota,
erroring or unreachable, it stops and asks you. It will not substitute a different model on
the grounds that independence would technically survive it, and it will not carry on
unreviewed.

Two things travel with the designation. It is not a rank: it does not have to be the most
capable model available, and naming a mid-tier one is a valid choice rather than a
compromise. And independence is the fresh context rather than a different engine, which is
what makes the rule hold together at all: where the designated reviewer and the builder are
the same model, that is two separate fresh contexts, one building and one reviewing, and the
review is not thereby weaker. What review buys is a reader who did not write the thing.

The correction reaches every place that taught the old shape, in both skills, both shipped
REMINDER files and README.md, since a reminder is printed into a live context and a stale
sentence there outranks a correct one in a skill body that may never load. README.md gains a
"Who reviews, and who builds" section stating the whole rule in one place.

## 2.2.0

The crosscheck skill told you to do the wrong thing at the end of a review loop, and this
version fixes that sentence.

It read: a cycle returning clean, or with only mediums and lows, "is a loop that CONVERGED.
Those get fixed, those fixes still get their own review, and the work is reported as done."
So convergence, which is supposed to be the end, instead handed over a queue. Work through
it and each fix is new development needing its own review, which produces new findings,
which are also real. The skill warns about exactly that regress in its aperture section and
then instructed it here.

Convergence is a STOP now, and the leftover mediums and lows are a report rather than a
queue. Acting on them is new scope: it goes to the requester with a recommendation, and that
recommendation defaults to fixing none of them.

Two things travel with that. A severity word is an inflated claim unless it carries the
condition that triggers it, because the reviewer graded the artifact in isolation and cannot
know what makes a finding rare in the real deployment; relaying its label unweighted is how a
narrow race arrives sounding like a fire, and a yes obtained that way was manufactured rather
than given. And when findings start landing only in machinery added after convergence rather
than in the work that was asked for, the loop is eating itself, which is the last honest
place to stop.

The operational form of all three lives in the shipped REMINDER, so it reaches a session
whether or not the skill is ever invoked; the skill body carries only the reasoning, and
stays inside its length target.

The work-order gate also stopped wedging a session after a restart.

A work order stays valid for WORKORDER_GATE_MAX_AGE_H hours, twelve by default, but the
quote proving a human asked for the work was only ever checked against the CURRENT
session's transcript. So any restart inside that window carried a live order into a
session that could not verify it, and the gate read the missing quote as the thing it
exists to stop: an assistant authorising itself. Every command whose head is not on the
READ_ONLY allowlist then hard-blocked until the order aged out. Observed in the field as
roughly eight hours of blocking after an unattended overnight restart.

The two causes of an unfindable quote are not alike. One is a paraphrased or invented
quote, which must block. The other is an order whose verifying session is simply gone,
which must not. An order belonging to a dead session is now allowed through with a logged
warning saying its quote was not re-verified, which is already how the gate behaves when
the transcript cannot be read at all, so the two unverifiable cases finally act the same.
An order opened DURING the session whose quote is not in that session's user text blocks
exactly as before.

What decides it is the work order FILE's own mtime, not anything written inside the file.
That distinction is the whole design. The obvious implementation compares the order's
`opened_at` against the session start, and it is wrong: `opened_at` is written by the
assistant, which is the party this gate exists to distrust, so backdating one number would
convert any invented quote, an empty one or none at all, into an allow-with-warning.
It would also mean that editing a live order mid-session to carry a new quote left the
fabrication check disarmed for the rest of the order's twelve hours. Writing the file is
what sets its mtime, so neither move survives the mtime test. `opened_at` is kept as a
corroborating claim and a non-empty quote is now required, but the file's own timestamp is
the load-bearing one.

Everything fails closed: an unreadable session start, an unparsable stamp, an unreadable
mtime, a missing `opened_at`, or an absent quote all leave the block standing. What this
does not stop is an assistant that both backdates `opened_at` and resets the file's mtime
with an explicit utime call: an adversary controlling both the input and the check, which
is the limit this hook has always stated and still does not claim to defeat.

## 2.1.6

The release validator proves its leak pattern still discriminates before it trusts that
pattern's results, and the pattern is now defined once instead of inlined at the scan site.

This exists because the rewrite of that pattern in 2.1.5 was checked against a hand-made
corpus that could not have failed: it contained no host or address sitting next to a dot or a
hyphen, which is exactly what a wrong boundary class breaks. A corpus that cannot fail is not
a test. This one can: substituting the wrong class flips ten of its lines, and the self-test
turns that into a hard failure rather than a quiet one.

The corpus covers hosts and addresses adjacent to a period, hyphen, colon, comma, quote,
paren and bracket, with `host:port` and `IP:port` included because those are the shapes most
likely to appear in a real document. It also covers a tilde dotfile path, which is what a
narrowing of the tilde alternative would silently stop matching, and three clean lines that
exist only to tell one dropped boundary from both at once, which the other clean lines
cannot distinguish.

Nothing changes for anyone installing the plugin: the skills, both hooks and the gate are
untouched. This is the maintainer's validator guarding its own instrument.

## 2.1.5

Portability. Nothing here changes what the skills say or how the gate decides on a machine
that already worked; it removes assumptions about the machine the plugin was written on.

**The release validator could certify a release it had not checked.** It resolved its
interpreter as `python3` only, while the shipped hooks have always probed `python3` then
`python`. Two of its checks were not guarded at all and fed an empty variable into an
emptiness test, so on a box carrying only `python` the hard-coded-name scan and the
version-has-a-tag gate silently did nothing and the run still printed a clean result. The
gate that makes the tagging rule a wall rather than advice was the first wall to go. The
interpreter is now resolved once, both spellings, and its major version is probed rather than
inferred from the name. Its absence is announced once, and under `--release` it is a failure:
a release cannot be certified by a run that could not read the manifest or check the tag.

**The gate battery crashed on a stock Windows Python.** `gate-test.py` read its own source in
the locale encoding to check its corpus for a known defect; the file carries a non-ASCII
character that cp1252 cannot decode, so all 224 cases died before the first one ran. Every
read and write in the gate and its battery now names UTF-8, which also repairs the transcript
read that decides whether a work order's quote appears in something you actually typed.

**`WORKORDER_GATE_EXEMPT` was split on a literal colon**, which is the drive separator on
Windows: `C:\work\repo` became `C` plus `\work\repo`, two exemptions matching nothing and the
real one gone. It splits on the platform's own path separator now, unchanged on macOS and
Linux.

**An inline interpreter body writing only to exempt paths was never relieved on Windows**,
because that relief recognised a quoted path only when it began with `/` or `~`. It now also
recognises a drive letter and a UNC prefix. The direction of the old bug was safe, blocking
rather than allowing, but it made an exempt path unwritable by heredoc.

The publish-time leak scan no longer uses `\b`, which is a GNU extension rather than standard
ERE. Apple's grep honours it; a minimal grep such as busybox does not, and there the
internal-hostname and IP alternatives match nothing while the scan still prints "ok". The
replacement was checked to match the original identically under GNU grep.

The executable-bit assertions on the hook scripts are gone. `hooks.json` hands each path to an
interpreter, which reads the file and never consults the bit.

README: the Requirements section said no particular shell was assumed. A hook's command string
runs through a shell and both of this plugin's are POSIX, so Git Bash is a real requirement on
Windows. It says so now, and says what each hook does without it, including that the
work-order gate reports an error on every file-changing and Bash call and enforces nothing.

New `.gitattributes` pinning LF. Without it a Windows clone rewrites every tracked file to
CRLF, which breaks a script's first line and trips the validator's own CRLF check, so the
repository would reject its own checkout.

## 2.1.4

The audit line a denial writes now names what was stopped. It used to carry the block
message's first line, which for a Bash denial is the generic "file change via Bash" and
identifies no target, so the log could say a write was refused but not which one. The
reason and the target are passed explicitly now: `BLOCKED <tool> <reason>; <target>`.

Two hardening fixes came out of reviewing that. A target containing a newline could have
forged a second log line, so all whitespace in an audit field is collapsed. And a lone
surrogate in a path or in a work order's scope made the log write raise, whereupon the
blanket exception around it discarded the whole line rather than the bad character,
erasing exactly the denial record the log exists to keep.

The crosscheck skill body is back inside the house length target, reached by tightening
four passages rather than by dropping any rule.

## 2.1.3

Denials were never recorded. The log carried only what got through: the verified passes,
the skipped verifications, the fail-opens. A blocked write left no trace once the session
ended, so the one question an audit trail exists to answer was the one it could not. A
denial now appends `BLOCKED <tool> <reason>` before the gate exits.

Enforcement is unchanged. The stderr message, the exit code, and every decision the gate
makes are the same. Reported from another install running these plugins.

## 2.1.2

Fixes a test case added in 2.1.1 that used a literal path the harness does not exempt, so
it reported a false positive against its own suite. 2.1.1 shipped with that suite failing.
The case is now built from the harness's real exempt directory.

## 2.1.1

Two fixes reported from another install running these plugins, both false positives that
made the tools obstructive rather than wrong:

- The skill-name-versus-directory check fired on every installed copy, because an
  installed plugin lives in a directory named for its version rather than for itself. It
  is a development hint, so it now runs only in a source checkout.
- An inline interpreter body containing a write primitive was blocked regardless of where
  it wrote, so a file inside an exempt path could not be written that way even though the
  same write through the editing tools passed. The shell path already honoured
  exemptions; this one never consulted them.

## 2.1.0

Two release rules the skill was missing, both learned by falling into them while
publishing 2.0.0:

- A release title is the version alone. Repeating the project name buys nothing, since it
  is already on every page, and goes wrong the day the project is renamed.
- Publishing a release out of order can silently demote the current one, because release
  hosts commonly mark the most recently created release as latest rather than the highest
  version. Backfilling history quietly pointed the repository at its oldest version. Such
  a release is now created with the host's latest flag off rather than repairing the
  demotion afterwards, which leaves a window advertising the wrong version.

`scripts/check.sh` gained a `--release` mode. At build time a version may legitimately
have no tag yet, so that is a warning; at release time it is a failure, which is what the
skill has been telling everyone else to do while this repo only warned. The release mode
also asks the host which release it advertises as latest and fails when that is not the
highest tag, so the rule above is enforced rather than remembered.

## 2.0.0

**Breaking: the plugin is renamed from `crosscheck` to `building`.** Existing installs
will not update across the rename. Install `building@nates-plugins` and remove
`crosscheck@nates-plugins`.

The plugin had been named after one of its practices, the review loop, and then treated
as the whole build discipline. Versioning, tagging and releasing are building practices
and were nowhere in it.

**New: the `building` skill.** The spine of the work: read the real contract rather than
a memory of it, implement, review, then make it findable. It carries what makes a version
real (one source of truth for the number, an annotated tag on the commit that declares
it, a release carrying the same text as the changelog), what a release note is actually
for, the repository conventions that are cheap at setup and expensive to retrofit, and a
definition of finished that is not "it runs".

**`crosscheck` is now a skill inside it**, not the whole plugin. Its content is unchanged:
the review discipline, bounded in how wide it looks and how many times it runs.

**The work-order gate now allowlists readers instead of listing writers.** A list of
commands known to write can only ever be incomplete, and every gap in it is silent. This
one shipped four rounds of one-more-missing-writer. The question is now inverted: a
command passes when it is known to only read, and anything unfamiliar needs a work order.
Failures became visible instead of silent. Newly stopped, all previously allowed:
`terraform apply`, `kubectl apply`, `pip install`, `cargo build`, `black .`, `./build.sh`,
and any tool the gate has never heard of.

**Fixed in the gate**, each found by review and each now pinned by a test:

- `2>&1` and `>&2` parsed as phantom command heads, blocking roughly 12% of ordinary
  read-only commands.
- An unquoted `VAR=$(cmd)` substitution was never captured, which both blocked reads with
  a nonsense message and let a write inside one through silently.
- `parallel <writer>` and `eval '<writer>'` passed with no message anywhere.
- `command -v <name>` blocked for any unlisted name, though it executes nothing.
- Read-only shell builtins were missing from the allowlist.
- A `CONDITIONAL` set was defined, documented as driving per-command scrutiny, and never
  referenced. Removed.

**The SessionStart hook no longer hard-codes anything.** It discovers every
`skills/*/REMINDER.md` rather than naming one file, and reads the plugin's name from its
own manifest. Both were hard-coded, so a rename or a second skill would have silently
shipped rules that reached nobody, and the header would have claimed the wrong plugin.

**The hook is Python rather than bash**, so the plugin's headline feature no longer
depends on a shell that may not exist. Both hooks probe `python3` then `python` and do
nothing at all if neither is present.

**`scripts/check.sh` enforces what the skill asks of everyone else:** a declared version
with no matching tag, or no changelog entry, stops the release. It also validates both
skills, the manifest, and runs the gate's own battery.

## 1.0.0

First release, as `crosscheck`. The review discipline as a skill, a declarative summary
injected at every fresh context, and a dormant work-order gate.
