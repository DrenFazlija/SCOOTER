import pandas as pd
import argparse


def load_data(file_path):
    data = pd.read_csv(file_path)
    return data

def get_scooter_metrics(attack_name):
    file_path = f"anonymized_{attack_name}_with_image_ids.csv"
    df = load_data(file_path)
    
    # Calculate metrics for modified images
    modified_ratings = df[df['image_type'] == 'modified']['rating']
    modified_mean = modified_ratings.mean()
    modified_std = modified_ratings.std()
    
    # Calculate metrics for real images
    real_ratings = df[df['image_type'] == 'real']['rating']
    real_mean = real_ratings.mean()
    real_std = real_ratings.std()
    
    # Create results dictionary
    metrics = {
        'modified': {
            'mean': modified_mean,
            'std': modified_std,
            'count': len(modified_ratings)
        },
        'real': {
            'mean': real_mean,
            'std': real_std,
            'count': len(real_ratings)
        }
    }
    
    return metrics

    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Calculate scooter metrics')
    parser.add_argument('--attack_name', type=str, required=True, help='Name of the attack', choices=['aca', 'advpp', 'cadv', 'cadv_4_6', 'diffattack', 'ncf', 'semanticadv'])
    args = parser.parse_args()
    
    attack_name = args.attack_name
    metrics = get_scooter_metrics(attack_name)
    
    print(f"\n{'='*50}")
    print(f"SCOOTER METRICS - {attack_name.upper()}")
    print(f"{'='*50}")
    
    print(f"\n📊 MODIFIED IMAGES:")
    print(f"   Mean Rating: {metrics['modified']['mean']:.3f}")
    print(f"   Std Dev:     {metrics['modified']['std']:.3f}")
    print(f"   Count:       {metrics['modified']['count']}")
    
    print(f"\n📊 REAL IMAGES:")
    print(f"   Mean Rating: {metrics['real']['mean']:.3f}")
    print(f"   Std Dev:     {metrics['real']['std']:.3f}")
    print(f"   Count:       {metrics['real']['count']}")
    
    print(f"\n{'='*50}")
    print(f"Total Samples: {metrics['modified']['count'] + metrics['real']['count']}")
    print(f"{'='*50}\n")