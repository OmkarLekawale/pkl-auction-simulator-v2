# INPUTS
Team instance, player list, approach=simple

# Evaluators
1. brute force
2. heurestic
3. old heuristic


# Heuristic
Raiders
3 Types of raiders combination
- 35, 35, 30 -> 0.5 -> 1.175, 1.175, 1.150 -> 0.5 * 0.35, 0.5 * 0.35, 0.5 * 0.30
- 70, 15, 15 -> 0.4 -> 1.280, 1.06, 1.06
- 40, 40, 20 -> 0.45 -> 1.18, 1.18, 1.09

All raiders do not have the same contribution
Team strength cannot be equal to sum of 3 raiders


Take the best 2 raiders, third raider gets 10% extra points if he brings synergy (left - right combination).
If the raiders units has synergy total attact score increases by 5%

How to select the players?
If the players are in order of how good they are? Then for each role we fill the player who has come first for that role!
Especially for defense!

Do we really need to choose top 3?
First three raiders will be playing 7!

First defender for each player will play that position

raider 1
raider 2
raider 2

defense = {}

support raider = [] -> max 3 raiders
support defense = [] -> max 3 defenders
