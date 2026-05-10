from __future__ import annotations

import pytest

from imagegen.template import (
    TemplateData,
    VariableSpec,
    apply_template,
    extract_variables,
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
