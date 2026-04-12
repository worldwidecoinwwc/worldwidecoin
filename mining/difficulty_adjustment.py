# mining/difficulty_adjustment.py
import time
import math
from typing import List
from core.block import Block


class DifficultyAdjustment:
    """Advanced difficulty adjustment algorithm"""
    
    def __init__(self, target_block_time: float = 10.0, window_size: int = 100):
        self.target_block_time = target_block_time
        self.window_size = window_size
        self.min_difficulty = 1
        self.max_difficulty = 32
        
        # Adjustment parameters
        self.adjustment_factor = 0.5  # Damping factor
        self.max_adjustment_ratio = 4.0  # Max 4x change per adjustment
        
    def calculate_difficulty(self, blocks: List[Block]) -> int:
        """
        Calculate optimal difficulty based on recent block times
        """
        if len(blocks) < 2:
            return self.min_difficulty
        
        # Get recent blocks for analysis
        recent_blocks = blocks[-self.window_size:] if len(blocks) >= self.window_size else blocks
        
        if len(recent_blocks) < 2:
            return self.min_difficulty
        
        # Calculate actual block times
        block_times = []
        for i in range(1, len(recent_blocks)):
            block_time = recent_blocks[i].timestamp - recent_blocks[i-1].timestamp
            block_times.append(block_time)
        
        # Filter outliers (remove times > 10x target)
        filtered_times = [t for t in block_times if t <= self.target_block_time * 10]
        
        if not filtered_times:
            return self.min_difficulty
        
        # Calculate average block time
        avg_block_time = sum(filtered_times) / len(filtered_times)
        
        # Calculate adjustment ratio
        if avg_block_time == 0:
            adjustment_ratio = self.max_adjustment_ratio
        else:
            adjustment_ratio = self.target_block_time / avg_block_time
        
        # Apply damping and limits
        adjustment_ratio = max(1/self.max_adjustment_ratio, 
                           min(self.max_adjustment_ratio, adjustment_ratio))
        
        # Get current difficulty
        current_difficulty = recent_blocks[-1].difficulty
        
        # Calculate new difficulty
        if adjustment_ratio > 1:
            # Blocks too slow → increase difficulty
            new_difficulty = current_difficulty * (1 + self.adjustment_factor * (adjustment_ratio - 1))
        else:
            # Blocks too fast → decrease difficulty  
            new_difficulty = current_difficulty * (1 + self.adjustment_factor * (adjustment_ratio - 1))
        
        # Apply bounds
        new_difficulty = max(self.min_difficulty, 
                          min(self.max_difficulty, int(new_difficulty)))
        
        # Log adjustment
        self._log_difficulty_change(current_difficulty, new_difficulty, 
                                avg_block_time, len(filtered_times))
        
        return new_difficulty
    
    def _log_difficulty_change(self, old_diff: int, new_diff: int, 
                           avg_time: float, sample_size: int):
        """Log difficulty adjustment details"""
        change = new_diff - old_diff
        change_percent = (change / old_diff * 100) if old_diff > 0 else 0
        
        direction = "📈" if change > 0 else "📉" if change < 0 else "➡️"
        
        print(f"{direction} Difficulty adjustment: {old_diff} → {new_diff} "
              f"({change_percent:+.1f}%)")
        print(f"⏱️ Average block time: {avg_time:.1f}s (target: {self.target_block_time}s)")
        print(f"📊 Sample size: {sample_size} blocks")
    
    def predict_next_difficulty(self, blocks: List[Block]) -> int:
        """Predict next difficulty change"""
        if len(blocks) < 2:
            return blocks[-1].difficulty if blocks else self.min_difficulty
        
        # Simulate what next difficulty would be
        predicted = self.calculate_difficulty(blocks)
        return predicted
    
    def get_mining_stats(self, blocks: List[Block]) -> dict:
        """Get mining difficulty statistics"""
        if not blocks:
            return {}
        
        recent_blocks = blocks[-self.window_size:] if len(blocks) >= self.window_size else blocks
        
        if len(recent_blocks) < 2:
            return {
                "current_difficulty": recent_blocks[0].difficulty,
                "avg_block_time": 0,
                "hash_rate_estimate": 0
            }
        
        # Calculate block times
        block_times = []
        for i in range(1, len(recent_blocks)):
            block_time = recent_blocks[i].timestamp - recent_blocks[i-1].timestamp
            block_times.append(block_time)
        
        avg_time = sum(block_times) / len(block_times)
        current_diff = recent_blocks[-1].difficulty
        
        # Estimate network hash rate
        # Hash rate ~ (2^difficulty * target_time) / avg_block_time
        estimated_hash_rate = (2 ** current_diff * self.target_block_time) / avg_time
        
        return {
            "current_difficulty": current_diff,
            "avg_block_time": avg_time,
            "target_block_time": self.target_block_time,
            "difficulty_trend": "increasing" if avg_time < self.target_block_time else "decreasing",
            "estimated_hash_rate": estimated_hash_rate,
            "sample_size": len(recent_blocks)
        }


class AdaptiveDifficulty:
    """Self-adapting difficulty adjustment with machine learning"""
    
    def __init__(self):
        self.base_adjuster = DifficultyAdjustment()
        self.difficulty_history = []
        self.performance_history = []
        
    def calculate_adaptive_difficulty(self, blocks: List[Block]) -> int:
        """
        Calculate difficulty with adaptive learning
        """
        base_difficulty = self.base_adjuster.calculate_difficulty(blocks)
        
        # Add adaptive adjustments based on history
        if len(self.difficulty_history) >= 10:
            adaptive_factor = self._calculate_adaptive_factor()
            adjusted_difficulty = int(base_difficulty * adaptive_factor)
            
            # Apply bounds
            adjusted_difficulty = max(self.base_adjuster.min_difficulty,
                                  min(self.base_adjuster.max_difficulty, adjusted_difficulty))
            
            self.difficulty_history.append(adjusted_difficulty)
            return adjusted_difficulty
        
        self.difficulty_history.append(base_difficulty)
        return base_difficulty
    
    def _calculate_adaptive_factor(self) -> float:
        """
        Calculate adaptive adjustment factor based on performance history
        """
        if len(self.difficulty_history) < 5:
            return 1.0
        
        # Analyze recent difficulty changes
        recent_changes = []
        for i in range(1, min(10, len(self.difficulty_history))):
            change = abs(self.difficulty_history[i] - self.difficulty_history[i-1])
            recent_changes.append(change)
        
        # If difficulty is oscillating too much, reduce adjustment sensitivity
        avg_change = sum(recent_changes) / len(recent_changes)
        
        if avg_change > 2:  # High volatility
            return 0.9  # Reduce sensitivity
        elif avg_change < 0.5:  # Low volatility
            return 1.1  # Increase sensitivity
        else:
            return 1.0  # Normal sensitivity
    
    def record_mining_performance(self, hash_rate: float, block_time: float):
        """Record mining performance for learning"""
        self.performance_history.append({
            "hash_rate": hash_rate,
            "block_time": block_time,
            "timestamp": time.time()
        })
        
        # Keep only recent history
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-100:]
    
    def get_optimal_difficulty_for_miner(self, miner_hash_rate: float) -> int:
        """
        Calculate optimal difficulty for a specific miner's hash rate
        """
        # Target: miner should find blocks in reasonable time
        target_time = 60  # 1 minute per block for solo mining
        
        # Calculate difficulty that gives target time
        # difficulty = log2(hash_rate * target_time / target_block_time)
        optimal_diff = math.log2(miner_hash_rate * target_time / self.base_adjuster.target_block_time)
        
        # Apply bounds
        return max(self.base_adjuster.min_difficulty,
                  min(self.base_adjuster.max_difficulty, int(optimal_diff)))


class DifficultyForecast:
    """Difficulty prediction and forecasting"""
    
    def __init__(self):
        self.difficulty_series = []
        self.time_series = []
    
    def add_difficulty_point(self, difficulty: int, timestamp: float):
        """Add a difficulty data point"""
        self.difficulty_series.append(difficulty)
        self.time_series.append(timestamp)
        
        # Keep only recent data
        if len(self.difficulty_series) > 1000:
            self.difficulty_series = self.difficulty_series[-1000:]
            self.time_series = self.time_series[-1000:]
    
    def forecast_difficulty(self, periods_ahead: int = 10) -> List[float]:
        """
        Forecast future difficulty using simple linear regression
        """
        if len(self.difficulty_series) < 10:
            return [self.difficulty_series[-1]] * periods_ahead
        
        # Simple linear regression on recent data
        n = len(self.difficulty_series)
        x = list(range(n))
        y = self.difficulty_series
        
        # Calculate regression coefficients
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        intercept = (sum_y - slope * sum_x) / n
        
        # Forecast
        forecast = []
        for i in range(1, periods_ahead + 1):
            future_x = n + i
            future_y = slope * future_x + intercept
            forecast.append(max(1, int(future_y)))  # Minimum difficulty 1
        
        return forecast
    
    def get_difficulty_trend(self) -> str:
        """Get current difficulty trend"""
        if len(self.difficulty_series) < 10:
            return "insufficient_data"
        
        recent = self.difficulty_series[-10:]
        older = self.difficulty_series[-20:-10]
        
        recent_avg = sum(recent) / len(recent)
        older_avg = sum(older) / len(older)
        
        change_percent = ((recent_avg - older_avg) / older_avg) * 100
        
        if change_percent > 10:
            return "strongly_increasing"
        elif change_percent > 2:
            return "increasing"
        elif change_percent < -10:
            return "strongly_decreasing"
        elif change_percent < -2:
            return "decreasing"
        else:
            return "stable"
