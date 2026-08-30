from typing import Optional
from auction_sim.team_evaluator.constants import OFFENSIVE_ROLE, DEFENSIVE_ROLE, LEFT_DEFENSE
from auction_sim.core.models import Player

BENCH_DEF_SYNERGY = 1.20
BENCH_OFFENSE_SYNERGY = 1.20

PLAY_OFFENSE_SYNERGY = 1.05

def bench_defense_eval(support_defenders : list[Player]):

    bench_defense_score = sum([player.defense for player in support_defenders])
    bench_defender_roles = [player.role for player in support_defenders]

    left_flag, right_flag = False, False
    for role in bench_defender_roles:
        if role in LEFT_DEFENSE:
            left_flag = True
        else:
            right_flag = True

    bench_defense_synergy = left_flag and right_flag

    if bench_defense_synergy:
        bench_defense_score *= BENCH_DEF_SYNERGY

    return bench_defense_score

def bench_offense_eval(support_raiders : list[Player]):
    bench_offense_score = sum([player.attack for player in support_raiders])

    # bench offense score
    bench_offense_roles = [player.role for player in support_raiders]
    bench_offense_synergy = True
    for role in OFFENSIVE_ROLE:
        if role not in bench_offense_roles:
            bench_offense_synergy = False

    if bench_offense_synergy:
        bench_offense_score *= BENCH_OFFENSE_SYNERGY

    return bench_offense_score

def play_defense_eval(raiders : dict[str, Optional[Player]], defenders : dict[str, Optional[Player]]):
    defense_score = 0
    play_raiders_defense_score, play_defenders_defense_score = 0, 0

    for _, player in defenders.items():
        if player is not None: 
            play_defenders_defense_score += player.defense
    
    for _, player in raiders.items():
        if player is not None:
            play_raiders_defense_score += player.defense

    defense_score = play_raiders_defense_score + play_defenders_defense_score

    return defense_score
        

def play_offense_eval(raiders : dict[str, Optional[Player]], defenders : dict[str, Optional[Player]]):

    offense_score = 0

    raiders_combinations = [
        [[35, 35, 30], 0.5],
        [[40, 40, 20], 0.45],
        [[70, 15, 15], 0.40]
    ]

    play_raiders_attack_score, play_defenders_attack_score = 0, 0

    play_raiders_attack_score_list = [0 if player is None else player.attack for _, player in raiders.items()]
    play_defenders_attack_score_list = [0 if player is None else player.attack for _, player in defenders.items()]

    play_raiders_attack_score_list = sorted(play_raiders_attack_score_list, reverse=True)
    play_defenders_attack_score_list = sorted(play_defenders_attack_score_list, reverse=True)

    play_raiders_role_list = [player.role for _, player in raiders.items() ]


    for ls in raiders_combinations:
        distr, wts = ls
        tmp = 0
        for i in range(3):
            contr, attack_score = distr[i], play_raiders_attack_score_list[i]
            tmp += attack_score * (1 + ( wts * contr / 100) )

        play_raiders_attack_score = max(play_raiders_attack_score, tmp)


    play_offense_synergy = True
    for role in OFFENSIVE_ROLE:
        if role not in play_raiders_role_list:
            play_offense_synergy = False

    if play_offense_synergy:
        play_raiders_attack_score *= PLAY_OFFENSE_SYNERGY


    # defenders offense score
    play_defenders_attack_score = sum(play_defenders_attack_score_list)

    offense_score = play_defenders_attack_score + play_raiders_attack_score
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

    team_score += (
        bench_defense_eval(support_defenders=support_defenders) +
        bench_offense_eval(support_raiders=support_raiders)
    )

    return team_score

    
    # bench_offense_score = sum([player.attack for player in support_defenders])
    # bench_defense_score = sum([player.defense for player in support_defenders])

    # # bench offense score
    # bench_offense_roles = [player.role for player in support_raiders]
    # bench_offense_synergy = True
    # for role in OFFENSIVE_ROLE:
    #     if role not in bench_offense_roles:
    #         bench_offense_synergy = False

    # if bench_offense_synergy:
    #     bench_offense_score *= BENCH_OFFENSE_SYNERGY


    # # bench defense score
    # bench_defender_roles = [player.role for player in support_defenders]
    # bench_defense_score = sum([player.defense for player in support_defenders])

    # left_flag, right_flag = False, False
    # for role in bench_defender_roles:
    #     if role in LEFT_DEFENSE:
    #         left_flag = True
    #     else:
    #         right_flag = True

    # bench_defense_synergy = left_flag and right_flag

    # if bench_defense_synergy:
    #     bench_defense_score *= BENCH_DEF_SYNERGY

    # team_score += (bench_defense_score + bench_offense_score)

    # # play  offense score
    # raiders_combinations = [
    #     [[35, 35, 30], 0.5],
    #     [[40, 40, 20], 0.45],
    #     [[70, 15, 15], 0.40]
    # ]

    # play_raiders_attack_score, play_raiders_defense_score = 0, 0
    # play_raiders_attack_score_list = [getattr(player, 'attack', 0) for _, player in raiders.items()]
    # play_raiders_attack_score_list = sorted(play_raiders_attack_score_list, reverse=True)
    # play_raiders_role_list = [player.role for _, player in raiders.items() ]

    # play_raiders_defense_score_list = [getattr(player, 'attack', 0) for _, player in raiders.items()]
    # play_raiders_defense_score = sum(play_raiders_defense_score_list)

    # for ls in raiders_combinations:
    #     distr, wts = ls
    #     tmp = 0
    #     for i in range(3):
    #         contr, attack_score = distr[i], play_raiders_attack_score_list[i]
    #         tmp += attack_score * (1 + ( wts * contr / 100) )

    #     play_raiders_attack_score = max(play_raiders_attack_score, tmp)


    # play_offense_synergy = True
    # for role in OFFENSIVE_ROLE:
    #     if role not in play_raiders_role_list:
    #         play_offense_synergy = False

    # if play_offense_synergy:
    #     play_offense_score *= PLAY_OFFENSE_SYNERGY

    # play_offense_score += play_raiders_attack_score
    # play_defense_score += play_raiders_defense_score


    # # defenders contribution
    # play_defenders_attack_score, play_defenders_defense_score = 0, 0

    # for _, player in defenders.items():
    #     if player is not None:
    #         play_defenders_attack_score += player.attack
    #         play_defenders_defense_score += player.defense
    

    # play_offense_score += play_defenders_attack_score
    # play_defense_score += play_defenders_defense_score
    # team_score += (play_defense_score + play_offense_score)

    # return team_score