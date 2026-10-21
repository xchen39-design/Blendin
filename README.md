# Blendin 🧋

**Mix your interests. Find your place.**

Blendin turns your hobbies into a blend of campus clubs and local event discoveries. Pick your interests like drink ingredients, watch your cup fill up, and find a place to connect at William & Mary or around Williamsburg.

Originally built by our team for **&hacks XI (2025)**. This repository restores and consolidates the recovered hackathon code, preserves the original hand-drawn artwork, and adds a reproducible setup.

[Project story on Devpost](https://devpost.com/software/project-5rayh1)

## Quick start

Requires **Node.js 22+**, **npm**, and **Python 3.11+**. Run these commands from the repository root:

```bash
git clone https://github.com/xchen39-design/Blendin.git
cd Blendin
npm ci
npm run setup
npm run dev
```

Open **http://127.0.0.1:5174**.

`npm run setup` creates an isolated `.venv` and installs the locked Python dependencies. It uses `python3` on macOS/Linux and `python` on Windows. Set `PYTHON` if your Python executable has a different name. Installation requires internet; local club matching does not.

**No API keys are required.** Choose interests and click **Mix my interests** to match against the saved campus directory. Enable **Also check live event calendars** to query online event listings as well.

## Features

- Original Blendin title artwork and illustrated campus scene.
- Responsive interface with an animated interest drink, selectable interests and custom keywords.
- Local matching against **538 saved campus club links**, with aliases for interests such as music, coding and sports.
- Optional live event discovery from William & Mary and Visit Williamsburg.
- Club recommendations remain available when external calendars fail or time out.
- Clear empty states, input validation and accessible button/checkbox controls.

## Commands

| Command | What it does |
| --- | --- |
| `npm ci` | Install locked frontend dependencies |
| `npm run setup` | Create the Python environment and install backend dependencies |
| `npm run dev` | Start Vite on 5174 and FastAPI on 8001 |
| `npm run build` | Type-check and build the frontend |
| `npm test` | Run backend and API tests without calling external calendars |
| `npm start` | Serve the built frontend and API together on 8001 |

For a production-style local run, stop the development servers and run:

```bash
npm run build
npm start
```

Then open **http://127.0.0.1:8001**. Both modes bind to the local computer by default. Port 8001 avoids the macOS AirPlay conflict commonly encountered on port 5000.

## How matching works

1. Interests are normalized and expanded with a small, explicit alias map.
2. The backend matches them against organization names inferred from the saved TribeLink URLs.
3. When enabled, live discovery fetches two fixed calendar pages concurrently and accepts matching event-detail links, excluding ordinary navigation and unsafe URLs.
4. Matching event listings appear first, followed by matching campus clubs. Requests have bounded timeouts; unavailable sources produce visible notices.

This is deterministic keyword matching, not an AI model. The drink animation visualizes your selected interests; it is not a recommendation score.

## Data and limitations

- **The campus directory was saved in September 2025.** Club names are derived from URL slugs and may be abbreviated. Current club status and link availability have not been verified individually.
- Event discovery reads public HTML. Sites can change, block requests, or render content with JavaScript, so not every event will be discovered.
- An event result is a link to a matching listing, not a guarantee that it is upcoming, available or open for registration. Confirm the date and details on the original page.
- If no matches are found, Blendin shows an honest empty state and direct calendar links rather than invented recommendations.
- This version has no accounts or persistent user profiles. Selected interests stay in the browser session and are sent to the local backend for matching. Live discovery fetches fixed listing pages and filters them locally.
- Google Fonts is an optional visual enhancement; system fonts are used when it is unavailable.

## Project structure

```text
client/                     React + TypeScript + Vite
  public/assets/            Original team illustrations
  src/                      Responsive interest builder and results UI
server/
  main.py                   FastAPI matching and event-discovery API
  requirements.txt          Direct Python dependencies
  requirements.lock.txt     Tested Python dependency versions
  tests/                    Backend/API tests
scripts/                    Setup and startup helpers
data/club_links.json        Recovered campus directory
archive/                    Original frontend and backend source snapshots
docs/RECOVERY.md             Recovery sources and consolidation notes
```

Vite proxies `/api` to the Python backend during development. The built application is served by FastAPI, so frontend API calls use the same origin in both modes.

### API

- `GET /api/health` — service status and directory size.
- `POST /api/recommend` — accepts an interest list, result limit and optional live search flag.

```json
{
  "interests": ["music", "coding"],
  "top_k": 12,
  "live_events": false
}
```

The response includes `items`, `warnings`, `mode`, `directory_note` and direct `calendars` links. Inputs require 1–20 nonempty interests of at most 60 characters each; `top_k` must be between 1 and 30.

## Validation completed during restoration

- TypeScript checking and Vite production build passed.
- **10 automated tests passed**, including input validation, local matching, unsafe/navigation link rejection, false substring matches, provider failure, timeout fallback and honest empty results.
- Browser verification covered the welcome screen, interest selection, actual club results and empty-input feedback.
- Checked desktop and 390-pixel mobile layouts; no horizontal overflow was observed.
- A live calendar request returned event listings. External-source reliability and individual club links are not guaranteed by that check.

## Team and provenance

Created by the team listed on [Devpost](https://devpost.com/software/project-5rayh1):

- **azhou1114 Zhou**
- **oucyzh Zhang**
- **CedricLiu87 Liu**
- **xchen39-design Chen**

This repository is a restored edition of that shared hackathon project. The original artwork and project concept remain credited to the team. The original source snapshots are retained under `archive/`; they are historical reference files, not the active application. No new license is assigned to the original team code or media.

## 中文使用说明

1. 安装 Node.js 22+ 和 Python 3.11+。
2. 在仓库根目录依次运行 `npm ci`、`npm run setup`、`npm run dev`。
3. 打开 `http://127.0.0.1:5174`，选择兴趣后点击 **Mix my interests**。
4. 默认使用本地保存的社团目录，无需 API key；勾选在线日历后会额外查询活动。
5. 社团目录是 2025 年 9 月的备份，活动日期与报名状态请以原网站为准。

若提示端口被占用，请先停止其他使用 5174 或 8001 的开发服务。若 Python 环境缺失，重新执行 `npm run setup`。原桌面文件和微信压缩包未被修改。
