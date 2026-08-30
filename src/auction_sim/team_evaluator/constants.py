ROLE_LIST = ["LR", "RR", "LC", "LCov", "RC", "RCov"]
DEFENSIVE_ROLE = ['RC', 'LC', 'LCov', 'RCov']
DEF_SLOTS = ['LC', 'LCov', 'RC', 'RCov']
OFFENSIVE_ROLE = ['LR', 'RR']
OFFENSIVE_SLOTS = ['LR', 'RR']

LEFT_DEFENSE = ['LC', 'LCov']
RIGHT_DEFENSE = ['RC', 'RCov']

ROLE_TO_IDX = {r: i for i, r in enumerate(ROLE_LIST)}
