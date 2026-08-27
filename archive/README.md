# Archive

Nothing in this repository is deleted. When a document, code surface, or
directory stops being live, it moves here — with its git history intact
(`git mv`) and a one-line entry in `ARCHIVE_INDEX.md` recording where it came
from, when, and what supersedes it.

These are records of thinking and work, not trash. Aspirational documents in
`docs/aspirations/` are kept as the founder's exploration of directions the
product could have taken; version-scoped records in `docs/releases/` are the
audit trail of past releases; `code/` mirrors the app's tree for retired
surfaces; `dirs/` holds whole directories from earlier eras.

To un-archive anything: `git mv` it back to its original path (recorded in the
index) and remove its index line. The state of the repo immediately before this
archive existed is tagged `archive/pre-consolidation-2026-08`.

Dart under `code/` is intentionally outside `ai_buddy_web/`, so `flutter
analyze` / `flutter test` / `pub get` never see it. It will not compile as it
sits — that is expected; restore to its original path to bring it back.
