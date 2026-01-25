# Nucleus CLI Setup (pipx Isolated Mode)

> **Why this exists:**
> GentleQuest Production requires Python 3.9.6 ("Nuclear Hazard Switch").
> Nucleus CLI requires Python 3.10+.
> **Solution:** Use `pipx` to run Nucleus in a safe, isolated container.

---

## 1. Prerequisites (Homebrew)

First, install `pipx` if you don't have it:

```bash
brew install pipx
pipx ensurepath
```

*Note: You may need to restart your terminal after `ensurepath`.*

---

## 2. Install Nucleus

**Important:** Navigate to your project folder first.

```bash
cd ~/ai-mvp-backend
pipx install ./mcp-server-nucleus
```

This will:
1. Create a virtual environment (likely using Python 3.11/3.12).
2. Install `fastmcp` and dependencies inside it.
3. Link the `nucleus` command to your global path.

---

## 3. Verify

Check that it works without breaking your local python:

```bash
# Check version (should clearly be from pipx)
nucleus --version

# Check local python (should still be 3.9.6)
python3 --version
```

---

## 4. Troubleshooting

If `pipx` fails to find a newer python:
```bash
brew install python@3.11
pipx install ./mcp-server-nucleus --python /opt/homebrew/bin/python3.11
```
