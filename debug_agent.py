from src.agents.code_executor_agent import CodeExecutorAgent
from src.database.db_manager import DatabaseManager
from src.utils.trading_mode import TradingMode
from src.utils.local_db import LocalDatabase
import os
from dotenv import load_dotenv

def main():
    # Load environment variables
    load_dotenv('config.env')
    
    # Get DB path from environment variable or use default
    db_path = os.getenv('DB_PATH', 'data/trading.db')
    
    # Initialize database manager
    db_manager = DatabaseManager(db_path)
    
    # Create LocalDatabase instance
    local_db = LocalDatabase(db_manager.get_connection())
    
    # Initialize trading mode
    trading_mode = TradingMode(os.getenv('TRADING_MODE', 'DRY_RUN'))
    
    try:
        # Initialize the agent with local_db and trading_mode
        agent = CodeExecutorAgent(
            db=local_db,
            trading_mode=trading_mode
        )
        
        # Test the agent with a prompt that includes test requirements
        response = agent.execute(
            """
            Write a Python function that calculates the RSI (Relative Strength Index) indicator 
            for a given price series using numpy and pandas. The function should:
            1. Accept a pandas Series of prices
            2. Calculate RSI with a default period of 14
            3. Handle edge cases and invalid inputs
            4. Return the RSI values as a pandas Series

            Also provide test code that:
            1. Creates sample price data
            2. Tests the function with different scenarios
            3. Prints the results
            4. Includes edge case testing
            """
        )
        print("Agent Response:", response)
    
    finally:
        # Clean up database connection
        db_manager.close()

if __name__ == "__main__":
    main() 