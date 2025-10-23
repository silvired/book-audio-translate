"""
Script to plot input vs output token ratio from CSV data.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Constants
INPUT_FILE = "gemini_token_ratio_thinking.csv"


def plot_token_ratio(csv_file):
    """
    Plot input tokens vs output tokens from a CSV file.
    If a 'thinking_tokens' column exists, it will also be plotted.
    
    Creates 2 or 3 subplots:
    1. Input vs Output/Thinking Tokens (scatter plot)
    2. Input Tokens vs Output/Input Ratio
    3. Input Tokens vs Thinking/Input Ratio (only if thinking tokens exist)
    
    Args:
        csv_file (str): Path to the CSV file containing input_tokens, output_tokens, 
                       and optionally thinking_tokens columns
    """
    # Read the CSV file
    df = pd.read_csv(csv_file)
    
    # Extract data
    input_tokens = df['input_tokens'].values
    output_tokens = df['output_tokens'].values
    
    # Check if thinking tokens column exists
    has_thinking = 'thinking_tokens' in df.columns or 'thinking_token' in df.columns or 'thinking token' in df.columns
    if 'thinking_tokens' in df.columns:
        thinking_col = 'thinking_tokens'
    elif 'thinking_token' in df.columns:
        thinking_col = 'thinking_token'
    else:
        thinking_col = 'thinking token'
    
    if has_thinking:
        thinking_tokens = df[thinking_col].values
        # If all thinking tokens are 0, treat as if column doesn't exist
        if np.all(thinking_tokens == 0):
            has_thinking = False
            print("Note: Thinking token column exists but all values are 0. Plotting only output tokens.")
    
    # Calculate the ratios for each point
    output_ratios = output_tokens / input_tokens
    avg_output_ratio = np.mean(output_ratios)
    
    if has_thinking:
        thinking_ratios = thinking_tokens / input_tokens
        avg_thinking_ratio = np.mean(thinking_ratios)
    
    # Create the plot with three subplots if thinking tokens exist, otherwise two
    if has_thinking:
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(24, 7))
    else:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
    
    # ========================= FIRST PLOT: Input vs Output/Thinking Tokens =========================
    # Scatter plot for output tokens
    ax1.scatter(input_tokens, output_tokens, s=100, alpha=0.7, color='blue', 
              edgecolors='black', linewidth=1.5, label='Output Tokens', marker='o')
    
    # Scatter plot for thinking tokens (if exists)
    if has_thinking:
        ax1.scatter(input_tokens, thinking_tokens, s=100, alpha=0.7, color='orange', 
                  edgecolors='black', linewidth=1.5, label='Thinking Tokens', marker='s')
    
    # Add trend line for output tokens
    z_output = np.polyfit(input_tokens, output_tokens, 1)
    p_output = np.poly1d(z_output)
    x_trend = np.linspace(input_tokens.min(), input_tokens.max(), 100)
    ax1.plot(x_trend, p_output(x_trend), "--", alpha=0.8, linewidth=2, color='blue',
           label=f'Output trend (slope={z_output[0]:.3f})')
    
    # Add trend line for thinking tokens (if exists)
    if has_thinking:
        z_thinking = np.polyfit(input_tokens, thinking_tokens, 1)
        p_thinking = np.poly1d(z_thinking)
        ax1.plot(x_trend, p_thinking(x_trend), "--", alpha=0.8, linewidth=2, color='orange',
               label=f'Thinking trend (slope={z_thinking[0]:.3f})')
    
    # Add reference line showing the average ratio for output
    ax1.plot(x_trend, x_trend * avg_output_ratio, ":", alpha=0.5, linewidth=2, color='blue',
           label=f'Output avg ratio ({avg_output_ratio:.3f})')
    
    # Add reference line for thinking tokens (if exists)
    if has_thinking:
        ax1.plot(x_trend, x_trend * avg_thinking_ratio, ":", alpha=0.5, linewidth=2, color='orange',
               label=f'Thinking avg ratio ({avg_thinking_ratio:.3f})')
    
    # Labels and title
    ax1.set_xlabel('Input Tokens', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Tokens', fontsize=12, fontweight='bold')
    title = 'Input vs Output Tokens'
    if has_thinking:
        title += ' (with Thinking Tokens)'
    ax1.set_title(title, fontsize=14, fontweight='bold')
    
    # Add grid
    ax1.grid(True, alpha=0.3, linestyle='--')
    
    # Add legend
    ax1.legend(loc='upper left', fontsize=9)
    
    # Add annotations for each point (output tokens)
    for i, (x, y, ratio) in enumerate(zip(input_tokens, output_tokens, output_ratios)):
        y_offset = 10 if not has_thinking else 20
        ax1.annotate(f'{y}', 
                   xy=(x, y), 
                   xytext=(5, y_offset), 
                   textcoords='offset points',
                   fontsize=8,
                   alpha=0.7,
                   color='blue',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='lightblue', alpha=0.5))
    
    # Add annotations for thinking tokens (if exists)
    if has_thinking:
        for i, (x, y, ratio) in enumerate(zip(input_tokens, thinking_tokens, thinking_ratios)):
            ax1.annotate(f'{y}', 
                       xy=(x, y), 
                       xytext=(5, -25), 
                       textcoords='offset points',
                       fontsize=8,
                       alpha=0.7,
                       color='orange',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='lightyellow', alpha=0.5))
    
    # Add statistics text box
    stats_text = f'Data Points: {len(input_tokens)}\n'
    stats_text += f'\nOutput Tokens:\n'
    stats_text += f'  Avg Ratio: {avg_output_ratio:.3f}\n'
    stats_text += f'  Min Ratio: {output_ratios.min():.3f}\n'
    stats_text += f'  Max Ratio: {output_ratios.max():.3f}'
    
    if has_thinking:
        stats_text += f'\n\nThinking Tokens:\n'
        stats_text += f'  Avg Ratio: {avg_thinking_ratio:.3f}\n'
        stats_text += f'  Min Ratio: {thinking_ratios.min():.3f}\n'
        stats_text += f'  Max Ratio: {thinking_ratios.max():.3f}'
    
    ax1.text(0.98, 0.02, stats_text, 
           transform=ax1.transAxes,
           fontsize=9,
           verticalalignment='bottom',
           horizontalalignment='right',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.6))
    
    # ========================= SECOND PLOT: Input Tokens vs Output/Input Ratio =========================
    # Scatter plot for output ratio
    ax2.scatter(input_tokens, output_ratios, s=100, alpha=0.7, color='green', 
              edgecolors='black', linewidth=1.5, label='Output/Input Ratio', marker='o')
    
    # Add horizontal line for average output ratio
    ax2.axhline(y=avg_output_ratio, color='green', linestyle='--', linewidth=2, 
               alpha=0.7, label=f'Avg output ratio ({avg_output_ratio:.3f})')
    
    # Add trend line for output ratio
    z_ratio = np.polyfit(input_tokens, output_ratios, 1)
    p_ratio = np.poly1d(z_ratio)
    ax2.plot(x_trend, p_ratio(x_trend), ":", alpha=0.6, linewidth=2, color='green',
           label=f'Ratio trend (slope={z_ratio[0]:.6f})')
    
    # Labels and title
    ax2.set_xlabel('Input Tokens', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Output/Input Ratio', fontsize=12, fontweight='bold')
    ax2.set_title('Input Tokens vs Output/Input Ratio', fontsize=14, fontweight='bold')
    
    # Add grid
    ax2.grid(True, alpha=0.3, linestyle='--')
    
    # Add legend
    ax2.legend(loc='best', fontsize=9)
    
    # Add annotations for each ratio point
    for i, (x, ratio) in enumerate(zip(input_tokens, output_ratios)):
        ax2.annotate(f'{ratio:.3f}', 
                   xy=(x, ratio), 
                   xytext=(5, 10), 
                   textcoords='offset points',
                   fontsize=8,
                   alpha=0.7,
                   color='green',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgreen', alpha=0.5))
    
    # Add statistics text box for ratios
    ratio_stats = f'Output Ratio Stats:\n'
    ratio_stats += f'  Mean: {avg_output_ratio:.4f}\n'
    ratio_stats += f'  Std: {output_ratios.std():.4f}\n'
    ratio_stats += f'  Min: {output_ratios.min():.4f}\n'
    ratio_stats += f'  Max: {output_ratios.max():.4f}'
    
    ax2.text(0.98, 0.98, ratio_stats, 
           transform=ax2.transAxes,
           fontsize=9,
           verticalalignment='top',
           horizontalalignment='right',
           bbox=dict(boxstyle='round', facecolor='lightcyan', alpha=0.6))
    
    # ========================= THIRD PLOT: Input Tokens vs Thinking/Input Ratio =========================
    if has_thinking:
        # Scatter plot for thinking/input ratio
        ax3.scatter(input_tokens, thinking_ratios, s=100, alpha=0.7, color='purple', 
                  edgecolors='black', linewidth=1.5, label='Thinking/Input Ratio', marker='s')
        
        # Add horizontal line for average thinking/input ratio
        ax3.axhline(y=avg_thinking_ratio, color='purple', linestyle='--', linewidth=2, 
                   alpha=0.7, label=f'Avg thinking ratio ({avg_thinking_ratio:.3f})')
        
        # Add trend line for thinking/input ratio
        z_thinking = np.polyfit(input_tokens, thinking_ratios, 1)
        p_thinking = np.poly1d(z_thinking)
        ax3.plot(x_trend, p_thinking(x_trend), ":", alpha=0.6, linewidth=2, color='purple',
               label=f'Ratio trend (slope={z_thinking[0]:.6f})')
        
        # Labels and title
        ax3.set_xlabel('Input Tokens', fontsize=12, fontweight='bold')
        ax3.set_ylabel('Thinking/Input Ratio', fontsize=12, fontweight='bold')
        ax3.set_title('Input Tokens vs Thinking/Input Ratio', fontsize=14, fontweight='bold')
        
        # Add grid
        ax3.grid(True, alpha=0.3, linestyle='--')
        
        # Add legend
        ax3.legend(loc='best', fontsize=9)
        
        # Add annotations for each ratio point
        for i, (x, ratio) in enumerate(zip(input_tokens, thinking_ratios)):
            ax3.annotate(f'{ratio:.3f}', 
                       xy=(x, ratio), 
                       xytext=(5, 10), 
                       textcoords='offset points',
                       fontsize=8,
                       alpha=0.7,
                       color='purple',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='plum', alpha=0.5))
        
        # Add statistics text box for thinking/input ratios
        thinking_stats = f'Thinking Ratio Stats:\n'
        thinking_stats += f'  Mean: {avg_thinking_ratio:.4f}\n'
        thinking_stats += f'  Std: {thinking_ratios.std():.4f}\n'
        thinking_stats += f'  Min: {thinking_ratios.min():.4f}\n'
        thinking_stats += f'  Max: {thinking_ratios.max():.4f}'
        
        ax3.text(0.98, 0.98, thinking_stats, 
               transform=ax3.transAxes,
               fontsize=9,
               verticalalignment='top',
               horizontalalignment='right',
               bbox=dict(boxstyle='round', facecolor='plum', alpha=0.3))
    
    # Tight layout
    plt.tight_layout()
    
    # Save the plot
    output_file = csv_file.replace('.csv', '_plot.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Plot saved to: {output_file}")
    
    # Show the plot
    plt.show()
    
    # Print summary statistics
    print("\n=== Token Ratio Statistics ===")
    print(f"Number of data points: {len(input_tokens)}")
    print(f"\nOutput Tokens:")
    print(f"  Average ratio (output/input): {avg_output_ratio:.4f}")
    print(f"  Min ratio: {output_ratios.min():.4f}")
    print(f"  Max ratio: {output_ratios.max():.4f}")
    print(f"  Std deviation of ratio: {output_ratios.std():.4f}")
    
    if has_thinking:
        print(f"\nThinking Tokens:")
        print(f"  Average ratio (thinking/input): {avg_thinking_ratio:.4f}")
        print(f"  Min ratio: {thinking_ratios.min():.4f}")
        print(f"  Max ratio: {thinking_ratios.max():.4f}")
        print(f"  Std deviation of ratio: {thinking_ratios.std():.4f}")
    
    print("\nIndividual data points:")
    if has_thinking:
        for i, (inp, out, think, out_ratio, think_ratio) in enumerate(zip(input_tokens, output_tokens, thinking_tokens, output_ratios, thinking_ratios), 1):
            print(f"  Point {i}: Input={inp}, Output={out} (ratio={out_ratio:.4f}), Thinking={think} (ratio={think_ratio:.4f})")
    else:
        for i, (inp, out, ratio) in enumerate(zip(input_tokens, output_tokens, output_ratios), 1):
            print(f"  Point {i}: Input={inp}, Output={out}, Ratio={ratio:.4f}")


if __name__ == "__main__":
    plot_token_ratio(INPUT_FILE)

