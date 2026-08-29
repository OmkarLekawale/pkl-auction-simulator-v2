import constants as cns
import data.data_loader as data_loader
from env.pkl_auction_env import PKLAuctionEnv
from policies.heurestic_policy import HeuresticPolicy

epochs = 1

current_player = None
for _ in range(epochs):
    Teams, Players, total_players_by_role, max_attack, max_defense = data_loader.get_data()
    env = PKLAuctionEnv(Teams, Players, total_players_by_role, max_attack, max_defense)

    Polices = [None] * len(Teams)
    for team in Teams:
        Polices[team.team_id] = HeuresticPolicy(team.team_id, env.state, Teams, Players)
    obs, _ = env.reset()
    while not env.done:
        current_team = env.state.current_team_id()
        action_mask = env.action_masks()
        Polices[current_team].AuctionState = env.state
        Polices[current_team].Teams = env.teams  
        action, _ = Polices[current_team].predict(
            obs,
            action_masks=action_mask,
            deterministic=True
            # deterministic=flag
        )
        
 
        
        acting_team = env.state.current_team()

        if current_player != env.state.ctx.player:
            print(env.player_idx)
        current_player = env.state.ctx.player
 
        print(f"phase={env.state.phase}, player={current_player.name[:10]:10s},  "
            f"Price={env.ctx.current_price:6.1f},  "
            f"acting_team={acting_team.name[:10]:10s}, purse={acting_team.remaining_purse:6.1f},  ACTION={cns.actions_[action][:15]:15s}, ")
        print('-' * 100)

        
        obs, reward, terminated, truncated, info  = env.step(action)

    print()
    for team in env.teams:
        print(f"player index in the auction : {env.player_idx}")
        print(f"team name : {team.name}")
        print(f"remaining purse : {team.remaining_purse}")
        print(f"total buys : {team.total_buys}")
        print(f"team score : {team.team_score}")
        for player in team.players:
            print(f"  {player['name'][:30]:30s}  {player['role']:5s}  "
                  f"Price={player['price']:6.1f}  "
                  f"ATK={player['attack']:6.1f}  DEF={player['defense']:6.1f} "
                  f"Delta Team Score={player['del_score']:6.1f}")

        print()
        print("="*150)
        print()



