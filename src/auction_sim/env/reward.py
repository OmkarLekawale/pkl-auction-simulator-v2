def get_reward(buyer, player, score_delta, price):
    b_price = player.base_price
    total_buys = buyer.total_buys
    C = (price / b_price - 1) * (0.5 if b_price >= 50 else 0.4)
    factor = min(C, 1)
    reduce = price * factor
    reward = (score_delta - reduce) / 100
    return reward 