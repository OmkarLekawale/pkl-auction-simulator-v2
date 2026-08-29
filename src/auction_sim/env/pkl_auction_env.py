import gymnasium as gym
from gymnasium import spaces
import numpy as np

import constants as cns
from core.auction_context import AuctionContext
from core.auction_state import AuctionState


class PKLAuctionEnv(gym.Env):
    """
    Multi-actor environment where the same policy acts for each team in turn.
    Each call to env.step(action) is interpreted as action by the current acting team.
    """
    metadata = {"render_modes": []}

    def __init__(self, teams, players, total_players_by_role, max_attack, max_defense):
        super().__init__()
        self.teams = teams     # list of team instances
        self.players = players # players is list of player instances

        self.total_players_by_role = total_players_by_role
        self.max_attack = max_attack 
        self.max_defense = max_defense

        self.action_space = spaces.Discrete(cns.NUM_ACTIONS)
        self.observation_space = spaces.Box(0.0, 1.0, (cns.OBS_SIZE,), dtype=np.float32)
        self.done = False
        

        self.ctx = None
        self.state = None


        # Track episode stats
        self.episode_reward = 0.0
        self.episode_length = 0

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        self.players_left_by_role = {r: sum(1 for p in self.players if p.role == r) for r in cns.ROLE_LIST}
        self.player_idx = 0
        self.done = False
        if cns.MAX_TEAM_SIZE != len(self.teams):
            print("error team size is not matching")
        self.ctx = AuctionContext(self.players[self.player_idx], self.players_left_by_role)
        self.state = AuctionState(self.teams, self.ctx)
        
        # RESET EPISODE TRACKING
        self.episode_reward = 0.0
        self.episode_length = 0
        
        obs = self._get_obs(self.state, self.max_attack, self.max_defense, self.total_players_by_role) 
        return obs, {}

    def _next_player(self):
        while self.state.phase == cns.PHASE_DONE:
            if self.player_idx < len(self.players) - 1:
                self.player_idx += 1
            else:
                self.done = True
                return
            self.ctx = AuctionContext(self.players[self.player_idx], self.players_left_by_role)
            self.state = AuctionState(self.teams, self.ctx)          
            self.state.turn_idx = -1
            self.state.advance_turn()


    def _get_obs(self, state, max_attack, max_defense, total_players_by_role):

        """
            Build observation for the *current acting team* (i.e., team whose turn it is).
            state -> instance of Class AuctionState which store the info needed for the current player's auction
            max_attack -> max value of attack score acrross all the players
            max_defense -> max value of defense score acrross all the players
            total_players_by_role -> Dictionary of role and total count of players for that role
        """
        obs = []
        acting_team_id = state.current_team_id() 
        agent = state.current_team()
        player = state.ctx.player

        # Team Identity -> no need

        # A. Own team
        obs.append(agent.remaining_purse / cns.MAX_PURSE)
        obs.append(agent.fbm_left / cns.MAX_FBM)

        # Role saturation normalized by max team size
        for r in cns.ROLE_LIST:
            obs.append(agent.role_count.get(r, 0) / cns.MAX_TEAM_SIZE)

        # B. Current player stats
        obs.append(player.attack / max_attack)
        obs.append(player.defense / max_defense)
        role_onehot = [0.0] * len(cns.ROLE_LIST)
        role_onehot[cns.ROLE_TO_IDX[player.role]] = 1.0
        obs.extend(role_onehot)
        obs.append(player.base_price / cns.MAX_PURSE)
        obs.append(state.ctx.current_price / cns.MAX_PURSE)

        # C. Market scarcity
        for r in cns.ROLE_LIST:
            left = state.ctx.players_left_by_role.get(r, 0)
            total = total_players_by_role.get(r, 1)
            obs.append(left / total)

        # D. Opponent pressure (aggregate across OTHER teams)
        opp_purses = [t.remaining_purse for t in state.teams if t.team_id != acting_team_id]
        if len(opp_purses) == 0:
            opp_mean = opp_min = opp_max = 0.0
            active_frac = 0.0
        else:
            opp_mean = np.mean(opp_purses)
            opp_min = np.min(opp_purses)
            opp_max = np.max(opp_purses)
            active = sum(1 for p in opp_purses if p >= state.ctx.current_price + 1)
            active_frac = active / len(opp_purses)

        obs.append(opp_mean / cns.MAX_PURSE)
        obs.append(opp_min / cns.MAX_PURSE)
        obs.append(opp_max / cns.MAX_PURSE)
        obs.append(active_frac)

        # E. FBM context (about original team and acting team)
        orig_team = state.teams[player.original_team]
        obs.append(orig_team.fbm_left / cns.MAX_FBM)
        obs.append(orig_team.remaining_purse / cns.MAX_PURSE)
        obs.append(1.0 if player.original_team == acting_team_id else 0.0)
        

        # F. Phase flags
        obs.extend([
            1.0 if state.phase == cns.PHASE_NORMAL else 0.0,
            1.0 if state.phase == cns.PHASE_FBM_ORIG else 0.0,
            1.0 if state.phase == cns.PHASE_FBM_WINNER else 0.0,
            1.0 if state.phase == cns.PHASE_FBM_REPLY else 0.0,
            1.0 if state.phase == cns.PHASE_PAY else 0.0
        ])

        obs = np.array(obs, dtype=np.float32)
        assert obs.shape == (cns.OBS_SIZE,), f"Obs shape mismatch {obs.shape}"
        return obs


    def action_masks(self):
        """
        Returns list[bool] mask of length cns.cns.NUM_ACTIONS for the current acting team.
        self.state -> instance of class Auctionself.state stores the info about who is current agent
        """
        mask = [False] * cns.NUM_ACTIONS
        acting_id = self.state.current_team_id()
        agent = self.state.current_team()
        ctx = self.state.ctx
        player = ctx.player
        price = ctx.current_price
        
        if self.state.phase == cns.PHASE_NORMAL:
            mask[cns.ACTION_PASS] = True
            if agent.can_bid(price):
                mask[cns.ACTION_BID] = True

        elif self.state.phase == cns.PHASE_FBM_ORIG:
            # we have to make sure the current team is acting agent
            # precaution
            if player.original_team != acting_id:
                print('cns.PHASE_FBM_ORIG started without going to orignal team')
            if player.original_team == acting_id:
                mask[cns.ACTION_PASS] = True
                if agent.can_use_fbm(price):
                    mask[cns.ACTION_FBM_USE] = True

        elif self.state.phase == cns.PHASE_FBM_WINNER:
            # precaution
            if ctx.last_bidder != acting_id:
                print('cns.PHASE_FBM_WINNER started without going to last bidder team')
            if ctx.last_bidder == acting_id:
                mask[cns.ACTION_PASS] = True
                price_10 = int(round(price * cns.FBM_MULT_10))
                price_20 = int(round(price * cns.FBM_MULT_20))
                if agent.remaining_purse >= price_10:
                    mask[cns.ACTION_FBM_INCR_10] = True
                if agent.remaining_purse >= price_20:
                    mask[cns.ACTION_FBM_INCR_20] = True

        elif self.state.phase == cns.PHASE_FBM_REPLY:
            # precaution
            if player.original_team != acting_id:
                print('cns.PHASE_FBM_REPLY started without going to orignal team')
            if player.original_team == acting_id:
                mask[cns.ACTION_PASS] = True
                if agent.remaining_purse >= price:
                    mask[cns.ACTION_FBM_TAKE] = True

        elif self.state.phase == cns.PHASE_PAY:
            mask[cns.ACTION_PAY] = True
        else:
            print(f"{self.state.phase} this is not the correct phase in action mask")
        return mask
    


    def calculate_score(self):
        team = self.state.current_team() 
        player = self.state.ctx.player
        price = self.state.ctx.current_price
        return team.add_player(player, price)   




    # def finalize_sale(self):
    #     """
    #         team_id -> team that gets the player 
    #     """
    #     buyer = self.state.current_team()
    #     player = self.state.ctx.player
    #     price = self.state.ctx.current_price
    #     b_price = player.base_price
    #     total_buys = self.state.current_team().total_buys
    #     C = (price / b_price - 1) * (0.5 if b_price >= 50 else 0.4)
    #     factor = min(C, 1)
    #     reduce = price * factor

    #     # Remove player from market
    #     self.state.ctx.players_left_by_role[player.role] -= 1

    #     # reduce fbm 
    #     if self.state.fbm_used:
    #         self.state.teams[player.original_team].fbm_left -= 1

    #     # End this player's auction
    #     self.state.phase = cns.PHASE_DONE 

    #     delta = self.calculate_score()
    #     buyer.team_score += delta
    #     reward = (delta - reduce) / 100
        
    #     # Buyer pays and gets the player
    #     buyer.remaining_purse -= price
    #     buyer.role_count[player.role] += 1
    #     buyer.total_buys += 1
        
    #     if buyer.total_buys == cns.MAX_TEAM_SIZE:
    #         reward += 1.0

    #     buyer.players.append({'name':player.name, 'role':player.role, 
    #                 'attack':player.attack, 'defense':player.defense,
    #                     'price' : price, 'del_score' : reward})
        
    #     return  reward

    def finalize_sale(self):
        """
            team_id -> team that gets the player 
        """
        buyer = self.state.current_team()
        player = self.state.ctx.player
        price = self.state.ctx.current_price
 
 

        # Remove player from market
        self.state.ctx.players_left_by_role[player.role] -= 1

        # reduce fbm 
        if self.state.fbm_used:
            self.state.teams[player.original_team].fbm_left -= 1

        # End this player's auction
        self.state.phase = cns.PHASE_DONE 

        delta = self.calculate_score() 
        
        # Buyer pays and gets the player
        buyer.remaining_purse -= price
        buyer.role_count[player.role] += 1
        buyer.total_buys += 1

        buyer.players.append({'name':player.name, 'role':player.role, 
                    'attack':player.attack, 'defense':player.defense,
                        'price' : price, 'del_score' : delta})
        
        buyer.team_score += delta
        
        return  delta

    def apply_action(self, action: int):
        """
        Apply action for current acting team (self.state.current_team_id()).
        Returns an event dict (or None) describing important outcomes.
        """

        team = self.state.current_team()

        if self.state.phase == cns.PHASE_NORMAL:
            
            if action == cns.ACTION_BID:
                flag = self.state.ctx.last_bidder is None
                self.state.ctx.current_price += cns.BID_INCREMENT
                self.state.ctx.last_bidder = team.team_id
                self.state.bid_happened_in_round = True
                # return (cons * (team.total_buys + 1))
                # return 0.0, this was not lettting it to move to next step
                    
                
            # PASS does nothing for normal besides advancing
            self.state.advance_turn()
            # no immediate finalize here
            return 0.0

        if self.state.phase == cns.PHASE_FBM_ORIG: 
            if action == cns.ACTION_FBM_USE:
                self.state.fbm_used = True
                self.state.phase = cns.PHASE_FBM_WINNER
                self.state.turn_idx = self.state.turn_index_of_team_id(self.state.ctx.last_bidder)
                # return (cons * (team.total_buys + 1))
                return 0.0
                
            else:
                # PASS -> winner gets player at current price
                self.state.phase = cns.PHASE_PAY
                self.state.turn_idx = self.state.turn_index_of_team_id(self.state.ctx.last_bidder)
            return 0.0

        if self.state.phase == cns.PHASE_FBM_WINNER: # current team here is final bidder
            price = self.state.ctx.current_price
            self.state.turn_idx = self.state.turn_index_of_team_id(self.state.ctx.player.original_team)
            if action == cns.ACTION_PASS:
                # original team gets player at original price (use_fbm True)
                self.state.phase = cns.PHASE_PAY
                return 0.0
            elif action == cns.ACTION_FBM_INCR_10:
                new_price = int(round(price * cns.FBM_MULT_10))
            elif action == cns.ACTION_FBM_INCR_20:
                new_price = int(round(price * cns.FBM_MULT_20))
            else:
                raise ValueError("Invalid FBM winner action")
            self.state.ctx.current_price = new_price
            self.state.phase = cns.PHASE_FBM_REPLY
            # return (cons * (team.total_buys + 1))
            return 0.0

        if self.state.phase == cns.PHASE_FBM_REPLY:
            self.state.phase = cns.PHASE_PAY
            if action == cns.ACTION_FBM_TAKE:
                self.state.turn_idx = self.state.turn_index_of_team_id(self.state.ctx.player.original_team) 
                # return (cons * (team.total_buys + 1))
                return 0.0
            else:
                # PASS -> winner gets at increased price
                self.state.turn_idx = self.state.turn_index_of_team_id(self.state.ctx.last_bidder) 
            return 0.0 

        if self.state.phase == cns.PHASE_PAY:
            return self.finalize_sale()

        raise RuntimeError("Invalid phase in apply_action")


    def _check(self): 
        return sum(1 if (team.total_buys >= cns.MAX_TEAM_SIZE or team.remaining_purse < 10) else 0 for team in self.teams) >= len(self.teams)

    def step(self, action):
        """
        Action is interpreted as chosen by the current acting team (state.current_team_id()).
        Returns obs(for the next agent), reward, terminated, truncated, info
        """
        assert not self.done, "step called after done"
        acting_team = self.state.current_team_id()

        # Apply the action for the current actor; capture event
        reward = self.apply_action(action)

        # TRACK EPISODE STATS
        self.episode_reward += reward
        self.episode_length += 1

        if self.state.phase == cns.PHASE_DONE:
            self._next_player()
            
        # Observation is always for the next acting team (or zeros if done)
        obs = np.zeros(self.observation_space.shape, dtype=np.float32) if self.done else self._get_obs(self.state, self.max_attack, self.max_defense, self.total_players_by_role)
        terminated = self.done
        truncated = False
        
        # ADD EPISODE INFO WHEN DONE
        info = {}
        if terminated:
            info['episode'] = {
                'r': self.episode_reward,
                'l': self.episode_length
            }
            print(f"Episode finished! Reward: {self.episode_reward:.2f}, Length: {self.episode_length}")

        return obs, reward, terminated, truncated, info

