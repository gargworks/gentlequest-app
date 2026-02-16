# 🗺️ Nucleus Version Reconciliation Map (Strike Target: v1.0.6)

This map identifies every location where the version string resides. To achieve a **Unified v1.1.0 Strike**, these files must be updated simultaneously.

---

## 🛠️ Package Manifests
| Component | File Path | Current | Target (Strike) |
|-----------|-----------|---------|-----------------|
| **NPM (Registry)** | [package.json](file:///Users/lokeshgarg/ai-mvp-backend/nucleus-mcp/package.json) | `1.0.4` | `1.0.6` |
| **PyPI (Registry)** | [pyproject.toml](file:///Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/pyproject.toml) | `1.0.5` | `1.1.0` |

> [!NOTE]
> If no further development occurs before launch, the fallback target is a unified **v1.0.5**.

## 🧠 Source Code (Internal Identity)
| Component | File Path | Line(s) | Current | Target |
|-----------|-----------|---------|---------|--------|
| **Main Init** | [__init__.py](file:///Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src/mcp_server_nucleus/__init__.py) | 6 | `1.0.4` | `1.0.6` |
| **Hypervisor** | [__init__.py](file:///Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src/mcp_server_nucleus/__init__.py) | 291 | `v0.8.0` | `v1.0.6` |
| **JSON Identity** | [__init__.py](file:///Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src/mcp_server_nucleus/__init__.py) | 7155+ | `0.6.0` | `1.0.6` |
| **CLI Metadata** | [cli.py](file:///Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src/mcp_server_nucleus/cli.py) | ~10 | `1.0.0` | `1.0.6` |

## 📝 Documentation & Badges
| Component | File Path | Target |
|-----------|-----------|--------|
| **Root README** | [README.md](file:///Users/lokeshgarg/ai-mvp-backend/README.md) | Update badges if static versions are used. |
| **Draft PH Post** | [PRODUCT_HUNT_FINAL_STRIKE.md](file:///Users/lokeshgarg/ai-mvp-backend/nucleus-launch-internal/PRODUCT_HUNT_FINAL_STRIKE.md) | Update "The Sovereign Trilogy" version mention. |

---

### 🚀 Strike Execution Protocol
1.  **Wait**: Do NOT bump yet (User directive: Deferred until pre-launch).
2.  **Batch Edit**: Update all local files once `1.0.6` (or final) is locked.
3.  **Git Tag**: `git tag -a v1.0.6 -m "Pre-launch Unified Strike"`
4.  **Ship**: `npm publish` & `python3 -m build && twine upload dist/*`

**Status**: Ready for Bump. 🛡️
