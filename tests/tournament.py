import random

team1_offense, team1_defense = 500, 250
team2_offense, team2_defense = 450, 350

team1_point_count, team2_point_count = 0, 0 

# team1 raiding
for _ in range(40):
    if random.randint(0, 10) < 3:
        continue
    number = random.randint(1, team1_offense + team2_defense)
    if number <= team1_offense:
        team1_point_count += 1
    else:
        team2_point_count += 1

print(team1_point_count, team2_point_count)
# team2 raiding
for _ in range(40):
    if random.randint(0, 10) < 3:
        continue
    number = random.randint(1, team2_offense + team1_defense)
    if number <= team2_offense:
        team2_point_count += 1
    else:
        team1_point_count += 1

print(team1_point_count, team2_point_count)