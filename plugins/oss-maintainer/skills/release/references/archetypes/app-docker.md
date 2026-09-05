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

## Rolling tag and re-cut

Container tags are mutable; that is what makes two things possible and dangerous:

- **Rolling promotion** (`[release].latest_promotion`): the publication step promotes the
  version tag to the rolling tag. Users receive it immediately, so it is behind the GO and
  verified again after promotion (repeat the manifest check for the rolling tag).
- **Re-cut after a post-tag fix**, before publication: the fix goes through the normal PR
  flow; the version stays; the tag moves to the new commit; the image is rebuilt; the artifact
  gate runs again on the rebuilt image; the version images are pushed again; the owner
  re-checks the RC stack; only then publication proceeds. A skipped rebuild ships the un-fixed
  artifact under a fixed-looking tag.

Version images may be pushed before the GO when the CI workflow supports "version tags only,
no rolling promotion"; that push is autonomous per the gates, the promotion is not.

## Release candidate for the owner (bucket C)

Offer a browsable stack from the *pushed* version image (never a local build that could
shadow the registry), with a copy of the owner's data when realism matters: export from the
running instance, import into the RC stack, originals untouched. Remind the owner that
in-container credentials pointing at host services need the container's host alias. Findings
go back to the fix loop.

## Testers before release

`[artifacts.docker].dev_tag` is the rolling development image rebuilt on every merge. When a
Discussion or issue is closed because its fix merged, point testers at that tag.

## Post-publish verification (phase 11)

Manifest check for every version reference and for the rolling tag after promotion; the
release page shows the tag and the approved notes; a fresh pull of the rolling tag boots and
answers its health check.
