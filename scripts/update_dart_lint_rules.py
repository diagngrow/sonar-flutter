#!/usr/bin/env python3
"""
Met a jour les regles du depot `dartanalyzer` a partir du linter Dart officiel.

Sources (lisibles par machine, publiees par l'equipe Dart) :
  - catalogue du linter : dart-lang/sdk  pkg/linter/tool/machine/rules.json
  - diagnostics         : dart-lang/sdk  pkg/analyzer/messages.yaml
  - jeux de regles      : package:lints (core, recommended) et
                          package:flutter_lints (flutter)

Fichiers produits :
  - dart-lang/src/main/resources/dartanalyzer/rules.json
  - dart-lang/src/main/resources/dartanalyzer/analysis_options.yaml

Regles de generation :
  - toutes les regles du linter sauf l'etat `removed` ;
  - tous les avertissements de l'analyseur (WarningCode, HintCode,
    StaticWarningCode) : actifs par defaut comme dans `dart analyze` ;
  - les erreurs de compilation deja presentes sont conservees si le SDK les
    definit encore ;
  - type et severite : tables explicites ci-dessous (BUG_LINTS, BUG_WARNINGS,
    ...), CODE_SMELL MINOR sinon. Les categories du linter ne suffisent pas :
    `errorProne` couvre aussi des regles de style (accolades, print...) ;
  - active (profil par defaut) : regle des jeux core + recommended + flutter,
    plus EXTRA_ACTIVE_LINTS.

analysis_options.yaml active toutes les regles stables ou experimentales
(le profil SonarQube filtre ensuite) ; les regles depreciees et les codes de
diagnostic n'y figurent pas (ce ne sont pas des lints).

Usage : python3 scripts/update_dart_lint_rules.py   (necessite `markdown` et `pyyaml`)
"""
import html
import json
import pathlib
import re
import sys
import urllib.request

import markdown
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
RES = ROOT / "dart-lang/src/main/resources/dartanalyzer"
RULES_FILE = RES / "rules.json"
OPTIONS_FILE = RES / "analysis_options.yaml"

LINTER_RULES_URL = "https://raw.githubusercontent.com/dart-lang/sdk/main/pkg/linter/tool/machine/rules.json"
MESSAGES_URL = "https://raw.githubusercontent.com/dart-lang/sdk/main/pkg/analyzer/messages.yaml"
WARNING_CLASSES = ("WarningCode", "HintCode", "StaticWarningCode")
SET_URLS = [
    "https://raw.githubusercontent.com/dart-lang/core/main/pkgs/lints/lib/core.yaml",
    "https://raw.githubusercontent.com/dart-lang/core/main/pkgs/lints/lib/recommended.yaml",
    "https://raw.githubusercontent.com/flutter/packages/main/packages/flutter_lints/lib/flutter.yaml",
]

# Lints qui signalent un comportement faux a l'execution, et leur severite.
# Une severite CRITICAL degrade fortement la note de fiabilite : elle est
# reservee aux erreurs presque toujours reelles.
BUG_LINTS = {
    "cancel_subscriptions": "CRITICAL",
    "close_sinks": "CRITICAL",
    "collection_methods_unrelated_type": "CRITICAL",
    "hash_and_equals": "CRITICAL",
    "no_duplicate_case_values": "CRITICAL",
    "recursive_getters": "CRITICAL",
    "test_types_in_equals": "CRITICAL",
    "unrelated_type_equality_checks": "CRITICAL",
    "avoid_double_and_int_checks": "MAJOR",
    "avoid_dynamic_calls": "MAJOR",
    "avoid_empty_else": "MAJOR",
    "avoid_js_rounded_ints": "MAJOR",
    "avoid_type_to_string": "MAJOR",
    "avoid_types_as_parameter_names": "MAJOR",
    "avoid_web_libraries_in_flutter": "MAJOR",
    "cast_nullable_to_non_nullable": "MAJOR",
    "conditional_uri_does_not_exist": "MAJOR",
    "control_flow_in_finally": "MAJOR",
    "discarded_futures": "MAJOR",
    "exhaustive_cases": "MAJOR",
    "invalid_runtime_check_with_js_interop_types": "MAJOR",
    "no_logic_in_create_state": "MAJOR",
    "no_self_assignments": "MAJOR",
    "no_wildcard_variable_uses": "MAJOR",
    "null_closures": "MAJOR",
    "throw_in_finally": "MAJOR",
    "unawaited_futures": "MAJOR",
    "use_build_context_synchronously": "MAJOR",
    "valid_regexps": "MAJOR",
    "unnecessary_statements": "MINOR",
}
# Code smells plus graves que la valeur par defaut (MINOR).
MAJOR_SMELL_LINTS = {
    "avoid_relative_lib_imports",
    "avoid_shadowing_type_parameters",
    "empty_statements",
    "overridden_fields",
}
INFO_LINTS = {
    "missing_code_block_language_in_doc_comment",
    "unintended_html_in_doc_comment",
}
# Hors jeux recommandes, mais utiles en audit : fuites de ressources, futures
# perdues, erreurs de logique. avoid_dynamic_calls et discarded_futures restent
# inactives (trop de bruit sur du code Flutter courant).
EXTRA_ACTIVE_LINTS = {
    "cancel_subscriptions",
    "close_sinks",
    "no_self_assignments",
    "test_types_in_equals",
    "throw_in_finally",
    "unawaited_futures",
}

# Avertissements de l'analyseur (codes en snake_case, ceux du rapport).
BUG_WARNINGS = {
    "null_check_always_fails": "CRITICAL",
    "cast_from_null_always_fails": "CRITICAL",
    "cast_from_nullable_always_fails": "CRITICAL",
    "assignment_of_do_not_store": "MAJOR",
    "body_might_complete_normally_catch_error": "MAJOR",
    "body_might_complete_normally_nullable": "MAJOR",
    "constant_pattern_never_matches_value_type": "MAJOR",
    "equal_elements_in_set": "MAJOR",
    "equal_keys_in_map": "MAJOR",
    "invalid_return_type_for_catch_error": "MAJOR",
    "invalid_return_type_for_then": "MAJOR",
    "missing_enum_constant_in_switch": "MAJOR",
    "missing_override_of_must_be_overridden": "MAJOR",
    "missing_required_param": "MAJOR",
    "missing_return": "MAJOR",
    "mixin_on_sealed_class": "MAJOR",
    "must_call_super": "MAJOR",
    "non_const_argument_for_const_parameter": "MAJOR",
    "null_argument_to_non_null_type": "MAJOR",
    "pattern_never_matches_value_type": "MAJOR",
    "receiver_of_type_never": "MAJOR",
    "return_of_do_not_store": "MAJOR",
    "subtype_of_sealed_class": "MAJOR",
    "tearoff_with_must_be_const_parameter": "MAJOR",
    "unnecessary_nan_comparison": "MAJOR",
    "unused_result": "MAJOR",
}
VULNERABILITY_WARNINGS = {
    # Caracteres de controle bidirectionnels (attaque « Trojan Source »).
    "text_direction_code_point_in_comment": "CRITICAL",
    "text_direction_code_point_in_literal": "CRITICAL",
}
MAJOR_SMELL_WARNINGS = {
    "dead_code",
    "import_of_legacy_library_into_null_safe",
    "invalid_override_of_non_virtual_member",
    "invalid_use_of_do_not_submit_member",
    "invalid_use_of_internal_member",
    "invalid_use_of_protected_member",
    "invalid_use_of_visible_for_overriding_member",
    "invalid_use_of_visible_for_testing_member",
    "must_be_immutable",
    "override_on_non_overriding_member",
}
INFO_WARNING_PREFIXES = ("doc_directive_", "doc_import_")
# Les codes `sdk_version_*` signalent une syntaxe plus recente que la
# contrainte SDK du pubspec : le code ne compile pas avec la version minimale.
SDK_VERSION_PREFIX = "sdk_version_"
# Erreurs de compilation : un projet qui compile ne devrait pas en avoir. En
# audit, elles viennent surtout d'un `pub get` ou d'une generation de code
# (build_runner) non lances : MAJOR plutot que BLOCKER pour ne pas noyer la
# note de fiabilite.
COMPILE_ERROR_SEVERITY = "MAJOR"
# Le fichier active tous les lints : un SDK plus ancien que le catalogue en
# ignore certains (undefined_lint) et des paires s'excluent (incompatible_lint).
# Ces avertissements portent sur analysis_options.yaml, hors de l'analyse
# SonarQube : on les masque. Les variantes _warning sont celles de Dart 3.0.
OPTIONS_HEADER = """analyzer:
  errors:
    incompatible_lint: ignore
    incompatible_lint_warning: ignore
    undefined_lint: ignore
    undefined_lint_warning: ignore
"""
DEFAULT_DEBT = "5min"
# Seuls lints dont le nom historique n'est pas en minuscules. Le catalogue les
# liste en minuscules, mais les SDK anterieurs a Dart 3.6 ne reconnaissent que
# ces noms dans analysis_options.yaml (undefined_lint sinon), et les cles
# SonarQube des versions <= 0.5.2 les utilisaient.
CAMEL_CASE_LINTS = {name.lower(): name for name in (
    "no_runtimeType_toString",
    "prefer_for_elements_to_map_fromIterable",
    "prefer_iterable_whereType",
)}


def fetch(url: str) -> str:
    with urllib.request.urlopen(url, timeout=60) as resp:
        return resp.read().decode("utf-8")


def rule_set(url: str) -> set:
    # Noms en minuscules : les jeux gardent le camelCase historique, pas le catalogue.
    names = re.findall(r"^\s*-\s+([A-Za-z0-9_]+)\s*$", fetch(url), re.MULTILINE)
    return {name.lower() for name in names}


def snake(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def lint_type_and_severity(key: str) -> tuple:
    if key in BUG_LINTS:
        return "BUG", BUG_LINTS[key]
    if key in MAJOR_SMELL_LINTS:
        return "CODE_SMELL", "MAJOR"
    if key in INFO_LINTS:
        return "CODE_SMELL", "INFO"
    return "CODE_SMELL", "MINOR"


def warning_type_and_severity(code: str) -> tuple:
    if code in VULNERABILITY_WARNINGS:
        return "VULNERABILITY", VULNERABILITY_WARNINGS[code]
    if code in BUG_WARNINGS:
        return "BUG", BUG_WARNINGS[code]
    if code.startswith(SDK_VERSION_PREFIX):
        return "BUG", "MAJOR"
    if code in MAJOR_SMELL_WARNINGS:
        return "CODE_SMELL", "MAJOR"
    if code.startswith(INFO_WARNING_PREFIXES):
        return "CODE_SMELL", "INFO"
    return "CODE_SMELL", "MINOR"


def warnings_by_code(messages: dict) -> dict:
    """Avertissements regroupes par code de rapport (sharedName ou nom)."""
    by_code = {}
    for cls in WARNING_CLASSES:
        for name, entry in messages[cls].items():
            if entry.get("removedIn"):
                continue
            by_code.setdefault(snake(entry.get("sharedName") or name), []).append(entry)
    return by_code


def describe_warning(code: str, entries: list) -> str:
    documented = next((e for e in entries if e.get("documentation")), None)
    if documented:
        # [! !] encadre la zone signalee dans les exemples de la doc du SDK.
        doc = documented["documentation"].replace("[!", "").replace("!]", "")
        # Directives des tests de la doc en tete d'exemple : %uri="lib/a.dart"
        # devient un commentaire, %language=... et autres disparaissent.
        doc = re.sub(r'^%uri="([^"]+)"$', r"// \1", doc, flags=re.MULTILINE)
        doc = re.sub(r"^%\w+=.*\n", "", doc, flags=re.MULTILINE)
        body = markdown.markdown(doc, extensions=["fenced_code"])
    else:
        entry = entries[0]
        parts = [entry.get("problemMessage", ""), entry.get("correctionMessage", "")]
        # Les parametres (#name) sont remplaces par <name>.
        texts = [html.escape(re.sub(r"#(\w+)", r"<\1>", part)) for part in parts if part]
        body = "".join(f"<p>{text}</p>" for text in texts)
    link = f"https://dart.dev/tools/diagnostic-messages#{code}"
    return body + f'\n<p>Avertissement de l\'analyseur Dart. Voir <a href="{link}">{link}</a></p>'


def describe(rule: dict) -> str:
    body = markdown.markdown(rule.get("details") or rule["description"],
                             extensions=["fenced_code"])
    notes = []
    if rule["state"] in ("experimental", "deprecated"):
        notes.append(f"<p><strong>Etat dans le linter Dart :</strong> {rule['state']}.</p>")
    if rule.get("incompatible"):
        notes.append("<p><strong>Incompatible avec :</strong> "
                     + ", ".join(f"<code>{html.escape(r)}</code>" for r in rule["incompatible"])
                     + ".</p>")
    if rule.get("sinceDartSdk"):
        notes.append(f"<p>Disponible depuis Dart {html.escape(rule['sinceDartSdk'])}.</p>")
    link = f"https://dart.dev/tools/linter-rules/{rule['name']}"
    notes.append(f'<p>Voir <a href="{link}">{link}</a></p>')
    return body + "\n" + "\n".join(notes)


def main() -> int:
    lints = json.loads(fetch(LINTER_RULES_URL))
    messages = yaml.safe_load(fetch(MESSAGES_URL))
    recommended = set().union(*(rule_set(u) for u in SET_URLS))

    old = json.loads(RULES_FILE.read_text(encoding="utf-8"))
    # Le capteur met les identifiants en minuscules : les cles le sont aussi.
    old_by_key = {r["key"].lower(): r for r in old}
    lint_names = {r["name"].lower() for r in lints}

    lint_rules = []
    for rule in sorted(lints, key=lambda r: r["name"]):
        if rule["state"] == "removed":
            continue
        key = rule["name"].lower()
        rule_type, severity = lint_type_and_severity(key)
        prev = old_by_key.get(key, {})
        lint_rules.append({
            "key": key,
            "name": rule["description"].strip().rstrip("."),
            "severity": severity,
            "description": describe(rule),
            "type": rule_type,
            "debt": prev.get("debt") or DEFAULT_DEBT,
            "active": (key in recommended or key in EXTRA_ACTIVE_LINTS) and rule["state"] != "deprecated",
        })

    # Avertissements de l'analyseur : signales par defaut par `dart analyze`.
    warnings = warnings_by_code(messages)
    warning_rules = []
    for code in sorted(warnings):
        if code in lint_names:
            continue
        rule_type, severity = warning_type_and_severity(code)
        prev = old_by_key.get(code, {})
        warning_rules.append({
            "key": code,
            "name": code.replace("_", " ").capitalize(),
            "severity": severity,
            "description": describe_warning(code, warnings[code]),
            "type": rule_type,
            "debt": prev.get("debt") or DEFAULT_DEBT,
            "active": True,
        })

    # Erreurs de compilation deja presentes : conservees tant que le SDK les
    # definit (une regle disparue du SDK ne peut plus etre signalee).
    sdk_codes = {snake(e.get("sharedName") or n) for entries in messages.values() for n, e in entries.items()}
    known = lint_names | set(warnings)
    error_rules = [dict(r, key=k, type="BUG", severity=COMPILE_ERROR_SEVERITY)
                   for k, r in sorted(old_by_key.items()) if k not in known and k in sdk_codes]

    out = lint_rules + warning_rules + error_rules
    RULES_FILE.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    enabled = [CAMEL_CASE_LINTS.get(r["name"].lower(), r["name"]) for r in sorted(lints, key=lambda r: r["name"])
               if r["state"] in ("stable", "experimental")]
    OPTIONS_FILE.write_text(OPTIONS_HEADER + "linter:\n  rules:\n" + "".join(f"    - {k}\n" for k in enabled),
                            encoding="utf-8")

    new_keys = {r["key"] for r in out}
    dropped = sorted(k for k in old_by_key if k not in new_keys)
    added = sorted(k for k in new_keys if k not in old_by_key)
    print(f"{len(out)} regles ({len(lint_rules)} lints, {len(warning_rules)} avertissements, "
          f"{len(error_rules)} erreurs de compilation), {sum(r['active'] for r in out)} actives par defaut")
    print(f"ajoutees ({len(added)}) : {', '.join(added)}")
    print(f"retirees ({len(dropped)}) : {', '.join(dropped)}")
    print(f"analysis_options.yaml : {len(enabled)} lints")
    return 0


if __name__ == "__main__":
    sys.exit(main())
