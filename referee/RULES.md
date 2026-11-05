# War Room Rules

## The setup
- **Target:** ChaiCart, a tiny shop API at `http://127.0.0.1:5050`, built vulnerable on purpose. It only listens on your own laptop.
- **5 hidden vulnerabilities**, each guarding a `FLAG{...}`.
- **Red Team** attacks black box. It gets the URL and a normal customer login (`alice` / `alice123`), nothing else.
- **Blue Team** reads the code and patches it.
- **Referee** verifies every claim with `referee/check.py` and keeps score.
- **You** are the Incident Commander. Blue cannot apply a patch until you say approve.

## Scoring
| Move | Points |
|---|---|
| Red captures a flag (verified) | 🔴 +1 |
| Red bypasses a patch Blue said was done | 🔴 +2 |
| Blue ships a fix that check.py marks FIXED | 🔵 +2 |
| Blue ships a patch that breaks the feature (BROKEN) | 🔵 -1 |

## Why Blue cannot cheat
`check.py` fires several attack variants per bug (case tricks, encodings, alternative paths, other accounts). A patch that only blocks one keyword stays VULNERABLE.
It also tests that the shop still works: search, login, your own orders, your own invoices, the real admin page. Deleting a feature shows BROKEN.

## A round
1. Referee hands Red the turn.
2. Red probes, captures one flag, posts a CLAIM with the exact command and proof.
3. Referee verifies with `check.py --vuln <key>`, awards Red, briefs Blue.
4. Blue posts a diff and asks you to approve.
5. You approve. Blue applies it.
6. Referee verifies. FIXED, BROKEN, or Red gets a bypass attempt.

## Ending
All five FIXED, or round 5, or you say "end match". The Referee posts the final scoreboard and an incident report.

## Commands you can type in the room
- `start match`
- `pause` / `resume`
- `approve` (or `reject, <reason>`)
- `end match`
