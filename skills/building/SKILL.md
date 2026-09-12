---
name: building
description: Use when building or changing anything that ships, and whenever a change is about to be committed, versioned, tagged, released or published. Covers the order of work, what makes a version real, and when a change is finished. Also use when setting up a repository, deciding a version number, writing a changelog entry, or cutting a release. For the adversarial review a change must pass, this skill hands off to the crosscheck skill. Not for read-only investigation.
license: MIT
---

# building

The order of work, and what finished actually means.

Most of what goes wrong here is not bad code. It is a change that works and is not
findable: a version number nothing points at, a release nobody can read, a claim in a
comment that the code stopped matching. This is about closing that gap every time,
without thinking about it each time.

## The order

1. **Read the real contract.** The source of the thing you are calling, not your memory
   of it, and not the field names its consumer happens to use.
2. **Implement.**
3. **Review it.** Independent, adversarial, and bounded at both ends.
4. **Make it findable.** Version, changelog, tag, release. The rest of this file.

Steps 3 and 4 are not optional extras at the end. A change that passed no review is
unverified, and a change nobody can locate by version is unshipped.

## The review loop, in short

The full discipline is the **crosscheck** skill, which ships beside this one. The shape,
so that it is never in doubt at the moment it matters:

- **The builder builds. A different, independent context reviews.** Not the same
  conversation grading its own work. The reviewer is the one the requester designated
  once, and it reviews every cycle. Independence is the fresh context, not a different
  engine.
- **Three strikes.** If three build-and-review cycles have not produced something that
  passes, the **builder tiers up one step** and builds from the reviewer's findings. The
  reviewer does not change: three failures say the builder is the wrong instrument, not
  the review.
- **Three more, then stop and bring it to the requester.** Six failed cycles is evidence
  the problem is misunderstood rather than unfinished, and that is a conversation, not
  more attempts.
- **A constraint on applying the result is not an exit.** A maintenance window, a live host,
  a deploy freeze: each is a reason to wait before applying a change, and none is a reason to
  stop reviewing one, because the review reaches nothing and changes nothing. A build that has
  been made but not reviewed is the middle of a cycle rather than the end of one. Finish the
  cycles, then hand the reviewed artifact and the constraint over together, as one decision.
  This does not touch the stops that are real. An unavailable reviewer, no reviewer designated
  yet, and scope that grows mid-build each stop the loop on their own terms.
- **The review looks at what changed and nothing else.** Two questions only: does this
  change do what it claims, and did it break what already worked. A prompt that asks what
  else is wrong commissions findings instead of checking work, and that list has no end.
- **A failure is a confirmed critical or high finding.** Mediums and lows are a sentence
  to the requester, not another cycle.

The requester names their always-reviewer once in their own instruction file, so it is not
decided per task, and where none is named yet the answer is asked for rather than chosen.
There is no builder to name: the builder is whatever model the build was triggered from.
Everything else about how the loop terminates, what counts as a
distinct change, and why a finding about your own check is a report rather than a
failure, is in crosscheck.

## What makes a version real

A version number is a claim. A tag is the evidence. Without the tag, nothing can check
the claim out, diff it against the one before, or pin to it, and the number is decoration
in a manifest.

**So: one source, one tag, one release, and they agree.**

- **One source of truth for the number.** A manifest field, or a VERSION file. Never two
  places that can disagree, and never a number that lives only in a commit message.
- **Every version that ships gets a tag**, on the commit that declares it. Annotated, not
  lightweight, so it carries a date and a message of its own.
- **Every tag gets a release.** A tag is retrievable; a release is readable. The tag
  serves whoever is at a terminal, the release serves whoever is looking at the project
  and deciding whether to care.
- **Do this even when the thing is private.** You do not know today what becomes public
  later, and a history without tags cannot be given them honestly after the fact once the
  commits stop saying which version they were.

**Semantic versioning, and what actually forces a bump:** the major moves when something
that used to work stops working; the minor when something new is there; the patch when
behaviour that was wrong becomes right. Ask which of those a change did, and the number
follows without a debate.

**A release note says what CHANGED, not what the thing IS.** The reader already has the
project in front of them; they came to find out whether this version affects them. Lead
with anything that breaks, then what is new, then what is fixed. A note that restates the
project's description has told them nothing.

**A changelog entry and the release note are the same text.** Write it once. Two versions
of the same account drift, and then neither is trustworthy.

**Title a release with its version and nothing else.** The project's name is already on
every page the release appears on, so repeating it buys nothing and costs something: a
title carrying the product name becomes wrong the day the project is renamed, and a
release list then reads as two different products sharing a repository. Put the naming
history in the note, where it is history rather than a label.

**Publishing a release out of order can silently demote the current one.** Release hosts
commonly mark the most recently CREATED release as the latest, not the highest version. So
backfilling history, or patching an old line after a newer one exists, points everyone
arriving at the project at the wrong version, quietly, with nothing failing.

Where the host has a per-release latest flag, create the out-of-order release with that
flag OFF, rather than repairing the demotion afterwards: repairing it leaves a window
where the project advertises the wrong version. Then look at what a visitor actually sees,
because that is the only check that catches this.

## Make skipping it impossible

This is the step that gets forgotten, because it happens after the part that felt like
the work. Do not rely on remembering it.

**Put the check where the release happens.** Whatever script or command validates a
release should refuse to proceed when the declared version has no matching tag, or when
the changelog has no entry for it. That turns a habit into a wall, and a wall is the only
thing that survives being in a hurry.

If there is no such script yet, the check is the reason to write one.

## The repository itself

Consistency here costs nothing at setup and is expensive to retrofit.

- **A default branch name, chosen once and used everywhere.** Tooling, links and muscle
  memory all assume it.
- **A LICENSE from the first commit** on anything that might ever be read by someone
  else. Adding one later is a conversation with every contributor since.
- **A README that answers what it is, how to install it, and what it requires**, in that
  order, before it answers anything else.
- **An ignore file that covers the runtime's own droppings** before the first commit:
  bytecode caches, dependency directories, build output, editor state. Anything committed
  once is in the history permanently, which matters most for the file you did not mean to
  commit.
- **Nothing in a published artifact assumes the machine it was written on.** No local
  paths, no personal names, no distro-specific commands, no assumption about which shell
  or interpreter spelling exists. State a real requirement in the README rather than
  letting an install fail mysteriously.

## When a change is finished

Not when it runs. A change is finished when all of these are true:

- It does what was asked, and the requester's own words are what "asked" means.
- It passed an independent review, bounded to the change itself. See **crosscheck**.
- Its version is bumped in one place, if it carries a version.
- Its changelog says what changed, in the reader's terms.
- Its tag exists, on the right commit.
- Its release exists, carrying that same text.
- Every claim made about it in a comment, a docstring, a README or a release note is true
  of the code as it now stands.

That last one is the one that rots. Prose is a claim, and a claim nobody re-checked is
just an old opinion sitting in a file where it will be believed.

## Two failure modes worth naming

**Documentation written from intent rather than from the artifact.** The sentence
describes what the change was supposed to do. Read it back against the code afterwards and
fix the sentence, not your memory of it.

**Verifying the thing rather than the wiring.** A component can be correct and completely
disconnected. A test suite that exercises a script proves nothing about the configuration
that decides whether the script is ever called. Exercise the path the real system takes,
including the config that routes to it, or the green result is about something nobody
runs.

## Scope

The boundary of the work is the boundary of the request. A defect found outside the ask is
a sentence to the requester, not a task, and scope growing mid-build is a reason to stop
and ask rather than to keep going because finishing feels cheaper.

The **kiss** skill carries that discipline in full and pairs well with this one. It is a
companion, not a dependency.
