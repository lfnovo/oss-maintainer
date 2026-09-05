# Archetype `pypi-library` — a package published to an index

There is no running service. The deliverable is a wheel and an sdist that downstream projects
install, sometimes straight from the index with a zero-install runner. A wheel that imports
can still ship a broken CLI or a missing template; the packaging gate is the highest-value
gate of this archetype, not a formality, and the publish workflow usually runs no tests.

## Version decision (phase 1)

`[release].consumer_surfaces` names what a breaking change can break: public exports and
signatures, response types, CLI flags and subcommands, MCP tool names and parameters,
configuration keys and environment variables, supported providers or engines. Removing or
renaming any of them is major; adding is minor; a back-compatible deprecation with a warning
is minor, not major; fixes and packaging are patch.

## Bucket A specifics (phase 3)

- The default suite must not reach the network: real-API tests live behind a marker that the
  default configuration excludes. Grep the diff of new providers or processors for unmocked
  HTTP or SDK calls in tests; a leaked key or a hung CI is the symptom.
- `[release.gates].not_gates` lists signals that never block (a lint or type check the project
  does not gate on). Never "fix" pre-existing findings as a side effect of the release.

## Packaging gate (phase 4, repeated in phase 7)

`[artifacts.pypi].gate` proves that the artifact that will ship works for every declared
surface, from a clean environment, with no repository on the path:

1. `rm -rf dist && uv build` (or the project's builder); the wheel's declared version equals
   `[release].version_files`.
2. **Wheel content inspection**: list the wheel and confirm every non-Python asset the runtime
   needs is inside (templates, data files, prompts). Any new non-`.py` asset is a packaging
   risk until confirmed inside.
3. **Clean-room install**: use the recipe below, with the project's module name.
   A bare install without extras must import: optional dependencies stay guarded.
4. **Surface smokes** per `[artifacts.pypi].surfaces`: `library` (import and one call),
   `cli` (`--help` plus one real invocation on a fixture), `mcp` (the server starts and
   answers a real `initialize` handshake).
5. **Extras resolve**: each entry in `[artifacts.pypi].extras` installs against the published
   pins.
6. `[artifacts.pypi].install_check` when set.

The portable gate recipe below also appears in the README profile example. Replace
`example_lib` with the import module, which may differ from the distribution name.

```bash
rm -rf dist && uv build &&
wheel="$(python3 -I -c 'from pathlib import Path; wheels = list(Path("dist").glob("*.whl")); assert len(wheels) == 1, "expected one wheel"; print(wheels[0].resolve())')" &&
(
  check_dir="$(mktemp -d)" &&
  trap 'rm -rf "$check_dir"' EXIT &&
  cd "$check_dir" &&
  uv run --isolated --no-project --with "$wheel" python -I -c 'import example_lib; print(example_lib.__file__)'
)
```

`uv --isolated --no-project` isolates environment selection, not Python's import path.
Changing directory and `python -I` remove checkout and inherited `PYTHONPATH` assistance.
Inspect the printed module origin: it must belong to the installed environment, never the
checkout. Apply the same isolation to CLI/MCP probes and runtime assets; editable installs
or source-only templates do not count as artifact evidence.

Identity: sha256 of the wheel and sdist. When the publish workflow rebuilds the package
before uploading, the published files differ from the tested ones; phase 11 verifies the
published ones and the run record says the local gate ran on another build.

## Bucket C (phase 5)

Real-API suites cost money and need credentials in a local environment file; they are a
maintainer ritual, never CI. Scope by the diff: every provider or engine whose code changed,
plus one baseline per modality that did not. Hand the owner the exact scopes to run against
the credentials they have; anything without credentials is unverified this release.

Triage every failure before calling it a blocker: a **stale expectation** (the test asserts on
content that changed upstream; fix in its own test-only PR), an **environment** problem
(missing or expired key, rate limit; record as unverified), or a **real regression** (the
changed code's own test fails; blocks). Then run `git status`: media and network suites write
intermediates next to fixtures.

## Cut and publish (phases 7 and 10)

- Bump every version file together, including manifests that must equal the package version;
  commit the lock file with the bump (`[release].lock_command`).
- **The tag push is the trigger** whenever the publish workflow runs on `push: tags`. Every
  path that pushes a tag publishes: a Makefile target, `gh release create`, a tag-creating
  workflow dispatch. None of them runs before the GO. Derive the tag from the version files;
  never hand-craft one.
- Two orderings exist: the release creates the tag (notes must exist first; the GO covers
  the release creation), or the tag is pushed and the notes are attached to it afterwards.
  Either way the notes are approved before anything irreversible happens.
- A published version is immutable. A bad publish burns the number: bump, re-cut, publish
  again. Never push a version-looking tag "just to test".

## Post-publish verification (phase 11)

```bash
(
  check_dir="$(mktemp -d)" &&
  trap 'rm -rf "$check_dir"' EXIT &&
  cd "$check_dir" &&
  uv run --isolated --no-project --with "<package>==<version>" python -I -c "import <module>; print(<module>.__file__)"
)
```

Repeat the surface smokes against the index install, not the local build. Propagation can lag
a minute; retry briefly. Confirm the release page shows the tag and the approved notes and is
marked latest.

## Notes (phase 8)

Group by consumer surface (library, CLI, MCP) when the project has several: a reader usually
cares about one. Include the install line and, when the project supports it, the zero-install
runner line and the extras line.
