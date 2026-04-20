#!/usr/bin/env bash
# Style-extraction gate for the frontend-design skill.
# Enforces: a fully-populated style file must exist before design-output
# files (HTML/CSS/JSX/TSX/Vue/Svelte in demos/test-output/app/pages/src/public)
# can be written.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
STYLES_DIR="$SKILL_DIR/references/styles"
INDEX="$STYLES_DIR/INDEX.md"
MARKER="$SKILL_DIR/.active-style"

usage() {
  cat <<EOF
Usage: style.sh <command> [args]

Commands:
  new <slug>   Create a style-file skeleton and activate the guard
  done         Clear the guard after the style file is complete
  check        Used by the PreToolUse hook; blocks if style incomplete
  status       Show current guard state

Examples:
  style.sh new editorial-japanese
  style.sh status
  style.sh done

The slug must be kebab-case (a-z, 0-9, hyphens).
EOF
}

cmd_new() {
  local slug="${1:-}"
  if [[ -z "$slug" ]]; then
    echo "Error: slug required" >&2
    usage >&2
    exit 2
  fi
  if [[ ! "$slug" =~ ^[a-z0-9][a-z0-9-]*$ ]]; then
    echo "Error: slug must be kebab-case (a-z, 0-9, hyphens); got: $slug" >&2
    exit 2
  fi

  mkdir -p "$STYLES_DIR"
  local style_file="$STYLES_DIR/$slug.md"

  if [[ -e "$style_file" ]]; then
    echo "Error: $style_file already exists." >&2
    echo "Either edit it directly, or pick a different slug." >&2
    exit 1
  fi

  cat > "$style_file" <<'TEMPLATE'
# <Style Name>

One-paragraph description: origin (which references inspired it), feel, and the
audience this style is meant for.

## When to use
- ??
- ??
- NOT for: ??

## Grid pairing
- Primary grid: ??
- Combinations: ??

## Color tokens
- --color-bg: ??
- --color-surface: ??
- --color-text-primary: ??
- --color-text-secondary: ??
- --color-text-tertiary: ??
- --color-accent: ??
- --color-border: ??
- --color-focus: ??

## Typography
- Display font: ??
- Body font: ??
- Import method: ??
- Fallback stack: ??
- Type scale ratio: ??
- Min body size: ??
- Special: ??

## Spacing rhythm
- Base scale: ??
- Notable rhythm: ??

## Visual signature
- ??
- ??
- ??

## Reference (optional — for human review)
- ??

## Avoid in this style
- ??
TEMPLATE

  printf '%s\n' "$slug" > "$MARKER"

  cat <<EOF
Created: $style_file
Marked active: $MARKER

Next steps (in order):
  1. Replace every '??' in the file with a concrete value derived from your
     cross-image analysis. Only leave '??' where you genuinely need user
     confirmation, and call that out explicitly.
  2. Show the filled style to the user for approval or edits.
  3. Run: bash "$0" done
  4. Add a one-line entry for '$slug' to $INDEX in alphabetical order.
  5. Only now begin designing.

Design-output writes are BLOCKED until step 3 succeeds.
EOF
}

cmd_done() {
  if [[ ! -e "$MARKER" ]]; then
    echo "No active style. Nothing to clear." >&2
    exit 0
  fi

  local slug
  slug=$(cat "$MARKER" | tr -d '[:space:]')
  if [[ ! "$slug" =~ ^[a-z0-9][a-z0-9-]*$ ]]; then
    echo "Error: $MARKER contains an invalid slug ('$slug')." >&2
    echo "Delete the marker manually (rm '$MARKER') and start over." >&2
    exit 1
  fi
  local style_file="$STYLES_DIR/$slug.md"

  if [[ ! -e "$style_file" ]]; then
    echo "Error: marker points to '$slug' but $style_file does not exist." >&2
    echo "Either create the file or remove the marker manually: rm '$MARKER'" >&2
    exit 1
  fi

  if grep -q '??' "$style_file"; then
    local remaining
    remaining=$(grep -c '??' "$style_file")
    echo "Error: $style_file still has $remaining unresolved '??' field(s)." >&2
    echo "Fill them in (or get user confirmation) before marking done." >&2
    exit 1
  fi

  rm "$MARKER"
  echo "Cleared active style '$slug'. Design writes are now allowed."
  if ! grep -q "^- $slug " "$INDEX" 2>/dev/null; then
    echo "Reminder: add a one-line entry for '$slug' to $INDEX."
  fi
}

cmd_check() {
  # PreToolUse hook entrypoint. Exit non-zero to block.

  # Not in style-extraction mode → allow.
  if [[ ! -e "$MARKER" ]]; then
    exit 0
  fi

  # Resolve target path from TOOL_INPUT (JSON passed by hook runner).
  # Fail open: if parsing fails for any reason, allow the write. The gate exists
  # to protect the style workflow, not to be a brittle JSON validator.
  local tool_input="${TOOL_INPUT:-}"
  local file_path=""

  if [[ -n "$tool_input" ]]; then
    if command -v jq >/dev/null 2>&1; then
      file_path=$(printf '%s' "$tool_input" | jq -r '.file_path // empty' 2>/dev/null || true)
    else
      file_path=$(printf '%s' "$tool_input" \
        | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' 2>/dev/null \
        | head -1 \
        | sed -E 's/.*"file_path"[[:space:]]*:[[:space:]]*"([^"]*)".*/\1/' \
        || true)
    fi
  fi

  # No path resolvable → allow.
  if [[ -z "$file_path" ]]; then
    exit 0
  fi

  # Extension filter: only care about design-output file types.
  case "$file_path" in
    *.html|*.htm|*.css|*.scss|*.tsx|*.jsx|*.vue|*.svelte) ;;
    *) exit 0 ;;
  esac

  # Path filter: conventional design-output folders, matched both as
  # root-relative (demos/foo.html) and nested (path/to/demos/foo.html).
  case "$file_path" in
    demos/*|test-output/*|app/*|pages/*|src/*|public/*|components/*) ;;
    */demos/*|*/test-output/*|*/app/*|*/pages/*|*/src/*|*/public/*|*/components/*) ;;
    *) exit 0 ;;
  esac

  # Validate marker contents before trusting the slug.
  local slug
  slug=$(cat "$MARKER" | tr -d '[:space:]')
  if [[ ! "$slug" =~ ^[a-z0-9][a-z0-9-]*$ ]]; then
    echo "BLOCKED: $MARKER is corrupted (invalid slug: '$slug')." >&2
    echo "Delete it (rm '$MARKER') and run: style.sh new <slug>" >&2
    exit 2
  fi

  local style_file="$STYLES_DIR/$slug.md"

  if [[ ! -e "$style_file" ]]; then
    echo "BLOCKED: active style '$slug' has no file at $style_file" >&2
    echo "Either create it (style.sh new $slug) or clear the marker (rm '$MARKER')" >&2
    exit 2
  fi

  if grep -q '??' "$style_file"; then
    echo "BLOCKED: $style_file has unresolved '??' fields." >&2
    echo "Fill all fields, confirm with user, then run: bash scripts/style.sh done" >&2
    exit 2
  fi

  exit 0
}

cmd_status() {
  if [[ ! -e "$MARKER" ]]; then
    echo "Active style: none (writes not gated)"
    exit 0
  fi

  local slug
  slug=$(cat "$MARKER" | tr -d '[:space:]')
  if [[ ! "$slug" =~ ^[a-z0-9][a-z0-9-]*$ ]]; then
    echo "Active style: CORRUPTED ('$slug')"
    echo "Marker:       $MARKER"
    echo "Status:       INVALID — delete the marker and start over"
    return 0
  fi
  local style_file="$STYLES_DIR/$slug.md"

  echo "Active style: $slug"
  echo "File:         $style_file"

  if [[ ! -e "$style_file" ]]; then
    echo "Status:       MISSING FILE"
    return 0
  fi

  if grep -q '??' "$style_file"; then
    local count
    count=$(grep -c '??' "$style_file")
    echo "Status:       INCOMPLETE ($count unresolved '??' fields)"
  else
    echo "Status:       COMPLETE"
  fi
}

main() {
  local cmd="${1:-}"
  case "$cmd" in
    new)              shift; cmd_new "$@" ;;
    done)             cmd_done ;;
    check)            cmd_check ;;
    status)           cmd_status ;;
    ""|-h|--help)     usage ;;
    *)                echo "Unknown command: $cmd" >&2; usage >&2; exit 2 ;;
  esac
}

main "$@"
