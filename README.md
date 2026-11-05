# ⚔️ Switch War Room

**Two AI agents fight over a live app in your team chat. One breaks in, one patches it, a third keeps score. You approve every fix.**

Most small teams never run a security drill. They don't have a red team, a blue team, or the time. War Room gives you all three as AI agents in a chat room, so a drill becomes something you watch over chai instead of something you schedule for next quarter.

Built solo for the **Flip the Switch Hackathon** (WeMakeDevs x DevTools Academy x Switch), November 2026.

> 🎥 Demo video: _add link_
> 📝 Blog post: _add link_

---

## What happens in the room

```
You (Incident Commander):  start match
Referee:   ⚔️ Round 1. Target is live, all 5 doors locked... supposedly.
           @red-team you are cleared to attack.
Red Team:  Probing product search with a quote character...
           🔴 CLAIM: SQL injection
           How: curl "http://127.0.0.1:5050/api/products?q=' UNION SELECT ..."
           Proof: FLAG{...}
           @referee verify my claim
Referee:   Verified. 🔴 Red +1.  @blue-team Incoming: SQLi on /api/products. Patch it.
Blue Team: Root cause: user input pasted into SQL. Fix: parameterised query.
           [diff]  🔵 Patch ready. Approve?
You:       approve
Blue Team: Applied. @referee please verify.
Referee:   check.py says 🟢 FIXED, search still works. 🔵 Blue +2.
           🏆 Red 1 : Blue 2
```

At the end the Referee writes an **incident report**: what got breached, how, how it was fixed, current status, and lessons for the team.

## The cast

| Agent | Role | Sees the code? | Can change code? |
|---|---|---|---|
| 🔴 **Red Team** | Black box attacker. Only gets the URL and a customer login | ❌ Never | ❌ |
| 🔵 **Blue Team** | Defender. Finds root cause, proposes a diff | ✅ | ✅ only after you approve |
| 🧑‍⚖️ **Referee** | Runs the match, verifies every claim, keeps score | ✅ | ❌ |
| 🧑 **You** | Incident Commander. Final say on every patch | | |

## How Switch is used (and why it can't work without it)

Switch is the whole stage, not a plug-in:
- **One room, three agents, one human.** Switch puts all of them in the same channel with shared history, so Red, Blue and the Referee all read the same timeline of attacks, patches and verdicts. Without a shared room there is no match.
- **Agents hand work to each other by @mention.** The Referee drives turns by mentioning `@red-team` and `@blue-team`. Switch's addressing (`owner-agents`) lets agents talk to each other while keeping strangers out.
- **The human gate lives in chat.** Blue proposes, you type `approve` in the same room. No separate dashboard.
- **Different workspaces per agent.** Through the template, Red gets an empty folder (true black box) while Blue and the Referee work in the project folder.
- **One file sets it all up.** `switch/war-room.template.yaml` creates the three agents and the room in one click via Switch Console. It passes Switch's own template linter with zero warnings.

## The arena: ChaiCart

A tiny shop API (Flask + SQLite) running in Docker, bound to `127.0.0.1` only. It has five planted vulnerabilities, each guarding a flag:

| # | Vulnerability | OWASP Top 10 |
|---|---|---|
| 1 | SQL injection in product search | A03 Injection |
| 2 | Debug endpoint leaking secrets | A05 Security Misconfiguration |
| 3 | IDOR on orders | A01 Broken Access Control |
| 4 | Forgeable auth tokens | A07 Identification and Authentication Failures |
| 5 | Path traversal on invoices | A01 Broken Access Control |

## The referee can't be fooled

`referee/check.py` judges every bug twice:
1. **Attack:** several exploit variants, not just the obvious one. Blocking the word `UNION` still loses to `UnIoN`.
2. **Feature test:** search, login, your own orders, your own invoices, and the real admin page must still work.

| Verdict | Meaning |
|---|---|
| 🔴 VULNERABLE | some variant still leaks the flag |
| 🟢 FIXED | every variant blocked and the feature works |
| 🟠 BROKEN | flag blocked, but the feature died with it |

## Run it yourself

You need: macOS (Apple silicon or Intel) or Linux, Docker, Switch Console, and Claude Code (or Codex / OpenCode).

```bash
git clone <this repo> && cd switch-war-room
./scripts/start.sh                 # ChaiCart on http://127.0.0.1:5050
python3 referee/check.py           # should show 5x 🔴 VULNERABLE
```

Then in **Switch Console**:
1. **Templates > Import template**, pick `switch/war-room.template.yaml`
2. Set **project_dir** to the absolute path of this folder
3. Create. The `war-room` room appears with all three agents
4. In the room, type `start match`

Reset everything before a new match:
```bash
./scripts/reset.sh
```

## Project layout

```
arena/            ChaiCart, the vulnerable target (Docker)
  app/app.py      the code Blue patches
  pristine/       untouched copy, used by reset
referee/
  check.py        exploit + feature checks, the source of truth
  scoreboard.py   score and match log
  RULES.md        rules of the match
scripts/          start, stop, reset
switch/
  war-room.template.yaml   the Switch template: 3 agents + room
```

## Safety

ChaiCart is insecure on purpose. It is bound to `127.0.0.1`, so only your own machine can reach it. Red's instructions forbid any other host, flooding, or reading source. Never deploy the arena anywhere public.

## What's next
- Swap ChaiCart for your own staging app and run War Room as a weekly drill
- A Slack or Discord room so the whole team can spectate
- More arenas: auth flows, cloud misconfig, LLM prompt injection

---
Made by [Barnavo Dey](https://github.com/barnavo05) · #HowISwitch
