# ⚔️ Switch War Room

**Two AI agents fight over a live app inside your team chat. One breaks in, one patches it, a third keeps score. Nothing ships until a human types `approve`.**

<p align="center"><img src="docs/lock-flip.gif" width="560" alt="A lock on the live dashboard flips from VULNERABLE to FIXED after Blue's patch is approved"></p>

### 🎥 Demo (80 sec)

[▶️ Download the demo video](docs/demo.mp4)

> 🧑‍💻 Built solo by [Barnavo Dey](https://github.com/barnavo05) for **Flip the Switch** (WeMakeDevs x Switch), Nov 2026 · Track 01, Best Business Workflow

---

## The problem

Most small teams never run a security drill. There's no red team, no blue team, and no free week to schedule one. So bugs like SQL injection or a forgotten debug endpoint sit in production until someone else finds them.

War Room turns a drill into a 15 minute match that runs in the chat room your team already lives in. The attacker, the defender and the referee are AI agents. **You stay in charge:** every fix waits for your approval, and every claim is verified by real exploit tests, not by an AI saying "trust me".

## What a match looks like

| 🔴 Red finds a hole and proves it | 🔵 Blue proposes a fix and waits for you |
|---|---|
| ![Red Team claims a SQL injection flag](docs/chat-red-claim.jpg) | ![Blue Team posts a diff and asks for approval](docs/chat-blue-patch.jpg) |

The Referee re-runs real exploits after every patch, updates the score, and when all five holes are closed writes an **incident report** with lessons for the team:

![Final scoreboard and incident report in the war-room](docs/chat-final-score.jpg)

And a live **spectator dashboard** so anyone walking past the screen gets it in five seconds:

![Live dashboard: score, five locks, live feed](docs/dashboard.jpg)

## The cast

| Who | Role | Sees the code? | Can change code? |
|---|---|---|---|
| 🔴 **Red Team** (agent) | Black box attacker. Gets a URL and a customer login, nothing else | ❌ | ❌ |
| 🔵 **Blue Team** (agent) | Defender. Finds the root cause, proposes a diff | ✅ | ✅ only after you approve |
| 🧑‍⚖️ **Referee** (agent) | Runs turns, verifies every claim with `check.py`, keeps score, writes the report | ✅ | ❌ |
| 🧑 **You** | Incident Commander. Final say on every patch | | |

## How Switch is used (and why it breaks without it)

| Switch feature | What it does in War Room | Without it |
|---|---|---|
| **Rooms with many agents and humans** | Red, Blue, Referee and you share one channel and one history | No shared timeline, no match |
| **Agent to agent @mentions** (`owner-agents` addressing) | The Referee hands turns with `@red-team` / `@blue-team`, agents reply to each other | You'd be copy-pasting between three terminals |
| **Human in the room** | Blue stops and waits for your `approve` in the same chat | The safety gate disappears |
| **Per-agent working directory** | Red gets an empty folder (true black box), Blue and Referee get the project | Red could just read the source |
| **Templates** | `switch/war-room.template.yaml` creates all three agents and the room in one import | Manual setup of 3 agents every time |
| **Bridges** | The same room runs in Mattermost today, Slack or Discord with one setting | Locked to one chat app |

## The referee can't be fooled

`referee/check.py` judges each bug twice:
1. **Attack:** several exploit variants, not just the obvious one. Blocking the word `UNION` still loses to `UnIoN SeLeCt`.
2. **Feature test:** search, login, your own orders, your own invoices and the real admin page must keep working.

| Verdict | Meaning | Score |
|---|---|---|
| 🔴 VULNERABLE | some variant still leaks the flag | Red can claim a bypass (+2) |
| 🟢 FIXED | every variant blocked and the feature works | Blue +2 |
| 🟠 BROKEN | flag blocked, but the feature died with it | Blue -1 |

## The arena: ChaiCart

A tiny shop API (Flask + SQLite) in Docker, bound to `127.0.0.1` only, with five planted bugs, each guarding a `FLAG{...}`:

| # | Vulnerability | OWASP Top 10 |
|---|---|---|
| 1 | SQL injection in product search | A03 Injection |
| 2 | Debug endpoint leaking secrets | A05 Security Misconfiguration |
| 3 | IDOR on orders | A01 Broken Access Control |
| 4 | Forgeable auth tokens | A07 Identification and Authentication Failures |
| 5 | Path traversal on invoices | A01 Broken Access Control |

## Run it yourself (about 10 minutes)

**You need:** Docker Desktop, [Switch Console](https://docs.switchagents.ai/switch-rooms/getting-started), and Claude Code (or Codex / OpenCode). macOS or Linux.

```bash
git clone https://github.com/barnavo05/switch-war-room && cd switch-war-room
./scripts/start.sh               # ChaiCart on http://127.0.0.1:5050
python3 referee/check.py         # should show 5x 🔴 VULNERABLE
```

In **Switch Console**:
1. **Templates > Import template**, pick `switch/war-room.template.yaml`
2. Set **project_dir** to the absolute path of this folder, then **Create**
3. Open the `war-room` room and type `@referee start match`
4. Approve each patch with `@blue-team approve`

Optional, in a second terminal, the spectator dashboard:
```bash
./scripts/dashboard.sh           # http://127.0.0.1:8099
```

Reset everything before a new match: `./scripts/reset.sh`

**Commands in the room:** `start match` · `approve` · `reject, <reason>` · `pause` / `resume` · `end match`

<details>
<summary>Troubleshooting</summary>

| Problem | Fix |
|---|---|
| `start.sh` says Docker is not running | Open Docker Desktop and wait for "Engine running" |
| Dashboard says port in use | `DASHBOARD_PORT=9000 ./scripts/dashboard.sh` |
| Dashboard shows "Arena is offline" | Run `./scripts/start.sh` first |
| An agent goes quiet | @mention it directly, e.g. `@referee continue` |
| Want a clean slate | `./scripts/reset.sh` |
</details>

## Use it on your own app

ChaiCart is the training ground. The same room works on a real staging service:
1. Point Red at your staging URL in the template (keep it internal, never production)
2. Point Blue's `project_dir` at your service repo
3. Write one check per known risk in `referee/check.py` (it's plain Python, standard library only)
4. Run it as a **weekly drill** in your team's Slack or Discord via a Switch bridge. Every patch still waits for a human

## Project layout

```
arena/                ChaiCart, the vulnerable target (Docker)
  app/app.py          the code Blue patches (reloads live)
  pristine/           untouched copy, used by reset
referee/
  check.py            exploit + feature checks, the source of truth
  scoreboard.py       score and match log
  RULES.md            rules of the match
dashboard/            live spectator view (standard library server)
scripts/              start, stop, reset, dashboard
switch/
  war-room.template.yaml   the Switch template: 3 agents + room + kickoff
docs/                 screenshots and GIF for this README
```

## Safety

ChaiCart is insecure on purpose. It only listens on `127.0.0.1`, so nothing outside your machine can reach it. Red's instructions forbid any other host, flooding, or reading source. Blue can only edit `arena/app/`, and only after a human approves. Never deploy the arena anywhere public.

## What's next
- Run the room in Slack or Discord so the whole team can spectate
- A "bypass round" mode where Red gets two tries against every patch
- More arenas: auth flows, cloud misconfig, LLM prompt injection

---
Made by [Barnavo Dey](https://github.com/barnavo05) · #HowISwitch
