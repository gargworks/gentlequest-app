# Publishing to PyPI

## Package Built

The package has been built successfully:

```
dist/
├── nucleus_mcp-1.0.0.tar.gz      # Source distribution
└── nucleus_mcp-1.0.0-py3-none-any.whl  # Wheel
```

## Publish Command

To publish to PyPI, run:

```bash
cd /Users/lokeshgarg/ai-mvp-backend/nucleus-mcp
source .venv/bin/activate
twine upload dist/*
```

You'll need:
- PyPI account at https://pypi.org
- API token (create at https://pypi.org/manage/account/token/)

## Environment Variable Method

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-your-token-here
twine upload dist/*
```

## GitHub Actions (Automated)

The CI workflow at `.github/workflows/ci.yml` will automatically publish on push to main if:
1. Tests pass
2. `PYPI_API_TOKEN` secret is set in GitHub repo settings

To set up:
1. Go to https://github.com/eidetic-works/nucleus-mcp/settings/secrets/actions
2. Add secret: `PYPI_API_TOKEN` with your PyPI token

## Test PyPI (Optional)

Test first on TestPyPI:

```bash
twine upload --repository testpypi dist/*
pip install --index-url https://test.pypi.org/simple/ nucleus-mcp
```

## After Publishing

Verify installation:

```bash
pip install nucleus-mcp
nucleus-init --version
```

---

*Package ready for PyPI publication.*
