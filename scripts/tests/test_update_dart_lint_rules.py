"""Tests du generateur de regles : uv run --no-project --with markdown --with pyyaml --with pytest pytest scripts/tests"""
import pathlib
import sys

import pytest
import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import update_dart_lint_rules as gen  # noqa: E402


def test_load_yaml_rejette_les_cles_dupliquees():
    with pytest.raises(yaml.constructor.ConstructorError, match="cle dupliquee"):
        gen.load_yaml("WarningCode:\n  DEAD_CODE: {}\n  DEAD_CODE: {}\n")


def test_load_yaml_accepte_un_document_valide():
    assert gen.load_yaml("a:\n  b: 1\n") == {"a": {"b": 1}}


def test_fetch_refuse_les_schemas_autres_que_https():
    with pytest.raises(SystemExit, match="HTTPS"):
        gen.fetch("file:///etc/passwd")


def test_classe_d_avertissements_absente():
    with pytest.raises(SystemExit, match="HintCode"):
        gen.warnings_by_code({"WarningCode": {}, "StaticWarningCode": {}})


def test_lints_incompatibles_actifs():
    lints = [{"name": "always_specify_types", "incompatible": ["omit_local_variable_types"]},
             {"name": "omit_local_variable_types", "incompatible": ["always_specify_types"]}]
    rules = [{"key": "always_specify_types", "active": True},
             {"key": "omit_local_variable_types", "active": True}]
    with pytest.raises(SystemExit, match="always_specify_types/omit_local_variable_types"):
        gen.check_no_incompatible_active(lints, rules)
    rules[1]["active"] = False
    gen.check_no_incompatible_active(lints, rules)
