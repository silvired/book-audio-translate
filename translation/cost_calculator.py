from typing import Dict


class CostCalculator:
    """
    A simple class to calculate translation costs based on token usage and pricing.
    
    Attributes:
        prices (dict): Dictionary with pricing for input_token, output_token, thinking_token (per million tokens)
    """
    
    def __init__(self, prices: Dict[str, float]):
        """
        Initialize the CostCalculator with pricing information.
        
        Args:
            prices: Dictionary with keys 'input_token', 'output_token', 'thinking_token' 
                   (prices per million tokens in USD)
        """
        self.prices = prices
    
    def calculate_cost(
        self, 
        tot_input_token: int, 
        tot_output_token: int, 
        tot_thinking_token: int = 0
    ) -> Dict[str, float]:
        """
        Calculate the total cost given token counts.
        
        Args:
            tot_input_token: Total input tokens
            tot_output_token: Total output tokens
            tot_thinking_token: Total thinking tokens (optional, defaults to 0)
        
        Returns:
            Dictionary containing:
                - input_cost: Cost of input tokens
                - output_cost: Cost of output tokens
                - thinking_cost: Cost of thinking tokens
                - total_cost: Total cost in USD
        """
        # Calculate costs (prices are per million tokens)
        input_cost = (tot_input_token / 1_000_000) * self.prices['input_token']
        output_cost = (tot_output_token / 1_000_000) * self.prices['output_token']
        thinking_cost = (tot_thinking_token / 1_000_000) * self.prices.get('thinking_token', 0)
        
        total_cost = input_cost + output_cost + thinking_cost
        
        return {
            'input_cost': input_cost,
            'output_cost': output_cost,
            'thinking_cost': thinking_cost,
            'total_cost': total_cost
        }
    
    def update_prices(self, prices: Dict[str, float]) -> None:
        """
        Update the pricing information.
        
        Args:
            prices: Dictionary with keys 'input_token', 'output_token', 'thinking_token'
                   (prices per million tokens in USD)
        """
        self.prices = prices


# Example usage
if __name__ == "__main__":
    # Example prices (per million tokens in USD)
    prices = {
        'input_token': 0.5,      # $0.50 per million input tokens
        'output_token': 1.2,     # $1.20 per million output tokens
        'thinking_token': 0.6    # $0.60 per million thinking tokens
    }
    
    # Initialize cost calculator
    calculator = CostCalculator(prices=prices)
    
    # Calculate cost for a translation job
    cost_breakdown = calculator.calculate_cost(
        tot_input_token=100_000,
        tot_output_token=150_000,
        tot_thinking_token=80_000
    )
    
    print("Cost breakdown:")
    print(f"  Input cost: ${cost_breakdown['input_cost']:.4f}")
    print(f"  Output cost: ${cost_breakdown['output_cost']:.4f}")
    print(f"  Thinking cost: ${cost_breakdown['thinking_cost']:.4f}")
    print(f"  Total cost: ${cost_breakdown['total_cost']:.4f}")
    
    # Example: Update prices if needed
    new_prices = {
        'input_token': 0.3,
        'output_token': 1.0,
        'thinking_token': 0.5
    }
    calculator.update_prices(new_prices)
    
    # Calculate cost with new prices
    new_cost_breakdown = calculator.calculate_cost(
        tot_input_token=100_000,
        tot_output_token=150_000,
        tot_thinking_token=80_000
    )
    
    print("\nCost breakdown with new prices:")
    print(f"  Input cost: ${new_cost_breakdown['input_cost']:.4f}")
    print(f"  Output cost: ${new_cost_breakdown['output_cost']:.4f}")
    print(f"  Thinking cost: ${new_cost_breakdown['thinking_cost']:.4f}")
    print(f"  Total cost: ${new_cost_breakdown['total_cost']:.4f}")

