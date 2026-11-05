#!/usr/bin/env python3
"""
War Room scoreboard. The Referee agent is the only one who should run this.

Scoring rules (also in referee/RULES.md):
  Red  +1  captures a flag (Referee verified it with check.py)
  Red  +2  bypasses a patch Blue said was done
  Blue +2  a fix that check.py marks FIXED
  Blue -1  a patch that breaks the feature (check.py says BROKEN)

Usage:
  python3 referee/scoreboard.py show
  python3 referee/scoreboard.py award red 1 "captured SQLi flag"
  python3 referee/scoreboard.py award blue 2 "fixed SQLi with parameterised query"
  python3 referee/scoreboard.py round            # start the next round
  python3 referee/scoreboard.py reset
"""

import json
import os
import sys
from datetime import datetime

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scoreboard.json")


def load():
    if not os.path.exists(PATH):
        return {"round": 0, "red": 0, "blue": 0, "log": []}
    with open(PATH, encoding="utf-8") as fh:
        return json.load(fh)


def save(board):
    with open(PATH, "w", encoding="utf-8") as fh:
        json.dump(board, fh, indent=2)


def show(board):
    red, blue = board["red"], board["blue"]
    if red > blue:
        lead = "🔴 Red leads"
    elif blue > red:
        lead = "🔵 Blue leads"
    else:
        lead = "⚖️ Level"
    out = [
        f"🏆 **WAR ROOM SCOREBOARD** (round {board['round']})",
        "",
        f"🔴 Red  **{red}**   vs   🔵 Blue **{blue}**   ({lead})",
    ]
    if board["log"]:
        out += ["", "Last moves:"]
        for e in board["log"][-5:]:
            sign = "+" if e["points"] >= 0 else ""
            team = "🔴 Red" if e["team"] == "red" else "🔵 Blue"
            out.append(f"- R{e['round']} {team} {sign}{e['points']}: {e['reason']}")
    return "\n".join(out)


def main(argv):
    if len(argv) < 2 or argv[1] not in {"show", "award", "round", "reset"}:
        print(__doc__)
        return 1
    cmd = argv[1]
    board = load()
    if cmd == "reset":
        board = {"round": 0, "red": 0, "blue": 0, "log": []}
        save(board)
        print("Scoreboard reset.")
        return 0
    if cmd == "round":
        board["round"] += 1
        save(board)
        print(f"⚔️ Round {board['round']} begins.")
        return 0
    if cmd == "award":
        if len(argv) < 5 or argv[2] not in {"red", "blue"}:
            print('Usage: award red|blue <points> "<reason>"')
            return 1
        team, points, reason = argv[2], int(argv[3]), " ".join(argv[4:])
        board[team] += points
        board["log"].append({
            "round": board["round"], "team": team, "points": points,
            "reason": reason, "at": datetime.now().strftime("%H:%M:%S"),
        })
        save(board)
    print(show(board))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
