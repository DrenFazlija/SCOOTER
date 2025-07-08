import numpy as np
import pandas as pd

def dummy_data(seed):
    np.random.seed(seed)

    names = ['Alice', 'Bob', 'Charlie', 'David', 'Eve', 'Frank', 'Grace', 'Hannah', 'Ivy', 'Jack']

    scores = []

    for i in range(10):
        entry = []
        entry.append(names[i])

        real_correct = np.random.randint(0, 51)
        fake_correct = np.random.randint(0, 51)
        total_correct = real_correct + fake_correct

        entry.append(total_correct)
        entry.append((real_correct / 50) * 100)
        entry.append((fake_correct / 50) * 100)

        check_performance = np.random.randint(0, 7)
        entry.append((check_performance / 6) * 100)

        scores.append(entry)

    return scores

def get_leaderboard(data):
    # Create DataFrame
    df = pd.DataFrame(data, columns=['User', 'Total Accuracy', 'Accuracy on Real Images', 'Accuracy on Modified Images', 'Attention Check Accuracy'])

    # Rank the users within each category
    for category in df.columns[1:]:
        df[f'Rank_{category}'] = df[category].rank(ascending=True, na_option='bottom', method='dense')

    # Calculate Borda score for each user
    df['Borda_Score'] = df.filter(like='Rank_').sum(axis=1)

    # Sort by Borda score
    df = df.sort_values(by='Borda_Score', ascending=False)

    df_output = df[['User', 'Total Accuracy', 'Accuracy on Real Images', 'Accuracy on Modified Images', 'Attention Check Accuracy', 'Borda_Score']]

    print(df_output)

data = dummy_data(0)
get_leaderboard(data)