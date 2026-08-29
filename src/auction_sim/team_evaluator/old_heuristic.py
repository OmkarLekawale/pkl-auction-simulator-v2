from .constants import DEFENSIVE_ROLE, LEFT_DEFENSE
import heapq

def flip_side(role):
    if role == "LC":
        return "RC"
    if role == "RC":
        return "LC"
    if role == "LCov":
        return "RCov"
    if role == "RCov":
        return "LCov"
    return role

def heuristic_team_score(team, ALPHA=0.8, ALPHA_DEF=0.4):  # teams = list[dict]
    
    raiders = sorted(
        [p for p in team.players if p["role"] in ("LR", "RR")],
        key=lambda p: p["attack"],
        reverse=True
    )

    team_attack = 0.0 
    for i, p in enumerate(raiders):
        team_attack += (ALPHA ** i) * (ALPHA if  i>= 3 else 1) * p["attack"]

    top3_roles = {p["role"] for p in raiders[:3]}
    # top3_sum = sum([p["attack"] for p in raiders[:3]])
    if "LR" in top3_roles and "RR" in top3_roles:
        team_attack *= 1.1

 
    team_def = 0.0
    for p in team.players:
        if p['role'] not in DEFENSIVE_ROLE:
            team_def += ALPHA_DEF * p["defense"]
 
    defenders = [
        (idx, p) for idx, p in enumerate(team.players)
        if p["role"] not in ("LR", "RR")
    ]

    # heap entry:
    # (-value, def_score, role, stage, player_id)
    heap = []

    for pid, p in defenders:
        heapq.heappush(
            heap,
            (-1.1 * p["defense"], p["defense"], p["role"], 0, pid)
        )

    role_filled = {r: False for r in ["LC", "LCov", "RC", "RCov"]}
    used_player = set()  

    while heap:
        neg_val, def_score, role, stage, pid = heapq.heappop(heap)

        # already accounted for
        if pid in used_player:
            continue

        val = -neg_val

 
        if role in role_filled and not role_filled[role]:
            team_def += val
            role_filled[role] = True
            used_player.add(pid)
            continue

        # stage 0 -> try flipped side at 0.75
        if stage == 0:
            heapq.heappush(
                heap,
                (-0.75 * def_score, def_score, flip_side(role), 1, pid)
            )
            continue

        # stage 1 -> try BOTH generic opposite-side slots at 0.5
        if stage == 1:
            if role in LEFT_DEFENSE:
                candidates = ["RC", "RCov"]
            else:
                candidates = ["LC", "LCov"]

            for r in candidates:
                heapq.heappush(
                    heap,
                    (-0.5 * def_score, def_score, r, 2, pid)
                )
            continue

        # stage 2 -> terminal fallback (ONCE PER PLAYER)
        if stage == 2:
            team_def += 0.4 * def_score
            used_player.add(pid)
            continue


    return team_attack + team_def