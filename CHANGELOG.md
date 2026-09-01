# Changelog

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
