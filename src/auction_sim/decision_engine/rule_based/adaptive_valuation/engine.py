from itertools import combinations
import math
import random
from dataclasses import dataclass, field
import numpy as np

from auction_sim.decision_engine.constants import ROLE_LIST, LEFT_DEFENSE, RIGHT_DEFENSE, MAX_TEAM_SIZE
from auction_sim.decision_engine.constants import PHASE_DONE, PHASE_FBM_ORIG, PHASE_FBM_REPLY, PHASE_FBM_WINNER, PHASE_NORMAL, PHASE_PAY
from auction_sim.decision_engine.constants import ACTION_BID, ACTION_FBM_INCR_10, ACTION_FBM_INCR_20, ACTION_FBM_TAKE, ACTION_FBM_USE, ACTION_PASS, ACTION_PAY, ACTION_LIST
from auction_sim.core.models import Player, Team, PlayerAuction
from auction_sim.decision_engine.rule_based.adaptive_valuation.target_player_role_distribution import distribution

ROLE_CAP = {r: 3 for r in ROLE_LIST}
SIDE_DEF_CAP = 3

MIN_REQ = 0.1
GAMMA = 1.0

MAX_ROLE = {
    "LR": 3,
    "RR": 3,
    "LC": 2,
    "LCov": 2,
    "RC": 2,
    "RCov": 2
}

# 0.8 <= k2 <= 1.0
# 0.8 <= k1 <= 1.0

K1 = [0.8, 1.0]
K2 = [0.8, 1.0]

@dataclass(kw_only=True)
class HeuresticPolicy:
    user : Team
    Teams : list[Team]
    
    Players : list[Player]   # total players
    players_left_by_role : dict[str, int] # this is not a deep copy

    player_auction : PlayerAuction | None = field(default=None, init=False)
    current_player : Player | None = field(default=None, init=False)
    fair_price : None | int = field(default=None, init=False)
    k1 : float = field(init=False)
    k2 : float = field(init=False)

    def __post_init__(self):
        self.k1, self.k2 = random.uniform(K1[0], K1[1]), random.uniform(K2[0], K2[1])

    def predict(self, *args, _obs : None | np.ndarray = None, action_masks : list[bool] = None, deterministic=False, player_auction : PlayerAuction, **kwargs) -> tuple[int, None]:

        if self.current_player is not self.player_auction.player:
            self.current_player = self.player_auction.player
            self.fair_price = self.get_fair_price()

        phase = self.player_auction.phase
        current_price = self.player_auction.current_price

        if phase == PHASE_NORMAL:
            if self.fair_price >= 1 + current_price and action_masks[ACTION_BID]:
                return ACTION_BID, None
             
        elif phase == PHASE_FBM_ORIG:
            if self.fair_price >= current_price and action_masks[ACTION_FBM_USE]:
                return ACTION_FBM_USE, None
             
        elif phase == PHASE_FBM_WINNER:
            if round(1.2 * current_price) <= self.fair_price and action_masks[ACTION_FBM_INCR_20]:
                return ACTION_FBM_INCR_20, None
            elif round(1.1 * current_price) <= self.fair_price and action_masks[ACTION_FBM_INCR_10]:
                return ACTION_FBM_INCR_10, None
             
        elif phase == PHASE_FBM_REPLY: # This expects that the player_auction.current_prices has the updated price
            if current_price <= self.fair_price and action_masks[ACTION_FBM_TAKE]:
                return ACTION_FBM_TAKE, None
            
        elif phase == PHASE_PAY:
            if action_masks[ACTION_PAY]:
                return ACTION_PAY, None
            else:
                raise ValueError("Action pay is not available?")
        
        return ACTION_PASS,None



    # score = player_req × role_pressure × player_pressure * pos_discount
    # fair_price = (base_price × spending_ratio) × (0.6 + 0.6 × score)
    def get_fair_price(self):
        ALPHA = 0.2
        # score = pR * rP * pP * pD
        # fP = eP * sR * 0.6 * (score + 1) 
        # fP = min(fP, mP)

        total_players = len(self.Players)
        auction_progress = self.current_player.index / total_players
        role_count = self.user.role_count
        player_role = self.current_player.role
        player_demand = self.player_demand()
        player_demand_by_role = self.role_demand()
        expected_price = self.expected_remaining_purse(self.k1, self.k2, self.user.total_buys / 12) - self.expected_remaining_purse(self.k1, self.k2, (self.user.total_buys + 1) / 12)
        max_price = self.max_price()
        spending_rate = self.spending_rate(auction_progress)
        remaing_supply = total_players - self.current_player.index
        

        pos_discount = self.position_discount(auction_progress) # pD
        player_pressure = min(2, player_demand / remaing_supply) # pP

        role_pressure = player_demand_by_role[player_role] / self.players_left_by_role[player_role] # rP -> tmp
        future_role_factor = 1 + self.future_role_need() / self.players_left_by_role[player_role] # fRF
        role_pressure = min(2.5, ALPHA * role_pressure + (1 - ALPHA) * future_role_factor) # rP

        player_requirement = self.role_requirement_by_target_method(role_count, distribution)[player_role] # pR

        score = player_requirement * role_pressure * player_pressure * pos_discount
        fair_price = expected_price * spending_rate * 0.6 * (1 + score)

        fair_price = min(fair_price, max_price)

        return fair_price

    def get_diff(self, target, role_count):
        delta = 0
        pos_wt = 3
        neg_wt = 2
        for role in ROLE_LIST:
            d = target[role] - role_count[role]
            if d >= 0:  
                delta += pos_wt * (1 + d) * d // 2 # pos_wt, 2 * pos_wt, 3 * pos_wt
            else:
                d = abs(d) # neg_wt, 2 * neg_wt, 3 * neg_wt
                delta += d * (d + 1) * neg_wt // 2
        return delta



    def role_requirement_by_target_method(self, role_count, targets_by_k):

        k = sum(role_count.values())
        if k >= 12:
            return {r: MIN_REQ for r in ROLE_LIST}

        targets_k = targets_by_k[k] if k >= 1 else []
        if not targets_k:
            delta_before = 10 ** 9
        else:
            delta_before = self.compute_min_delta_to_targets(role_count, targets_k)

        role_deltas = {}

        for role in ROLE_LIST:
            role_count2 = role_count.copy()
            role_count2[role] = role_count2.get(role, 0) + 1

            delta_after = self.compute_min_delta_to_targets(
                role_count2,
                targets_by_k[k + 1]
            )

            role_deltas[role] = delta_after - delta_before

        values = [-role_deltas[r] for r in ROLE_LIST]
        max_val = max(values)

        exp_vals = []
        for v in values:
            exp_vals.append(math.exp(v - max_val))

        sum_exp = sum(exp_vals)

        softmax_vals = []
        for v in exp_vals:
            softmax_vals.append(v / sum_exp)

        max_soft = max(softmax_vals)

        req = {}

        tau = 5
        for i, role in enumerate(ROLE_LIST):
            d = max_soft - softmax_vals[i]
            req_val = MIN_REQ + (1.0 - MIN_REQ) * math.exp(-tau * d)
            req[role] = req_val

        return req

    def expected_remaining_purse(self, k1, k2, x):
        c = 5 * (k1 ** k2)
        return (-c + (5 + c)/(1 + (x/k1)**k2)) * 100
    
    
    def role_demand(self):

        demand = {role: 0 for role in ROLE_LIST}

        for team in self.Teams:

            rc = team.role_count 

            left_def = rc["LC"] + rc["LCov"]
            right_def = rc["RC"] + rc["RCov"]

            for role in ROLE_LIST:

                deficit = MAX_ROLE[role] - rc[role]

                if role in LEFT_DEFENSE:
                    deficit = min(deficit, 3 - left_def)

                if role in RIGHT_DEFENSE:
                    deficit = min(deficit, 3 - right_def) 
                
                deficit = max(deficit, 0)
                
                if rc[role] == 0:
                    deficit = max(1, deficit)

                demand[role] += deficit

        return demand
    
    def player_demand(self):
        demand = 0
        for team in self.Teams:
            rc = team.role_count 
            
            demand += 12 - sum(rc.values())
        
        return demand
    

    def position_discount(self, x):
        C = 0.7
        return C ** x


    def max_price(self):
        # K1 = [0.3, 0.7]
        # K2 = [0.7, 0.9]

        min_price = 10 ** 9
        for k1 in K1:
            for k2 in K2:
                cand = self.expected_remaining_purse(k1, k2, (self.user.total_buys + 1) / 12)
                min_price = min(min_price, cand)

        price = self.user.remaining_purse - min_price
        price = max(price, 0)
        return price
    

    def spending_rate(self, auction_progress):
        buy_progress = self.user.total_buys / MAX_TEAM_SIZE
        return math.exp(auction_progress - buy_progress)
    
    def future_role_need(self):
        rc = self.user.role_count 
        role = self.current_player.role
        left_def = rc["LC"] + rc["LCov"]
        right_def = rc["RC"] + rc["RCov"]


        future_need = MAX_ROLE[role] - rc[role]

        if role in LEFT_DEFENSE:
            future_need = min(future_need, 3 - left_def)

        if role in RIGHT_DEFENSE:
            future_need = min(future_need, 3 - right_def) 
        
        future_need = max(future_need, 0)
        
        if rc[role] == 0:
            future_need = max(1, future_need)

        return future_need

       



if __name__ == "__main__":
    pass