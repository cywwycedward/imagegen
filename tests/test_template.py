from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from imagegen.template import (
    TemplateData,
    VariableSpec,
    apply_template,
    delete_template,
    extract_variables,
    list_templates,
    load_template,
    save_template,
)


class TestExtractVariables:
    def test_single_variable(self) -> None:
        assert extract_variables("hello {name}") == ["name"]

    def test_multiple_variables(self) -> None:
        result = extract_variables("{a} and {b} and {c}")
        assert result == ["a", "b", "c"]

    def test_no_variables(self) -> None:
        assert extract_variables("plain text") == []

    def test_escaped_braces(self) -> None:
        assert extract_variables("{{literal}} and {real}") == ["real"]

    def test_duplicate_variables(self) -> None:
        result = extract_variables("{x} then {x} again")
        assert result == ["x"]


class TestApplyTemplate:
    def _make_template(
        self,
        template_str: str,
        variables: dict[str, VariableSpec] | None = None,
    ) -> TemplateData:
        return TemplateData(
            name="test",
            description="test template",
            template=template_str,
            variables=variables or {},
        )

    def test_basic_substitution(self) -> None:
        t = self._make_template(
            "draw {prompt} in {style}",
            {
                "prompt": VariableSpec(description="subject", required=True),
                "style": VariableSpec(description="art style", required=True),
            },
        )
        result = apply_template(t, prompt="a cat", var_overrides={"style": "watercolor"})
        assert result == "draw a cat in watercolor"

    def test_default_value_used(self) -> None:
        t = self._make_template(
            "{prompt}, {bg} background",
            {
                "prompt": VariableSpec(description="subject", required=True),
                "bg": VariableSpec(description="background", default="white"),
            },
        )
        result = apply_template(t, prompt="a tree", var_overrides={})
        assert result == "a tree, white background"

    def test_default_overridden(self) -> None:
        t = self._make_template(
            "{prompt}, {bg} background",
            {
                "prompt": VariableSpec(description="subject", required=True),
                "bg": VariableSpec(description="background", default="white"),
            },
        )
        result = apply_template(t, prompt="a tree", var_overrides={"bg": "black"})
        assert result == "a tree, black background"

    def test_missing_required_variable_raises(self) -> None:
        t = self._make_template(
            "{prompt} in {style}",
            {
                "prompt": VariableSpec(description="subject", required=True),
                "style": VariableSpec(description="art style"),
            },
        )
        with pytest.raises(SystemExit):
            apply_template(t, prompt="a cat", var_overrides={})

    def test_unknown_var_override_warns(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        t = self._make_template(
            "{prompt}",
            {"prompt": VariableSpec(description="subject", required=True)},
        )
        result = apply_template(t, prompt="a cat", var_overrides={"bogus": "val"})
        assert result == "a cat"
        captured = capsys.readouterr()
        assert "bogus" in captured.err

    def test_escaped_braces_preserved(self) -> None:
        t = self._make_template(
            "{{literal}} {prompt}",
            {"prompt": VariableSpec(description="subject", required=True)},
        )
        result = apply_template(t, prompt="test")
        assert result == "{literal} test"

    def test_prompt_auto_mapped(self) -> None:
        t = self._make_template(
            "render {prompt} nicely",
            {"prompt": VariableSpec(description="subject", required=True)},
        )
        result = apply_template(t, prompt="a dog", var_overrides={})
        assert result == "render a dog nicely"


class TestTemplateCRUD:
    def test_save_and_load(self, tmp_path: Path) -> None:
        with patch("imagegen.template.get_templates_dir", return_value=tmp_path):
            save_template(
                name="my-tpl",
                template_str="draw {prompt} in {style}",
                description="test template",
                variables={
                    "prompt": VariableSpec(description="subject", required=True),
                    "style": VariableSpec(description="art style", default="oil"),
                },
            )
            loaded = load_template("my-tpl")

        assert loaded.name == "my-tpl"
        assert loaded.description == "test template"
        assert loaded.template == "draw {prompt} in {style}"
        assert loaded.variables["prompt"].required is True
        assert loaded.variables["style"].default == "oil"

    def test_load_nonexistent_exits(self, tmp_path: Path) -> None:
        with patch("imagegen.template.get_templates_dir", return_value=tmp_path):
            with pytest.raises(SystemExit):
                load_template("nope")

    def test_list_templates_empty(self, tmp_path: Path) -> None:
        with patch("imagegen.template.get_templates_dir", return_value=tmp_path):
            assert list_templates() == []

    def test_list_templates_returns_summaries(self, tmp_path: Path) -> None:
        with patch("imagegen.template.get_templates_dir", return_value=tmp_path):
            save_template(
                name="tpl-a",
                template_str="{prompt}",
                description="first",
                variables={"prompt": VariableSpec(description="s", required=True)},
            )
            save_template(
                name="tpl-b",
                template_str="{prompt} {x}",
                description="second",
                variables={
                    "prompt": VariableSpec(description="s", required=True),
                    "x": VariableSpec(description="extra", default="y"),
                },
            )
            result = list_templates()

        names = [t["name"] for t in result]
        assert "tpl-a" in names
        assert "tpl-b" in names

    def test_delete_template(self, tmp_path: Path) -> None:
        with patch("imagegen.template.get_templates_dir", return_value=tmp_path):
            save_template(
                name="to-delete",
                template_str="{prompt}",
                description="will be deleted",
                variables={"prompt": VariableSpec(description="s", required=True)},
            )
            delete_template("to-delete")
            assert list_templates() == []

    def test_delete_nonexistent_exits(self, tmp_path: Path) -> None:
        with patch("imagegen.template.get_templates_dir", return_value=tmp_path):
            with pytest.raises(SystemExit):
                delete_template("ghost")
