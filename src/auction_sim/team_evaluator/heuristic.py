from __future__ import annotations
from .constants import ROLE_LIST, OFFENSIVE_ROLE, DEFENSIVE_ROLE, LEFT_DEFENSE, RIGHT_DEFENSE

BENCH_DEF_SYNERGY = 1.20
BENCH_DEF_SYNERGY = 1.20


def eval_team(player_list : list) -> int: # player_list : list[Player]
    team_score = 0
    play_offense_synergy, bench_offense_synergy, bench_defense_synergy = False, False, False
    bench_offense_score, bench_defense_score = 0, 0
    play_offense_score, play_defense_score = 0, 0
    

    support_raiders, support_defenders = [], []
    raiders = {"Raider1":None, "Raider2":None, "Raider3":None}
    defenders = {role : None for role in DEFENSIVE_ROLE} 

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

    
    bench_offense_score = sum([player.attack for player in support_defenders])
    bench_defense_score = sum([player.defense for player in support_defenders])

    # bench offense score
    bench_offense_roles = [player.role for player in support_raiders]
    bench_offense_synergy = True
    for role in OFFENSIVE_ROLE:
        if role not in bench_offense_roles:
            bench_offense_synergy = False

    if bench_offense_synergy:
        bench_offense_score *= BENCH_DEF_SYNERGY


    # bench defense score
    bench_defender_roles = [player.role for player in support_defenders]
    bench_defense_score = sum([player.defense for player in support_defenders])

    left_flag, right_flag = False, False
    for role in bench_defender_roles:
        if role in LEFT_DEFENSE:
            left_flag = True
        else:
            right_flag = True

    bench_defense_synergy = left_flag and right_flag

    if bench_defense_synergy:
        bench_defense_score *= BENCH_DEF_SYNERGY

    team_score += (bench_defense_score + bench_offense_score)

    # play  offense score
    raiders_combinations = [
        [[35, 35, 30], 0.5],
        [[40, 40, 20], 0.45],
        [[70, 15, 15], 0.40]
    ]

    play_raiders_attack_score, play_raiders_defense_score = 0, 0
    play_raiders_attack_score_list = [getattr(player, 'attack', 0) for position, player in raiders.items()]
    play_raiders_attack_score_list = sorted(play_raiders_attack_score_list, reverse=True)

    play_raiders_defense_score_list = [getattr(player, 'attack', 0) for position, player in raiders.items()]
    play_raiders_defense_score = sum(play_raiders_defense_score_list)

    for ls in raiders_combinations:
        distr, wts = ls
        tmp = 0
        for i in len(3):
            contr, attack_score = distr[i], play_raiders_attack_score_list[i]
            tmp += attack_score * (1 + ( wts * contr / 100) )

        play_raiders_attack_score = max(play_raiders_attack_score, tmp)

    play_offense_score += play_raiders_attack_score
    play_defense_score += play_raiders_defense_score


    # defenders contribution
    play_defenders_attack_score, play_defenders_defense_score = 0, 0

    for position, player in defenders:
        if player is not None:
            play_defenders_attack_score += player.attack
            play_defenders_defense_score += player.defense
    

    play_offense_score += play_defenders_attack_score
    play_defense_score += play_defenders_defense_score
    team_score += (play_defense_score + play_offense_score)


    return team_score

    

        




    
    
