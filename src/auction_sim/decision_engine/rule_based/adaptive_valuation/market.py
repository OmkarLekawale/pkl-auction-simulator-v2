ROLE_LIST = ["LR", "RR", "LC", "LCov", "RC", "RCov"]
OFFENSIVE_ROLE = ['LR', 'RR']
LEFT_DEFENSE = ['LC', 'LCov']
RIGHT_DEFENSE = ['RC', 'RCov']

class MarketAnalyzer:
    # Teams, Player
    def __init__(self, team_id, player_left_by_role, Teams):

        self.team_id = team_id
        self.total_buys = sum([team.total_buys for team in Teams])
        self.total_role_count = {
            role : sum(team.role_count[role] for team in Teams) 
            for role in ROLE_LIST
        }

        self.player_count = Teams[self.team_id].total_buys
    
    def market_role_worst_case_demand():
        # high demand
        pass

    def market_role_best_case_demand():
        # low demand
        pass

    def market_player_demand():
        pass
    

