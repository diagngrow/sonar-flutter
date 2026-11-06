#!/usr/bin/env python3
"""
Met a jour les regles du depot `dartanalyzer` a partir du linter Dart officiel.

Sources (lisibles par machine, publiees par l'equipe Dart) :
  - catalogue du linter : dart-lang/sdk  pkg/linter/tool/machine/rules.json
  - jeux de regles      : package:lints (core, recommended) et
                          package:flutter_lints (flutter)

Fichiers produits :
  - dart-lang/src/main/resources/dartanalyzer/rules.json
  - dart-lang/src/main/resources/dartanalyzer/analysis_options.yaml

Regles de generation :
  - toutes les regles du linter sauf l'etat `removed` ;
  - type   : BUG pour les categories errorProne / unintentional / memoryLeaks,
             CODE_SMELL sinon ;
  - severite : conservee si la regle existait deja (choix manuels de
             l'ancien fichier), sinon deduite de la categorie ;
  - active (profil par defaut) : regle des jeux core + recommended + flutter ;
  - les diagnostics de l'analyseur (non-lints) deja presents sont conserves.

analysis_options.yaml active toutes les regles stables ou experimentales
(le profil SonarQube filtre ensuite) ; les regles depreciees et les codes de
diagnostic n'y figurent pas (ce ne sont pas des lints).

Usage : python3 scripts/update_dart_lint_rules.py   (necessite `markdown`)
"""
import html
import json
import pathlib
import re
import sys
import urllib.request

import markdown

ROOT = pathlib.Path(__file__).resolve().parent.parent
RES = ROOT / "dart-lang/src/main/resources/dartanalyzer"
RULES_FILE = RES / "rules.json"
OPTIONS_FILE = RES / "analysis_options.yaml"

LINTER_RULES_URL = "https://raw.githubusercontent.com/dart-lang/sdk/main/pkg/linter/tool/machine/rules.json"
SET_URLS = [
    "https://raw.githubusercontent.com/dart-lang/core/main/pkgs/lints/lib/core.yaml",
    "https://raw.githubusercontent.com/dart-lang/core/main/pkgs/lints/lib/recommended.yaml",
    "https://raw.githubusercontent.com/flutter/packages/main/packages/flutter_lints/lib/flutter.yaml",
]

BUG_CATEGORIES = {"errorProne", "unintentional", "memoryLeaks"}
SEVERITY_BY_CATEGORY = [  # premiere categorie trouvee gagne
    ("memoryLeaks", "CRITICAL"),
    ("errorProne", "MAJOR"),
    ("unintentional", "MAJOR"),
    ("nonPerformant", "MAJOR"),
    ("web", "MAJOR"),
    ("publicInterface", "MINOR"),
    ("flutter", "MINOR"),
    ("style", "MINOR"),
]
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


def severity_for(categories) -> str:
    for cat, sev in SEVERITY_BY_CATEGORY:
        if cat in categories:
            return sev
    return "MINOR"


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
    recommended = set().union(*(rule_set(u) for u in SET_URLS))

    old = json.loads(RULES_FILE.read_text(encoding="utf-8"))
    # Le capteur met les identifiants en minuscules : les cles le sont aussi.
    old_by_key = {r["key"].lower(): r for r in old}
    lint_names = {r["name"].lower() for r in lints}

    out = []
    for rule in sorted(lints, key=lambda r: r["name"]):
        if rule["state"] == "removed":
            continue
        cats = rule.get("categories", [])
        prev = old_by_key.get(rule["name"].lower(), {})
        out.append({
            "key": rule["name"].lower(),
            "name": rule["description"].strip().rstrip("."),
            "severity": prev.get("severity") or severity_for(cats),
            "description": describe(rule),
            "type": "BUG" if BUG_CATEGORIES & set(cats) else "CODE_SMELL",
            "debt": prev.get("debt") or DEFAULT_DEBT,
            "active": rule["name"].lower() in recommended and rule["state"] != "deprecated",
        })

    # Diagnostics de l'analyseur (erreurs/avertissements, hors linter) : conserves.
    diagnostics = [dict(r, key=k) for k, r in old_by_key.items() if k not in lint_names]
    out.extend(sorted(diagnostics, key=lambda r: r["key"]))

    RULES_FILE.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    enabled = [CAMEL_CASE_LINTS.get(r["name"].lower(), r["name"]) for r in sorted(lints, key=lambda r: r["name"])
               if r["state"] in ("stable", "experimental")]
    OPTIONS_FILE.write_text("linter:\n  rules:\n" + "".join(f"    - {k}\n" for k in enabled),
                            encoding="utf-8")

    state = {r["name"].lower(): r["state"] for r in lints}
    removed = sorted(k for k in old_by_key if state.get(k) == "removed")
    added = sorted(r["key"] for r in out if r["key"] not in old_by_key)
    print(f"{len(out)} regles ({len(out) - len(diagnostics)} lints, {len(diagnostics)} diagnostics), "
          f"{sum(r['active'] for r in out)} actives par defaut")
    print(f"ajoutees ({len(added)}) : {', '.join(added)}")
    print(f"retirees (removed dans le linter, {len(removed)}) : {', '.join(removed)}")
    print(f"analysis_options.yaml : {len(enabled)} lints")
    return 0


if __name__ == "__main__":
    sys.exit(main())
