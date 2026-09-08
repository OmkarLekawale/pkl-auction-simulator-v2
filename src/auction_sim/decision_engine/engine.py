# inputs : all the input required for generating the deceasion, which method to use

# goal is to return a policy : deceasion engine

import numpy as np

from auction_sim.core.models import Team
from auction_sim.decision_engine.rule_based.adaptive_valuation.engine import HeuresticPolicy


def get_model_based_policy():
    print("No model based models yet!") 

def get_rule_based_policy(
        user : Team,
        Teams : list[Team],
        policy_name : str,
        total_players_by_role : dict[str,int]
):
    if policy_name == "adaptive_valuation":
        return HeuresticPolicy(user=user, Teams=Teams, players_left_by_role=total_players_by_role) 

def get_policy(
        user : Team | None = None,
        Teams : list[Team] | None = None,
        policy_name : str = "adaptive_valuation",
        total_players_by_role : dict[str,int] | None = None,
        model_based : bool = False,
        obs : np.ndarray | None = None

):
    if user is None or Teams is None:
        raise ValueError("Teams and user not provided!")
    if model_based:
        get_model_based_policy()
    else:
        return get_rule_based_policy(user=user, Teams=Teams, policy_name=policy_name, total_players_by_role=players_by_role)