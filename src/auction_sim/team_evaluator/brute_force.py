# # Need some work!

# import constants as const
# from itertools import combinations, permutations
# import copy

# base_atk = -30
# base_def = -30
# base_player = {'attack': base_atk, 'defense': base_def, 'role':'no_role', 'name':'dummy'}

# def defense_slot_weight_play7(slot, role):
#     if role == slot:
#         return 1.1
#     if slot in left:
#         if role in left: return 0.75
#         if role in right: return 0.50
#         return 0.2
#     else:
#         if role in right: return 0.75
#         if role in left: return 0.50
#         return 0.2


# def defense_slot_weight_sub(slot, role):

#     if slot == 'left':
#         if role in left: return 1.1
#         if role in right: return 0.50
#         return 0.2
#     else:
#         if role in right: return 1.1
#         if role in left: return 0.50
#         return 0.2


# class team_eval:
#     def __init__(self):  
        
#         self.r7_cache = {} 
#         self.d7_cache = {}
#         self.sub_d_cache = {}
#         self.sub_r_cache = {}
#         self.players = [base_player.copy() for _ in range(const.MAX_TEAM_SIZE)]
 
#         self.history = []
#         self.best_team = {}
#         self.build_all_caches()
        
#     def _save_state(self):
#         return {
#             "r7_cache": copy.deepcopy(self.r7_cache),
#             "d7_cache": copy.deepcopy(self.d7_cache),
#             "sub_d_cache": copy.deepcopy(self.sub_d_cache),
#             "sub_r_cache": copy.deepcopy(self.sub_r_cache),
#             "players": copy.deepcopy(self.players),
#             "team_eval": self.team_eval,
#             "best_team": copy.deepcopy(self.best_team),
#         }

#     def _restore_state(self, state):
#         self.r7_cache = state["r7_cache"]
#         self.d7_cache = state["d7_cache"]
#         self.sub_d_cache = state["sub_d_cache"]
#         self.sub_r_cache = state["sub_r_cache"]
#         self.players = state["players"]
#         self.team_eval = state["team_eval"]
#         self.best_team = state["best_team"]

    
#     def build_all_caches(self): 
#         n = const.MAX_TEAM_SIZE

#         # play7 raider cache (3-combinations)
#         play_3_atk = sum([(const.ALPHA ** i) * base_atk for i in range(3)])
#         play_3_def = 2 * base_def * const.ALPHA_DEF # only taking in position (left in, right in) not the center 
#         for comb in combinations(range(n), 3):
#             self.r7_cache[frozenset(comb)] = {"attack": play_3_atk, "defense": play_3_def, "order": comb}
    
#         # play7 defender cache (4-combinations)
#         play_4_atk = base_atk * (const.ALPHA ** 3) # taking only 1 allrounder
#         play_4_def = 4 * base_def * 2 # * 4 for four players, * 2 for missing all positions
#         for comb in combinations(range(n), 4):
#             self.d7_cache[frozenset(comb)] = {"defense": play_4_def, "raid_attack": play_4_atk, "assignment": comb}
    
#         # sub defenders (2-combinations)
#         sub_2_def = const.BETA * 2 * base_def * 2 # *2 for 2 two players * 2 for missing all positions
#         for comb in combinations(range(n), 2):
#             self.sub_d_cache[frozenset(comb)] = {"defense": sub_2_def, "assignment": comb}

#         # sub raiders (3-combinations)
#         sub_3_atk = const.BETA * 3 * base_atk 
#         for comb in combinations(range(n), 3): 
#             self.sub_r_cache[frozenset(comb)] = {"attack": sub_3_atk, "order": comb}

        
#         self.team_eval = (sub_2_def + sub_3_atk + (play_4_atk + play_4_def) + (play_3_atk + play_3_def))


#     def update_play7_raider_cache(self, new_idx):
#         # all 3-combinations that include new_idx: choose 2 older indices
#         n = len(self.players)
#         for i, j in combinations([x for x in range(n) if x != new_idx], 2):
#             comb = (i, j, new_idx)
#             ordered = sorted(comb, key=lambda x: self.players[x]['attack'], reverse=True)
#             atk = sum((const.ALPHA ** k) * self.players[ordered[k]]['attack'] for k in range(3))
#             roles = {self.players[x]['role'] for x in comb}
#             if 'LR' in roles and 'RR' in roles:
#                 atk *= const.SYNERGY_MULT
#             ordered2 = sorted(comb, key=lambda i: self.players[i]['defense'], reverse=True)
#             rdef =  const.ALPHA_DEF * sum(self.players[ordered2[i]]['defense'] for i in range(2))
#             self.r7_cache[frozenset(comb)] = {"attack": atk, "defense": rdef, "order": ordered}
    


#     def update_play7_defender_cache(self, new_idx):
#         n = len(self.players)
#         # all 4-combinations including new_idx: choose 3 older indices
#         for comb3 in combinations([x for x in range(n) if x != new_idx], 3):
#             comb = (*comb3, new_idx)
#             ordered_atk = sorted(comb, key=lambda i: self.players[i]['attack'], reverse=True)
#             raid_atk = (const.ALPHA ** 3) * self.players[ordered_atk[0]]['attack'] # only one all rounder
    
#             best = -1e18
#             best_assign = None
#             for perm in permutations(comb):
#                 s = 0.0
#                 assign = {}
#                 roles = []
#                 for slot, idx in zip(const.PLAY_DEF_SLOTS, perm):
#                     s += wts.defense_slot_weight_play7(slot, self.players[idx]['role']) * self.players[idx]['defense']
#                     assign[slot] = self.players[idx]['name']
#                     roles.append(self.players[idx]['role'])
                
#                 for slot in const.PLAY_DEF_SLOTS:
#                     if slot not in roles:
#                         s += base_def
#                 if s > best:
#                     best = s
#                     best_assign = assign
    
#             self.d7_cache[frozenset(comb)] = {"defense": best, "raid_attack": raid_atk, "assignment": best_assign}
    




#     def update_sub_defender_cache(self, new_idx):
#         n = len(self.players)
#         # all 2-combinations including new_idx: pair new_idx with each older index
#         for i in [x for x in range(n) if x != new_idx]:
#             comb = (i, new_idx)
#             best = -1e18
#             best_assign = None
#             for p1, p2 in permutations(comb):
#                 r1, r2 = self.players[p1]['role'], self.players[p2]['role']
#                 C3 = 1.1 if ((r1 in {'RC', 'RCov'} and r2 in {'LC', 'LCov'}) or
#                              (r2 in {'RC', 'RCov'} and r1 in {'LC', 'LCov'})) else const.ALPHA
#                 val = C3 * const.BETA * (
#                     self.players[p1]['defense'] * wts.defense_slot_weight_sub('left', r1) +
#                     self.players[p2]['defense'] * wts.defense_slot_weight_sub('right', r2)
#                 )

#                 # if (r1 in {'RC', 'RCov'} and r2 in {'RC', 'RCov'}) or (r1 in {'LC', 'LCov'} and r2 in {'LC', 'LCov'}):
#                 #     val -= base_def * const.BETA
                
#                 if r1 not in const.defensive_role:
#                     val += base_def * const.BETA
#                 if r2 not in const.defensive_role:
#                     val += base_def * const.BETA

#                 if val > best:
#                     best = val
#                     best_assign = {'SubD1': self.players[p1]['name'], 'SubD2': self.players[p2]['name']}
#             self.sub_d_cache[frozenset(comb)] = {"defense": best, "assignment": best_assign}
    


#     def update_sub_raider_cache(self, new_idx):
#         n = len(self.players)
#         # all 3-combinations including new_idx: choose 2 older indices
#         for i, j in combinations([x for x in range(n) if x != new_idx], 2):
#             comb = (i, j, new_idx)
#             best = -1e18
#             best_order = None
            
#             for perm in permutations(comb):
#                 r1, r2, r3 = perm
#                 role1 = self.players[r1]['role']
#                 role2 = self.players[r2]['role']
            
#                 C2 = 1.1 if (
#                     (role1 == 'LR' and role2 == 'RR') or
#                     (role1 == 'RR' and role2 == 'LR')
#                 ) else const.ALPHA
            
#                 val = const.BETA * C2 * (
#                     self.players[r1]['attack'] +
#                     self.players[r2]['attack'] +
#                     const.ALPHA * self.players[r3]['attack']
#                 )
            
#                 if val > best:
#                     best = val
#                     best_order = perm
            
#             self.sub_r_cache[frozenset(comb)] = {
#                 "attack": best,
#                 "order": best_order,
#             }
    

#     # Compute exact evaluations using caches
#     def compute_best_score(self):
#         n = len(self.players)
#         best_score = -1e18
#         best_team = None
    
#         # iterate over all raider triples (3)
#         for raiders in combinations(range(n), 3):
#             r = self.r7_cache[frozenset(raiders)]
#             rem9 = set(range(n)) - set(raiders)
    
#             # choose defenders (4)
#             for defenders in combinations(rem9, 4):
#                 d = self.d7_cache[frozenset(defenders)]
#                 rem5 = rem9 - set(defenders)
    
#                 # sub defenders (2) and sub raiders (3) are complementary
#                 for sub_def in combinations(rem5, 2):
#                     sd = self.sub_d_cache[frozenset(sub_def)]
#                     sub_off = tuple(rem5 - set(sub_def))  # remaining 3 indices
#                     sr = self.sub_r_cache[frozenset(sub_off)]
    
#                     score = (
#                         r["attack"] + r["defense"] +
#                         d["defense"] + d["raid_attack"] +
#                         sd["defense"] + sr["attack"]
#                     )
    
#                     if score > best_score:
#                         best_score = score
#                         best_team = {
#                             "play7_raiders": [self.players[i]['name'] for i in r["order"]],
#                             "play7_defenders": d["assignment"],
#                             "sub_defenders": sd["assignment"],
#                             "sub_raiders": [self.players[i]['name'] for i in sr['order']]
#                         }
    
#         return best_score, best_team




#     def add_player(self, team, player, price=0):
 
#         self.history.append(self._save_state())

#         new_idx = team.total_buys

#         self.players[new_idx] = {
#             'name': player.name,
#             'role': player.role,
#             'attack': player.attack,
#             'defense': player.defense,
#             'price': price
#         }

#         self.update_play7_raider_cache(new_idx)
#         self.update_play7_defender_cache(new_idx)
#         self.update_sub_defender_cache(new_idx)
#         self.update_sub_raider_cache(new_idx)

#         prv = self.team_eval

#         self.team_eval, self.best_team = self.compute_best_score()

#         delta = self.team_eval - prv


#         return delta

#     def revert(self):
#         if not self.history:
#             return  # nothing to undo

#         state = self.history.pop()
#         self._restore_state(state)

     
# if __name__ == '__main__':
#     import pandas as pd
#     import constants as const

 
#     class Player:
#         def __init__(self, name, role, attack, defense):
#             self.name = name
#             self.role = role
#             self.attack = attack
#             self.defense = defense


#     class DummyTeam:
#         """Only tracks number of players bought."""
#         def __init__(self):
#             self.total_buys = 0


 
#     def get_best_12(players):
#         if len(players) <= 12:
#             return players

#         players.sort(
#             key=lambda x: x.attack + 1.1 * x.defense,
#             reverse=True
#         )
#         return players[:12]


 
#     def best_12_player_team(players):

#         players = get_best_12(players)

#         t_eval = team_eval()
#         dummy_team = DummyTeam()

#         total_delta = 0

#         for p in players:
#             total_delta += t_eval.add_player(dummy_team, p)
#             dummy_team.total_buys += 1

#         final_score, best_team = t_eval.compute_best_score()

#         return total_delta, best_team


 
#     def evaluate_teams_from_csv(csv_path):
#         df = pd.read_csv(csv_path)
#         results = []

#         for team_name, tdf in df.groupby("team_name"):
#             print(f"\nEvaluating: {team_name}")

#             players = [
#                 Player(
#                     row["player_name"],
#                     const.ROLE_MAP[row["Role"]],
#                     row["Attack score"],
#                     row["Defense score"]
#                 )
#                 for _, row in tdf.iterrows()
#             ]

#             score, best_team = best_12_player_team(players)

#             results.append({
#                 "team": team_name,
#                 "score": round(score, 2),
#                 "assignment": best_team
#             })


#         return sorted(results, key=lambda x: x["score"], reverse=True)


 
#     results = evaluate_teams_from_csv(
#         r"E:\ML\Projects\PKL Auction Sim\Multi Agent RL\Data.csv"
#     )

#     for r in results:
#         print("=" * 120)
#         print(f"Team: {r['team']}")
#         print(f"Score: {r['score']}")

#         a = r["assignment"]

#         print("\nPLAY7 Raiders:", a["play7_raiders"])
#         print("PLAY7 Defenders:", a["play7_defenders"])
#         print("Sub Defenders:", a["sub_defenders"])
#         print("Sub Raiders:", a["sub_raiders"])
