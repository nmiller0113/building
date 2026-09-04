This summary ships with the building skill. Where the plugin is installed, the full
text loads through the Skill tool under this plugin's building skill, and where that
text is not loaded, the statements below are the rule in effect.

- The order of work is: read the real contract rather than a memory of it, implement,
  send it for an independent bounded review, then make it findable. The last two are not
  extras at the end. A change nobody reviewed is unverified, and a change nobody can
  locate by version is unshipped.
- The review is run by a context independent of the one that built, and it looks at what
  changed and nothing else: does this change do what it claims, and did it break what
  already worked. The reviewer is the one the requester designated once in their own
  instruction file, and it reviews every cycle whoever built; independence is the fresh
  context rather than a different engine. The builder holds the first three cycles; after
  three failures the builder tiers up one step and that next tier builds from the
  reviewer's findings; after three more the work stops and goes back to the requester.
  A failure is a confirmed critical or high finding, and mediums and lows are a sentence
  to the requester rather than another cycle.
- A version number is a claim and a tag is the evidence for it. Anything that declares a
  version carries exactly one source of truth for that number, an annotated tag on the
  commit that declares it, and a release carrying the same text as the changelog entry.
  This holds for private work as well as public, because what is internal today is not
  reliably internal later, and a history cannot be tagged honestly long after the fact.
- A release note says what CHANGED rather than what the thing is: anything that breaks
  first, then what is new, then what is fixed. The reader already has the project and
  came to learn whether this version affects them. Its title is the version alone, since
  the project name is already on the page and a title carrying it goes wrong at a rename.
- Publishing ANY release out of order, whether backfilling history or patching an older
  line, can silently demote the current one, because release hosts commonly treat the most
  recently created release as the latest rather than the highest version. Such a release
  is created with the host's latest flag off where one exists, and what a visitor actually
  sees is then checked.
- The step that gets skipped is the one after the part that felt like the work, so the
  check for it belongs in whatever validates a release rather than in anyone's memory: a
  declared version with no matching tag, or no changelog entry, stops the release.
- A published artifact assumes nothing about the machine it was written on: no local
  paths, no personal names, no distro-specific commands, and no assumption about which
  shell or interpreter spelling exists. A genuine requirement is stated in the README
  instead of being discovered when an install fails.
- Finished is not the same as running. It means the ask is met in the requester's own
  words, the review passed, the version and changelog and tag and release all exist and
  agree, and every claim made in a comment, a docstring or a note is true of the code as
  it now stands. That last one is what rots, because prose is a claim and an unchecked
  claim is an old opinion sitting somewhere it will be believed.
- A component can be correct and entirely disconnected. Exercising a script proves
  nothing about the configuration that decides whether the script is ever called, so what
  gets verified is the path the real system takes, including the wiring that routes to it.
