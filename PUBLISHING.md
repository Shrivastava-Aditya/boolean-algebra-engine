# Publishing — PyPI and CI/CD

Reference doc for how releases work, how the CI pipeline is wired, and how to do a release manually if needed.

---

## Package

**Name:** `boolean-algebra-engine`
**PyPI:** https://pypi.org/project/boolean-algebra-engine/
**Install:** `pip install boolean-algebra-engine`

### Extras

| Extra | What it installs | When to use |
|---|---|---|
| `cli` | typer, rich | Terminal usage — `boolcalc` command |
| `mcp` | mcp[cli] | Claude Desktop / MCP agent integration |
| `api` | fastapi, uvicorn | REST API server |
| `api-cache` | fastapi, uvicorn, redis | REST API with Redis caching |
| `nl-anthropic` | anthropic | NL layer via Claude |
| `nl-openai` | openai | NL layer via OpenAI or Ollama |
| `dev` | pytest, httpx | Development and testing |

```bash
pip install "boolean-algebra-engine[cli]"
pip install "boolean-algebra-engine[mcp]"
pip install "boolean-algebra-engine[cli,mcp,nl-anthropic]"
```

---

## How a release works — automated path

The full release flow is triggered by pushing a version tag:

```bash
# 1. bump version in pyproject.toml
# 2. commit
git add pyproject.toml
git commit -m "Bump version to 0.x.x"

# 3. tag and push — workflow fires automatically
git tag v0.x.x
git push origin <branch>
git push origin v0.x.x
```

That's it. GitHub Actions handles everything after step 3.

---

## What the CI workflow does

File: `.github/workflows/publish.yml`
Trigger: any tag matching `v*`

### Steps in order

**1. Checkout** — full repo at the tagged commit.

**2. Set up Python 3.11** — consistent build environment regardless of local machine.

**3. Install build tools** — `pip install build twine`.

**4. Patch image URLs** — the README references images via raw GitHub URLs that include a branch or tag name. The workflow substitutes whatever was hardcoded with the current tag name so image URLs are permanently stable at each release:

```
https://raw.githubusercontent.com/.../engine-PyPI/images/foo.png
                                        ↓
https://raw.githubusercontent.com/.../v0.1.5/images/foo.png
```

This runs `sed` on README.md in-place before building.

**5. Build** — `python -m build` produces:
- `dist/boolean_algebra_engine-X.Y.Z-py3-none-any.whl`
- `dist/boolean_algebra_engine-X.Y.Z.tar.gz`

**6. Restore README** — `git checkout README.md` reverts the sed patch so the repo copy stays clean. Only the built artifacts carry the patched README.

**7. Publish to PyPI** — `twine upload dist/*` using credentials from GitHub Secrets:
- `TWINE_USERNAME`: always `__token__`
- `TWINE_PASSWORD`: `${{ secrets.PYPI_API_TOKEN }}`

**8. Create GitHub release** — `gh release create` attaches the dist files as release assets and auto-generates release notes from commits since the last tag.

---

## Secrets required

| Secret | Where to set | Value |
|---|---|---|
| `PYPI_API_TOKEN` | Repo → Settings → Secrets → Actions | PyPI API token scoped to `boolean-algebra-engine` |

`GITHUB_TOKEN` is provided automatically by GitHub Actions — no setup needed.

### When the repo goes public

Switch to **Trusted Publishing** (PyPI OIDC) — no token stored anywhere, no rotation needed:
1. Go to PyPI → `boolean-algebra-engine` → Publishing → Add a trusted publisher
2. Set: owner `Shrivastava-Aditya`, repo `boolean-algebra-engine-python`, workflow `publish.yml`
3. Replace the Publish step in the workflow with `pypa/gh-action-pypi-publish`
4. Delete `PYPI_API_TOKEN` from secrets

---

## Manual release — local path

Use `publish.sh` if you need to publish outside of CI (e.g. repo is private and Actions can't reach PyPI, or debugging a build issue):

```bash
# uses current git branch for image URLs
./publish.sh

# override branch/tag for image URLs
RELEASE_BRANCH=v0.2.0 ./publish.sh
```

The script does the same steps as the workflow — patches README, builds, restores README, uploads. Credentials are read from `~/.pypirc`.

### ~/.pypirc format

```ini
[pypi]
username = __token__
password = pypi-YOUR_TOKEN_HERE
```

```bash
chmod 600 ~/.pypirc
```

---

## Versioning

Versions follow `MAJOR.MINOR.PATCH` (semver).

| Change | Version bump |
|---|---|
| Breaking API change | MAJOR |
| New feature, backwards compatible | MINOR |
| Bug fix, metadata update, docs | PATCH |

**PyPI versions are permanent.** Once published, a version cannot be overwritten or deleted — only yanked (marked as not recommended). Always bump before publishing.

The version lives in one place: `pyproject.toml`:

```toml
[project]
version = "0.1.5"
```

---

## Image URL strategy

README images are hosted on the repo. Raw GitHub URLs only resolve publicly when the repo is public.

**Current state (repo private):** images will 404 on PyPI. The CI workflow pins them to the git tag, so they will resolve correctly once the repo goes public.

**When the repo goes public:** no changes needed. The tag-pinned URLs will work immediately.

**Alternative (repo stays private):** upload images as GitHub release assets and use the release asset URLs — those are always public regardless of repo visibility.

---

## Current token

Token name on PyPI: `Bool-1`
Scope: `boolean-algebra-engine` package only
Stored: `~/.pypirc` locally, `PYPI_API_TOKEN` in repo secrets

Rotate if the token is ever exposed in plaintext (e.g. pasted in a chat).
