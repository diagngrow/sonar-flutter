# Contributing

This documentation is a guide for plugin developers / contributors.

## Requirements

- Java JDK 21 (the SonarQube 26.x test fixtures target Java 21; with JDK 17 the plugin can only
  be built without the tests, see below)
- Maven 3.8 or later
- [uv](https://docs.astral.sh/uv/) to run the rule generator
- A local SonarQube 26.10+ instance for local testing

## Main commands

#### Check and add license headers on source files

The header template is `license-header.txt`. The CI fails when a Java file does not match it.

```bash
$ mvn license:check
$ mvn license:format
```

#### Local plugin deployment

In order to deploy the plugin locally, the SONARQUBE_HOME environment variable must be set
(the `ant.xml` helper restarts SonarQube with the macOS launcher).

If variable is already set, use:
```bash
$ mvn install
```

If variable is not set, it can be set inline:
```bash
$ SONARQUBE_HOME=~/path/to/sonarqube mvn install
```

When started locally SonarQube UI is available at http://localhost:9000

#### Packaging

```bash
$ mvn package
```

With JDK 17, skip the tests:

```bash
$ mvn package -Dmaven.test.skip=true
```

## Updating rules

The rules of the `dartanalyzer` repository (`dart-lang/src/main/resources/dartanalyzer/rules.json`)
and the plugin's `analysis_options.yaml` are generated from the Dart SDK sources: the linter
catalogue, the analyzer diagnostics (`pkg/analyzer/messages.yaml`) and the `lints` /
`flutter_lints` rule sets.

When a new Dart SDK is released, regenerate them with:

```bash
$ uv run --no-project --with markdown --with pyyaml python scripts/update_dart_lint_rules.py
```

The script prints the added and removed rules. It fails when a source has an unexpected format
(duplicate YAML key, missing diagnostic class, empty rule set) or when the default profile would
activate two mutually exclusive lints.

The generator tests run with:

```bash
$ uv run --no-project --with markdown --with pyyaml --with pytest python -m pytest scripts/tests
```

 Rule types and severities are computed from the
explicit tables at the top of the script (`BUG_LINTS`, `MAJOR_SMELL_LINTS`, `BUG_WARNINGS`...):
update these tables to change how a rule is classified, then run the script again.

## Releasing

A new stable release is published on GitHub on every new `0.X.Y` tag (for example `0.6.1`), by the `release.yml`
GitHub Actions workflow. The workflow sets the project version from the tag.

The steps to issue a new stable release are:
1. Update the version in the `pom.xml` files and the `CHANGELOG.md`, then merge into `master`.
2. Create a new tag from `master` with the release number. Example:
```bash
$ git tag -a 0.6.1 -m "0.6.1"
```
3. Push the new tag with:
```bash
$ git push origin 0.6.1
```
