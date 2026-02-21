# Pychromeless Backlog

## Terraform

- [x] **Migrate DynamoDB GSI `hash_key`/`range_key` to `key_schema`** - Completed 2026-02-21
  - Migrated `task_states` GSI from deprecated `hash_key`/`range_key` to `key_schema` blocks
  - Note: `key_schema` only applies to GSI blocks, not table-level keys (`hash_key`/`range_key` remain correct at table level)
  - Also fixed perpetual diff from GSI `write_capacity`/`read_capacity` on PAY_PER_REQUEST table
  - Provider upgraded from v6.30.0 → v6.33.0
