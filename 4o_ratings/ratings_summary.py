import numpy as np
import json
import argparse


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--attack_name", type=str, required=True, choices=["aca", "advpp", "cadv", "cadv_4_6", "diffattack", "ncf", "semanticadv", "real"])
    args = parser.parse_args()

    with open(f"{args.attack_name}.json", 'r') as file:
        data = json.load(file)

    ratings = []


    for item in data:
        ratings.append(int(data[item]))
    ratings = np.array(ratings)

    # Calculate the mean and standard deviation
    mean = np.mean(ratings)
    std_dev = np.std(ratings)
    # Calculate the number of ratings
    num_ratings = len(ratings)
    # Calculate the number of positive ratings
    num_positive_ratings = np.sum(ratings > 0)
    # Calculate the number of negative ratings
    num_negative_ratings = np.sum(ratings < 0)
    # Calculate the number of neutral ratings
    num_neutral_ratings = np.sum(ratings == 0)


    print(f"\n{'='*50}")
    print(f"RATINGS SUMMARY - {args.attack_name.upper()}")
    print(f"{'='*50}")
    
    print(f"\n📊 BASIC STATISTICS:")
    print(f"   Mean Rating:     {mean:.3f}")
    print(f"   Std Deviation:   {std_dev:.3f}")
    print(f"   Total Ratings:   {num_ratings}")

    
    # Calculate the percentage of positive ratings
    percentage_positive = (num_positive_ratings / num_ratings) * 100
    # Calculate the percentage of negative ratings
    percentage_negative = (num_negative_ratings / num_ratings) * 100
    # Calculate the percentage of neutral ratings
    percentage_neutral = (num_neutral_ratings / num_ratings) * 100

    print(f"\n📊 RATING DISTRIBUTION:")
    print(f"   Positive (+1/+2): {num_positive_ratings:>3} ({percentage_positive:>5.1f}%)")
    print(f"   Negative (-1/-2): {num_negative_ratings:>3} ({percentage_negative:>5.1f}%)")
    print(f"   Neutral (0):      {num_neutral_ratings:>3} ({percentage_neutral:>5.1f}%)")

    # Calculate the accuracy of the ratings
    if args.attack_name == "real":
        accuracy = (num_positive_ratings) / num_ratings
        accuracy_type = "Positive Rate"
    else:
        accuracy = (num_negative_ratings) / num_ratings
        accuracy_type = "Negative Rate"

    print(f"\n🎯 {accuracy_type}: {accuracy:.1%}")
    print(f"{'='*50}\n")



