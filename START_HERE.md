# START HERE (Barnavo's run guide)

Everything below is copy paste. Do it in order. About 20 minutes the first time.

---

## Part 1: Put the project on your Mac (2 min)

1. Unzip `switch-war-room.zip` into your home folder, so you get `/Users/barnavodey/switch-war-room`
2. Open Terminal and run:
```bash
cd ~/switch-war-room
chmod +x scripts/*.sh
```

## Part 2: Start the arena (3 min)

Docker must be running (whale icon in the menu bar). If not: `open -a Docker`, wait 30 seconds.

```bash
./scripts/start.sh
```
You should see: `ChaiCart is live at http://127.0.0.1:5050`

Now check the Referee sees all 5 bugs:
```bash
python3 referee/check.py
```
Expected: five rows, all 🔴 VULNERABLE. If yes, the arena is perfect.

## Part 3: Create the agents in Switch (5 min)

1. Open **Switch Console**
2. In the left sidebar click **Templates**
3. Click **Import template** and choose `~/switch-war-room/switch/war-room.template.yaml` (or drag the file in)
4. It asks for **project_dir**. Enter exactly:
   `/Users/barnavodey/switch-war-room`
5. Leave the rest as default (provider Claude Code, location this computer, Mattermost)
6. Click **Create**

You should now see 3 new agents (**referee**, **red-team**, **blue-team**) and a room called **war-room**. The kickoff message posts automatically and all three say hello.

## Part 4: First test match (10 min)

In the **war-room** room, type:
```
start match
```
Then just watch. When Blue says "Patch ready. Approve?", read the diff and type:
```
approve
```

If an agent asks for permission to run a command (like curl or python3), allow it. That's Switch's safety mode.

## Before every recording or new match

```bash
cd ~/switch-war-room && ./scripts/reset.sh
```
Puts all 5 bugs back and clears the scoreboard.

---

## If something breaks

| Problem | Fix |
|---|---|
| `start.sh` says ChaiCart did not start | `docker compose -f arena/docker-compose.yml logs` and send me the output |
| check.py says offline | Run `./scripts/start.sh` again |
| Template import shows an error | Screenshot it to me |
| An agent says "name taken" | You already created it once. Delete the old agent in Your Agents, then create again |
| An agent goes silent | @mention it directly in the room, e.g. `@referee continue` |
| Red tries something outside 127.0.0.1 | Type `@red-team stop, only 127.0.0.1:5050` (it shouldn't, its rules forbid it) |

---

# The plan till Saturday

**Deadline: Sat Nov 7, 11:59 PM IST. We submit by Sat 8 PM.**

### Wed (today, evening)
- Parts 1 to 4 above. Goal: one full round works (Red claims, you approve, Blue fixes, Referee scores)
- Send me screenshots of anything weird, I'll tune the agent instructions

### Thu
- Run 2 or 3 full matches. Note anything awkward (agent too chatty, skipped a step)
- I tighten the instructions based on what you see
- Create a **public GitHub repo** `switch-war-room`, push the code
- Keep Wispr Flow on while prompting, for the voice side track

### Fri
- Optional polish: connect **Discord** in Switch Connectors and recreate the room there, so the demo is in Discord (more relatable on social)
- Record the **demo video** (script below). Do 2 or 3 takes, keep the best
- Screenshot the **Wispr Insights scorecard**

### Sat
- Final README with video link and screenshots
- Submit on the hackathon page: repo link, demo video, README
- Post on LinkedIn and X with **#HowISwitch** (keyboard prize)
- Optional: blog post on Hashnode or Medium for the AirPods side track

---

# Demo video script (2.5 to 3 min)

Record your screen with QuickTime (File > New Screen Recording) or Loom. Talk over it casually.

**0:00 to 0:15 Hook**
"Most teams never run a security drill. So I made two AI agents fight over a live app in a chat room, while a third keeps score. I'm the only one who can approve a fix."

**0:15 to 0:35 Setup**
Show the arena running and `check.py` with 5 red rows. Show the template in Switch Console: "One YAML file creates all three agents and the room."

**0:35 to 2:00 The fight (speed up boring parts 2x in editing)**
Type `start match`. Show Red's claim with the flag. Referee verifies and scores. Blue posts the diff. You type `approve`. Referee shows 🟢 FIXED. Show one round where Red tries a bypass, it's the most dramatic moment.

**2:00 to 2:30 The report**
End the match, show the final scoreboard and the incident report. Run `check.py` again: all green.

**2:30 to 2:50 Why Switch**
"Without Switch there's no shared room, no handoffs, no human gate in chat. Switch is the arena."

**2:50 to 3:00 Close**
"Repo link below. #HowISwitch"
