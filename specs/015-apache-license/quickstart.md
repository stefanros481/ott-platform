# Quickstart: Verify License Implementation

**Feature**: 015-apache-license

## Prerequisites

No new dependencies required. All verification is done with standard file system and text tools.

---

## 1. Verify LICENSE file

```bash
# Check file exists at repo root
ls LICENSE

# Check copyright line
head -3 LICENSE
# Expected: "                                 Apache License"
# Check that "Copyright 2026 Stefan Rosander" appears (it's above the Apache header)

# Optional: compare checksum against canonical text
# (The project adds a copyright preamble, so full checksum only applies to the Apache body)
```

---

## 2. Verify package metadata

```bash
# Python
grep 'license' backend/pyproject.toml
# Expected: license = "Apache-2.0"

# Frontend client
node -e "const p=require('./frontend-client/package.json'); console.log(p.license)"
# Expected: Apache-2.0

# Frontend admin
node -e "const p=require('./frontend-admin/package.json'); console.log(p.license)"
# Expected: Apache-2.0
```

---

## 3. Verify SPDX headers on source files

```bash
# Check all Python files have the header
find backend/app -name "*.py" | xargs grep -L "SPDX-License-Identifier: Apache-2.0"
# Expected: no output (all files have the header)

# Check all TypeScript files have the header
find frontend-client/src frontend-admin/src \( -name "*.ts" -o -name "*.tsx" \) \
  | xargs grep -L "SPDX-License-Identifier: Apache-2.0"
# Expected: no output (all files have the header)

# Confirm count
find backend/app -name "*.py" | xargs grep -l "SPDX-License-Identifier" | wc -l
# Expected: 64

find frontend-client/src frontend-admin/src \( -name "*.ts" -o -name "*.tsx" \) \
  | xargs grep -l "SPDX-License-Identifier" | wc -l
# Expected: 65 (45 + 20)
```

---

## 4. Verify README License section

```bash
grep -A 4 "^## License" README.md
# Expected:
# ## License
#
# Copyright 2026 Stefan Rosander
#
# Licensed under the [Apache License, Version 2.0](LICENSE).
```

---

## 5. Review third-party audit

```bash
# The audit report is pre-generated
cat specs/015-apache-license/third-party-licenses.md | grep "Overall Verdict"
# Expected: ✅ PASS
```

---

## All-in-one check

```bash
echo "=== LICENSE ===" && ls LICENSE && head -1 LICENSE
echo "=== pyproject.toml ===" && grep "^license" backend/pyproject.toml
echo "=== frontend-client ===" && node -e "console.log(require('./frontend-client/package.json').license)"
echo "=== frontend-admin ===" && node -e "console.log(require('./frontend-admin/package.json').license)"
echo "=== Python files missing header ===" && find backend/app -name "*.py" | xargs grep -L "SPDX-License-Identifier" | wc -l
echo "=== TS files missing header ===" && find frontend-client/src frontend-admin/src \( -name "*.ts" -o -name "*.tsx" \) | xargs grep -L "SPDX-License-Identifier" | wc -l
echo "=== README License section ===" && grep -c "^## License" README.md
```

All counts of "missing header" should be `0`. README check should be `1`.
