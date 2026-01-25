# Feature Map

This directory contains the living inventory of all features across products.

## Files

- `gentlequest.json` - GentleQuest mental health app features
- `nucleus.json` - Nucleus MCP toolkit features

## Schema

Each feature has:
- `id` - Unique identifier (snake_case)
- `name` - Human-readable name
- `description` - What it does
- `product` - "gentlequest" or "nucleus"
- `status` - development/staged/production/released/deprecated/broken
- `how_to_test` - Array of test steps
- `expected_result` - What should happen
- `last_validated` - When last tested
- `validation_result` - passed/failed

## Commands

```bash
# List all features
nucleus features list

# Get test instructions
nucleus features test <feature_id>
```
