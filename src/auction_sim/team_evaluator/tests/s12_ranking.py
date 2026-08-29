from ...data.data_loader import get_data
from ..heuristic import eval_team

# command python3 -m prod.team_evaluator.tests.s12_ranking
 
Teams, Players, _, _, _ = get_data()

for player in Players:
    team = player.orignal_team
    if team.total_buys < 12 :
        team.total_buys += 1
        team.players.append(player)


for team in Teams:
    team.team_score = eval_team(team.players)
    print(team.name, team.team_score)
    for player in team.players:
        print(player.name)
    print('')




