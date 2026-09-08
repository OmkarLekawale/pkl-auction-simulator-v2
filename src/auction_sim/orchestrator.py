from auction_sim.constants import BID_INCREMENT
from auction_sim.constants import ACTION_BID, ACTION_FBM_INCR_10, ACTION_FBM_INCR_20, ACTION_FBM_TAKE, ACTION_FBM_USE, ACTION_PASS, ACTION_PAY
from auction_sim.constants import PHASE_NORMAL, PHASE_FBM_ORIG, PHASE_FBM_WINNER, PHASE_FBM_REPLY, PHASE_PAY, ACTION_PAY
from auction_sim.data.data_loader import get_data
from auction_sim.decision_engine.engine import get_policy
from auction_sim.core.models import Team, Player, PlayerAuction

Teams, Players, total_players_by_role, _, __ = get_data()

Policy : dict[dict, get_policy]
for team in Teams:
    Policy[team] = get_policy(user=team, Teams=Teams, total_players_by_role=total_players_by_role)





# where to add this in the progress or here only? progress seems better option!
    # player_auction.progress()
    # lets add everything needed for player auction in the PlayerAuction






for player in Players:
    
    player_auction = PlayerAuction(player=player, round_order=Teams)
    current_team = player_auction.round_order[player_auction.order_idx]
    mask = get_action_mask(player_auction)
    action, _ = Policy[team].predict(action_masks = mask, player_auction = player_auction)



    Teams.sort(key=lambda team : team.id)




