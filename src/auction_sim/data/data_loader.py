import pandas as pd
from pathlib import Path

from auction_sim.data.constants import ROLE_MAP, ROLE_LIST, DEFENSIVE_ROLE
from auction_sim.core.models import Team, Player 


def build_players_from_df(df, Teams : list[Team]) -> list[dict]: # return players as dict
    
    name_2_team = {team.name : team for team in Teams}

    players = []

    for _, row in df.iterrows():
        role = ROLE_MAP.get(row["Role"])
        if role is None:
            continue  # skip unknown roles safely

        player = {
            "name" : row["player_name"],
            "role": role, 
            "attack": float(row["Attack score"]),
            "defense": float(row["Defense score"]),
            "base_price": int(round(row["price"])),
            "original_team": name_2_team[row["team_name"]],
        }
        players.append(player)

    return players


def compute_globals_from_players(players):
    total_players_by_role = {r: 0 for r in ROLE_LIST}
    max_attack = 0.0
    max_defense = 0.0

    for p in players:
        total_players_by_role[p.role] += 1
        max_attack = max(max_attack, p.attack)
        max_defense = max(max_defense, p.defense)

    return total_players_by_role, max_attack, max_defense


def arrange_player_order(players : list[dict]):
    players = sorted(players, key = lambda x : [
                                                    x["base_price"], 
                                                    x["attack"] * (0.4 if x["role"] in DEFENSIVE_ROLE else 0.9) + (1.1 if x["role"] in DEFENSIVE_ROLE else 0.4) * x["defense"]
                                                ], 
                                                reverse = True)
    return players

def get_data(path = None):

    if path is None: 
        path = Path(__file__).parent / "player_data.csv"
        
    df = pd.read_csv(str(path)) 
    

    team_names = sorted(df["team_name"].unique())

    Teams = []
    for tId, _name in enumerate(team_names):
        Teams.append(Team(team_id=tId, name=_name))

    
    players = build_players_from_df(df, Teams) # list[dict]

    players = arrange_player_order(players)

    Players = [] # list[Player]

    for pId, p in enumerate(players): 
        player = Player(index=pId, **p)
        Players.append(player)

    total_players_by_role, max_attack, max_defense = compute_globals_from_players(Players)

    return Teams, Players, total_players_by_role, max_attack, max_defense

