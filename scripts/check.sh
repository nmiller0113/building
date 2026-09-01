#!/usr/bin/env bash
# Release validator for the crosscheck plugin.
#
# Run by a human before publishing. Never invoked by the model, and SKILL.md does not
# reference it: a skill that tells the model to run a script to check the skill is
# theatre.
#
# Two authorities are mixed on purpose, and each check says which it enforces:
#   [spec]  the portable Agent Skills frontmatter spec (name charset, 1024 chars)
#   [house] this project's own rules, stricter than anything a loader enforces
#
#   ./scripts/check.sh          exit 0 clean, exit 1 on any FAIL
#
# No pipefail: the leak scan pipes into `grep -q`, which exits at the first match and
# SIGPIPEs its producer. With pipefail that returns 141, the `if` goes false, and a
# genuinely leaking file prints "ok". Nothing here needs pipefail.
set -u

cd "$(dirname "$0")/.." || { printf 'FAIL  cannot cd to package root\n' >&2; exit 1; }
SKILLS="skills/building skills/crosscheck"
SKILLS_MD="skills/building/SKILL.md skills/crosscheck/SKILL.md"
# Deep validation loops over EVERY skill. Hardcoding one meant naming a new
# primary skill silently dropped the other's frontmatter and body checks.
SKILL="skills/building/SKILL.md"
# DERIVED, never listed. A hardcoded set ships every new file unscanned, and the first
# version of this line excluded this validator itself, which is the file that then
# carried the very tokens it certifies absent. Exemptions must be principled: the only
# files exempt from the private-token scan are the two that legitimately carry the
# author's name, and they are named by that principle rather than by convenience.
# Tracked AND untracked-but-not-ignored, so a file written and not yet added is still
# scanned: "write file, run check.sh clean, add-commit-push" would otherwise publish it
# unscanned, which is the exact guarantee this derivation exists to make. --others with
# --exclude-standard works with zero commits too, so there is one code path, not two.
if git rev-parse --git-dir >/dev/null 2>&1; then
    SHIPPED=$( { git ls-files; git ls-files --others --exclude-standard; } \
        | sort -u | grep -vE '^(LICENSE|\.gitignore)$')
else
    SHIPPED=$(find . -type f -not -path './.git/*' -not -path '*/__pycache__/*' \
        -not -path './.claude/*' -not -name LICENSE -not -name '.gitignore' \
        -not -name 'private-tokens.txt' -not -name '*.pyc' | sed 's|^\./||')
fi
AUTHORED=".claude-plugin/plugin.json"   # legitimately carries the author name
fails=0
warns=0

fail() { printf 'FAIL  %s\n' "$1" >&2; fails=$((fails + 1)); }
warn() { printf 'WARN  %s\n' "$1" >&2; warns=$((warns + 1)); }
ok()   { printf 'ok    %s\n' "$1"; }
done_() { printf '\n%d fail, %d warn\n' "$fails" "$warns"; [ "$fails" -eq 0 ]; }

for SKILL in $SKILLS_MD; do
    [ -f "$SKILL" ] || { fail "$SKILL not found"; done_; exit 1; }

    # CRLF breaks every anchored match below, so rule it out before matching anything.
    if grep -q $'\r' "$SKILL"; then
        fail "$SKILL has CRLF line endings; convert to LF"
        done_; exit 1
    fi

    # --- frontmatter boundaries ---------------------------------------------------
    # Tolerate trailing whitespace on the fences: YAML parsers do, and a strict match
    # silently picks up a later thematic break as the closer and shifts every check.
    head -n 1 "$SKILL" | grep -qE '^---[[:space:]]*$' || fail "line 1 must be '---'"
    fm_end=$(awk 'NR>1 && /^---[[:space:]]*$/{print NR; exit}' "$SKILL")
    [ -n "$fm_end" ] || { fail "frontmatter is never closed"; done_; exit 1; }
    [ "$fm_end" -ge 3 ] || { fail "frontmatter is empty"; done_; exit 1; }
    fm=$(sed -n "2,$((fm_end - 1))p" "$SKILL")
    ok "frontmatter closes at line $fm_end"

    # --- keys must be ones we recognise -------------------------------------------
    allowed="name description license compatibility metadata allowed-tools when_to_use \
    disable-model-invocation model context hooks version author"
    while IFS= read -r key; do
        case " $allowed " in
            *" $key "*) ;;
            *) fail "unrecognised frontmatter key: $key" ;;
        esac
    done < <(printf '%s\n' "$fm" | grep -oE '^[A-Za-z0-9_-]+:' | tr -d ':')

    unquote() {
        local v=$1
        case $v in
            \"*\") v=${v#\"}; v=${v%\"} ;;
            \'*\') v=${v#\'}; v=${v%\'} ;;
        esac
        printf '%s' "$v"
    }

    # scalar_or_die enforces [house]: single-line plain scalars only. Sets SCALAR, returns
    # non-zero on failure. NOT called via $( ): command substitution runs in a subshell, so
    # a fail() inside one increments a copy of the counter and is never tallied.
    SCALAR=""
    scalar_or_die() {
        local key=$1 raw
        SCALAR=""
        raw=$(printf '%s\n' "$fm" | sed -n "s/^$key[[:space:]]*:[[:space:]]*//p" | head -n 1)
        case $raw in
            '>'*|'|'*) fail "$key: is a block scalar; keep it on one line"; return 1 ;;
        esac
        if [ -z "$raw" ]; then
            fail "$key: has no value on its own line; keep it on one line"
            return 1
        fi
        raw=$(unquote "$raw")
        case $raw in
            *[![:space:]]*) ;;
            *) fail "$key: is empty or whitespace only"; return 1 ;;
        esac
        SCALAR=$raw
    }

    # --- name ---------------------------------------------------------------------
    if scalar_or_die name; then
        name=$SCALAR
        printf '%s' "$name" | grep -qE '^[a-z0-9]+(-[a-z0-9]+)*$' \
            || fail "name '$name' must be lowercase letters, numbers and hyphens [spec]"
        [ ${#name} -le 64 ] || fail "name is ${#name} chars, spec limit is 64"
        # Compare against the SKILL's own directory, not the package's. Comparing to
        # the package basename was right when a plugin held one skill and became
        # wrong the moment it held two.
        [ "$name" = "$(basename "$(dirname "$SKILL")")" ] \
            || warn "skill name '$name' does not match its directory '$(basename "$(dirname "$SKILL")")'"
        ok "name: $name"
    fi

    # --- description: the field that decides whether the skill ever loads ----------
    if scalar_or_die description; then
        desc=$SCALAR
        n=${#desc}
        if   [ "$n" -gt 1024 ]; then fail "description is $n chars, spec limit is 1024"
        elif [ "$n" -gt 500 ];  then warn "description is $n chars, house target is 500"
        else ok "description: $n chars"
        fi
    fi

    # --- body length [house] ------------------------------------------------------
    lines=$(awk 'END{print NR}' "$SKILL")
    body=$((lines - fm_end))
    if   [ "$body" -gt 500 ]; then fail "body is $body lines, best-practice ceiling is 500"
    elif [ "$body" -gt 250 ]; then warn "body is $body lines, house target is 250"
    else ok "body: $body lines"
    fi

    # --- no code in SKILL.md [house] ----------------------------------------------
    # Any fence at all, not a language allowlist: the allowlist version passed a bare fence
    # containing a whole program. Examples here use blockquotes.
    if grep -qE '^[[:space:]]*(```|~~~)' "$SKILL"; then
        fail "SKILL.md contains a code fence; instructions belong here, code in hooks/"
    else
        ok "no code fences in SKILL.md"
    fi

    # --- referenced companion files exist -----------------------------------------
    while IFS= read -r ref; do
        while [ "${ref%[.,;:)]}" != "$ref" ]; do ref=${ref%[.,;:)]}; done
        [ -e "$ref" ] || fail "SKILL.md references '$ref', which does not exist"
    done < <(grep -oE '(\./)?(scripts|references|assets|hooks)/[A-Za-z0-9._/-]+' "$SKILL" | sort -u)
done

# --- publishable: every shipped file ------------------------------------------
# Modest by design. This catches the leaks that actually happen (a pasted path, a host,
# an address); it is not a general secret scanner and is not claimed to be.
for f in $SHIPPED; do
    [ -f "$f" ] || continue
    # A SCANNER CANNOT BE SCANNED BY ITS OWN PATTERNS: this file necessarily contains the
    # literal path, traversal and em-dash regexes it searches for, so matching them here
    # says nothing. That is a property of scanners, not a convenience exemption, and it is
    # deliberately narrow: this file IS scanned for private tokens (below), which is the
    # check that matters and the one an earlier version wrongly exempted itself from.
    case "$f" in scripts/check.sh) continue ;; esac
    # A CRLF shebang is an exec failure the executable-bit check cannot see.
    if grep -q $'\r' "$f"; then
        fail "$f has CRLF line endings; convert to LF"
    fi
    # TRAVERSAL FIRST, BEFORE ANY MASKING. Masking a path prefix strips the trigger from
    # paths that merely START there and then escape.
    if grep -qE '\.\./' "$f"; then
        fail "$f contains a '../' path segment; it can smuggle a local path past the mask"
    fi
    if grep -E '(/home/|/Users/|~/|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|\b([a-z0-9-]+\.)+(local|lan|internal)\b|\b[0-9]{1,3}(\.[0-9]{1,3}){3}\b)' "$f" >/dev/null; then
        fail "$f contains a local path, address, internal hostname, or IP"
    else
        ok "$f: no local paths, addresses or hosts"
    fi
    if grep -q '—' "$f"; then
        fail "$f contains em dashes [house]"
    fi
done

# --- this skill was extracted from a private one; prove nothing came with it ---
# THE TOKEN LIST IS NOT IN THIS REPO. Writing it here would publish, in cleartext and
# under a comment explaining what they are, exactly the names the extraction removed.
# The first version of this check did that and then excluded itself from its own scan,
# so it reported "no private tokens" while being the only file carrying them.
# Keep the words in an untracked file, one extended-regex pattern per line.
TOKENS="scripts/private-tokens.txt"
if [ -f "$TOKENS" ]; then
    hits=0
    for f in $SHIPPED; do
        [ -f "$f" ] || continue
        case " $AUTHORED " in *" $f "*) continue ;; esac
        if grep -qiEf "$TOKENS" "$f"; then
            fail "$f contains a private token from the source this skill was extracted from"
            hits=1
        fi
    done
    [ "$hits" -eq 0 ] && ok "no private tokens in any tracked file"
else
    warn "$TOKENS absent; private-token scan SKIPPED (expected for anyone but the author)"
fi

# --- the shipped hooks must actually be able to run ---------------------------
if [ ! -s hooks/hooks.json ]; then
    fail "hooks/hooks.json missing or empty; nothing this plugin ships would register"
elif command -v python3 >/dev/null 2>&1 \
        && ! python3 -c 'import json,sys;json.load(open(sys.argv[1]))' hooks/hooks.json 2>/dev/null; then
    fail "hooks/hooks.json is not valid JSON; the hooks will not register"
else
    for ref in hooks/session-start.py hooks/workorder-gate.py; do
        grep -q "$ref" hooks/hooks.json || fail "hooks/hooks.json does not reference $ref"
    done
fi
[ -s hooks/session-start.py ] || fail "hooks/session-start.py missing or empty"
[ -x hooks/session-start.py ] || fail "hooks/session-start.py is not executable"
[ -s hooks/workorder-gate.py ] || fail "hooks/workorder-gate.py missing or empty"
command -v python3 >/dev/null 2>&1 && { python3 -m py_compile hooks/session-start.py 2>/dev/null \
    || fail "hooks/session-start.py does not compile"; }
command -v python3 >/dev/null 2>&1 && { python3 -m py_compile hooks/workorder-gate.py 2>/dev/null \
    || fail "hooks/workorder-gate.py does not compile"; }
rm -rf hooks/__pycache__ 2>/dev/null
# The SessionStart hook prints this file and nothing else. Absent, it injects silently
# nothing and the plugin's headline behaviour is gone with no error anywhere.
for d in $SKILLS; do
    [ -s "$d/SKILL.md" ] || fail "$d/SKILL.md missing or empty"
    [ -s "$d/REMINDER.md" ] || fail "$d/REMINDER.md missing or empty; the shipped hook prints nothing for it"
done
ok "shipped hooks are present, valid and runnable"

# --- the manifest every install reads -----------------------------------------
MAN=".claude-plugin/plugin.json"
if [ ! -s "$MAN" ]; then
    fail "$MAN missing or empty; the plugin cannot install"
elif command -v python3 >/dev/null 2>&1; then
    if ! python3 -c 'import json,sys
d = json.load(open(sys.argv[1]))
missing = [k for k in ("name", "description", "version") if not d.get(k)]
sys.exit(1 if missing else 0)' "$MAN" 2>/dev/null; then
        fail "$MAN is not valid JSON, or is missing name/description/version"
    else
        ok "$MAN is valid and complete"
    fi
fi

# --- the gate's own battery must pass, not merely compile ---------------------
if [ -f scripts/gate-test.py ] && command -v python3 >/dev/null 2>&1; then
    if python3 scripts/gate-test.py >/dev/null 2>&1; then
        ok "gate battery passes"
    else
        fail "scripts/gate-test.py FAILS; the shipped gate does not behave as tested"
    fi
fi

# --- files a published package must carry -------------------------------------
if [ -f LICENSE ]; then
    ok "LICENSE present"
else
    if printf '%s\n' "$fm" | grep -qE '^license[[:space:]]*:'; then
        fail "no LICENSE file, but the frontmatter declares one"
    else
        fail "no LICENSE file"
    fi
fi

# --- no shipped file may hard-code a name the manifest can change ------------------
# The hook once announced a plugin name in its header. A rename turned that into a false
# provenance claim in the one text this plugin asks the model to trust, and no test read
# it, so everything stayed green while it was wrong.
name=$(python3 -c 'import json;print(json.load(open(".claude-plugin/plugin.json"))["name"])' 2>/dev/null)
if [ -n "$name" ]; then
    # The REMINDER files ARE the hook's output, so scanning only hooks/ missed the place
    # the stale name actually lived: an opening line telling every session the skill loads
    # at an address the rename had already invalidated.
    if grep -rqE "(installed (crosscheck|building|kiss) plugin|as .(crosscheck|building|kiss):)" \
            hooks/ skills/ 2>/dev/null; then
        fail "a shipped file hard-codes a plugin name or skill address; derive it or reword"
    else
        ok "no shipped file hard-codes a plugin name or skill address"
    fi
fi

# --- a declared version with no tag is a claim with no evidence -----------------
# The building skill states this rule; enforcing it here is what makes it a wall rather
# than advice, and forgetting the tag is precisely what happens after the work feels done.
if command -v git >/dev/null 2>&1 && git rev-parse --git-dir >/dev/null 2>&1; then
    v=$(python3 -c 'import json;print(json.load(open(".claude-plugin/plugin.json"))["version"])' 2>/dev/null)
    if [ -n "$v" ]; then
        if git rev-parse "v$v" >/dev/null 2>&1; then
            ok "v$v is tagged"
        else
            warn "version $v has no tag v$v yet; tag it as part of the release"
        fi
    fi
fi

done_
