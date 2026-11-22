#!/usr/bin/env python3
"""Check that every skill and manifest stays portable across Claude Code, Codex and SKILL.md agents.

  python3 tools/check_skills.py                            # skills, manifests, README
  python3 tools/check_skills.py --codex-prompt prompt.json # also check Codex lists every skill
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Fields accepted everywhere: Claude Code, claude.ai uploads, Codex and the Agent Skills spec.
PORTABLE_FIELDS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
NAME_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
# Tool names that only exist in one agent; skill bodies must stay agent-neutral.
AGENT_SPECIFIC = ["${AGENT_TOOL_NAME}", "questions_v2", "AskUserQuestion", "TodoWrite", "update_plan"]


def frontmatter(text):
    if not text.startswith("---\n"):
        raise ValueError("missing frontmatter")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError("unterminated frontmatter")
    fields = {}
    for line in text[4:end].splitlines():
        if not line.strip():
            continue
        key, sep, value = line.partition(": ")
        if not sep or line.startswith(" "):
            raise ValueError(f"only single-line `key: value` fields are supported, got {line!r}")
        fields[key] = value
    return fields, text[end + 5:]


def check_skills(errors):
    names = []
    for skill_file in sorted(ROOT.glob("skills/*/SKILL.md")):
        folder = skill_file.parent.name
        where = f"skills/{folder}/SKILL.md"
        try:
            fields, body = frontmatter(skill_file.read_text(encoding="utf-8"))
        except ValueError as error:
            errors.append(f"{where}: {error}")
            continue
        unknown = set(fields) - PORTABLE_FIELDS
        if unknown:
            errors.append(f"{where}: non-portable frontmatter fields {sorted(unknown)}")
        name, description = fields.get("name", ""), fields.get("description", "")
        if name != folder:
            errors.append(f"{where}: name {name!r} must equal the folder name")
        if not NAME_PATTERN.match(name) or len(name) > 64:
            errors.append(f"{where}: name must be lowercase-hyphenated and at most 64 characters")
        if not description:
            errors.append(f"{where}: description is required")
        if len(description) > 1024:
            errors.append(f"{where}: description is {len(description)} characters (max 1024)")
        if ": " in description or " #" in description or description[:1] in "'\"[{>|*&!%@`":
            errors.append(f"{where}: description contains characters that break plain YAML")
        if "Use when" not in description:
            errors.append(f"{where}: description should say when to use the skill ('Use when …')")
        if len(body.strip().splitlines()) > 500:
            errors.append(f"{where}: body over 500 lines; move detail to a references/ file")
        for token in AGENT_SPECIFIC:
            if token in body:
                errors.append(f"{where}: agent-specific tool name {token!r} in body")
        names.append(name)
    if not names:
        errors.append("no skills found under skills/*/SKILL.md")
    return names


def load_json(path, errors):
    try:
        return json.loads((ROOT / path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        errors.append(f"{path}: {error}")
        return {}


def check_manifests(errors):
    claude_plugin = load_json(".claude-plugin/plugin.json", errors)
    portable_plugin = load_json("plugin.json", errors)
    for key in ("name", "version", "description", "license"):
        if claude_plugin.get(key) != portable_plugin.get(key):
            errors.append(f"plugin.json and .claude-plugin/plugin.json disagree on {key!r}")
    plugin_name = claude_plugin.get("name")
    for path in (".claude-plugin/marketplace.json", ".agents/plugins/marketplace.json"):
        marketplace = load_json(path, errors)
        if marketplace.get("name") != "product-engineer-skills":
            errors.append(f"{path}: marketplace name must be 'product-engineer-skills'")
        entries = [entry.get("name") for entry in marketplace.get("plugins", [])]
        if entries != [plugin_name]:
            errors.append(f"{path}: must list exactly the plugin {plugin_name!r}, found {entries}")
    return plugin_name


def check_readme(names, errors):
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for name in names:
        if f"`{name}`" not in readme:
            errors.append(f"README.md: skill `{name}` is not documented")


def check_codex_prompt(path, plugin_name, names, errors):
    prompt = Path(path).read_text(encoding="utf-8")
    for name in names:
        if f"{plugin_name}:{name}" not in prompt:
            errors.append(f"Codex does not list the skill {plugin_name}:{name}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--codex-prompt", help="output of `codex debug prompt-input` with the plugin installed")
    args = parser.parse_args()

    errors = []
    names = check_skills(errors)
    plugin_name = check_manifests(errors)
    check_readme(names, errors)
    if args.codex_prompt:
        check_codex_prompt(args.codex_prompt, plugin_name, names, errors)

    if errors:
        print("\n".join(f"✘ {error}" for error in errors))
        sys.exit(1)
    print(f"✔ {len(names)} skills, manifests and README are consistent"
          + (" — and Codex lists every skill" if args.codex_prompt else ""))


if __name__ == "__main__":
    main()
