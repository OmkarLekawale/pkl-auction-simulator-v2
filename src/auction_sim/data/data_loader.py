import pandas as pd

from ..constants import ROLE_MAP, ROLE_LIST, defensive_role
from ..core.models import Team, Player 


def build_players_from_df(df, Teams):
    
    name_2_team = {team.name : team for team in Teams}

    players = []

    for _, row in df.iterrows():
        role = ROLE_MAP.get(row["Role"])
        if role is None:
            continue  # skip unknown roles safely

        player = Player(
            name= row["player_name"],
            role= role,
            index=0, # need to change this, this should reflect the position in the list
            attack= float(row["Attack score"]),
            defense= float(row["Defense score"]),
            base_price= int(round(row["price"])),
            original_team= name_2_team[row["team_name"]],
        )
        players.append(player)

    return players


def compute_globals_from_players(players):
    total_players_by_role = {r: 0 for r in ROLE_LIST}
    max_attack = 0.0
    max_defense = 0.0

    for p in players:
        total_players_by_role[p["role"]] += 1
        max_attack = max(max_attack, p.attack)
        max_defense = max(max_defense, p.defense)

    return total_players_by_role, max_attack, max_defense



def get_data(path = "player_data.csv"):


    df = pd.read_csv(path, Teams)  # your dataframe

    team_names = sorted(df["team_name"].unique())

    Teams = []
    for tId, _name in enumerate(team_names):
        Teams.append(Team(team_id=tId, name=_name))

    players = build_players_from_df(df)
    total_players_by_role, max_attack, max_defense = compute_globals_from_players(players)

    players = sorted(players, key = lambda x : [
                                                    x.base_price, 
                                                    x.attack * (0.4 if x.role in defensive_role else 0.9) + (1.1 if x.role in defensive_role else 0.4) * x.defense
                                                ], 
                                                reverse = True)


    Players = []

    for pId, player in enumerate(players):
        player.index = pId
        Players.append(player)

    return Teams, Players, total_players_by_role, max_attack, max_defense


