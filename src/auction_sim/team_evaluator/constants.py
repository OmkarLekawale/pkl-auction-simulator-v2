ROLE_LIST = ["LR", "RR", "LC", "LCov", "RC", "RCov"]
DEFENSIVE_ROLE = ['RC', 'LC', 'LCov', 'RCov']
DEF_SLOTS = ['LC', 'LCov', 'RC', 'RCov']
OFFENSIVE_ROLE = ['LR', 'RR']
OFFENSIVE_SLOTS = ['LR', 'RR']

LEFT_DEFENSE = ['LC', 'LCov']
RIGHT_DEFENSE = ['RC', 'RCov']

ROLE_TO_IDX = {r: i for i, r in enumerate(ROLE_LIST)}

# PLAY_7 = {
#     "offense" : ["main_raider", "support_raider_1", "support_raider_2"], 
#     "defense" : ["right_corner", "right_cover", "left_cover", "left_corner"]
# }



PLAY_7 = {
    "offense" : ["main_raider", "support_raider_1", "support_raider_2"], 
    "defense" : ["right_corner", "right_cover", "left_cover", "left_corner"]
}