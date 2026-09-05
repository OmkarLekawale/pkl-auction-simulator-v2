from auction_sim.data.data_loader import get_data
from auction_sim.core.models import Player, Team, PlayerAuction
from auction_sim.decision_engine.rule_based.adaptive_valuation.engine import HeuresticPolicy

Teams, Players, total_players_by_role, _, _ = get_data()
Policy : dict[Team, HeuresticPolicy] = {
    team : HeuresticPolicy(
        user=team,
        Teams=Teams,
        players_left_by_role=total_players_by_role
    ) for team in Teams
}
