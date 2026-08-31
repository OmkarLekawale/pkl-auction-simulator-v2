from __future__ import annotations
from dataclasses import dataclass, field
import random

from .constants import MAX_PURSE, MAX_FBM, ROLE_LIST, BID_INCREMENT, MAX_TEAM_SIZE
from .constants import PHASE_NORMAL, PHASE_FBM_ORIG, PHASE_DONE

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

@dataclass(kw_only = True)
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


@dataclass(kw_only = True)
class AuctionContext: 
    """
        This class instance corresponds to each player class in bidding 
    """
    player : Player
    current_price : int = field(init=False)
    last_bidder_id : int | None = field(default=None, init=False)

    def __post_init__(self):
        self.current_price = self.player.base_price 

@dataclass(kw_only=True)
class PlayerAuction:
    """
        Conducts auction for a player.
        This class instance stores info needed for the current player's auction for all rounds
        (there will be multiple round of bidding for a player, one round is going through all the teams and giving choice to bid or pass)
        this class will go through different phases of player auction, bidding, fbm, unsold etc.
    """
    teams : list[Team]                      
    player : Player

    current_price : int = field(init=False)
    round_order : list[int] = field(init=False)
    order_idx_to_team_id : list[int] = field(init=False) # can we do order_id_to_team instead?

    fbm_used : bool = field(default=False, init=False)
    last_bidder_id : int | None = field(default=None, init=False) # do we need team id?, we can just keep there a team instead of id?
    phase : str = field(default=PHASE_NORMAL, init=False)
    bid_happened_in_round : bool = field(default=False, init=False) # I think we can remove this by checking if the current turn team = last bidder id, what about the case when there is no bid?
    order_idx : int = field(default=0, init=False)
    

    def __post_init__(self):
        self.current_price = self.player.base_price
        self.round_order = list(range(len(self.teams)))
        random.shuffle(self.round_order)
        for turn in range(len(self.teams)):
            team_id = self.order_idx[turn] 
            self.order_idx_to_team_id[team_id] = turn

    def player_auction_ends(self):
        if self.phase is not PHASE_DONE:
            raise ValueError("phase is not PHASE_DONE")   

    def next_phase(self):
        if self.phase == PHASE_NORMAL:
            if self.last_bidder is None:
                self.phase = PHASE_DONE
                self.player_auction_ends()
            else:
                self.phase = PHASE_FBM_ORIG
                self.order_idx = self.turn_index_of_team_id(self.player.original_team)        
        else:
            raise ValueError()

    def should_skip_team(self):
        # prevent out of bound
        if self.order_idx >= len(self.round_order): return False

        # already bid
        if (self.ctx.last_bidder is not None) and self.order_idx == self.turn_index_of_team_id(self.ctx.last_bidder): return True # should i remove the turn index of team, instead it should be team only
        else: return False

    def progress(self):
        # move to next phase or next order_idx 

        # move to the next team
        self.order_idx += 1

        # skip the teams if they can't bid. No! let them bid with pass! This will let them know they have to preserve money for bidding!
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
            self.next_phase()

    def start_new_round(self):
        self.order_idx = -1
        self.bid_happened_in_round = False
        random.shuffle(self.round_order)
        for turn in range(len(self.teams)):
            self.order_idx_to_team_id[self.round_order[turn]] = turn
        self.progress() # first team might be the last bidder we want to skip it, so order_idx is -1

    def current_team_id(self):
        return self.round_order[self.order_idx]

    def current_team(self):
        return self.teams[self.current_team_id()]

