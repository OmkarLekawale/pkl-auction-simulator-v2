from __future__ import annotations
from dataclasses import dataclass, field
import random

from auction_sim.core.constants import MAX_PURSE, MAX_FBM, ROLE_LIST, BID_INCREMENT, MAX_TEAM_SIZE
from auction_sim.constants import PHASE_NORMAL, PHASE_FBM_ORIG, PHASE_FBM_WINNER, PHASE_FBM_REPLY, PHASE_PAY, PHASE_DONE
from auction_sim.constants import ACTION_BID, ACTION_FBM_INCR_10, ACTION_FBM_INCR_20, ACTION_FBM_TAKE, ACTION_FBM_USE, ACTION_PASS, ACTION_PAY


@dataclass(kw_only = True, frozen=True)
class Player:
    """ 
        original_team -> is the id of the orignal team of the player
    """
    name : str
    role : str
    index : int
    attack : int
    defense : int
    base_price : int
    original_team : Team

@dataclass(kw_only = True, eq=False)
class Team:
    team_id : int
    name : str
    remaining_purse : int = field(default=MAX_PURSE, init=False)
    players : list[Player] = field(default_factory=list, init=False)
    total_buys : int = field(default=0, init=False)
    role_count : dict[str, int] = field(init=False, default_factory=dict)
    fbm_left : int = field(default=MAX_FBM, init=False)
    team_score : int = field(default=0, init=False)

    def __post_init__(self): 
        self.role_count = {r : 0 for r in ROLE_LIST} 

    def can_bid(self, price):
        return (self.remaining_purse >= price + BID_INCREMENT) and self.total_buys < MAX_TEAM_SIZE

    def can_use_fbm(self, price):
        return self.remaining_purse >= price and self.fbm_left > 0 and self.total_buys < MAX_TEAM_SIZE



@dataclass(kw_only=True)
class PlayerAuction:
    """
        Conducts auction for a player.
        This class instance stores info needed for the current player's auction for all rounds
        (there will be multiple round of bidding for a player, one round is going through all the teams and giving choice to bid or pass)
        this class will go through different phases of player auction, bidding, fbm, unsold etc.
    """
    round_order : list[Team]                      
    player : Player

    current_price : int = field(init=False)
    order_idx_to_team : list[Team] = field(init=False) 

    fbm_used : bool = field(default=False, init=False)
    last_bidder : Team | None = field(default=None, init=False) 
    phase : str = field(default=PHASE_NORMAL, init=False)
    bid_happened_in_round : bool = field(default=False, init=False) 
    order_idx : int = field(default=0, init=False)
    team_to_order_idx : dict[Team,int] = field(default_factory=dict[Team, int], init=False)
    

    def __post_init__(self):
        self.current_price = self.player.base_price
        random.shuffle(self.round_order)

        for turn, team in enumerate(self.round_order):
            self.team_to_order_idx[team] = turn

    def player_auction_ends(self):

        if self.phase is not PHASE_DONE:
            raise ValueError("phase is not PHASE_DONE")   
        else:
            if self.last_bidder is None:
                print("Player was unsold")
                # We can log this information
            else:
                team = self.last_bidder
                if team.can_bid(self.last_bidder - 1):
                    team.players.append(self.player)
                    team.remaining_purse -= self.current_price
                    team.role_count[self.player.role] += 1
                else:
                    raise ValueError("Player was sold to the team which cannot pay")


    def should_skip_team(self):
        # prevent out of bound
        if self.order_idx >= len(self.round_order): return False

        # already bid
        if (self.last_bidder is not None) and self.round_order[self.order_idx] == self.last_bidder: return True 
        else: return False



    def move_order_idx_in_round(self):
        # move to next phase or next order_idx 

        # move to the next team
        self.order_idx += 1

        # skip the teams if they can't bid. No! let them bid with pass! This will let them know they have to preserve money for bidding!
        # skip when last bidders was the current team
        while self.should_skip_team():
            self.order_idx += 1

        # normal case: still within the round
        if self.order_idx < len(self.round_order):
            return

        # End of round: 
        if self.bid_happened_in_round:  
            # if bid happened start new round
            self.start_new_round()
        else:
            # If no one bid in this round -> next phase, unsold or fbm original
            if self.phase == PHASE_NORMAL:
                if self.last_bidder is None:
                    self.phase = PHASE_DONE
                    self.player_auction_ends()
                else:
                    self.phase = PHASE_FBM_ORIG
                    self.order_idx = self.team_to_order_idx[self.player.original_team]        
            else:
                raise ValueError("Wrong phased used next_phase function")

    def step(self, action : int):
        current_team = self.round_order[self.order_idx]
        phase = self.phase
        if action == ACTION_PASS:
            if phase == PHASE_NORMAL:
                self.move_order_idx_in_round()
            elif phase == PHASE_FBM_ORIG or phase == PHASE_FBM_REPLY or phase == PHASE_FBM_WINNER:
                self.phase = PHASE_PAY
                self.order_idx = self.team_to_order_idx[self.last_bidder] 
            else:
                raise ValueError("Wrong phase used this action : ACTION_PASS")
            
        elif action == ACTION_BID:
            self.bid_happened_in_round = True
            self.current_price += 1
            self.last_bidder = current_team
            self.move_order_idx_in_round()

        elif action == ACTION_FBM_USE:
            self.fbm_used = True
            self.player.original_team.fbm_left -= 1
            
            self.phase = PHASE_FBM_WINNER
            self.order_idx = self.team_to_order_idx[self.last_bidder]
            self.last_bidder = current_team

        elif action == ACTION_FBM_INCR_10:
            self.current_price = round(1.1 * self.current_price)
            self.order_idx = self.team_to_order_idx[self.player.original_team]
            self.phase = PHASE_FBM_REPLY
            self.last_bidder = current_team

        elif action == ACTION_FBM_INCR_20:
            self.current_price = round(1.2 * self.current_price)
            self.phase = PHASE_FBM_REPLY
            self.order_idx = self.team_to_order_idx[self.player.original_team]
            self.last_bidder = current_team
            
        elif action == ACTION_FBM_TAKE:
            self.phase = PHASE_PAY

        elif action == ACTION_PAY:
            self.phase = PHASE_DONE
            self.last_bidder = current_team
            self.player_auction_ends()

        else:
            raise ValueError("Wrong action")

    def start_new_round(self):
        self.order_idx = -1
        self.bid_happened_in_round = False
        random.shuffle(self.round_order)

        for turn, team in enumerate(self.round_order):
            self.team_to_order_idx[team] = turn

        self.move_order_idx_in_round() # first team might be the last bidder we want to skip it, so order_idx is -1

    def get_action_mask(self):
        team = self.round_order[self.order_idx]
        phase = self.phase
        mask = [False] * 7
        mask[ACTION_PASS] = True
        if phase == PHASE_NORMAL:
            if team.can_bid(self.current_price):
                mask[ACTION_BID] = True
        elif phase == PHASE_FBM_ORIG:
            if team.can_use_fbm(self.current_price):
                mask[ACTION_FBM_USE] = True
        elif phase == PHASE_FBM_WINNER:
            if team.remaining_purse >= round(1.2 * self.current_price):
                mask[ACTION_FBM_INCR_20] = True
                mask[ACTION_FBM_INCR_10] = True
            elif team.remaining_purse >= round(1.1 * self.current_price):
                mask[ACTION_FBM_INCR_10] = True
        elif phase == PHASE_FBM_REPLY:
            if team.can_bid(self.current_price - BID_INCREMENT):
                mask[ACTION_FBM_TAKE] = True
        elif phase == PHASE_PAY:
            if team.can_bid(self.current_price - BID_INCREMENT):
                mask[ACTION_PAY] = True
            else:
                raise ValueError("team doesn't have enough money! How they won the auction?")

if __name__ == "__main__":
    pass