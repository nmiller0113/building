#!/usr/bin/env bash
# SessionStart hook for the crosscheck plugin.
#
# Prints the shipped summary (skills/crosscheck/REMINDER.md) so it is in the model's
# context at every fresh-context boundary. A skill loads only when the model reads its
# description and judges it applies, so an installed skill can sit unread for a whole
# session while the model does the things it forbids. This removes that dependency on
# judgement.
#
# Claude Code adds a SessionStart hook's plain stdout to the context.
#
# Fails closed and silent: an unset CLAUDE_PLUGIN_ROOT, a missing file or an empty file
# all produce no output and exit 0. A boundary hook must never turn a session start into
# an error, and printing nothing is better than a false claim that the rule is in force.
set -u

root="${CLAUDE_PLUGIN_ROOT:-}"
[ -n "$root" ] || exit 0
reminder="$root/skills/crosscheck/REMINDER.md"
[ -s "$reminder" ] || exit 0

# Read BEFORE printing the header. `-s` stats the file and does not prove it is readable,
# so printing the header first can announce a rule and then emit nothing.
text=$(cat "$reminder" 2>/dev/null) || exit 0
[ -n "$text" ] || exit 0

printf '=== review discipline, from the installed crosscheck plugin ===\n\n%s\n' "$text"

# The work-order gate ships with this plugin and is DORMANT unless armed. Say so once,
# so it is discoverable without anyone having to read the repository to find it.
if [ "${WORKORDER_GATE:-}" != "1" ]; then
    printf '\nA work-order gate also ships with this plugin and is currently dormant.\n'
    printf 'Setting WORKORDER_GATE=1 in the environment arms it.\n'
fi
exit 0
