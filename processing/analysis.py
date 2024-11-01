import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
import seaborn as sns
from dataclasses import dataclass

@dataclass
class ParticipantStats:
    user_id: str
    total_trials: int
    correct_black: int
    total_black: int
    correct_red: int
    total_red: int
    avg_rt_fast: float
    avg_rt_slow: float
    correct_fast: int
    total_fast: int
    correct_slow: int
    total_slow: int

def safe_divide(numerator: int, denominator: int) -> str:
    """Safely calculate percentage, handling division by zero."""
    if denominator == 0:
        return "N/A"
    return f"{(numerator/denominator*100):.1f}%"

def format_rt(rt: float) -> str:
    """Format response time, handling NaN values."""
    if pd.isna(rt):
        return "N/A"
    return f"{rt:.3f}s"

def calculate_participant_stats(df: pd.DataFrame) -> Dict[str, ParticipantStats]:
    """Calculate statistics for each participant."""
    stats = {}
    
    for user_id in df['user_id'].unique():
        user_data = df[df['user_id'] == user_id]
        
        # Calculate color-based stats
        black_trials = user_data[user_data['arrow_color'] == 'black']
        red_trials = user_data[user_data['arrow_color'] == 'red']
        
        # Calculate speed-based stats
        fast_trials = user_data[user_data['speed_group'].str.contains('Fast')]
        slow_trials = user_data[user_data['speed_group'].str.contains('Slow')]
        
        stats[user_id] = ParticipantStats(
            user_id=user_id,
            total_trials=len(user_data),
            correct_black=len(black_trials[black_trials['is_correct']]),
            total_black=len(black_trials),
            correct_red=len(red_trials[red_trials['is_correct']]),
            total_red=len(red_trials),
            avg_rt_fast=fast_trials['response_time'].mean(),
            avg_rt_slow=slow_trials['response_time'].mean(),
            correct_fast=len(fast_trials[fast_trials['is_correct']]),
            total_fast=len(fast_trials),
            correct_slow=len(slow_trials[slow_trials['is_correct']]),
            total_slow=len(slow_trials)
        )
    
    return stats

def create_comparison_visualization(stats: Dict[str, ParticipantStats]) -> None:
    """Create a visualization comparing fast vs slow performance."""
    # Prepare data for plotting
    plot_data = []
    
    for stat in stats.values():
        # Only include data points where trials exist
        if stat.total_fast > 0:
            plot_data.append({
                'user_id': stat.user_id,
                'Speed': 'Fast',
                'Accuracy (%)': (stat.correct_fast / stat.total_fast * 100)
            })
        if stat.total_slow > 0:
            plot_data.append({
                'user_id': stat.user_id,
                'Speed': 'Slow',
                'Accuracy (%)': (stat.correct_slow / stat.total_slow * 100)
            })
    
    plot_data = pd.DataFrame(plot_data)
    
    if len(plot_data) == 0:
        print("Warning: No data available for visualization")
        return
    
    # Create the visualization
    plt.figure(figsize=(10, 6))
    sns.set_style("whitegrid")
    
    # Create box plot with individual points
    sns.boxplot(data=plot_data, x='Speed', y='Accuracy (%)', color='lightgray')
    sns.swarmplot(data=plot_data, x='Speed', y='Accuracy (%)', color='darkblue', size=8)
    
    # Customize the plot
    plt.title('Accuracy Comparison: Fast vs Slow Display Times', pad=20)
    plt.ylabel('Accuracy (%)')
    
    # Add mean lines for each condition
    means = plot_data.groupby('Speed')['Accuracy (%)'].mean()
    for i, speed in enumerate(means.index):
        plt.hlines(means[speed], i-0.3, i+0.3, color='red', linestyles='dashed', label='Mean' if i == 0 else '')
    
    plt.legend()
    plt.tight_layout()

def create_accuracy_trend_visualization(df: pd.DataFrame) -> None:
    """Create a line plot showing accuracy trends over days for each participant."""
    # Calculate daily accuracy for each participant
    daily_accuracy = df.groupby(['user_id', 'day']).agg({
        'is_correct': ['count', 'sum']
    }).reset_index()
    
    # Calculate accuracy percentage
    daily_accuracy.columns = ['user_id', 'day', 'total_trials', 'correct_trials']
    daily_accuracy['accuracy'] = (daily_accuracy['correct_trials'] / 
                                daily_accuracy['total_trials'] * 100)
    
    # Create the visualization
    plt.figure(figsize=(12, 6))
    sns.set_style("whitegrid")
    
    # Create line plot
    sns.lineplot(data=daily_accuracy, x='day', y='accuracy', 
                hue='user_id', marker='o', markersize=8)
    
    # Customize the plot
    plt.title('Accuracy Trends Over Time by Participant', pad=20)
    plt.xlabel('Day')
    plt.ylabel('Accuracy (%)')
    
    # Adjust x-axis to show only integer days
    plt.xticks(sorted(daily_accuracy['day'].unique()))
    
    # Add legend with a title
    plt.legend(title='Participant ID', bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # Ensure no labels are cut off
    plt.tight_layout()

def main():
    # Load and process data
    df = pd.read_csv('processed_data.csv')
    
    # Calculate statistics
    participant_stats = calculate_participant_stats(df)
    
    # Print summary statistics
    print("\nParticipant Summary Statistics:")
    print("-" * 80)
    for user_id, stats in participant_stats.items():
        print(f"\nUser ID: {user_id}")
        print(f"Total trials: {stats.total_trials}")
        print(f"Black arrows: {stats.correct_black}/{stats.total_black} correct ({safe_divide(stats.correct_black, stats.total_black)})")
        print(f"Red arrows: {stats.correct_red}/{stats.total_red} correct ({safe_divide(stats.correct_red, stats.total_red)})")
        print(f"Average response time (Fast): {format_rt(stats.avg_rt_fast)}")
        print(f"Average response time (Slow): {format_rt(stats.avg_rt_slow)}")
        print(f"Fast trials: {stats.correct_fast}/{stats.total_fast} correct ({safe_divide(stats.correct_fast, stats.total_fast)})")
        print(f"Slow trials: {stats.correct_slow}/{stats.total_slow} correct ({safe_divide(stats.correct_slow, stats.total_slow)})")
    
    # Create and save fast vs slow comparison visualization
    create_comparison_visualization(participant_stats)
    plt.savefig('accuracy_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Create and save accuracy trend visualization
    create_accuracy_trend_visualization(df)
    plt.savefig('accuracy_trend.png', dpi=300, bbox_inches='tight')
    plt.close()

if __name__ == "__main__":
    main()