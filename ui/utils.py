from numpy.random import randint, shuffle
import numpy as np

# Returns a random boolean array of size 'size'
# Used to randomly alternate between real and modified images in the comprehension check
def random_bool_array(size):
    return np.array(randint(0, 2, size), dtype=bool)


def shuffled_bool_array(size):
    # Create a boolean array of size 'size' with half True and half False
    boolean_array = np.array(
        [True] * int(size / 2) + [False] * int(size / 2), dtype=bool
    )
    return shuffle(boolean_array)

def subsampling(pids, sample_size, number_of_sets, seed=0):
    # The binomial coefficient of C(75, 60) is too high for practical assessments
    # Therefore, we will use a subsampling method to reduce the number of possible combinations
    # We will take a sample of 60 images from the 75 available images
    # We will repeat this process 'number_of_sets' times

    # Create a list to store the subsampled data
    subsampled_data = []

    # Set the seed for reproducibility
    rng = np.random.default_rng(seed)

    for _ in range(number_of_sets):
        # Randomly select 60 indices from the list of indices
        subsample = rng.choice(pids, sample_size, replace=False)
        # Append the selected indices to the subsampled data
        subsampled_data.append(subsample)

    return subsampled_data

def long_string(ratings, sequences=None):
    if sequences is None:
        sequences = {}
    current_val = ratings[0]
    current_count = 1
    for i in range(1, len(ratings)):
        if ratings[i] == current_val:
            current_count += 1
        else:
            if current_count not in sequences and current_count > 1:
                sequences[current_count] = 1
            elif current_count > 1:
                sequences[current_count] += 1
            
            current_val = ratings[i]
            current_count = 1
    
    seq_lengths = []
    for key in sequences.keys():
        seq_lengths += [key] * sequences[key]

    
    return sequences, max(seq_lengths), np.mean(seq_lengths), np.median(seq_lengths)



# Draw a chart of the distribution of sequence lengths
def draw_chart(sequences, mean_length, median_length, save=False, previous_means=None):
    import matplotlib.pyplot as plt
    import seaborn as sns
    sns.set(style="whitegrid")
    plt.figure(figsize=(12, 6))
    plt.title("Distribution of sequence lengths")
    plt.xlabel("Sequence length")
    plt.ylabel("Frequency")
    sns.lineplot(x=list(sequences.keys()), y=list(sequences.values()))
    plt.axvline(mean_length, color='r', linestyle='--', label=f'Mean: {mean_length:.2f}')
    if previous_means is not None:
        # Define colors for the previous means
        colors = ['b', 'y', 'm', 'c']
        i = 0
        for attack in previous_means:
            plt.axvline(previous_means[attack], color=colors[i], linestyle='--', label=f'{attack}: {previous_means[attack]:.2f}')
            i += 1
        #plt.axvline(previous_mean, color='b', linestyle='--', label=f'Previous Mean: {previous_mean:.2f}')
    plt.axvline(median_length, color='g', linestyle='--', label=f'Median: {median_length:.2f}')
    plt.legend()
    if save:
        plt.savefig("sequence_lengths.png")
    else:
        plt.show()


def accumulate_ls_stats(pids):
    from data_processing import get_main_study_ratings
    sequences = {}
    for pid in pids:
        ratings = get_main_study_ratings(pid)
        sequences, _, mean_seq_length, median_seq_length = long_string(ratings, sequences)
    
    draw_chart(sequences, mean_seq_length, median_seq_length)
    print(sequences)
    print(mean_seq_length)
    print(median_seq_length)


if __name__ == "__main__":
    """pids = [
        "65fbd90b219c311ec4ef8040",
        "65635d1d39993ffa840e7e00",
        "66945ed6eccf6e78ece68276",
        "6597e98b074e8eaf09525214",
        "5fdac6ef252afc58740d5560",
        "666efc01519a8d810a4c3ca0",
        "668c102e1bbf383ee009e868"
    ]"""
    dir = "/home/dren.fazlija/data/Scooter/pids/"

    with open(dir + "pids.txt", "r") as file:
        pids = file.readlines()
        pids = [pid.strip() for pid in pids]
    
    accumulate_ls_stats(pids)