from typing import Optional
from auction_sim.team_evaluator.constants import OFFENSIVE_ROLE, DEFENSIVE_ROLE, LEFT_DEFENSE
from auction_sim.core.models import Player

BENCH_DEF_SYNERGY = 1.20
BENCH_OFFENSE_SYNERGY = 1.20

PLAY_OFFENSE_SYNERGY = 1.05

def bench_defense_eval(support_defenders : list[Player]):

    defender_roles = [player.role for player in support_defenders]

    defense_score = sum([player.defense for player in support_defenders])
    

    left_flag, right_flag = False, False
    for role in defender_roles:
        if role in LEFT_DEFENSE:
            left_flag = True
        else:
            right_flag = True

    defense_synergy = left_flag and right_flag

    if defense_synergy:
        defense_score *= BENCH_DEF_SYNERGY

    return defense_score

def bench_offense_eval(support_raiders : list[Player]):

    offense_roles = [player.role for player in support_raiders]

    offense_score = sum([player.attack for player in support_raiders])

    offense_synergy = True
    for role in OFFENSIVE_ROLE:
        if role not in offense_roles:
            offense_synergy = False

    if offense_synergy:
        offense_score *= BENCH_OFFENSE_SYNERGY

    return offense_score

def play_defense_eval(raiders : dict[str, Optional[Player]], defenders : dict[str, Optional[Player]]):
    defense_score = 0
    raiders_defense_score, defenders_defense_score = 0, 0

    for _, player in defenders.items():
        if player is not None: 
            defenders_defense_score += player.defense
    
    for _, player in raiders.items():
        if player is not None:
            raiders_defense_score += player.defense

    defense_score = raiders_defense_score + defenders_defense_score

    return defense_score
        

def play_offense_eval(raiders : dict[str, Optional[Player]], defenders : dict[str, Optional[Player]]):

    offense_score = 0

    raiders_combinations = [
        [[35, 35, 30], 0.5],
        [[40, 40, 20], 0.45],
        [[70, 15, 15], 0.40]
    ]

    raiders_attack_score, defenders_attack_score = 0, 0

    raiders_attack_score_list = [0 if player is None else player.attack for _, player in raiders.items()]
    defenders_attack_score_list = [0 if player is None else player.attack for _, player in defenders.items()]

    raiders_attack_score_list = sorted(raiders_attack_score_list, reverse=True)
    defenders_attack_score_list = sorted(defenders_attack_score_list, reverse=True)

    raiders_role_list = [player.role if player is not None else None for _, player in raiders.items()]

    for ls in raiders_combinations:
        distr, wts = ls
        tmp = 0
        for i in range(3):
            contr, attack_score = distr[i], raiders_attack_score_list[i]
            tmp += attack_score * (1 + ( wts * contr / 100) )

        raiders_attack_score = max(raiders_attack_score, tmp)

    offense_synergy = True
    for role in OFFENSIVE_ROLE:
        if role not in raiders_role_list:
            offense_synergy = False

    if offense_synergy:
        raiders_attack_score *= PLAY_OFFENSE_SYNERGY

    # defenders offense score
    defenders_attack_score = sum(defenders_attack_score_list)

    offense_score = defenders_attack_score + raiders_attack_score
    return offense_score

def eval_team(player_list : list[Player]) -> int: # player_list : list[Player]
    team_score = 0

    support_raiders : list[Player] = []
    support_defenders : list[Player] = []
    
    raiders : dict[str, Optional[Player]] = {"Raider1":None, "Raider2":None, "Raider3":None}
    defenders : dict[str, Optional[Player]] = {role : None for role in DEFENSIVE_ROLE} 

    for player in player_list:
        if player.role in DEFENSIVE_ROLE:
            if defenders[player.role] == None:
                defenders[player.role] = player
            elif len(support_defenders) < 3:
                support_defenders.append(player)
        else:
            if raiders["Raider1"] == None:
                raiders["Raider1"] = player
            elif raiders["Raider2"] == None:
                raiders["Raider2"] = player 
            elif raiders["Raider3"] == None:
                raiders["Raider3"] = player
            elif len(support_raiders) < 3:
                support_raiders.append(player) 

    
    team_score += (     play_defense_eval(raiders=raiders, defenders=defenders) + 
                        play_offense_eval(raiders=raiders, defenders=defenders)
    )

    tmp = team_score
    print(f"playing 7 team score : {tmp}")
    team_score += (
        bench_defense_eval(support_defenders=support_defenders) +
        bench_offense_eval(support_raiders=support_raiders)
    )
    print(f"Bench Strength : {team_score - tmp}")

    return team_score

