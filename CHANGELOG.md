# Changelog

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
