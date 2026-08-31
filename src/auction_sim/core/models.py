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
        teams -> list of instances of class Team
        auction_ctx -> instance of class AuctionContext
    """
    teams : list[Team]                      
    player : Player

    current_price : int = field(init=False)
    turn_sequence : list[int] = field(init=False)
    turn_seq_idx_2_team_id : list[int] = field(init=False)

    fbm_used : bool = field(default=False, init=False)
    last_bidder_id : int | None = field(default=None, init=False) 
    phase : str = field(default=PHASE_NORMAL, init=False)
    bid_happened_in_round : bool = field(default=False, init=False) # I think we can remove this by checking if the current turn team = last bidder id, what about the case when there is no bid?
    turn_seq_idx : int = field(default=0, init=False)
    

    def __post_init__(self):
        self.current_price = self.player.base_price
        self.turn_sequence = list(range(len(self.teams)))
        random.shuffle(self.turn_sequence)
        for turn in range(len(self.teams)):
            team_id = self.turn_seq_idx[turn] 
            self.turn_seq_idx_2_team_id[team_id] = turn


    def start_new_round(self):
        self.turn_seq_idx = -1
        self.bid_happened_in_round = False
        random.shuffle(self.turn_sequence)
        for turn in range(len(self.teams)):
            self.turn_seq_idx_2_team_id[self.turn_sequence[turn]] = turn
        self.progress()

    def current_team_id(self):
        return self.turn_sequence[self.turn_seq_idx]

    def current_team(self):
        return self.teams[self.current_team_id()]

    def check(self):
        # weather to move to next iterator
        if self.turn_seq_idx >= len(self.turn_sequence): return False
        team = self.current_team()
        price = self.ctx.current_price
        if (self.ctx.last_bidder is not None) and self.turn_seq_idx == self.turn_index_of_team_id(self.ctx.last_bidder): return True
        elif self.current_team().total_buys >= MAX_TEAM_SIZE: return True
        elif team.remaining_purse < price + BID_INCREMENT : return True
        else: return False

    def next_phase(self):
        curr_phase = self.phase
        if self.last_bidder is None:
            self.finalize_unsold()
        else:
            self.phase = PHASE_FBM_ORIG
            self.turn_seq_idx = self.turn_index_of_team_id(self.player.original_team)

    def progress(self):
        """
            move to next phase or next turn_seq_idx 
        """
        player_orignal_team_id = self.player.original_team
        # move to the next team
        self.turn_seq_idx += 1

        # skip the teams if they can't bid. No! let them bid with pass! This will let them know they have to preserve money for bidding!

        while self.check():
            self.turn_seq_idx += 1

        
        # normal case: still within the round
        if self.turn_seq_idx < len(self.turn_sequence):
            return

        # End of round: 
        # If no one bid in this round -> if final bidder is None then unsold player, if final bidder is a team then move to PHASE_FBM_ORIG
        # if bid happened start new round
        if self.bid_happened_in_round: 
            self.start_new_round()
        else:
            self.next_phase()

    
    def finalize_unsold(self):
        player = self.ctx.player
        self.ctx.players_left_by_role[player.role] -= 1
        self.phase = PHASE_DONE 









if __name__ == "__main__":
    team = Team(team_id=10, name="Puneri Paltan") 
    player = Player(name="Omkar", role="Right Corner",  index=0, attack = 50, defense = 100, base_price = 10, original_team = team)
    print(player)
    print(team)