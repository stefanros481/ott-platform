# Third-Party License Compatibility Audit

**Feature**: 015-apache-license
**Date**: 2026-02-23
**Project License**: Apache-2.0
**Scope**: Direct dependencies only (transitive deps excluded per spec)

## Compatibility Reference

Licenses compatible with Apache-2.0 distribution:
- Apache-2.0 ✅
- MIT ✅
- BSD-2-Clause ✅
- BSD-3-Clause ✅
- ISC ✅
- Python-2.0 ✅
- LGPL-2.1 ✅ (dynamic linking, compatible as library dependency)

Licenses **incompatible** with Apache-2.0 distribution:
- GPL-2.0, GPL-3.0 ❌
- AGPL-3.0 ❌
- SSPL ❌

---

## Python Dependencies (`backend/pyproject.toml`)

| Package | SPDX License | Verdict | Source |
|---------|-------------|---------|--------|
| fastapi | MIT | ✅ Compatible | [PyPI](https://pypi.org/project/fastapi/) |
| uvicorn | BSD-3-Clause | ✅ Compatible | [PyPI](https://pypi.org/project/uvicorn/) |
| sqlalchemy | MIT | ✅ Compatible | [PyPI](https://pypi.org/project/SQLAlchemy/) |
| alembic | MIT | ✅ Compatible | [PyPI](https://pypi.org/project/alembic/) |
| asyncpg | Apache-2.0 | ✅ Compatible | [PyPI](https://pypi.org/project/asyncpg/) |
| pgvector | MIT | ✅ Compatible | [PyPI](https://pypi.org/project/pgvector/) |
| pydantic | MIT | ✅ Compatible | [PyPI](https://pypi.org/project/pydantic/) |
| pydantic-settings | MIT | ✅ Compatible | [PyPI](https://pypi.org/project/pydantic-settings/) |
| python-jose | MIT | ✅ Compatible | [PyPI](https://pypi.org/project/python-jose/) |
| passlib | BSD-2-Clause | ✅ Compatible | [PyPI](https://pypi.org/project/passlib/) |
| redis | MIT | ✅ Compatible | [PyPI](https://pypi.org/project/redis/) |
| sentence-transformers | Apache-2.0 | ✅ Compatible | [PyPI](https://pypi.org/project/sentence-transformers/) |
| httpx | BSD-3-Clause | ✅ Compatible | [PyPI](https://pypi.org/project/httpx/) |
| slowapi | MIT | ✅ Compatible | [PyPI](https://pypi.org/project/slowapi/) |
| jinja2 | BSD-3-Clause | ✅ Compatible | [PyPI](https://pypi.org/project/Jinja2/) |

**Result**: 15/15 dependencies — all Compatible. No flagged or unknown entries.

---

## Node.js Dependencies (`frontend-client/package.json` + `frontend-admin/package.json`)

Both frontends share the same dependency set (frontend-admin is a subset of frontend-client).

| Package | SPDX License | Verdict | Source |
|---------|-------------|---------|--------|
| react | MIT | ✅ Compatible | [npm](https://www.npmjs.com/package/react) |
| react-dom | MIT | ✅ Compatible | [npm](https://www.npmjs.com/package/react-dom) |
| react-router-dom | MIT | ✅ Compatible | [npm](https://www.npmjs.com/package/react-router-dom) |
| @tanstack/react-query | MIT | ✅ Compatible | [npm](https://www.npmjs.com/package/@tanstack/react-query) |
| shaka-player | Apache-2.0 | ✅ Compatible | [npm](https://www.npmjs.com/package/shaka-player) |
| @types/react | MIT | ✅ Compatible | [npm](https://www.npmjs.com/package/@types/react) |
| @types/react-dom | MIT | ✅ Compatible | [npm](https://www.npmjs.com/package/@types/react-dom) |
| @vitejs/plugin-react | MIT | ✅ Compatible | [npm](https://www.npmjs.com/package/@vitejs/plugin-react) |
| autoprefixer | MIT | ✅ Compatible | [npm](https://www.npmjs.com/package/autoprefixer) |
| postcss | MIT | ✅ Compatible | [npm](https://www.npmjs.com/package/postcss) |
| tailwindcss | MIT | ✅ Compatible | [npm](https://www.npmjs.com/package/tailwindcss) |
| typescript | Apache-2.0 | ✅ Compatible | [npm](https://www.npmjs.com/package/typescript) |
| vite | MIT | ✅ Compatible | [npm](https://www.npmjs.com/package/vite) |

**Result**: 13/13 dependencies — all Compatible. No flagged or unknown entries.

---

## Overall Verdict

✅ **PASS** — All 28 direct dependencies (15 Python + 13 Node.js) carry permissive licenses (MIT, BSD-2-Clause, BSD-3-Clause, or Apache-2.0). No GPL, AGPL, or other copyleft licenses found.

The project is clear to distribute under Apache License, Version 2.0.

---

## Decisions Required

None. No flagged or unknown entries.

---

## Notes

- `python-jose[cryptography]` pulls in `cryptography` as a dependency, which is dual-licensed Apache-2.0/BSD. As a transitive dependency it is out of scope, but noted for completeness — it is compatible.
- `uvicorn[standard]` pulls in websockets (BSD), httptools (MIT), and uvloop (Apache-2.0/MIT). All transitive; all compatible.
- This audit covers **direct** dependencies only. Transitive dependency audit is deferred as a follow-up per spec scope definition.
