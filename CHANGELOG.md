# Changelog

## 0.6.1

#### Breaking

- Maintained by Diagngrow: Maven `groupId` and Java packages renamed to `com.diagngrow.sonarqube`
  (the plugin key `flutter` and the rule repository `dartanalyzer` are unchanged).

#### Enhancements

- README rewritten for the Diagngrow fork: compatibility table, rules and default profile,
  build instructions, fixed `sonar.dart.analyzer.options.override` example (`false` keeps the
  project's own `analysis_options.yaml`), documented `sonar.dart.file.suffixes`; outdated
  screenshot removed.

## 0.6.0 (fork diagngrow)

#### Breaking

- Requires SonarQube 26.10+ (Sonar Plugin API 14.1.0.5543) and Java 17+.
- Default quality profile now activates the Dart recommended rule sets
  (`package:lints` core + recommended, `package:flutter_lints`) instead of every rule,
  plus `close_sinks`, `cancel_subscriptions`, `unawaited_futures`, `throw_in_finally`,
  `test_types_in_equals` and `no_self_assignments`, and all analyzer warnings.
- Rule types and severities are recomputed from explicit tables instead of linter categories
  and the 0.5.2 values: style lints (`curly_braces_in_flow_control_structures`, `avoid_print`,
  `empty_statements`...) are code smells, CRITICAL is reserved to near-certain bugs, and compile
  errors are MAJOR instead of BLOCKER. Ratings of existing projects change.

#### Enhancements

- Migrated to `org.sonarsource.api.plugin:sonar-plugin-api` 14.1, SLF4J logging and the
  SonarQube 26.x test fixtures; removed internal API usage (`DefaultIssueLocation`) and Guava.
- Plugin is only downloaded by the scanner for projects containing Dart (`requiredForLanguages`).
- Rules regenerated from the official Dart linter catalogue (`pkg/linter/tool/machine/rules.json`):
  28 added, 14 removed (removed from the linter), descriptions rendered from the linter docs.
- `analysis_options.yaml` only lists real lints (no analyzer diagnostic codes, no removed/deprecated lints).
- Rule keys are lowercase, matching the issues reported by the analyzer. The three former
  camelCase keys are declared as deprecated keys, so existing profiles and issues are kept.
- Analyzer warnings are now rules (142, from `pkg/analyzer/messages.yaml`): `unused_import`,
  `dead_code`, `deprecated_member_use`, `must_call_super`... were silently dropped before.
- `analysis_options.yaml` keeps the historical camelCase lint names (Dart < 3.6 rejects the
  lowercase ones) and ignores `undefined_lint` / `incompatible_lint` on itself.
- Compile errors no longer defined by the Dart SDK are dropped by the generator.
- New rule generator `scripts/update_dart_lint_rules.py` replaces the HTML scraping Groovy script.

## 0.5.2

#### Breaking

- None.

#### Experimental

- None.

#### Enhancements

- Analyzer rules update (7 added)

#### Bug Fixes

- #187 pubspec.yaml parser fails when no dependencies are declared
- #223 some dartanalyzer rules disappeared

## 0.5.1

#### Breaking

- None.

#### Experimental

- None.

#### Enhancements

- Analyzer rules update: there are now 279 rules available

#### Bug Fixes

- #177 analyzer execution fails when errors detected.
- #212 source file not indexed with SonarQube 10.4+
- PR #201 bump snakeyaml and jackson-databind to latest versions
- Updated Apache Ivy to 2.5.2

## 0.5.0

#### Breaking

- SonarQube API update to 7.9 for latest LTS support (9.9)
- Removed `dartanalyzer` implementation that scans each file individual, this may affect projects running on a (pretty) old Dart SDK.
  The replacement runs legacy `dartanalyzer .` instead which is much faster.
- Renamed `sonar.flutter.analyzer.mode` to `sonar.dart.analyzer.mode` and reworked implementation.
  - Available options `DETECT|DART|FLUTTER|MANUAL|DARTANALYZER`
  - Defaults to automatic detection by parsing the `pubspec.yaml`.
  - Uses `flutter analyze` when `environment.flutter` is configured in `pubspec.yaml`.
  - Uses `dart analyze` when `environment.flutter` is NOT configured in `pubspec.yaml`.
  - Allows to be configured for legacy `dartanalyzer` if required (`DARTANALYZER`)
  - Allows to be configured for pre-existing analysis reports (`MANUAL`)
- Renamed `sonar.dart.analysis.useExistingOptions` to `sonar.dart.analyzer.options.override`, now defaults to `true`
- Renamed `sonar.dart.analysis.reportPath` to `sonar.dart.analyzer.report.path` - this is only evaluated when `sonar.dart.analyzer.mode`is set to `MANUAL`
- Added `sonar.dart.analyzer.report.mode` option
  - Available options `DETECT|MACHINE|LEGACY`
  - Defaults to automatic detection by parsing the Dart SDK version and defaults to `--format=machine` for Dart when SDK >= 2.12
  - Can be set to legacy mode when using pre-existing analysis report or an older Dart SDK

#### Experimental

- None.

#### Enhancements

- Add a `pubspec.yaml` sensor which adds the file to SonarQube and allow showing lints for this file
- Add support for multi-module projects (`sonar.modules=mylib,mylib_generator,example`) 
- Added missing dart keywords and corrected some
  - `try`
  - `hide`
  - `show`
  - `late`
  - `of`
  - `continue`
  - `covariant`
  - `out`
  - `do`
  - `dynamic`
  - `native`
- Rules update
- Better rules description

#### Bug Fixes

- #160 dart analysis with an exception of NumberFormatException


## 0.4.0

#### Breaking

- None.

#### Experimental

- None.

#### Enhancements

- (#65) Support SonarQube 9 - (thanks to @kuhnroyal)
- (#32) make perfer final issue type to CODE_SMELL - (thanks to @magaofei)
- (#70) Automate changelog and releases - (thanks to @kuhnroyal)
- (#66) CI improvements - (thanks to @kuhnroyal)
- (#56) Update README.md - (thanks to @thiagoloureiro)

#### Bug Fixes

- None.

## 0.3.2

#### Breaking

- None.

#### Experimental

- None.

#### Enhancements

- Allow re-using an existing dartanalyzer report with `sonar.dart.analysis.reportPath` (thanks to [Peter Leibiger](https://github.com/kuhnroyal))
- Add missing dart keywords `extension`, `on`, `mixin` (thanks to [Peter Leibiger](https://github.com/kuhnroyal))
- Add pedantic 1.9.0 profile (thanks to [Daniel Morawetz](https://github.com/dmorawetz))
- Faster analysis with 'flutter analyze' and support for different analysis modes with `sonar.flutter.analyzer.mode` (thanks to [Marc Reichelt](https://github.com/mreichelt))

#### Bug Fixes

- Ensure analyzer encoding is UTF-8 (thanks to [Daniel Morawetz](https://github.com/dmorawetz))


## 0.3.1

#### Breaking

- None.

#### Experimental

- None.

#### Enhancements

- Better handling of missing test report file.
- Faster analysis on large projects (increased analyser page size to 50).

#### Bug Fixes

- Test report parsing fix for Windows (thanks to [victorgilc](https://github.com/victorgilc)).
- Removed duplicated issues on the same file.

## 0.3.0

#### Breaking

- None.

#### Experimental

- None.

#### Enhancements

- Add Flutter 1.20.0 test report compatibility (thanks to [Peter Leibiger](https://github.com/kuhnroyal)), fixes #19
- Improve test report parsing (thanks to [Peter Leibiger](https://github.com/kuhnroyal)), fixes #13
- Ability to use existing analysis options (configurable behavior) (thanks to [Stephane Janicaud](https://github.com/stephanecodes])), fixes #23, #18
- Paginated analysis with dartanalyzer (thanks to [victorgilc](https://github.com/victorgilc))

#### Bug Fixes

- Report the correct test case count (thanks to [Peter Leibiger](https://github.com/kuhnroyal))
- Better test report parsing (thanks to [victorgilc](https://github.com/victorgilc))
- Restore Java 8 compatibility required by the sonar-scanner (thanks to [Peter Leibiger](https://github.com/kuhnroyal))
- Restore the original analysis options file when analysis crashes (thanks to [amond](https://github.com/amondnet))
- Windows support (thanks to [victorgilc](https://github.com/victorgilc)), fixes #12, #24
- Running sonar-scanner does not result no 0 exit code anymore when issues are found by dartanalyzer (thanks to [amond](https://github.com/amondnet)), fixes #11

## 0.2.1

#### Breaking

- None.

#### Experimental

- None.

#### Enhancements

- Added diagnostic rules (thanks to [etiennecadicidean](https://github.com/etiennecadicidean))

#### Bug Fixes

- None

## 0.2.0

#### Breaking

- None.

#### Experimental

- None.

#### Enhancements

- Syntax coloration
- Cyclomatic complexity computation
- More accurate code line count 

#### Bug Fixes

- None

## 0.1.0

#### Breaking

- Initial release.

#### Experimental

- None.

#### Enhancements

- None.

#### Bug Fixes

- None.
