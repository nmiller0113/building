#!/usr/bin/env python3
"""SessionStart hook: inject every shipped skill's summary at a fresh context.

Prints the shipped summary of EVERY skill in this plugin, so their rules are in the
model's context at every fresh-context boundary. A skill loads only when the model reads
its description and judges it applies, so an installed skill can sit unread for a whole
session while the model does the things it forbids. This removes that dependency on
judgement.

Claude Code adds a SessionStart hook's plain stdout to the context.

⭐ THE SKILL LIST IS DISCOVERED, NEVER HARD-CODED. An earlier version named one skill's
reminder by path. That made two ordinary events silently break the plugin's whole point:
renaming the plugin, and adding a second skill whose rules then reached nobody. Globbing
skills/*/REMINDER.md means a rename cannot break it and a new skill is picked up by
existing.

PYTHON RATHER THAN SHELL, ON PURPOSE. The first version was a bash script, which meant
this plugin's headline feature silently did nothing on any machine without bash. The gate
alongside it already needs Python, so using Python here means one runtime to have rather
than two to have separately, and it is the one more likely to be present.

Fails closed and silent: an unset CLAUDE_PLUGIN_ROOT, a missing directory, an unreadable
file or an empty one all produce no output and exit 0. A boundary hook must never turn a
session start into an error, and printing nothing is better than a false claim that a
rule is in force. Each file is READ BEFORE its header is printed, so this never announces
a rule and then emits nothing.
"""
import os
import sys


def _reminders(root):
    """(skill name, text) for every skill shipping a non-empty, readable REMINDER.md."""
    skills_dir = os.path.join(root, "skills")
    try:
        names = sorted(os.listdir(skills_dir))
    except OSError:
        return []
    out = []
    for name in names:
        path = os.path.join(skills_dir, name, "REMINDER.md")
        if not os.path.isfile(path):
            continue
        try:
            with open(path, encoding="utf-8") as fh:
                text = fh.read().strip()
        except (OSError, ValueError, UnicodeError):
            continue
        if text:
            out.append((name, text))
    return out


def _plugin_name(root):
    """The plugin's own name, read from its manifest.

    Hard-coding it meant the header made a provenance claim that a rename turned into a
    lie, in the one piece of text this plugin puts in front of the model and tells it to
    trust. Nothing here should have to be updated by hand when the package is renamed.
    """
    try:
        import json
        with open(os.path.join(root, ".claude-plugin", "plugin.json"), encoding="utf-8") as fh:
            name = json.load(fh).get("name")
        return name if isinstance(name, str) and name.strip() else None
    except Exception:  # noqa: BLE001
        return None


def main():
    root = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if not root:
        return 0
    plugin = _plugin_name(root)
    if not plugin:
        return 0
    found = _reminders(root)
    if not found:
        return 0

    for name, text in found:
        sys.stdout.write("=== %s, from the installed %s plugin ===\n\n" % (name, plugin))
        sys.stdout.write(text + "\n\n")

    # The work-order gate ships with this plugin and is DORMANT unless armed. Say so
    # once, so it is discoverable without reading the repository to find it, and so an
    # armed gate is never a surprise.
    if os.environ.get("WORKORDER_GATE") != "1":
        sys.stdout.write("A work-order gate also ships with this plugin and is currently "
                         "dormant.\nSetting WORKORDER_GATE=1 in the environment arms it.\n")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:  # noqa: BLE001
        # A boundary hook that throws prints a traceback into a context nobody is awake
        # to read. Stay quiet and stay zero.
        sys.exit(0)
