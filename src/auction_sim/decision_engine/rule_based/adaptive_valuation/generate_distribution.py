# Need to work on this

# from auction_sim.decision_engine.constants import ROLE_LIST, ROLE_CAP, LEFT_DEFENSE, RIGHT_DEFENSE

# from itertools import combinations
# SIDE_DEF_CAP = 3

# distr : list[dict[str, int]] = []


# def _can_add_role_to_target(target, role):
#     if target[role] + 1 > ROLE_CAP[role]:
#         return False

#     if role in LEFT_DEFENSE:
#         if sum(target[r] for r in LEFT_DEFENSE) + 1 > SIDE_DEF_CAP:
#             return False

#     if role in RIGHT_DEFENSE:
#         if sum(target[r] for r in RIGHT_DEFENSE) + 1 > SIDE_DEF_CAP:
#             return False

#     return True


# def _role_tuple_key( counts):
#     return tuple(counts[r] for r in ROLE_LIST)

# def generate_target_distributions( max_team_size=12):

#     targets_by_k = {k: {} for k in range(1, max_team_size + 1)}

#     for k in range(1, 7):
#         for comb in combinations(ROLE_LIST, k):
#             counts = {r: 0 for r in ROLE_LIST}
#             for r in comb:
#                 counts[r] = 1
#             key = _role_tuple_key(counts) # avoids duplicates
#             targets_by_k[k][key] = counts

#     base6 = {r: 1 for r in ROLE_LIST}
#     for add in ['LR', 'RR']:
#         if base6[add] + 1 <= ROLE_CAP[add]:
#             new = base6.copy()
#             new[add] += 1
#             key = _role_tuple_key(new)
#             targets_by_k[7][key] = new

#     for k in range(8, max_team_size + 1):
#         for prev in targets_by_k[k - 1].values():
#             for r in ROLE_LIST:
#                 if _can_add_role_to_target(prev, r):
#                     cand = prev.copy()
#                     cand[r] += 1
#                     key = _role_tuple_key(cand)
#                     targets_by_k[k][key] = cand

#     for k in range(1, max_team_size + 1):
#         targets_by_k[k] = list(targets_by_k[k].values())

#     return targets_by_k

# print(generate_target_distributions(12))