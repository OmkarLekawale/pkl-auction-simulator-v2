# game.py
"""
Interactive PKL auction CLI:
- Lets a human choose one of the 12 teams to play as.
- Runs the auction with all teams controlled by heuristic bots.
- The user's team will *not* actively bid during the automated bidding rounds.
- When a player's auction finishes (sold or unsold), the script reports the result.
  If the player went unsold (or finalizes), the user is prompted to buy (unless skipped).
- QoL options: skip entire roles, set a price threshold to auto-skip prompts.
"""

import sys
import traceback
import constants as cns
import data.data_loader as data_loader
from env.pkl_auction_env import PKLAuctionEnv
from policies.heurestic_policy import HeuresticPolicy

# ---- helpers for robust input ----
def input_int(prompt, min_v=None, max_v=None, default=None):
    while True:
        try:
            s = input(prompt).strip()
            if s == "" and default is not None:
                return default
            v = int(s)
            if min_v is not None and v < min_v:
                print(f"Enter a number >= {min_v}")
                continue
            if max_v is not None and v > max_v:
                print(f"Enter a number <= {max_v}")
                continue
            return v
        except ValueError:
            print("Invalid integer. Try again.")

def input_float(prompt, min_v=None, max_v=None, default=None):
    while True:
        try:
            s = input(prompt).strip()
            if s == "" and default is not None:
                return default
            v = float(s)
            if min_v is not None and v < min_v:
                print(f"Enter a number >= {min_v}")
                continue
            if max_v is not None and v > max_v:
                print(f"Enter a number <= {max_v}")
                continue
            return v
        except ValueError:
            print("Invalid number. Try again.")

def input_yes_no(prompt, default="n"):
    default = default.lower()
    while True:
        s = input(prompt + f" (y/n) [{default}]: ").strip().lower()
        if s == "":
            s = default
        if s in ("y", "yes"):
            return True
        if s in ("n", "no"):
            return False
        print("Enter y or n.")

# ---- main game logic ----
def main():
    try:
        print("Loading data...")
        Teams, Players, total_players_by_role, max_attack, max_defense = data_loader.get_data()

        n_teams = len(Teams)
        print(f"Loaded {n_teams} teams and {len(Players)} players.")

        # show teams
        print("\nTeams:")
        for team in Teams:
            print(f" {team.team_id}. {team.name}   (purse={team.remaining_purse})")

        # choose team
        user_team_id = input_int(f"\nChoose your team by id (0 to {n_teams-1}): ", min_v=0, max_v=n_teams-1)
        user_team = Teams[user_team_id]
        print(f"You will play as: {user_team.name} (id={user_team_id})\n")

        # QoL settings
        print("Quality-of-life settings (skip prompts):")
        print("Available roles:", ", ".join(cns.ROLE_LIST))
        skip_roles_input = input("Enter roles to skip (comma separated), or press Enter for none: ").strip()
        skip_roles = [r.strip() for r in skip_roles_input.split(",") if r.strip()]
        if skip_roles:
            invalid = [r for r in skip_roles if r not in cns.ROLE_LIST]
            if invalid:
                print("Warning: some roles not recognized and will be ignored:", invalid)
                skip_roles = [r for r in skip_roles if r in cns.ROLE_LIST]
        price_skip = input_float("Enter max base/final price that you'll consider (0 = auto-skip all prompts): ", min_v=0, default=0)

        confirm = input_yes_no(f"Start auction as team '{user_team.name}'? ")
        if not confirm:
            print("Aborted by user.")
            return

        # create environment
        env = PKLAuctionEnv(Teams, Players, total_players_by_role, max_attack, max_defense)
        # create heuristics for all teams (we will not use user team policy)
        Polices = [None] * len(Teams)
        for team in Teams:
            Polices[team.team_id] = HeuresticPolicy(team.team_id, env.state, Teams, Players)

        # reset env
        obs, _ = env.reset()
        prev_player_idx = getattr(env, "player_idx", 0)
        prev_player_obj = Players[prev_player_idx] if 0 <= prev_player_idx < len(Players) else None

        print("\nAuction started. Bots will run automatically; you'll be prompted only at finalization of items (unsold / finalize).")
        print("Type Ctrl+C to quit early (your purchases will be shown).")
        print("-" * 80)

        # main loop
        while not env.done:
            current_team_id = env.state.current_team_id()
            action_mask = env.action_masks()

            if current_team_id != user_team_id:
                # bot acts
                Polices[current_team_id].AuctionState = env.state
                Polices[current_team_id].Teams = env.teams
                action, _ = Polices[current_team_id].predict(obs, action_masks=action_mask, deterministic=True)
                acting_team = env.state.current_team()
                # Debug print for visibility (comment out if too verbose)
                # print(f"[BOT] team={acting_team.name} action={cns.actions_[action]}")
            else:
                # User team - remain passive during automated bidding.
                # We send ACTION_PASS so auction runs without user's participation.
                action = cns.ACTION_PASS

            # perform step
            obs, reward, terminated, truncated, info = env.step(action)

            # detect player index change -> previous player's auction finished
            curr_player_idx = getattr(env, "player_idx", None)
            if curr_player_idx is None:
                # fallback: try from state.ctx.player index if available
                try:
                    curr_player_idx = env.state.ctx.player_idx
                except Exception:
                    curr_player_idx = None

            if curr_player_idx is not None and curr_player_idx != prev_player_idx:
                # previous player finished auction
                prev_idx = prev_player_idx
                if 0 <= prev_idx < len(Players):
                    prev_player = Players[prev_idx]
                    final_price = prev_player.get("price", None)
                    role = prev_player.get("role", "UNKNOWN")
                    name = prev_player.get("name", f"Player-{prev_idx}")

                    # check which team (if any) owns this player now
                    owner = None
                    for t in env.teams:
                        # team.players is a list of player dicts (in run_simulation they print it this way)
                        for p in getattr(t, "players", []):
                            # compare by name (robust if players are re-instantiated)
                            if p.get("name") == name:
                                owner = t
                                break
                        if owner:
                            break

                    if owner:
                        sold_to_user = (owner.team_id == user_team_id)
                        if sold_to_user:
                            print(f"\n>>> {name} ({role}) SOLD to you for {final_price}")
                        else:
                            print(f"\n>>> {name} ({role}) sold to {owner.name} for {final_price}")
                    else:
                        # unsold -> prompt user (respect skip settings)
                        print(f"\n>>> {name} ({role}) went UNSOLD at price {final_price}")
                        skip_for_role = (role in skip_roles)
                        skip_for_price = (price_skip > 0 and final_price is not None and final_price > price_skip)
                        if skip_for_role:
                            print(f"Skipping prompt because role '{role}' is in your skip list.")
                        elif skip_for_price:
                            print(f"Skipping prompt because price {final_price} > your price threshold {price_skip}.")
                        else:
                            want = input_yes_no(f"Do you want to buy {name} for {final_price}? ")
                            if want:
                                # check budget
                                if user_team.remaining_purse >= (final_price or 0):
                                    # Assign to user team
                                    # Create a shallow copy of player dict and set price
                                    player_copy = dict(prev_player)
                                    player_copy["price"] = final_price
                                    user_team.players.append(player_copy)
                                    user_team.remaining_purse -= (final_price or 0)
                                    user_team.total_buys = getattr(user_team, "total_buys", 0) + 1
                                    print(f"You bought {name} for {final_price}. Remaining purse: {user_team.remaining_purse:.1f}")
                                else:
                                    print("You do not have enough purse to buy this player.")
                    print("-" * 80)

                # update prev index
                prev_player_idx = curr_player_idx
            # loop continues

        # Auction done - final summary
        print("\nAuction finished. Final rosters:\n")
        for team in env.teams:
            print(f"Team: {team.name}  (id={team.team_id})  purse={team.remaining_purse:.1f}  buys={getattr(team,'total_buys',0)}")
            for p in getattr(team, "players", []):
                print(f"   {p.get('name','?')[:30]:30s}  {p.get('role',''):5s}  Price={p.get('price',0):6.1f}")
            print("-" * 60)

        print("\nYour team summary:")
        print(f"{user_team.name}  purse={user_team.remaining_purse:.1f}  total_buys={getattr(user_team,'total_buys',0)}")
        for p in getattr(user_team, "players", []):
            print(f"  {p.get('name','')[:30]:30s} {p.get('role',''):5s} Price={p.get('price',0):6.1f}")
        print("\nThanks for playing!")

    except KeyboardInterrupt:
        print("\n\n[Interrupted] Exiting. Showing your team purchases so far...\n")
        try:
            print(f"{user_team.name}  purse={user_team.remaining_purse:.1f}  total_buys={getattr(user_team,'total_buys',0)}")
            for p in getattr(user_team, "players", []):
                print(f"  {p.get('name','')[:30]:30s} {p.get('role',''):5s} Price={p.get('price',0):6.1f}")
        except Exception:
            pass
    except Exception:
        traceback.print_exc()
        print("Error occurred. Exiting.")

if __name__ == "__main__":
    main()