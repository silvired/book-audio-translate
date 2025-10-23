#!/usr/bin/env python3
"""
Script to visualize translation evaluation results as a grouped bar chart.
Reads from translation_evaluations.csv and saves the chart to a file.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys
import os


def create_evaluation_chart(csv_path, output_path='evaluation_chart.png'):
    """
    Create a grouped bar chart from translation evaluation CSV.
    
    Args:
        csv_path: Path to the CSV file containing evaluation data
        output_path: Path to save the output chart image
    """
    # Read the CSV file
    df = pd.read_csv(csv_path)
    
    # Extract model names and criteria
    model_names = df['model_name'].tolist()
    criteria = df.columns[1:].tolist()  # All columns except model_name
    
    # Set up the plot
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Set the width of bars and positions
    x = np.arange(len(criteria))
    width = 0.08  # Width of each bar
    n_models = len(model_names)
    
    # Calculate offset for centering the groups
    offset = width * (n_models - 1) / 2
    
    # Color palette - use a color map for distinct colors
    colors = plt.cm.tab20(np.linspace(0, 1, n_models))
    
    # Create bars for each model
    bars_list = []
    for i, model in enumerate(model_names):
        values = df.iloc[i, 1:].values  # Get values for all criteria
        position = x - offset + (i * width)
        bars = ax.bar(position, values, width, label=model, color=colors[i], 
                     edgecolor='black', linewidth=0.5)
        bars_list.append(bars)
    
    # Customize the chart
    ax.set_xlabel('Evaluation Criteria', fontsize=12, fontweight='bold')
    ax.set_ylabel('Score', fontsize=12, fontweight='bold')
    ax.set_title('Translation Model Evaluation Comparison', fontsize=14, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(criteria, rotation=15, ha='right', fontsize=9)
    ax.set_ylim(0, 5.5)  # Set y-axis limit slightly above max score
    ax.set_yticks(np.arange(0, 6, 0.5))
    ax.grid(axis='y', alpha=0.3, linestyle='--', linewidth=0.5)
    ax.legend(loc='upper left', bbox_to_anchor=(1, 1), fontsize=8, ncol=1)
    
    # Add value labels on top of bars (optional - can be removed if cluttered)
    for bars in bars_list:
        for bar in bars:
            height = bar.get_height()
            if height > 0:  # Only add label if there's a value
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.1f}',
                       ha='center', va='bottom', fontsize=6, rotation=0)
    
    # Adjust layout to prevent label cutoff
    plt.tight_layout()
    
    # Save the figure
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Chart saved to: {output_path}")
    
    # Display the chart (optional - comment out if running in headless environment)
    # plt.show()
    
    plt.close()


def create_evaluation_chart_by_model(csv_path, output_path='evaluation_chart_by_model.png'):
    """
    Create a grouped bar chart from translation evaluation CSV, grouped by model.
    
    Args:
        csv_path: Path to the CSV file containing evaluation data
        output_path: Path to save the output chart image
    """
    # Read the CSV file
    df = pd.read_csv(csv_path)
    
    # Extract model names and criteria
    model_names = df['model_name'].tolist()
    criteria = df.columns[1:].tolist()  # All columns except model_name
    
    # Set up the plot
    fig, ax = plt.subplots(figsize=(16, 8))
    
    # Set the width of bars and positions
    x = np.arange(len(model_names))
    width = 0.15  # Width of each bar
    n_criteria = len(criteria)
    
    # Calculate offset for centering the groups
    offset = width * (n_criteria - 1) / 2
    
    # Color palette - use a color map for distinct colors
    colors = plt.cm.Set3(np.linspace(0, 1, n_criteria))
    
    # Create bars for each criterion
    bars_list = []
    for i, criterion in enumerate(criteria):
        values = df[criterion].values  # Get values for all models
        position = x - offset + (i * width)
        bars = ax.bar(position, values, width, label=criterion, color=colors[i], 
                     edgecolor='black', linewidth=0.5)
        bars_list.append(bars)
    
    # Customize the chart
    ax.set_xlabel('Model', fontsize=12, fontweight='bold')
    ax.set_ylabel('Score', fontsize=12, fontweight='bold')
    ax.set_title('Translation Model Evaluation Comparison (Grouped by Model)', 
                 fontsize=14, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(model_names, rotation=45, ha='right', fontsize=9)
    ax.set_ylim(0, 5.5)  # Set y-axis limit slightly above max score
    ax.set_yticks(np.arange(0, 6, 0.5))
    ax.grid(axis='y', alpha=0.3, linestyle='--', linewidth=0.5)
    ax.legend(loc='upper left', bbox_to_anchor=(1, 1), fontsize=9, ncol=1)
    
    # Add value labels on top of bars (optional - can be removed if cluttered)
    for bars in bars_list:
        for bar in bars:
            height = bar.get_height()
            if height > 0:  # Only add label if there's a value
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.1f}',
                       ha='center', va='bottom', fontsize=6, rotation=0)
    
    # Adjust layout to prevent label cutoff
    plt.tight_layout()
    
    # Save the figure
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Chart (grouped by model) saved to: {output_path}")
    
    plt.close()


def create_average_score_chart(csv_path, output_path='evaluation_chart_average.png'):
    """
    Create a bar chart showing average score per model.
    
    Args:
        csv_path: Path to the CSV file containing evaluation data
        output_path: Path to save the output chart image
    """
    # Read the CSV file
    df = pd.read_csv(csv_path)
    
    # Calculate average score for each model
    model_names = df['model_name'].tolist()
    avg_scores = df.iloc[:, 1:].mean(axis=1).values
    
    # Sort by average score (descending)
    sorted_indices = np.argsort(avg_scores)[::-1]
    model_names_sorted = [model_names[i] for i in sorted_indices]
    avg_scores_sorted = avg_scores[sorted_indices]
    
    # Set up the plot
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Create color gradient based on scores
    colors = plt.cm.RdYlGn(avg_scores_sorted / 5.0)  # Normalize to 0-1
    
    # Create bars
    bars = ax.bar(range(len(model_names_sorted)), avg_scores_sorted, 
                  color=colors, edgecolor='black', linewidth=1.5, width=0.7)
    
    # Customize the chart
    ax.set_xlabel('Model', fontsize=12, fontweight='bold')
    ax.set_ylabel('Average Score', fontsize=12, fontweight='bold')
    ax.set_title('Average Translation Quality Score per Model', 
                 fontsize=14, fontweight='bold', pad=20)
    ax.set_xticks(range(len(model_names_sorted)))
    ax.set_xticklabels(model_names_sorted, rotation=45, ha='right', fontsize=10)
    ax.set_ylim(0, 5.5)
    ax.set_yticks(np.arange(0, 6, 0.5))
    ax.grid(axis='y', alpha=0.3, linestyle='--', linewidth=0.5)
    
    # Add value labels on top of bars
    for i, (bar, score) in enumerate(zip(bars, avg_scores_sorted)):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
               f'{score:.2f}',
               ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    # Add a horizontal line for the overall average
    overall_avg = avg_scores.mean()
    ax.axhline(y=overall_avg, color='red', linestyle='--', linewidth=2, 
               label=f'Overall Average: {overall_avg:.2f}', alpha=0.7)
    ax.legend(loc='lower left', fontsize=10)
    
    # Adjust layout to prevent label cutoff
    plt.tight_layout()
    
    # Save the figure
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Chart (average scores) saved to: {output_path}")
    
    plt.close()


def main():
    """Main function to handle command line arguments."""
    # Default paths
    default_csv = 'translation_evaluations.csv'
    default_output_criteria = 'evaluation_chart_by_criteria.png'
    default_output_model = 'evaluation_chart_by_model.png'
    default_output_average = 'evaluation_chart_average.png'
    
    # Check if CSV path is provided as argument
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
    else:
        csv_path = default_csv
    
    # Check if output paths are provided as arguments
    if len(sys.argv) > 2:
        output_path_criteria = sys.argv[2]
    else:
        output_path_criteria = default_output_criteria
    
    if len(sys.argv) > 3:
        output_path_model = sys.argv[3]
    else:
        output_path_model = default_output_model
    
    if len(sys.argv) > 4:
        output_path_average = sys.argv[4]
    else:
        output_path_average = default_output_average
    
    # Check if CSV file exists
    if not os.path.exists(csv_path):
        print(f"Error: CSV file '{csv_path}' not found.")
        print(f"Usage: python {sys.argv[0]} [csv_path] [output_by_criteria] [output_by_model] [output_average]")
        sys.exit(1)
    
    # Create all three charts
    print("Generating charts...")
    create_evaluation_chart(csv_path, output_path_criteria)
    create_evaluation_chart_by_model(csv_path, output_path_model)
    create_average_score_chart(csv_path, output_path_average)
    
    # Print summary statistics
    df = pd.read_csv(csv_path)
    print("\n=== Summary Statistics ===")
    print(f"Number of models evaluated: {len(df)}")
    print(f"Number of criteria: {len(df.columns) - 1}")
    print("\nAverage score per model:")
    for idx, row in df.iterrows():
        avg_score = row[1:].mean()
        print(f"  {row['model_name']}: {avg_score:.2f}")
    
    print("\nAverage score per criterion:")
    for col in df.columns[1:]:
        avg_score = df[col].mean()
        print(f"  {col}: {avg_score:.2f}")


if __name__ == '__main__':
    main()
