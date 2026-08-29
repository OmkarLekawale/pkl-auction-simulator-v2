# Auction constants
MAX_PURSE = 500
BID_INCREMENT = 1
MAX_FBM = 4
MAX_TEAM_SIZE = 12

FBM_MULT_10 = 1.10
FBM_MULT_20 = 1.20

ALPHA = 0.8
ALPHA_DEF = 0.3
BETA = 0.25
SYNERGY_MULT = 1.1

ROLE_LIST = ["LR", "RR", "LC", "LCov", "RC", "RCov"]
DEFENSIVE_ROLE = ['RC', 'LC', 'LCov', 'RCov']
DEF_SLOTS = ['LC', 'LCov', 'RC', 'RCov']
OFFENSIVE_ROLE = ['LR', 'RR']

LEFT_DEFENSE = ['LC', 'LCov']
RIGHT_DEFENSE = ['RC', 'RCov']

ROLE_TO_IDX = {r: i for i, r in enumerate(ROLE_LIST)}


NUM_ACTIONS = 7  # PASS, BID, FBM_USE, FBM_INCR_10, FBM_INCR_20, FBM_TAKE, PAY
ACTION_LIST = ['ACTION_PASS', 'ACTION_BID', 'ACTION_FBM_USE', 'ACTION_FBM_INCR_10', 'ACTION_FBM_INCR_20', 'ACTION_FBM_TAKE', 'ACTION_PAY']
ACTION_PASS = 0
ACTION_BID = 1
ACTION_FBM_USE = 2
ACTION_FBM_INCR_10 = 3
ACTION_FBM_INCR_20 = 4
ACTION_FBM_TAKE = 5
ACTION_PAY = 6

PHASE_NORMAL = "normal"
PHASE_FBM_ORIG = "fbm_orig"
PHASE_FBM_WINNER = "fbm_winner"
PHASE_FBM_REPLY = "fbm_reply"
PHASE_PAY = "pay_current_price"
PHASE_DONE = "done"
PHASE_LIST = [ "normal", "fbm_orig", "fbm_winner", "fbm_reply", "pay_current_price", "done"]

ROLE_MAP = {
    "Left Raider": "LR",
    "Right Raider": "RR",
    "Left Corner": "LC",
    "Left Cover": "LCov",
    "Right Corner": "RC",
    "Right Cover": "RCov",
}