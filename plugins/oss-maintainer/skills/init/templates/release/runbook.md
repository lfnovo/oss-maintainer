# Release runbook

Exact commands for this repository, by phase. The plugin's `release` skill supplies the
phases and the gates; this file supplies what to type.

## Bucket A

```bash
# TODO canonical validator, mandatory checks and selected risk probes
```

## Artifact gate

```bash
# TODO fresh + upgrade image gate, or build + clean-room install
```

## Cut

```bash
# TODO bump version files, date the changelog, lock, agreed PR or direct-commit process
```

## Publish (only after the GO)

```bash
# TODO the distribution trigger
```

## Post-publish verification

```bash
# TODO verify from the registry, never from the local build
```

## Cleanup

```bash
# TODO
```

## Known gotchas

- TODO
