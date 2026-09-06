# Archetype `app-docker` — an application shipped as a container image

The deliverable is an image users pull and run. A green suite on the default branch is not a
working image: the gate tests the artifact, not the repository.

## Artifact gate (phase 4, repeated in phase 7)

`[artifacts.docker].gate` runs the two scenarios that matter to users, against real
containers:

- **Fresh install**: the new image on an empty data directory boots, migrates, answers its
  health check and completes the smoke journey.
- **Upgrade**: the genuine previous tag (`OLD_TAG`, pulled from the registry, never a local
  build) is started with data, then replaced by the new image; migrations apply, data survives,
  the journey completes.

Add container-level probes that unit tests cannot cover: process supervision, environment
variables reaching in-image workers, proxies and `NO_PROXY`, opt-in runtimes gated off by
default. The repository's runbook holds the exact commands.

Build the candidate image from a clean worktree of the candidate commit
(`git worktree add --detach <dir> HEAD`), or confirm that `git status` is clean before
building from the checkout: the Docker build context is the working tree, and an untracked
file that `.dockerignore` does not exclude ends up in the image.

Identity: the manifest digest per registry and variant. Record the digests of the locally
built candidate; the CI build that publishes may differ, so phase 11 verifies the published
manifests.

## Registries, variants, platforms

`[artifacts.docker].registries` × `variants` × `platforms`. Verify each published reference:

```bash
for ref in <registry>/<image>:<version><variant> ...; do
  docker manifest inspect "$ref" | jq -r '[.manifests[] | select(.platform.architecture != "unknown") | .platform.architecture] | unique'
done
```

Every reference must list every platform in the profile.

## Final publication, rolling tags and re-cuts

Pushing `image:<version>` to a public registry distributes that version even when `latest`
does not move. Both the version push and rolling promotion require the final candidate's GO
and run in phase 10. Ordinary build or merge approval covers neither action.

Before any publication, fixes produce a new candidate and invalidate the affected evidence
and approval. After a final version is distributed, preserve its tag and image identity:
a correction gets a new version, a new cut and a new GO. Do not move the published tag or
push replacement images under that version.

## Release candidate for the owner (pre-publication bucket C)

By default, start a browsable stack from the exact locally tested candidate image, pinned by
image ID/digest. When remote testers need an image, propose **separate RC staging**: an
immutable prerelease reference such as `image:<version>-rc.<n>`, the tested digest, target
registry and exact push action. Obtain explicit approval for that staging operation before
pushing; it is not covered by build/merge approval or inferred from a future final GO.
Never use the final version reference, a final Git tag or `latest` for staging. A rebuilt RC
gets a new RC reference and new staging approval; never overwrite the previous one.

Run manual checks on that local image or pull the approved RC by digest. Record which one
was tested; final GO still covers only the named final publication action and candidate.
Use a copy of the owner's data when realism matters, with their authorization; originals
stay untouched. In-container credentials that point at host services need the host alias.
Findings go back to the fix loop; they do not justify an early final-version push.

## Testers before release

`[artifacts.docker].dev_tag` is the rolling development image rebuilt on every merge. When a
Discussion or issue is closed because its fix merged, point testers at that tag.

## Post-publish verification (phase 11)

Manifest check for every version reference and for the rolling tag after promotion; the
release page shows the tag and the approved notes; a fresh pull of the rolling tag boots and
answers its health check.
