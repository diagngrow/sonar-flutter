![CI](https://github.com/diagngrow/sonar-flutter/workflows/CI/badge.svg)

# SonarQube plugin for Flutter / Dart

A plugin to enable analysis of Dart and Flutter projects into SonarQube, maintained by
[Diag n' Grow](https://github.com/diagngrow).

This project is a fork of the original [sonar-flutter](https://github.com/insideapp-fr/sonar-flutter) plugin.

## Features

| Feature    | Supported                                                                    |
|------------|------------------------------------------------------------------------------|
| Size       | YES                                                                          |
| Issues     | YES (Dart linter, analyzer warnings and compile errors, see [Rules](#rules)) |
| Tests      | YES                                                                          |
| Coverage   | YES (LCOV)                                                                   |
| Complexity | YES                                                                          |
| Syntax     | YES                                                                          |

## Compatibility

| Plugin version | SonarQube                | Java (server and scanner) |
|----------------|--------------------------|---------------------------|
| 0.6.0+         | 26.10+ (Plugin API 14.1) | 17+                       |

Version 0.6.0+ is not compatible with SonarQube versions older than 26.x.

## Download

Download the plugin JAR from the [Releases](https://github.com/diagngrow/sonar-flutter/releases) page.

The changelog is available [here](CHANGELOG.md).

## Installation (on the server)

- Remove any previous version of the plugin (`sonar-flutter-plugin-*.jar`) from the
  **$SONARQUBE_HOME/extensions/plugins** directory.
- Copy the new plugin JAR into the same directory.
- Restart the server.

## Prerequisites (on the machine running the analysis)

The plugin runs the Dart or Flutter analyzer on the machine that runs `sonar-scanner`, so the
following tools must be installed there and available on the `PATH`.

### Flutter SDK (when analyzing a Flutter project)

Install Flutter as explained in the [Flutter installation instructions](https://docs.flutter.dev/get-started/install).

### Dart SDK

The Flutter SDK ships Dart in **$FLUTTER_HOME/bin/cache/dart-sdk**, but this directory is not on the
`PATH` by default, and `dart` must be on the `PATH`.

For reliability in a CI/CD environment, install the Dart SDK separately as explained in
[Get the Dart SDK](https://dart.dev/get-dart). Dart 2.12+ is required for the machine readable
analyzer output.

### sonar-scanner (requires Java 17+)

Install sonar-scanner as explained in the
[SonarScanner CLI documentation](https://docs.sonarsource.com/sonarqube-server/latest/analyzing-source-code/scanners/sonarscanner/).

## Project configuration

Create a **sonar-project.properties** file at the root with this content:

```properties
# Project identification
sonar.projectKey=flutter_rocks
sonar.projectName=Flutter Rocks
sonar.projectVersion=1.0

# Source code location.
# Path is relative to the sonar-project.properties file. Defaults to .
# Use commas to specify more than one file/folder.
# It is good practice to add pubspec.yaml to the sources as the analyzer
# may produce warnings for this file as well.
sonar.sources=lib,pubspec.yaml
sonar.tests=test

# Encoding of the source code. Default is default system encoding.
sonar.sourceEncoding=UTF-8

# Analyzer mode
# Can be:
# - DETECT (flutter analyze if pubspec.yaml declares Flutter, dart analyze otherwise) - default
# - MANUAL (an existing report needs to be provided)
# - FLUTTER (flutter analyze)
# - DART (dart analyze)
# - DARTANALYZER (legacy dartanalyzer, for old Dart SDKs)
# sonar.dart.analyzer.mode=

# Allows reuse of an existing analyzer report when mode is MANUAL
# sonar.dart.analyzer.report.path=

# Analyzer report output mode
# Can be:
# - DETECT (MACHINE when the Dart SDK on the PATH is 2.12+, LEGACY otherwise and for Flutter) - default
# - MACHINE (machine readable output, available for Dart 2.12+)
# - LEGACY (attempts to parse human readable output from dart/flutter)
# sonar.dart.analyzer.report.mode=
```

*For a complete list of available options, please refer to the
[SonarQube analysis parameters](https://docs.sonarsource.com/sonarqube-server/latest/analyzing-source-code/analysis-parameters/).*

### Use existing analysis options

The plugin uses its own analysis options file, which enables the rules of the default quality
profile. If an `analysis_options.yaml` file already exists under the project root, it is saved
during the analysis and then restored to its initial state.

To use the existing `analysis_options.yaml` file instead, add the following line to the
`sonar-project.properties` file:

```properties
# Use the project's own analysis_options.yaml
sonar.dart.analyzer.options.override=false
```

Issues are only reported for rules that are active in the SonarQube quality profile: a lint
enabled in your own `analysis_options.yaml` but inactive in the profile is ignored.

### Multi-module sample

It is possible to analyze a project with multiple modules. For example a Dart generator library with an example.

```properties
sonar.projectKey=mylib
sonar.sourceEncoding=UTF-8

sonar.modules=mylib,mylib_generator,example

# mylib
mylib.sonar.sources=lib,pubspec.yaml
mylib.sonar.dart.analyzer.mode=MANUAL
mylib.sonar.dart.analyzer.report.mode=LEGACY
mylib.sonar.dart.analyzer.report.path=build/reports/analysis-results.txt

# mylib_generator
mylib_generator.sonar.sources=lib,pubspec.yaml
mylib_generator.sonar.dart.analyzer.options.override=false
mylib_generator.sonar.dart.analyzer.mode=MANUAL
mylib_generator.sonar.dart.analyzer.report.mode=MACHINE
mylib_generator.sonar.dart.analyzer.report.path=build/reports/analysis-results.txt

# example
example.sonar.sources=lib,pubspec.yaml
example.sonar.tests=test
example.sonar.exclusions=**/*/*.g.dart
example.sonar.dart.analyzer.options.override=false
example.sonar.dart.analyzer.mode=MANUAL
example.sonar.dart.analyzer.report.mode=LEGACY
example.sonar.dart.analyzer.report.path=build/reports/analysis-results.txt
```

## Run analysis

Use the following commands from the root folder to start an analysis:

```console
# Download dependencies
flutter pub get
# Run tests with user feedback (in case some tests are failing)
flutter test
# Run tests without user feedback, generating tests.output and coverage/lcov.info
flutter test --machine --coverage > tests.output

# Run the analysis and publish to the SonarQube server
sonar-scanner
```

## Using `dart_test.yaml`

Dart and Flutter support a `dart_test.yaml` file to configure test behavior, including the test
report format and location. More information can be found
[here](https://github.com/dart-lang/test/blob/master/pkgs/test/doc/configuration.md).

```yaml
file_reporters:
  json: build/reports/test-results.json
```

With this, the `--machine` switch and the output redirection are no longer needed. Point the
plugin to the report with `sonar.flutter.tests.reportPath=build/reports/test-results.json`.

The coverage output cannot be configured in this file yet. You may follow and upvote these
related issues if interested:
* Configuration option - https://github.com/dart-lang/test/issues/1361
* Dart coverage support - https://github.com/dart-lang/test/issues/1265

## Available options

All options are configurable in the SonarQube UI, via `sonar-project.properties` or `-D` parameters.

| Name                                   | Options                                                                  | Default              | Description                                                                                                                                                                                                                                                    |
|----------------------------------------|--------------------------------------------------------------------------|----------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `sonar.dart.analyzer.mode`             | <code>DETECT&#124;DART&#124;FLUTTER&#124;MANUAL&#124;DARTANALYZER</code> | `DETECT`             | By default the plugin detects the analyzer (`flutter analyze` or `dart analyze`) from the `environment` of `pubspec.yaml`. Set it to `MANUAL` to provide an existing report file. For compatibility with older Dart versions, it can be set to `DARTANALYZER`. |
| `sonar.dart.analyzer.options.override` | <code>true&#124;false</code>                                             | `true`               | By default any local `analysis_options.yaml` is replaced for the analysis. Set it to `false` to use the project's own file.                                                                                                                                    |
| `sonar.dart.analyzer.report.mode`      | <code>DETECT&#124;MACHINE&#124;LEGACY</code>                             | `DETECT`             | `DETECT` uses the machine readable output when the Dart SDK on the `PATH` is 2.12+, and the legacy output for Flutter. It must be set when the analyzer mode is `MANUAL`.                                                                                      |
| `sonar.dart.analyzer.report.path`      | A file path                                                              | -                    | Required when the analyzer mode is `MANUAL`.                                                                                                                                                                                                                   |
| `sonar.dart.file.suffixes`             | Comma separated list of suffixes                                         | `.dart`              | Suffixes of the Dart files to analyze.                                                                                                                                                                                                                         |
| `sonar.flutter.tests.reportPath`       | Comma separated list of file paths (wildcard not supported)              | `tests.output`       | The path to the test report JSON file.                                                                                                                                                                                                                         |
| `sonar.flutter.coverage.reportPath`    | A file path                                                              | `coverage/lcov.info` | The path to the test coverage file in LCOV format.                                                                                                                                                                                                             |

## Rules

The `dartanalyzer` rule repository contains 436 rules, generated from the official Dart SDK:

- 250 lints from the Dart linter catalogue;
- 142 analyzer warnings (`unused_import`, `dead_code`, `deprecated_member_use`, `must_call_super`...);
- 44 compile errors.

The built-in `dartanalyzer` quality profile activates 298 rules: the recommended rule sets
(`package:lints` core and recommended, `package:flutter_lints`), all analyzer warnings, and
`close_sinks`, `cancel_subscriptions`, `unawaited_futures`, `throw_in_finally`,
`test_types_in_equals` and `no_self_assignments`. Other rules can be activated in a custom profile.

## Building

Building with tests requires JDK 21 (the SonarQube 26.x test fixtures target Java 21):

```console
mvn verify
```

With JDK 17, build the plugin without the tests:

```console
mvn package -Dmaven.test.skip=true
```

The plugin JAR is written to `sonar-flutter-plugin/target/`.

To regenerate the rules and the plugin's `analysis_options.yaml` from the latest Dart SDK sources:

```console
uv run --no-project --with markdown --with pyyaml python scripts/update_dart_lint_rules.py
```

Pushing a `0.*` tag publishes the JAR in a GitHub release.

## Contributing

Any help is welcome, and PRs will be greatly appreciated!

Please read [CONTRIBUTING](CONTRIBUTING.md) for more information.

## License

SonarQube Plugin for Flutter / Dart is released under the GNU LGPL v3 license. See the [LICENSE](LICENSE.md) file for more information.
