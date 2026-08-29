import random
import constants as cns

class AuctionState:
    def __init__(self, teams, auction_ctx): 

        """
            This class instance stores info needed for the current player's auction for all rounds
            (there will be multiple round of bidding for a player, one round is going through all the teams and giving choice to bid or pass)
            teams -> list of instances of class Team
            auction_ctx -> instance of class AuctionContext
        """
        
        self.teams = teams                      
        self.ctx = auction_ctx                
        self.phase = cns.PHASE_NORMAL

        # random turn order among teams for the current player
        self.turn_order = list(range(len(teams)))
        random.shuffle(self.turn_order)
        self.turn_idx = 0
        self.bid_happened_in_round = False
        self.turn_idx_team = [0] * len(teams)
        for i in range(len(self.teams)):
            self.turn_idx_team[self.turn_order[i]] = i

        # FBM bookkeeping
        self.fbm_used = False 

    def start_new_round(self):
        self.turn_idx = -1
        self.bid_happened_in_round = False
        random.shuffle(self.turn_order)
        for i in range(len(self.teams)):
            self.turn_idx_team[self.turn_order[i]] = i
        self.advance_turn()

    def current_team_id(self):
        return self.turn_order[self.turn_idx]

    def current_team(self):
        return self.teams[self.current_team_id()]

    def turn_index_of_team_id(self, team_id):
        return self.turn_idx_team[team_id]
    
    def check(self):
        # weather to move to next iterator
        if self.turn_idx >= len(self.turn_order): return False
        team = self.current_team()
        price = self.ctx.current_price
        if (self.ctx.last_bidder is not None) and self.turn_idx == self.turn_index_of_team_id(self.ctx.last_bidder): return True
        elif self.current_team().total_buys >= cns.MAX_TEAM_SIZE: return True
        elif team.remaining_purse < price + cns.BID_INCREMENT : return True
        else: return False

    def advance_turn(self):
        """
            move to next phase or next turn_idx 
        """
        player_orignal_team_id = self.ctx.player.original_team
        # move to the next team
        self.turn_idx += 1

        # skip the teams if they can't bid

        while self.check():
            self.turn_idx += 1

        
        # normal case: still within the round
        if self.turn_idx < len(self.turn_order):
            return

        # End of round: 
        # If no one bid in this round -> if final bidder is None then unsold player, if final bidder is a team then move to PHASE_FBM_ORIG
        # if bid happened start new round
        if self.bid_happened_in_round: 
            self.start_new_round()
        else:
            if self.ctx.last_bidder is None:
                self.finalize_unsold()
            else:
                self.phase = cns.PHASE_FBM_ORIG
                self.turn_idx = self.turn_index_of_team_id(player_orignal_team_id)
    
    def finalize_unsold(self):
        player = self.ctx.player
        self.ctx.players_left_by_role[player.role] -= 1
        self.phase = cns.PHASE_DONE 


    def __repr__(self):
        return f"AuctionState(phase={self.phase}, price={self.ctx.current_price}, turn={self.turn_idx}/{len(self.turn_order)}, last_bidder={self.ctx.last_bidder})"



