# Changelog

## [0.1.0] - 2026-04-22

### Features
- **cli**: add CLI tool with provider/model resolution and image generation
- **cli**: add image options (`--aspect-ratio`, `--image-size`), `edit` and `chat` commands, grounding support (`--grounding`), and session management
- **cli**: add `--options` flag to `provider list` to show model parameter support
- **cli**: add Model ID column to `provider list --model` output

### Bug Fixes
- **types**: resolve mypy arg-type errors in generate and chat modules

### Documentation
- add install, configuration, and user guide documentation
- sync development guide with current codebase

### Chores
- initial commit with reference docs
