# Template Versioning

This repository is a product template, not just an application repository.

That means versioning should describe changes in the template contract, not only changes in one demo app.

## Recommended Versioning Model

Use semantic versioning for the template itself:

- `MAJOR`: breaking template changes
- `MINOR`: backward-compatible capabilities or new supported modules
- `PATCH`: fixes, docs corrections, dependency bumps, and small quality improvements

Example:

- `1.0.0`: first stable internal platform starter release
- `1.1.0`: add a new optional cache helper or worker capability without breaking existing adopters
- `2.0.0`: change config names, remove modules, or alter API/security defaults in a way that requires migration work

## What Counts As Breaking

Treat these as `MAJOR` changes:

- renaming environment variables
- changing response contracts in a non-compatible way
- removing documented modules, routes, or jobs
- changing auth behavior that requires adopter code or operational changes
- changing required deployment steps, migration flow, or bootstrap flow

## Suggested Release Discipline

For each template release:

1. update the template version in [pyproject.toml](../pyproject.toml)
2. tag the release in git
3. summarize changes in release notes or your internal changelog
4. call out any adopter action items clearly

## Suggested Release Notes Shape

For each release, record:

- what changed
- whether it is breaking
- what adopters need to do
- whether config, secrets, migrations, or bootstrap steps changed

Short example:

```text
1.2.0
- Added first-admin bootstrap command
- Added CI and pre-commit baseline
- No breaking migration for adopters
```

## Adoption Guidance

Teams using the template should pin or record which template version they started from.

This makes it easier to answer:

- which security baseline they inherited
- which docs apply
- whether a later template release is worth backporting

## Minimum Policy

If you do not want a full changelog yet, at least keep:

- a git tag per stable template release
- one short release note per tag
- a note in PRs when a change is template-breaking
