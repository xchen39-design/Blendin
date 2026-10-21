# Recovery notes

Restored on 2026-10-21 from the local `hack` source directory and inspected backup archives.

## Sources

- Desktop project: `CS/CSCI 141/hack`, containing the React/TypeScript frontend, FastAPI backend, artwork and campus directory.
- Desktop `hack.zip`: another source snapshot bundled with old dependencies/environment files.
- WeChat `hack 2.zip`: same frontend and artwork; backend differs mainly in CORS configuration and includes launch scripts.
- WeChat `blendin_splash_ready.zip`: frontend and artwork backup.
- WeChat `hack.zip`: an earlier modular implementation with additional setup files.
- Project description and team attribution: https://devpost.com/software/project-5rayh1

## Consolidation decisions

The desktop source was used as the primary recovered version. Original `App.tsx` and backend `main.py` are preserved in `archive/`. Original source folders and ZIP archives were left untouched.

The active version has a single root npm workflow, a project-local Python environment, locked dependencies, same-origin API calls, separate frontend/backend directories and a responsive layout using the team's original title and scene assets. The drink is rendered with CSS for a controllable fill animation; original drink assets remain available in the asset folder.

The original backend could index an empty interest list, match ordinary navigation as events, and silently return unrelated fallbacks. The restored version validates inputs, separates local club matching from optional online discovery, filters event-detail URLs, bounds network work and shows source failures explicitly. It does not guess dates or present old directory entries as current verified organizations.

Copied dependency directories, virtual environments, personal environment files and macOS metadata are excluded from the repository. The two original archive source files are kept only for provenance and are not used at runtime.

The publishing credential available during restoration lacks GitHub's workflow-editing scope. Automated checks are therefore provided as local commands; no active GitHub Actions workflow is installed.
