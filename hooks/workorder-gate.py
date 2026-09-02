#!/usr/bin/env python3
"""workorder-gate.py - authorisation and review gate for file-changing tool calls.

WHY THIS EXISTS
  A skill is text. Every check it describes lives inside the assistant's judgment at
  the moment the assistant is most motivated to skip it. This hook moves two of those
  checks out of judgment and into the harness.

WHAT IT ENFORCES
  1. SCOPE. Before the first file change, a WORK ORDER must exist naming, in the USER'S
     OWN WORDS, what was asked. The quote is verified against the real session
     transcript on disk, so the assistant cannot author its own authorisation.
  2. REVIEW. A work order declares whether a review is owed. A commit is blocked
     while one is owed and unrecorded.

FAIL-OPEN, DELIBERATELY. A gate that wedges a session is worse than the gap it closes.
  Any unexpected error lets the call through and is logged. It blocks only when certain.
  Because a permanently-failing-open gate is indistinguishable from a working one, every
  fail-open is logged AND surfaced to the user via systemMessage.

FALSE POSITIVES ARE THE OTHER REAL FAILURE MODE. The first thing anyone does with an
  obstructive gate is switch it off, which costs more than the gap it closed. So the
  command is TOKENIZED in one quote-aware pass before anything is matched. Quoted
  strings, comments, arithmetic and heredoc bodies are never scanned as shell. An
  earlier regex-over-the-raw-string version blocked 23% of ordinary read-only commands.

WHAT IT CANNOT DO. Writes performed inside an interpreted script are detected by
  scanning the script body for write primitives. A body written deliberately to evade
  that scan will evade it, and a script already on disk is never read at all. The scan's
  job is catching an ACCIDENTAL write, not defeating an adversary who controls both the
  input and the check.

CONFIGURATION (all optional, all environment):
  WORKORDER_GATE          set to 1 to ARM the gate. Dormant otherwise.
  CLAUDE_PROJECT_DIR      project root. Falls back to the payload's cwd, then $HOME.
  WORKORDER_GATE_STATE    work-order path. Default <root>/.claude/workorder.json
  WORKORDER_GATE_EXEMPT   colon-separated extra path prefixes needing no work order.
  WORKORDER_GATE_MAX_AGE_H  work-order lifetime in hours. Default 12.
  WORKORDER_GATE_IGNORE_PREFIXES  colon-separated message prefixes treated as not-the-user.
"""
import json, os, re, sys, tempfile, time

DEFAULT_MAX_AGE_H = 12

# ⭐ THE ALLOWLIST. A list of commands known to WRITE can only ever be incomplete: this
# gate shipped four rounds of "one more missing writer" (rm, then piped xargs rm, then
# for-loops hiding the head, then a here-string swallowing the rest of the line). Each
# miss was silent, which is the failure that matters. So the question is inverted: a
# segment passes when its resolved head is a command known to only READ. Anything else
# needs a work order.
#
# The failure direction flips with it. An unlisted read-only tool now BLOCKS, which costs
# one work order and is visible; an unlisted writer no longer passes silently.
#
# This bounds the SHELL level only. An interpreter's inline body is still a best-effort
# scan (see BODY_WRITE), because the interpreters are on this list: they are the primary
# way anything gets read here, and gating every one of them would make the gate
# unusable. That limit is stated in the docstring and the README rather than hidden.
READ_ONLY = {
    # reading files and directories
    "cat", "head", "tail", "less", "more", "nl", "od", "xxd", "strings", "file",
    "ls", "dir", "find", "tree", "stat", "readlink", "realpath", "basename", "dirname",
    "du", "df", "wc", "cksum", "md5sum", "sha1sum", "sha256sum", "b2sum",
    # searching and transforming a STREAM (none of these write without a redirect,
    # and a redirect is caught separately)
    "grep", "egrep", "fgrep", "rg", "ag", "ack", "diff", "comm", "cmp", "join",
    "cut", "paste", "tr", "rev", "fold", "expand", "unexpand", "column", "uniq",
    "jq", "yq", "xmllint", "base64", "iconv", "date", "seq", "printf", "echo",
    # sed and awk are read-only WITHOUT -i, which is checked separately below
    "sed", "awk", "gawk", "mawk",
    # navigation and shell builtins that change no file
    "cd", "pwd", "true", "false", "test", "[", "[[", "type", "which", "command",
    "hash", "alias", "set", "unset", "export", "local", "read", "eval", "exit",
    "return", "shift", "getopts", "let", "declare", "typeset", "readonly", "source",
    "sleep", "wait", "jobs", "kill", "trap", "umask", "ulimit", "id", "whoami",
    "break", "continue", ":", "exec", "disown", "pushd", "popd", "dirs", "times",
    "]]", "]",
    "caller", "builtin", "enable", "logout", "suspend", "fc", "history",
    "groups", "hostname", "uname", "arch", "tty", "env", "printenv", "locale",
    # process and system inspection
    "ps", "top", "htop", "pgrep", "pidof", "lsof", "uptime", "free", "vmstat",
    "iostat", "netstat", "ss", "ip", "ifconfig", "dmesg", "journalctl", "systemctl",
    "service", "lscpu", "lsblk", "lsusb", "lspci", "mount", "getent",
    # version control, reading only. The write verbs are handled by the git branch.
    "git", "gh", "hg", "svn",
    # language and tool inspection that does not write by itself
    # ⚠️ THE LINE FOR THIS LIST: a command belongs here only if its ORDINARY USE creates
    # or modifies nothing. A build tool, a package manager and a deploy tool all fail
    # that test, and putting them here was the first mistake made writing this list:
    # `terraform apply`, `kubectl apply`, `pip install` and `cargo build` were all
    # allowed by a gate whose entire purpose is stopping unasked-for changes. They are
    # deliberately absent, and gating them costs one work order each.
    #
    # The interpreters ARE here, because they are the primary way anything gets read and
    # gating every one would make this unusable. Their inline bodies get the best-effort
    # scan instead, and that limit is stated rather than hidden.
    "python", "python2", "python3", "node", "nodejs", "perl", "ruby", "deno", "bun",
    "php", "osascript",
    # test runners: running what already exists is the floor of verification, and
    # blocking it would obstruct the one thing the method requires before claiming done
    "pytest", "tox", "jest", "mocha", "vitest", "rspec", "phpunit", "unittest",
    # network and remote inspection that writes nothing locally
    "http", "ping", "dig", "nslookup", "host", "traceroute", "nc", "ssh",
    # shells and wrappers: their contents are resolved recursively, never trusted
    "sh", "bash", "zsh", "ksh", "dash", "sudo", "doas", "nohup", "setsid", "stdbuf",
    "time", "timeout", "nice", "ionice", "watch", "xargs", "parallel",
    "man", "help", "info", "whatis", "apropos",
}
# Commands that place bytes in a file or remove one, and where their destination sits.
#   all    - every non-flag operand
#   last   - the final operand, when there are at least two
#   opt:X  - the value of flag X (comma-separated alternative spellings allowed)
#   cwd    - writes into the working directory under a name the command does not name
WRITE_CMDS = {
    "cp": "last", "install": "last", "rsync": "last", "ln": "last",
    # mv REMOVES its source. Checking only the destination made `mv important.py
    # /tmp/x` an ungated delete of a project file, because the destination sat in the
    # exempt temp dir. Every operand of an mv is a file change.
    "mv": "all",
    "tee": "all", "truncate": "all", "touch": "all", "patch": "all", "shred": "all",
    # Deletion is a file change. Omitting it while BODY_WRITE counted os.remove made the
    # gate inconsistent with itself, and an unrequested rm -rf is the single most
    # damaging thing this exists to stop.
    "rm": "all", "rmdir": "all", "unlink": "all", "mkdir": "all",
    # GNU long spellings write the same file the short flags do: `sort --output=d.txt`
    # and `curl --output page.html` were invisible while only -o was known.
    "dd": "opt:of=", "sort": "opt:-o,--output", "curl": "opt:-o,--output",
    "wget": "dl:-O,--output-document",
    # Extractors write names chosen by their payload, not by the command line.
    "tar": "cwd", "unzip": "cwd", "gunzip": "cwd", "bunzip2": "cwd",
}

# Wrappers that delay the real command, mapped to how many operands they consume first.
WRAPPERS = {"sudo": 0, "command": 0, "env": 0, "nohup": 0, "setsid": 0, "stdbuf": 0,
            "time": 0, "timeout": 1, "nice": 0, "ionice": 0, "watch": 0}
# Wrapper flags that take a SEPARATE value. Popping only the flag left the value
# standing as the head: `sudo -u bob rm /etc/f` resolved its head to `bob` and the rm
# sailed through.
WRAPPER_VALUE_FLAGS = {
    "sudo": {"-u", "-g", "-h", "-p", "-U", "-C", "-D", "-R", "-T", "-r", "-t",
             "--user", "--group", "--host", "--prompt", "--other-user",
             "--close-from", "--chdir", "--chroot", "--role", "--type"},
    "env": {"-u", "-C", "-S", "--unset", "--chdir", "--split-string"},
    "nice": {"-n", "--adjustment"},
    "ionice": {"-c", "-n", "-p", "-P", "-u", "--class", "--classdata"},
    "timeout": {"-s", "-k", "--signal", "--kill-after"},
    "stdbuf": {"-i", "-o", "-e"},
    "watch": {"-n", "-d", "--interval", "--differences"},
}
# xargs flags that take a separate value, for _xargs_inner.
XARGS_VALUE_FLAGS = {"-n", "-I", "-L", "-P", "-d", "-s", "-E", "-e", "-i", "-a", "-J",
                     "--max-args", "--max-procs", "--max-lines", "--max-chars",
                     "--delimiter", "--eof", "--arg-file", "--replace",
                     "--process-slot-var"}
# Shell reserved words that stand in front of the real command inside a compound.
# The WRITE_CMDS lookup used to run against the keyword itself, so
# `for f in a b; do cp $f /etc/backup/; done` and `if [ -f x ]; then rm x; fi` were
# never seen as writes: the write segment's head was `do` / `then`. `case` needs its
# own handling (the arm pattern follows `in`), as does a glued subshell paren
# (`(cp a b)` tokenizes its head as `(cp`); both live in words_of.
RESERVED_WORDS = {"if", "then", "elif", "else", "fi", "while", "until", "do",
                  "done", "esac", "in", "coproc",
                  "{", "}", "!", "[[", "]]"}
# -i / -pi mean in-place. Uppercase must be excluded, or perl -Ilib matches on the i in
# lib and a read-only one-liner is reported as an edit.
IN_PLACE = re.compile(r"^(-i(\..*)?|--in-place(=.*)?)$|^-[a-hj-z]*i[a-hj-z]*$")
INTERPRETERS = ("python", "python2", "python3", "node", "nodejs", "perl", "ruby",
                "deno", "bun", "osascript", "php")
SHELLS = ("sh", "bash", "zsh", "ksh", "dash")
BODY_WRITE = re.compile(
    # The mode must follow a comma or be the mode= keyword. Without that, [^)]* skips to
    # the first quoted string and open('x') reads as a write.
    r"open\s*\((?:[^()]|\([^()]*\))*?,\s*['\"][rwa+bxt]*[wax][rwa+bxt]*['\"]"
    r"|open\s*\([^)]*mode\s*=\s*['\"][rwa+bxt]*[wax][rwa+bxt]*['\"]"
    # A real call is preceded by ')' or an identifier. A mention inside a string or a
    # regex literal is preceded by a quote or an escape. stdout/stderr are not files.
    r"|(?<![\\'\"])(?<!stdout)(?<!stderr)\.(write|writelines|write_text|write_bytes)\s*\("
    r"|(?<![A-Za-z0-9_])(writeFileSync|writeFile|createWriteStream|appendFileSync|appendFile)\s*\("
    r"|(?<![A-Za-z0-9_.])shutil\.(copy|copy2|copyfile|move|rmtree)"
    r"|(?<![A-Za-z0-9_.])(File|FileUtils)(\.|::)(delete|unlink|rename|rm_rf|rm|mv|cp)\s*[\s(]"
    # Matched on the METHOD, not on an `fs.` receiver: the idiomatic spelling is
    # require('fs').unlinkSync(...), where the receiver is a call and not the name.
    r"|(?<![\\'\"])\.(unlinkSync|rmSync|rmdirSync|renameSync|mkdirSync|appendFileSync)\s*\("
    r"|(?<![A-Za-z0-9_.])os\.(replace|rename|remove|unlink|mkdir|makedirs|rmdir)"
    r"|(?<![A-Za-z0-9_.])Path\([^)]*\)\.(write_text|write_bytes|touch|unlink|mkdir|rename)"
)
REDIR_OPS = (">>", ">|", ">")


# --------------------------------------------------------------------------- tokenizer
class Tok:
    __slots__ = ("text", "op")

    def __init__(self, text, op=None):
        self.text, self.op = text, op


def tokenize(cmd):
    """One quote-aware pass. Returns (segments, heredocs, substs).

    segments  list of token lists, split on ; && || | &
    heredocs  list of (segment_index, body)
    substs    list of command-substitution bodies found inside double quotes

    Everything that is not shell is skipped IN THE SAME PASS that tracks quoting, which
    is the point: a pre-pass regex over the raw string cannot tell a heredoc operator
    from the same characters inside a quoted argument, and that mistake both invented
    writes and swallowed real ones.
    """
    segments, heredocs, substs = [], [], []
    seg, buf, has_word = [], "", False
    pending = []
    i, n = 0, len(cmd)

    def flush():
        nonlocal buf, has_word
        if has_word:
            seg.append(Tok(buf))
        buf, has_word = "", False

    def endseg():
        nonlocal seg
        flush()
        if seg:
            segments.append(seg)
        seg = []

    while i < n:
        c = cmd[i]

        if c == "#" and not has_word:
            j = cmd.find("\n", i)
            i = n if j == -1 else j
            continue

        if c == "'":
            j = cmd.find("'", i + 1)
            if j == -1:
                buf += cmd[i + 1:]
                has_word = True
                break
            buf += cmd[i + 1:j]
            has_word = True
            i = j + 1
            continue

        if c == '"':
            # Honour backslash escapes. find() closed the string at the first \" and the
            # remainder was then parsed as shell, inventing redirect targets.
            j, out = i + 1, []
            while j < n and cmd[j] != '"':
                if cmd[j] == "\\" and j + 1 < n:
                    out.append(cmd[j + 1])
                    j += 2
                    continue
                if cmd[j:j + 2] == "$(":
                    # A command substitution stays LIVE inside double quotes, so a
                    # write in it is real: echo "$(make 2> err.log)" writes err.log,
                    # and the flat token pass could not see it because the whole
                    # quoted region became one word. Capture the body for callers to
                    # recurse into. $(( is arithmetic, not a command, and is skipped.
                    d, k = 0, j + 1
                    while k < n:
                        if cmd[k] == "(":
                            d += 1
                        elif cmd[k] == ")":
                            d -= 1
                            if d == 0:
                                break
                        k += 1
                    body = cmd[j + 2:k]
                    if not body.startswith("("):
                        substs.append(body)
                    end = k + 1 if k < n else n
                    out.append(cmd[j:end])
                    j = end
                    continue
                out.append(cmd[j])
                j += 1
            buf += "".join(out)
            has_word = True
            i = j + 1
            continue

        if c == "\\" and i + 1 < n:
            if cmd[i + 1] == "\n":
                i += 2
                continue
            buf += cmd[i + 1]
            has_word = True
            i += 2
            continue

        # An UNQUOTED command substitution runs too. Capture its body the same way the
        # quoted branch does rather than letting its characters become part of a word.
        if c == "`":
            j = cmd.find("`", i + 1)
            if j == -1:
                i = n
                break
            substs.append(cmd[i + 1:j])
            i = j + 1
            continue
        if cmd[i:i + 2] == "$(" and cmd[i:i + 3] != "$((":
            depth, j = 0, i + 1
            while j < n:
                if cmd[j] == "(":
                    depth += 1
                elif cmd[j] == ")":
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            substs.append(cmd[i + 2:j])
            i = j + 1
            continue
        if cmd[i:i + 3] == "$((" or (cmd[i:i + 2] == "((" and not has_word):
            depth, j = 0, i
            while j < n:
                if cmd[j] == "(":
                    depth += 1
                elif cmd[j] == ")":
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            i = j + 1
            continue

        if cmd[i:i + 3] == "<<<":
            # A here-string is INPUT. Guarding only the first '<' let the tokenizer
            # re-enter the heredoc branch on the remaining '<<' and register a phantom
            # heredoc, so in `grep -q foo <<< hello\nsed -i s/a/b/ config.py` every
            # line after the first became heredoc body and the sed was never parsed -
            # a silent total bypass. Emit a redirect-shaped token so the data word
            # after it is skipped like any redirect target.
            flush()
            seg.append(Tok("<<<", op="<"))
            i += 3
            continue

        if cmd[i:i + 2] == "<<" and cmd[i:i + 3] != "<<<":
            j = i + 2
            dash = j < n and cmd[j] == "-"
            if dash:
                j += 1
            while j < n and cmd[j] in " \t":
                j += 1
            q = ""
            if j < n and cmd[j] in "'\"":
                q = cmd[j]
                j += 1
            k = j
            while k < n and (cmd[k].isalnum() or cmd[k] in "_-."):
                k += 1
            delim = cmd[j:k]
            if q and k < n and cmd[k] == q:
                k += 1
            if delim:
                pending.append((delim, dash, len(segments)))
                flush()
                seg.append(Tok("<<", op="<"))
                i = k
                continue
            i += 2
            continue

        if c == "\n" and pending:
            rest = cmd[i + 1:]
            consumed = 0
            for delim, dash, segidx in pending:
                pat = (r"^\t*" if dash else r"^") + re.escape(delim) + r"$"
                m = re.search(pat, rest, re.M)
                if m:
                    heredocs.append((segidx, rest[:m.start()]))
                    consumed += m.end()
                    rest = rest[m.end():]
                else:
                    heredocs.append((segidx, rest))
                    consumed += len(rest)
                    rest = ""
            pending = []
            i = i + 1 + consumed
            endseg()
            continue

        two = cmd[i:i + 2]
        if two in ("&&", "||"):
            endseg()
            i += 2
            continue
        if c in ";|&\n":
            endseg()
            i += 1
            continue

        if c == "<":
            flush()
            seg.append(Tok("<", op="<"))
            i += 1
            continue

        if c == ">" or (c.isdigit() and cmd[i + 1:i + 2] == ">" and not has_word):
            fd = ""
            if c.isdigit():
                fd, i = c, i + 1
            op = ">"
            for cand in REDIR_OPS:
                if cmd[i:i + len(cand)] == cand:
                    op, i = cand, i + len(cand)
                    break
            flush()
            # `>&N`, `>&-`, `2>&1`: an fd DUPLICATION, not a file. Consume the target so
            # it never becomes a phantom command head, and emit no redirect at all.
            if i < n and cmd[i] == "&":
                j = i + 1
                while j < n and (cmd[j].isdigit() or cmd[j] == "-"):
                    j += 1
                if j > i + 1:
                    i = j
                    continue
            seg.append(Tok(fd + op, op=op))
            continue

        if c.isspace():
            flush()
            i += 1
            continue

        buf += c
        has_word = True
        i += 1

    endseg()
    return segments, heredocs, substs


def _is_lookup(words):
    """`command -v X` and `command -V X` resolve a name and run nothing."""
    return (words and os.path.basename(words[0]) == "command"
            and any(w in ("-v", "-V") for w in words[1:]))


def words_of(seg):
    """Operand tokens: no redirect targets, no leading VAR=VAL, compound-command
    keywords resolved through, wrappers unwrapped.

    Without the redirect exclusion, `cp a b 2>/dev/null` resolves its last operand to
    /dev/null and the real destination vanishes.
    """
    out, skip = [], False
    for t in seg:
        if t.op is not None:
            skip = True
            continue
        if skip:
            skip = False
            continue
        out.append(t.text)
    if _is_lookup(out):
        return []

    # Compound keywords hide the real head: splitting on ';' makes the write segment
    # of `for f in a b; do cp $f /etc/backup/; done` start with `do`, and
    # `{ cp a /etc/b; }` starts with `{`. Resolve through them so the WRITE_CMDS
    # lookup sees the actual command.
    # A function DEFINITION runs nothing. `function cp { echo hi; }` and `cp() { ... }`
    # both name a command without calling it, and reading the name as a call blocked a
    # harmless definition.
    # `cp () { ... }` tokenizes as ['cp', '()'], so endswith("()") never fired and the
    # POSIX spaced spelling of a harmless definition was blocked as a call.
    # A test compound runs no command. Popping "[[" as a reserved word left its first
    # operand standing as the head, so the most ordinary conditional in bash blocked.
    if out and out[0] in ("[[", "["):
        return []
    if out and (out[0] == "function" or out[0].endswith("()")
                or (len(out) > 1 and (out[1] in ("()", "(", ")")
                                      or out[1].startswith("()")))):
        return []

    while out:
        w = out[0]
        if w in RESERVED_WORDS:
            out.pop(0)
            continue
        if w in ("for", "select"):
            # `for VAR in LIST` runs nothing itself - the body is its own segment
            # after `do`. Popping only `for` left the loop VARIABLE standing as the
            # head, which false-positived the moment someone named it after a write
            # command (`for cp in a b; do ...`).
            out.pop(0)
            if out:
                out.pop(0)          # the loop variable
            if out and out[0] == "in":
                return []           # the rest is a word list, not a command
            continue
        if w == "case":
            # A case arm parses as `case WORD in PATTERN) cmd`, so
            # `case $x in a) cp s d;; esac` hid its cp behind the word and the
            # pattern. Drop through `in` and one pattern token ending in ')'.
            out.pop(0)
            if "in" in out:
                out = out[out.index("in") + 1:]
            if out and out[0].endswith(")") and out[0] != ")":
                out.pop(0)
            continue
        if w == "(":
            out.pop(0)
            continue
        if w.startswith("("):
            # A subshell glues to its first word: `(cp a /etc/b)` tokenizes as `(cp`.
            out[0] = w.lstrip("(")
            if not out[0]:
                out.pop(0)
            continue
        break

    seen = 0
    while out and seen < 8:
        # VAR=VAL is stripped on EVERY pass, not once up front: stripping only before
        # unwrapping meant `env LC_ALL=C sed -i s/a/b/ f.txt` unwrapped env and then
        # resolved its head to LC_ALL=C, letting the in-place sed through.
        while out and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", out[0]):
            out.pop(0)
        if not out:
            break
        head = os.path.basename(out[0])
        if head in WRAPPERS and len(out) > 1 + WRAPPERS[head]:
            vals = WRAPPER_VALUE_FLAGS.get(head, ())
            out = out[1 + WRAPPERS[head]:]
            while out and (out[0].startswith("-") or out[0].isdigit()):
                f = out.pop(0)
                # A flag that takes a separate value consumes the next token too,
                # or `sudo -u bob rm /etc/f` stops at `-u` and bob becomes the head.
                if f in vals and out:
                    out.pop(0)
            seen += 1
            continue
        # A wrapper may sit in FRONT of a compound, so resolving keywords once up front
        # is not enough. Re-run the keyword pass and loop until the head is stable.
        before = list(out)
        while out:
            w = out[0]
            if w in RESERVED_WORDS:
                out.pop(0)
                continue
            if w == "(":
                out.pop(0)
                continue
            if w.startswith("("):
                out[0] = w.lstrip("(")
                if not out[0]:
                    out.pop(0)
                continue
            break
        if out == before:
            break
        seen += 1
    return out


def _xargs_inner(words):
    """The command xargs runs, with xargs and its own flags stripped."""
    out = words[1:]
    while out and out[0].startswith("-"):
        f = out.pop(0)
        if f.split("=", 1)[0] in XARGS_VALUE_FLAGS and "=" not in f and out:
            out.pop(0)
    return out


def redirect_targets(seg):
    out = []
    for idx, t in enumerate(seg):
        if t.op in REDIR_OPS and idx + 1 < len(seg) and seg[idx + 1].op is None:
            out.append(seg[idx + 1].text)
    return out


def _is_extracting(words):
    head = os.path.basename(words[0])
    if head == "unzip":
        # -l lists, -t tests, -z prints the comment, -v lists verbosely, -p pipes to
        # stdout: `unzip -l bundle.zip` is read-only, and blocking it made the gate
        # obstruct plain archive inspection.
        if any(re.match(r"^-[ltzvp]+$", w) for w in words[1:]):
            return False
        return True
    if head in ("gunzip", "bunzip2"):
        # -t tests, -l lists, -c/--stdout decompresses to stdout: `gunzip -t f.gz`
        # writes nothing.
        if any(w in ("--test", "--list", "--stdout", "--to-stdout")
               or re.match(r"^-[A-Za-z]*[tlc][A-Za-z]*$", w) for w in words[1:]):
            return False
        return True
    for w in words[1:]:
        if w == "--extract" or w in ("x", "xf", "xzf", "xvf", "xjf"):
            return True
        if w.startswith("-") and "x" in w:
            return True
    return False


def _opt_values(words, flagspec):
    """Values of an output flag, in every spelling: exact, attached, --long=, and a
    short-flag cluster ending in the flag letter (`curl -sSo page.html` is -o)."""
    flags = flagspec.split(",")
    out = []
    for i, w in enumerate(words):
        if i == 0:
            continue
        for flag in flags:
            if flag.endswith("="):
                if w.startswith(flag):
                    out.append(w.split("=", 1)[1])
            elif w == flag:
                if i + 1 < len(words):
                    out.append(words[i + 1])
            elif w.startswith(flag) and len(w) > len(flag) and not w.startswith(flag + "-"):
                v = w[len(flag):]
                # a long flag carries its value after '=': --output=page.html
                if v.startswith("="):
                    v = v[1:]
                if v:
                    out.append(v)
            elif len(flag) == 2 and re.match(r"^-[A-Za-z]+$", w) and w[-1] == flag[1] \
                    and i + 1 < len(words):
                # short-flag cluster ending in the output letter: -sSo FILE
                out.append(words[i + 1])
        if "-o" in flags and w in ("-O", "--remote-name"):
            out.append(".")
    return out


def _dests(words, kind):
    ops = [w for w in words[1:] if not w.startswith("-")]
    if kind == "cwd":
        return ["."] if _is_extracting(words) else []
    if kind.startswith("dl:"):
        named = _opt_values(words, kind[3:])
        if named:
            # '-' names STDOUT, not a file: `wget -O - url` is read-only, and it must
            # not fall through to the no-flag cwd default below.
            return [v for v in named if v != "-"]
        # A fetcher with no explicit output still lands a file in the working directory
        # under a name taken from the URL, so absence of the flag is not absence of a
        # write.
        return ["."]
    if kind.startswith("opt:"):
        # '-' names STDOUT, not a file: `curl -o - url` is read-only.
        return [v for v in _opt_values(words, kind[4:]) if v != "-"]
    if kind == "last":
        return ops[-1:] if len(ops) >= 2 else ops
    return ops


def _checkout_branch_only(rest):
    """True for `git checkout -b/-B NAME` or `git switch -c/-C NAME` with no start point: it creates a branch and
    changes NO files, and it is the first thing anyone does on a task, so blocking it
    made the gate obstructive on move one. A start-point operand
    (`git checkout -b f origin/main`) does check files out and stays gated."""
    if not any(w in ("-b", "-B", "-c", "-C", "--orphan") for w in rest):
        return False
    ops, skip = [], False
    for w in rest:
        if skip:
            skip = False
            continue
        if w in ("-b", "-B", "-c", "-C", "--orphan"):
            skip = True            # the token after is the branch name
            continue
        if w.startswith("-"):
            continue
        ops.append(w)
    return not ops


def bash_targets(cmd, cwd, depth=0):
    """Every path this command would write or remove, absolute."""
    if depth > 3:
        return []
    segments, _, substs = tokenize(cmd)
    targets = []
    for seg in segments:
        targets.extend(redirect_targets(seg))
        words = words_of(seg)
        if not words:
            continue
        head = os.path.basename(words[0])
        # xargs is neither wrapper nor write command, so the piped-delete idiom
        # `ls *.pyc | xargs rm` passed untouched. Unwrap it and gate what it runs;
        # a write command left with NO operands takes them from stdin, so the
        # working directory stands in as the destination.
        via_xargs = False
        if head in ("xargs", "parallel"):
            words = _xargs_inner(words)
            if not words:
                continue
            head = os.path.basename(words[0])
            via_xargs = True
        if head == "eval" and len(words) > 1:
            targets.extend(bash_targets(" ".join(words[1:]), cwd, depth + 1))
            continue
        if head in SHELLS:
            # `sh -c '...'` hides an entire command. Recurse rather than let it through.
            # The flag may sit inside a cluster: `bash -lc 'echo x > f.txt'` carries
            # -c inside -lc and was never recursed when only the exact token matched.
            for i, w in enumerate(words):
                if i and re.match(r"^-[A-Za-z]*c[A-Za-z]*$", w) and i + 1 < len(words):
                    targets.extend(bash_targets(words[i + 1], cwd, depth + 1))
            continue
        if head in WRITE_CMDS:
            kind = WRITE_CMDS[head]
            d = _dests(words, kind)
            # Only where the operands ARE the destinations. For opt: and cwd kinds an
            # empty result means this invocation reads, and forcing a target there made
            # `xargs tar -tzf` contradict a direct `tar -tzf`.
            if via_xargs and not d and kind in ("all", "last"):
                d = ["."]
            targets.extend(d)
        elif head in ("sed", "perl", "ruby", "gawk", "awk") and \
                any(IN_PLACE.match(w) for w in words[1:]):
            d = [w for w in words[1:] if not w.startswith("-")]
            if via_xargs and not d:
                d = ["."]
            targets.extend(d)
        elif head == "find":
            if "-delete" in words or (
                    any(w in ("-exec", "-execdir") for w in words)
                    and any(os.path.basename(w) in ("rm", "mv", "cp", "truncate") for w in words)):
                targets.append(".")
        elif head == "git":
            # Resolve the ACTUAL subcommand, skipping global flags and their values.
            # A positional scan over words[1:4] blocked `git stash list` because the word
            # appeared, and `git log --grep merge` because a VERB was its argument.
            sub, wi = None, 1
            while wi < len(words):
                w = words[wi]
                if w in ("-C", "-c", "--git-dir", "--work-tree", "--namespace"):
                    wi += 2
                    continue
                if w.startswith("-"):
                    wi += 1
                    continue
                sub = w
                break
            rest = words[wi + 1:] if sub else []
            if sub in ("clean", "apply", "clone", "rm", "mv", "reset", "rebase",
                       "merge", "revert", "pull", "cherry-pick", "am", "worktree"):
                targets.append(".")
            elif sub in ("checkout", "switch"):
                # Creating a branch changes no file, and it is the first move of any task.
                if not _checkout_branch_only(rest):
                    targets.append(".")
            elif sub == "restore":
                targets.append(".")
            elif sub == "stash":
                # `stash list` and `stash show` only read.
                if not (rest and rest[0] in ("list", "show")):
                    targets.append(".")

    # A command substitution inside double quotes still RUNS: echo "$(make 2> err.log)"
    # writes err.log. The tokenizer captures those bodies rather than treating the whole
    # quoted region as inert text, and they are gated like any other command.
    for body in substs:
        targets.extend(bash_targets(body, cwd, depth + 1))

    res = []
    for t in targets:
        if not t or t in ("/dev/null", "/dev/stdout", "/dev/stderr", "/dev/tty") \
                or t.startswith("/dev/fd/"):
            continue        # sinks, not files. /dev/shm is a real tmpfs and is NOT one.
        t = os.path.expanduser(t)
        res.append(t if os.path.isabs(t) else os.path.join(cwd, t))
    return res


def unrecognised_heads(cmd, depth=0):
    """Command heads that are not known to be read-only.

    This is the allowlist half of the gate and the reason it stops leaking. The
    write-detection below still runs and still names the specific path a known writer
    would touch, which makes for a better block message; this catches everything that
    detection was never told about.

    Wrappers and shells are resolved through rather than trusted: `sudo rm` reports rm,
    and `sh -c "curl ... | tar x"` reports whatever is inside.
    """
    if depth > 3:
        return []
    out = []
    segments, _, substs = tokenize(cmd)
    for seg in segments:
        words = words_of(seg)
        if not words:
            continue
        head = os.path.basename(words[0])
        if head in SHELLS:
            # The flag may sit inside a cluster: `bash -lc '...'` is an everyday spelling.
            # Matching only the exact token let anything the allowlist would stop run
            # ungated behind it.
            for i, w in enumerate(words):
                if i and re.match(r"^-[A-Za-z]*c[A-Za-z]*$", w) and i + 1 < len(words):
                    out.extend(unrecognised_heads(words[i + 1], depth + 1))
            continue
        if head in ("xargs", "parallel"):
            inner = _xargs_inner(words)
            if inner:
                out.extend(unrecognised_heads(" ".join(inner), depth + 1))
            continue
        # A path invocation of something local, whether relative or absolute, is never
        # on a list of names, and it is exactly the shape that should not pass
        # unexamined.
        # A head in WRITE_CMDS is RECOGNISED: the gate knows exactly what it writes and
        # bash_targets already decides whether THIS invocation does. Reporting it here as
        # well double-counted it and discarded the exemption logic, so `unzip -l` and a
        # mv between two exempt paths both blocked.
        if head in WRITE_CMDS or head in ("find", "git", "sed", "perl", "ruby",
                                          "gawk", "awk"):
            continue
        if words[0].startswith("./") or words[0].startswith("/") or "/" in words[0]:
            if head not in READ_ONLY:
                out.append(words[0])
            continue
        if head not in READ_ONLY:
            out.append(head)
    for body in substs:
        out.extend(unrecognised_heads(body, depth + 1))
    return out


def interpreter_writes(cmd, depth=0):
    """True when an INTERPRETER is handed a script body containing a write primitive.

    A heredoc body counts only when the segment owning it runs an interpreter: a `cat`
    heredoc displaying example code that mentions a write is not a write.
    """
    if depth > 3:
        return False
    segments, heredocs, substs = tokenize(cmd)
    scripts = []
    for idx, seg in enumerate(segments):
        words = words_of(seg)
        if not words:
            continue
        head = os.path.basename(words[0])
        if head == "xargs":
            # keep head resolution consistent with bash_targets
            words = _xargs_inner(words)
            if not words:
                continue
            head = os.path.basename(words[0])
        if head in SHELLS:
            for i, w in enumerate(words):
                # clustered -c, same shape as bash_targets: `bash -lc '...'`
                if i and re.match(r"^-[A-Za-z]*c[A-Za-z]*$", w) and i + 1 < len(words) and \
                        interpreter_writes(words[i + 1], depth + 1):
                    return True
            continue
        if not any(head == x or head.startswith(x) for x in INTERPRETERS):
            continue
        for body_idx, body in heredocs:
            if body_idx == idx:
                scripts.append(body)
        for i, w in enumerate(words):
            if i and w in ("-c", "-e", "--eval") and i + 1 < len(words):
                scripts.append(words[i + 1])
    if any(BODY_WRITE.search(s) for s in scripts):
        return True
    # an interpreter invoked inside a double-quoted "$(...)" is still an interpreter
    return any(interpreter_writes(s, depth + 1) for s in substs)


def is_commit(cmd):
    """A real commit, not a command that merely mentions the word."""
    for seg in tokenize(cmd)[0]:
        words = words_of(seg)
        if not words or os.path.basename(words[0]) != "git":
            continue
        i = 1
        while i < len(words):
            w = words[i]
            if w in ("-C", "-c", "--git-dir", "--work-tree", "--namespace"):
                i += 2
                continue
            if w.startswith("-"):
                i += 1
                continue
            if w == "commit":
                return True
            break
    return False


# ------------------------------------------------------------------------------ paths
def _root(ev):
    for cand in (os.environ.get("CLAUDE_PROJECT_DIR"), ev.get("cwd")):
        if cand and os.path.isdir(cand):
            return os.path.realpath(cand)
    return os.path.realpath(os.path.expanduser("~"))


def _paths(root):
    state = os.environ.get("WORKORDER_GATE_STATE") or \
        os.path.join(root, ".claude", "workorder.json")
    state = os.path.realpath(os.path.abspath(os.path.expanduser(state)))
    return state, state + ".log"


def _exempt_prefixes(root, state, log):
    # REALPATH every prefix. _is_exempt realpaths the candidate, so an abspath-only
    # prefix never matches on a symlinked root, which made the gate block the very file
    # its own message tells you to write: an unsatisfiable loop.
    out = [state, log]
    tmp = os.path.realpath(tempfile.gettempdir())
    # ...unless the project itself lives under the temp dir, where exempting it would
    # silently disable the whole gate.
    if not (root == tmp or root.startswith(tmp + os.sep)):
        out.append(tmp + os.sep)
    for extra in (os.environ.get("WORKORDER_GATE_EXEMPT") or "").split(":"):
        extra = extra.strip()
        if extra:
            out.append(os.path.realpath(os.path.abspath(os.path.expanduser(extra))))
    return out


def _is_exempt(path, prefixes, state, deleting=False):
    if not path:
        return True
    p = os.path.realpath(os.path.abspath(os.path.expanduser(path)))
    if p == state:
        # Writing the work order is how you satisfy the gate. DELETING it would be a way
        # to cancel a recorded review debt, so that is not exempt.
        return not deleting
    for pre in prefixes:
        if p == pre or p.startswith(pre if pre.endswith(os.sep) else pre + os.sep):
            return True
    return False


# ------------------------------------------------------------------------------- io
def log(logpath, m):
    try:
        d = os.path.dirname(logpath)
        if d:
            os.makedirs(d, exist_ok=True)
        with open(logpath, "a") as f:
            f.write(time.strftime("%Y-%m-%dT%H:%M:%S") + " " + m + "\n")
    except Exception:
        pass


def block(msg):
    print("work-order gate: " + msg, file=sys.stderr)
    sys.exit(2)


def notify(m):
    print(json.dumps({"systemMessage": "work-order gate: " + m}))


def open_fail(logpath, reason):
    log(logpath, "FAIL-OPEN " + reason)
    notify("failed open (" + reason + "); it is NOT enforcing. See " + logpath)
    sys.exit(0)


def order(state, ignore_age=False):
    try:
        with open(state) as f:
            o = json.load(f)
    except Exception:
        return None
    if not isinstance(o, dict):
        return None
    if ignore_age:
        return o
    try:
        age = time.time() - float(o.get("opened_at", 0))
    except (TypeError, ValueError):
        return None
    max_age = float(os.environ.get("WORKORDER_GATE_MAX_AGE_H") or DEFAULT_MAX_AGE_H)
    return None if age > max_age * 3600 else o


def _user_rows(path):
    """Rows the HUMAN actually typed.

    The transcript's user-role rows are mostly not the user: tool results, loaded skill
    bodies, injected notices and cross-session agent messages all arrive with
    type=='user'. Measured on a live transcript: 4 of 61 user rows were typed by a human.
    Provenance is decided per FILE: if the transcript carries it anywhere, an unmarked
    row is not trusted. Per-row trust looked kinder to a transcript spanning a format
    change, but unmarked is exactly what injected text looks like, and the two failure
    directions are not comparable. Wrongly blocking a genuine quote surfaces as a
    question to the user; wrongly accepting a hook's words as authorisation is the hole
    this exists to close.
    A message typed WHILE a turn is running is not a user row at all: it lands in a
    queue-operation record. Reading only user rows meant a mid-turn instruction could
    never authorise anything, which blocked real authorisation.
    """
    ignore = [p for p in (os.environ.get("WORKORDER_GATE_IGNORE_PREFIXES") or "").split(":") if p]
    out = []
    has_provenance = False
    with open(path, errors="replace") as f:
        for line in f:
            # Provenance must be a FIELD on a user-role row. The old substring sniff
            # ('"origin" in line') flipped the whole file into provenance mode when a
            # pasted log or a tool result merely contained the quoted word - e.g. a
            # tool result carrying {"origin": ...} JSON - and every genuinely typed
            # message was then disenfranchised.
            if '"promptSource"' not in line and '"origin"' not in line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            if isinstance(r, dict) and r.get("type") == "user" and \
                    ("promptSource" in r or "origin" in r):
                has_provenance = True
                break
    with open(path, errors="replace") as f:
        for line in f:
            if '"user"' not in line and '"queue-operation"' not in line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            t = r.get("type")
            if t == "queue-operation":
                if r.get("operation") == "enqueue" and isinstance(r.get("content"), str):
                    out.append(r["content"])
                continue
            if t != "user" or r.get("isMeta"):
                continue
            src = r.get("promptSource")
            kind = (r.get("origin") or {}).get("kind")
            c = (r.get("message") or {}).get("content")
            if isinstance(c, list):
                c = " ".join(x.get("text", "") for x in c if isinstance(x, dict))
            if not isinstance(c, str) or not c.strip():
                continue
            if has_provenance:
                if src != "typed" and kind != "human":
                    continue
            else:
                c = re.sub(r"<\system-reminder>.*?<\/system-reminder>", " ", c, flags=re.S)
                c = re.sub(r"<[a-z-]*(reminder|notification|hook)[a-z-]*>.*?</[a-z-]*>", " ",
                           c, flags=re.S | re.I)
                if c.lstrip().startswith("Caveat:"):
                    continue
            if any(c.lstrip().startswith(p) for p in ignore):
                continue
            out.append(c)
    return out


# Smart punctuation is normalised on BOTH sides of the quote match: a user typing on a
# phone gets U+2019 apostrophes and U+201C quotes, and the ASCII transcription of the
# same words then failed to match, telling the user, falsely, that they never asked.
# The keys are written as ESCAPES on purpose. They ARE the punctuation, so a rule
# banning those literals and a table that must contain them can only both hold this
# way, and a search-and-replace over the literals once turned a one-character key
# into two and crashed this module at import.
_PUNCT_MAP = str.maketrans({
    "\u2018": "'", "\u2019": "'", "\u201a": "'", "\u201b": "'",
    "\u201c": '"', "\u201d": '"', "\u201e": '"', "\u201f": '"',
    "\u2013": "-", "\u2014": "-", "\u2212": "-",
    "\u00a0": " ", "\u2026": "...",
})


def _norm(s):
    return " ".join(str(s).translate(_PUNCT_MAP).split()).lower()


def user_said(quote, ev):
    tp = ev.get("transcript_path")
    if not tp or not os.path.exists(tp):
        return None
    q = _norm(quote)
    if len(q) < 2:
        return False
    try:
        msgs = _user_rows(tp)
    except Exception:
        return None
    if not msgs:
        return None
    for c in msgs:
        t = _norm(c)
        # A long quote may be a fragment; a SHORT one must be the whole message.
        if q in t and (len(q) >= 12 or t == q):
            return True
    return False


NO_ORDER = """NO WORK ORDER - blocked before a file change, by design.

The user has not been shown to have asked for this. Before changing files, write
{state} with:
  {{"quote": "<their LITERAL words authorising THIS work>",
   "scope": "<one line: what you are about to change>",
   "review": "required" | "not-required",
   "opened_at": <unix seconds, read from the real clock, never guessed>}}

If you cannot quote them asking for THIS item, you do not have a go. A plan, your own
suggestion, or silence is not one. Ask. Ambiguous authorisation IS NO authorisation."""


def main():
    if os.environ.get("WORKORDER_GATE") != "1":
        return                                  # dormant unless armed
    raw = sys.stdin.read()
    if not raw.strip():
        return
    tmplog = os.path.join(os.path.realpath(tempfile.gettempdir()), "workorder-gate.log")
    try:
        ev = json.loads(raw, strict=False)
    except Exception as e:
        open_fail(tmplog, "unparsable payload: " + type(e).__name__)
        return
    if not isinstance(ev, dict):
        return
    tool = ev.get("tool_name", "")
    inp = ev.get("tool_input") or {}
    if not isinstance(inp, dict):
        inp = {}
    root = _root(ev)
    state, logpath = _paths(root)
    exempt = _exempt_prefixes(root, state, logpath)

    def require_order(what):
        o = order(state)
        if not o:
            block("BLOCKED: " + what + "\n\n" + NO_ORDER.format(state=state))
        said = user_said(o.get("quote", ""), ev)
        if said is False:
            block("WORK ORDER QUOTE NOT FOUND IN ANYTHING THE USER TYPED.\n\n"
                  "  quote: " + str(o.get("quote", ""))[:160] + "\n\n"
                  "It is not a verbatim fragment of any message the user typed in this\n"
                  "session. Either it was paraphrased, or it came from a hook, a loaded\n"
                  "skill, another agent, or the assistant's own earlier text.")
        if said is None:
            log(logpath, "VERIFY-SKIPPED transcript unusable; allowing")
            notify("could not read the transcript; the quote was NOT verified.")
        else:
            log(logpath, "VERIFY-OK " + tool)
        return o

    if tool in ("Edit", "Write", "NotebookEdit"):
        path = str(inp.get("file_path") or inp.get("notebook_path") or "")
        if _is_exempt(path, exempt, state):
            return
        require_order(tool + " " + path)
        return

    if tool == "Bash":
        cmd = str(inp.get("command", ""))
        cwd = ev.get("cwd") or root
        # mv relocates a file OUT of existence at its old path, so an mv touching the
        # work order is the same debt-cancelling move an rm is.
        deleting = bool(re.search(r"(?:^|[\s;|&])(rm|rmdir|unlink|shred|mv)\s", cmd))
        targets = [t for t in bash_targets(cmd, cwd)
                   if not _is_exempt(t, exempt, state, deleting)]
        # An inline interpreter body names its own paths, so honour the exemptions the
        # shell path already honours: a body every one of whose quoted paths is exempt is
        # writing somewhere the user said needs no order. Reported from the field, where
        # it made an exempt file unwritable by heredoc while the same write through the
        # Write tool passed.
        interp = interpreter_writes(cmd)
        if interp:
            # Class written [/~] rather than the other order: the release validator scans
            # this file for local paths, and the reversed spelling is itself one.
            quoted = re.findall(r"""['"]([/~][^'"]*)['"]""", cmd)
            if quoted and all(_is_exempt(q, exempt, state, deleting) for q in quoted):
                interp = False
        unknown = unrecognised_heads(cmd)
        if targets or interp or unknown:
            if targets:
                why = "would write: " + ", ".join(targets[:3])
            elif unknown:
                why = ("not a command known to only read: " + ", ".join(sorted(set(unknown))[:3])
                       + "\n  This gate allowlists readers rather than listing writers, so a"
                       + "\n  command it does not recognise needs a work order.")
            else:
                why = "an interpreter script body containing a write primitive"
            require_order("file change via Bash\n\n  " + why)

        if not is_commit(cmd):
            return
        # Gated on the order REGARDLESS of age: letting a stale order cancel a recorded
        # review debt turns the strongest state into no enforcement, exactly in the long
        # sessions where the review is likeliest to have been forgotten.
        o = order(state, ignore_age=True)
        if not o:
            return
        if o.get("review") == "required" and not str(o.get("review_done", "")).strip():
            block("REVIEW OWED - commit blocked.\n\n"
                  'This work order says review: "required" and records no review.\n'
                  "  scope: " + str(o.get("scope", "?")) + "\n\n"
                  "All new development gets reviewed, not just the code that looked risky.\n"
                  "Run the review (aperture = this diff, two questions), then set\n"
                  '  "review_done": "<agent id / one-line verdict>"\n'
                  "in " + state + " and try again.")


try:
    main()
except SystemExit:
    raise
except Exception as e:
    try:
        open_fail(os.path.join(os.path.realpath(tempfile.gettempdir()), "workorder-gate.log"),
                  type(e).__name__ + ": " + str(e))
    except SystemExit:
        raise
    except Exception:
        sys.exit(0)
