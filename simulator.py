from scipy.stats import binom_test

from src.importsTools import import_bot

from playGame import play_one_game


def play(bot1, bot2, n_games):
    wins = [0, 0]
    scores = [0, 0]
    for g in range(n_games):
        result = play_one_game(bot1, bot2)
        wins[result['metadata']['winner'] - 1] += 1
        scores[0] += result['metadata']['score'][0]
        scores[1] += result['metadata']['score'][1]
    print(f'Total games: {n_games}')
    print(f'Wins: {wins[0]}:{wins[1]} ({int(wins[0] / n_games * 100)}%)')
    print(f'Score: {scores[0]}:{scores[1]}')
    print('P-value: {:.3f}'.format(binom_test(wins[0], n_games)))


random_bot1 = import_bot('random_bot.py', 'random1')
random_bot2 = import_bot('random_bot.py', 'random2')

play(random_bot1, random_bot2, 100)
