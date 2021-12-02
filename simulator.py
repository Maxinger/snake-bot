from collections import Counter
from scipy.stats import binom_test
from tqdm import tqdm

from src.importsTools import import_bot
from playGame import play_one_game


def play(bot1, bot2, n_games):
    wins = [0, 0]
    scores = [0, 0]
    descriptions = Counter()
    for _ in tqdm(range(n_games)):
        result = play_one_game(bot1, bot2)
        for i in range(2):
            wins[i] += result['metadata']['result'][i]
            scores[i] += result['metadata']['score'][i]
        descriptions.update({result['metadata']['description']: 1})
    n_wins = sum(wins)
    print(f'Total games: {n_games}')
    print(f'Results: +{wins[0]}={n_games - n_wins}-{wins[1]} ({int(wins[0] / n_wins * 100)}%)')
    print('Average score: {:.1f}:{:.1f}'.format(scores[0] / n_games, scores[1] / n_games))
    print('P-value: {:.3f}'.format(binom_test(max(wins), n_wins, alternative='greater')))

    for desc in descriptions.most_common():
        print(f'{desc[1]}: {desc[0]}')


new_bot = import_bot('estimate_bot.py', 'estimate1')
baseline_bot = import_bot('random_bot.py', 'random')

play(new_bot, baseline_bot, 100)
