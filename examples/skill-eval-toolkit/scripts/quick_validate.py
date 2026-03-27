#!/usr/bin/env python3
"""
Quick validation script for skills - minimal version (no external dependencies)
"""

import sys
import re
from pathlib import Path


def _parse_frontmatter(text):
    """Parse YAML frontmatter using only stdlib.

    Handles simple key: value pairs and multi-line strings via YAML '>'
    folded scalar or '|' literal scalar syntax. Does NOT handle nested
    structures beyond top-level keys — but that's all we need for
    SKILL.md validation.
    """
    result = {}
    current_key = None
    current_value_lines = []
    is_multiline = False

    for line in text.splitlines():
        # New top-level key?  pattern: "key:" or "key: value"
        m = re.match(r'^([a-z][a-z0-9_-]*)\s*:\s*(.*)', line)
        if m and not (is_multiline and line.startswith((' ', '\t'))):
            # Flush previous key
            if current_key is not None:
                result[current_key] = _flush_value(current_value_lines)
            current_key = m.group(1)
            rest = m.group(2).strip()
            if rest in ('>', '|'):
                is_multiline = True
                current_value_lines = []
            elif rest:
                is_multiline = False
                current_value_lines = [rest]
            else:
                is_multiline = False
                current_value_lines = []
        elif current_key is not None:
            # Continuation line for current key
            current_value_lines.append(line.strip())

    if current_key is not None:
        result[current_key] = _flush_value(current_value_lines)

    return result


def _flush_value(lines):
    """Join collected value lines into a single string."""
    joined = ' '.join(l for l in lines if l)
    # Remove surrounding quotes if present
    if len(joined) >= 2 and joined[0] == joined[-1] and joined[0] in ('"', "'"):
        joined = joined[1:-1]
    return joined


def validate_skill(skill_path):
    """Basic validation of a skill"""
    skill_path = Path(skill_path)

    # Check SKILL.md exists
    skill_md = skill_path / 'SKILL.md'
    if not skill_md.exists():
        return False, "SKILL.md not found"

    # Read and validate frontmatter
    content = skill_md.read_text()
    if not content.startswith('---'):
        return False, "No YAML frontmatter found"

    # Extract frontmatter
    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return False, "Invalid frontmatter format"

    frontmatter_text = match.group(1)
    frontmatter = _parse_frontmatter(frontmatter_text)

    if not frontmatter:
        return False, "Frontmatter must be a YAML dictionary"

    # Define allowed properties
    ALLOWED_PROPERTIES = {
        'name', 'description', 'license', 'allowed-tools', 'metadata', 'compatibility',
        'disable-model-invocation', 'user-invocable', 'context', 'agent',
        'argument-hint', 'model', 'effort', 'hooks',
    }

    # Check for unexpected properties
    unexpected_keys = set(frontmatter.keys()) - ALLOWED_PROPERTIES
    if unexpected_keys:
        return False, (
            f"Unexpected key(s) in SKILL.md frontmatter: {', '.join(sorted(unexpected_keys))}. "
            f"Allowed properties are: {', '.join(sorted(ALLOWED_PROPERTIES))}"
        )

    # Check required fields
    if 'name' not in frontmatter:
        return False, "Missing 'name' in frontmatter"
    if 'description' not in frontmatter:
        return False, "Missing 'description' in frontmatter"

    # Extract name for validation
    name = frontmatter.get('name', '')
    if not isinstance(name, str):
        return False, f"Name must be a string, got {type(name).__name__}"
    name = name.strip()
    if name:
        # Check naming convention (kebab-case: lowercase with hyphens)
        if not re.match(r'^[a-z0-9-]+$', name):
            return False, f"Name '{name}' should be kebab-case (lowercase letters, digits, and hyphens only)"
        if name.startswith('-') or name.endswith('-') or '--' in name:
            return False, f"Name '{name}' cannot start/end with hyphen or contain consecutive hyphens"
        if len(name) > 64:
            return False, f"Name is too long ({len(name)} characters). Maximum is 64 characters."

    # Extract and validate description
    description = frontmatter.get('description', '')
    if not isinstance(description, str):
        return False, f"Description must be a string, got {type(description).__name__}"
    description = description.strip()
    if description:
        if '<' in description or '>' in description:
            return False, "Description cannot contain angle brackets (< or >)"
        if len(description) > 1024:
            return False, f"Description is too long ({len(description)} characters). Maximum is 1024 characters."

    # Validate compatibility field if present (optional)
    compatibility = frontmatter.get('compatibility', '')
    if compatibility:
        if not isinstance(compatibility, str):
            return False, f"Compatibility must be a string, got {type(compatibility).__name__}"
        if len(compatibility) > 500:
            return False, f"Compatibility is too long ({len(compatibility)} characters). Maximum is 500 characters."

    return True, "Skill is valid!"

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m scripts.quick_validate <skill_directory>")
        sys.exit(1)

    valid, message = validate_skill(sys.argv[1])
    print(message)
    sys.exit(0 if valid else 1)
