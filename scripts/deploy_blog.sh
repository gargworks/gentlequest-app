#!/bin/bash
set -euo pipefail

# Deploy the GentleQuest Astro blog to Cloudflare Pages via wrangler.
#
# Usage:
#   scripts/deploy_blog.sh                # production deploy
#   scripts/deploy_blog.sh --preview      # preview branch deploy
#   scripts/deploy_blog.sh --skip-build   # deploy existing dist without rebuilding
#
# Env overrides:
#   BLOG_DIR     (default: gentlequest-blog at repo root)
#   PROJECT_NAME (default: gentlequest-blog)
#   BRANCH       (default: main; ignored for --preview)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

BLOG_DIR="${BLOG_DIR:-$REPO_ROOT/gentlequest-blog}"
PROJECT_NAME="${PROJECT_NAME:-gentlequest-www}"
BRANCH="${BRANCH:-main}"

PREVIEW=0
SKIP_BUILD=0
while [[ $# -gt 0 ]]; do
	case "$1" in
		--preview)    PREVIEW=1; shift ;;
		--skip-build) SKIP_BUILD=1; shift ;;
		-h|--help)
			echo "Usage: $0 [--preview] [--skip-build]"
			exit 0
			;;
		*)
			echo "Unknown option: $1" >&2
			exit 2
			;;
	esac
done

if [[ ! -d "$BLOG_DIR" ]]; then
	echo "ERROR: blog directory not found: $BLOG_DIR" >&2
	exit 1
fi

if ! command -v wrangler >/dev/null 2>&1; then
	echo "ERROR: wrangler not found on PATH. Install with: npm i -g wrangler" >&2
	exit 1
fi

# CLOUDFLARE_API_TOKEN env var can conflict with wrangler OAuth if it lacks
# Pages permissions. Unset it so wrangler uses its cached OAuth credentials.
if [[ -n "${CLOUDFLARE_API_TOKEN:-}" ]]; then
	echo "==> Unsetting CLOUDFLARE_API_TOKEN (using wrangler OAuth instead)..."
	unset CLOUDFLARE_API_TOKEN
fi

cd "$BLOG_DIR"

# 1. Build
if [[ $SKIP_BUILD -eq 0 ]]; then
	echo "==> Installing dependencies (npm ci)..."
	if [[ -f package-lock.json ]]; then
		npm ci
	else
		npm install
	fi

	echo "==> Building Astro site..."
	npm run build
else
	echo "==> Skipping build (--skip-build); using existing dist/"
fi

# Astro writes to ./dist/blog (see astro.config.mjs outDir with base: '/blog').
# We deploy the parent dist/ directory so the blog/ subdirectory is preserved
# at /blog/ on Cloudflare Pages, matching the base path URLs.
DIST_DIR="$BLOG_DIR/dist"
if [[ ! -d "$DIST_DIR/blog" ]]; then
	echo "ERROR: build output not found: $DIST_DIR/blog" >&2
	echo "       Run without --skip-build, or check astro.config.mjs outDir." >&2
	exit 1
fi

# 2. Deploy via wrangler pages
WRANGLER_ARGS=(pages deploy "$DIST_DIR" --project-name "$PROJECT_NAME" --commit-dirty)
if [[ $PREVIEW -eq 1 ]]; then
	WRANGLER_ARGS+=(--branch preview)
else
	WRANGLER_ARGS+=(--branch "$BRANCH")
fi

if [[ $PREVIEW -eq 1 ]]; then
	DEPLOY_BRANCH="preview"
else
	DEPLOY_BRANCH="$BRANCH"
fi
echo "==> Deploying to Cloudflare Pages (project: $PROJECT_NAME, branch: $DEPLOY_BRANCH)..."
DEPLOY_OUTPUT_FILE="$(mktemp)"
wrangler "${WRANGLER_ARGS[@]}" 2>&1 | tee "$DEPLOY_OUTPUT_FILE"
DEPLOY_OUTPUT="$(cat "$DEPLOY_OUTPUT_FILE")"
rm -f "$DEPLOY_OUTPUT_FILE"

# 3. Print the deployment URL
URL="$(printf '%s\n' "$DEPLOY_OUTPUT" | grep -oE 'https://[a-zA-Z0-9./_-]+\.pages\.dev' | head -n1)"
if [[ -z "$URL" ]]; then
	# Fallback: some wrangler versions print a custom-domain or alias URL.
	URL="$(printf '%s\n' "$DEPLOY_OUTPUT" | grep -oE 'https://[a-zA-Z0-9./_-]+' | grep -iE 'pages\.dev|blog\.gentlequest' | head -n1)"
fi

echo
echo "==> Deployment complete."
if [[ -n "$URL" ]]; then
	echo "    URL: $URL"
else
	echo "    (Could not parse URL from wrangler output — check the log above.)"
	exit 3
fi
