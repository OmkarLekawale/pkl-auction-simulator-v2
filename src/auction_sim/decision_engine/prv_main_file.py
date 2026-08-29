from itertools import combinations
import math
import constants as cns
import random

ROLE_LIST = cns.ROLE_LIST
LEFT_DEF = cns.left_defense
RIGHT_DEF = cns.right_defense

ROLE_CAP = {r: 3 for r in ROLE_LIST}
SIDE_DEF_CAP = 3

MIN_REQ = 0.1
GAMMA = 1.0


max_role = {
    "LR": 3,
    "RR": 3,
    "LC": 2,
    "LCov": 2,
    "RC": 2,
    "RCov": 2
}

 


# 0.8 <= k2 <= 1.0
# 0.8 <= k1 <= 1.0

# K1 = [0.8, 1.0]
# K2 = [0.8, 1.0]

K1 = [0.7, 1.0] # good one
K2 = [0.6, 1.0]


class HeuresticPolicy:

    def __init__(self, teamId, AuctionState, Teams, Players):
        self.teamId = teamId
        self.Teams = Teams
        self.user = self.Teams[self.teamId]
        self.Players = Players
        self.AuctionState = AuctionState
        self.totalPlayers = len(self.Players)
       
        self.cuurentPlayer = None
        self.fairPrice = None
        self.phase = None

        self.k1, self.k2 = random.uniform(K1[0], K1[1]), random.uniform(K2[0], K2[1])
        self.targets_by_k = self.generate_target_distributions()

    def predict(self, _obs, action_mask=None, action_masks=None, deterministic=False, *_, **__):
        # accept both 'action_mask' and legacy 'action_masks' keywords
        if action_masks is not None and action_mask is None:
            action_mask = action_masks

        self.phase = self.AuctionState.phase

        if self.cuurentPlayer != self.AuctionState.ctx.player:
            self.cuurentPlayer = self.AuctionState.ctx.player
            self.fairPrice = self.get_fair_price()
            # if self.cuurentPlayer.index == 0:
            #     print(self.cuurentPlayer.name, self.fairPrice)

        if self.phase == cns.PHASE_NORMAL:
            currentPrice = self.AuctionState.ctx.current_price
            
            if self.fairPrice >= 1 + currentPrice and action_mask[cns.ACTION_BID] == 1.0:
                return cns.ACTION_BID, ''
            else:
                return cns.ACTION_PASS, ''
        elif self.phase == cns.PHASE_FBM_ORIG:
            return cns.ACTION_PASS, ''
        # elif self.phase == cns.PHASE_FBM_WINNER:
        #     pass
        # elif self.phase == cns.PHASE_FBM_REPLY:
        #     pass
        # elif self.phase == cns.PHASE_PAY:
        #     cns.ACTION_PAY
        # else:
        #      cns.ACTION_PASS
        
        return cns.ACTION_PASS,''

    def get_diff(self, target, role_count):
        delta = 0
        pos_wt = 3
        neg_wt = 2
        for role in cns.ROLE_LIST:
            d = target[role] - role_count[role]
            if d >= 0:  
                delta += pos_wt * (1 + d) * d // 2 # pos_wt, 2 * pos_wt, 3 * pos_wt
            else:
                d = abs(d) # neg_wt, 2 * neg_wt, 3 * neg_wt
                delta += d * (d + 1) * neg_wt // 2
        return delta


    def _role_tuple_key(self, counts):
        return tuple(counts[r] for r in ROLE_LIST)

    def generate_target_distributions(self, max_team_size=12):

        targets_by_k = {k: {} for k in range(1, max_team_size + 1)}

        for k in range(1, 7):
            for comb in combinations(ROLE_LIST, k):
                counts = {r: 0 for r in ROLE_LIST}
                for r in comb:
                    counts[r] = 1
                key = self._role_tuple_key(counts) # avoids duplicates
                targets_by_k[k][key] = counts

        base6 = {r: 1 for r in ROLE_LIST}
        for add in ['LR', 'RR']:
            if base6[add] + 1 <= ROLE_CAP[add]:
                new = base6.copy()
                new[add] += 1
                key = self._role_tuple_key(new)
                targets_by_k[7][key] = new

        for k in range(8, max_team_size + 1):
            for prev in targets_by_k[k - 1].values():
                for r in ROLE_LIST:
                    if self._can_add_role_to_target(prev, r):
                        cand = prev.copy()
                        cand[r] += 1
                        key = self._role_tuple_key(cand)
                        targets_by_k[k][key] = cand

        for k in range(1, max_team_size + 1):
            targets_by_k[k] = list(targets_by_k[k].values())

        return targets_by_k

    def _can_add_role_to_target(self, target, role):
        if target[role] + 1 > ROLE_CAP[role]:
            return False

        if role in LEFT_DEF:
            if sum(target[r] for r in LEFT_DEF) + 1 > SIDE_DEF_CAP:
                return False

        if role in RIGHT_DEF:
            if sum(target[r] for r in RIGHT_DEF) + 1 > SIDE_DEF_CAP:
                return False

        return True


    def compute_min_delta_to_targets(self, role_count, targets_for_k):
        best = math.inf
        best_dist = {}
        for target in targets_for_k:
            d = self.get_diff(target, role_count)
            if d < best:
                best_dist = target
                best = d
        # print(best, best_dist)
        return best


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



        demand = {role: 0 for role in cns.ROLE_LIST}

        for team in self.Teams:

            rc = team.role_count 

            left_def = rc["LC"] + rc["LCov"]
            right_def = rc["RC"] + rc["RCov"]

            for role in cns.ROLE_LIST:

                deficit = max_role[role] - rc[role]

                if role in cns.left_defense:
                    deficit = min(deficit, 3 - left_def)

                if role in cns.right_defense:
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
    

    def position_discount(slef, x):
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

        price = self.user.remaining_purse- min_price
        price = max(price, 0)
        return price
    

    def spending_rate(self, auctionProgress):
        buy_progress = self.user.total_buys / cns.MAX_TEAM_SIZE
        return math.exp(auctionProgress - buy_progress)
    
    def future_role_need(self):
        rc = self.user.role_count 
        role = self.cuurentPlayer.role
        left_def = rc["LC"] + rc["LCov"]
        right_def = rc["RC"] + rc["RCov"]


        future_need = max_role[role] - rc[role]

        if role in cns.left_defense:
            future_need = min(future_need, 3 - left_def)

        if role in cns.right_defense:
            future_need = min(future_need, 3 - right_def) 
        
        future_need = max(future_need, 0)
        
        if rc[role] == 0:
            future_need = max(1, future_need)

        return future_need

       


    # score = player_req × role_pressure × player_pressure * pos_discount
    # fair_price = (base_price × spending_ratio) × (0.6 + 0.6 × score)
    def get_fair_price(self):
        ALPHA = 0.2
        # score = pR * rP * pP * pD
        # fP = eP * sR * 0.6 * (score + 1) 
        # fP = min(fP, mP)

        auctionProgress = self.cuurentPlayer.index / self.totalPlayers
        roleCount = self.user.role_count
        playerRole = self.cuurentPlayer.role
        playersLeftByRole = self.AuctionState.ctx.players_left_by_role
        playerDemand = self.player_demand()
        playerDemandByRole = self.role_demand()
        expectedPrice = self.expected_remaining_purse(self.k1, self.k2, self.user.total_buys / 12) - self.expected_remaining_purse(self.k1, self.k2, (self.user.total_buys + 1) / 12)
        maxPrice = self.max_price()
        spendingRate = self.spending_rate(auctionProgress)
        remaingSupply = self.totalPlayers - self.cuurentPlayer.index
        

        posDiscount = self.position_discount(auctionProgress) # pD
        playerPressure = min(2, playerDemand / remaingSupply) # pP

        rolePressure = playerDemandByRole[playerRole] / playersLeftByRole[playerRole] # rP -> tmp
        futureRoleFactor = 1 + self.future_role_need() / playersLeftByRole[playerRole] # fRF
        rolePressure = min(2.5, ALPHA * rolePressure + (1 - ALPHA) * futureRoleFactor) # rP

        playerRequirement = self.role_requirement_by_target_method(roleCount, self.targets_by_k)[playerRole] # pR

        score = playerRequirement * rolePressure * playerPressure * posDiscount
        fairPrice = expectedPrice * spendingRate * 0.6 * (1 + score)

        fairPrice = min(fairPrice, maxPrice)

        return fairPrice

