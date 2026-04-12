# core/fees.py
import time
import math
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal, ROUND_UP
from dataclasses import dataclass
from collections import deque


@dataclass
class FeeRate:
    """Fee rate with amount and time"""
    rate: Decimal  # satoshis per byte
    timestamp: float
    block_height: int
    confirmations: int = 0


@dataclass
class FeeEstimate:
    """Fee estimation result"""
    fee_rate: Decimal
    confidence: float  # 0.0 to 1.0
    target_blocks: int
    estimated_time: int  # seconds
    decay_factor: float = 0.95


class FeeCalculator:
    """Calculates transaction fees based on various factors"""
    
    def __init__(self):
        # Base fee rates
        self.min_relay_fee = Decimal('0.00001')  # 1 satoshi per byte
        self.min_fee_rate = Decimal('0.00001')
        self.max_fee_rate = Decimal('0.001')  # 100 satoshis per byte
        
        # Fee calculation parameters
        self.dust_threshold = Decimal('0.00001')
        self.base_fee = Decimal('0.0001')
        self.size_penalty_rate = Decimal('0.000001')
        self.priority_rate = Decimal('0.00001')
        
        # Dynamic fee adjustment
        self.mempool_pressure_factor = Decimal('1.0')
        self.network_congestion_factor = Decimal('1.0')
    
    def calculate_transaction_fee(self, tx_size: int, inputs_count: int, outputs_count: int, 
                                priority: str = 'medium') -> Decimal:
        """
        Calculate transaction fee
        
        Args:
            tx_size: Transaction size in bytes
            inputs_count: Number of inputs
            outputs_count: Number of outputs
            priority: 'low', 'medium', or 'high'
            
        Returns:
            Fee amount in WWC
        """
        # Base fee calculation
        base_fee = self.base_fee
        
        # Size-based fee
        size_fee = Decimal(tx_size) * self.min_fee_rate
        
        # Input complexity fee
        complexity_fee = Decimal(inputs_count) * self.size_penalty_rate
        
        # Output fee
        output_fee = Decimal(outputs_count) * self.size_penalty_rate
        
        # Priority multiplier
        priority_multipliers = {
            'low': Decimal('0.5'),
            'medium': Decimal('1.0'),
            'high': Decimal('2.0')
        }
        
        priority_multiplier = priority_multipliers.get(priority, Decimal('1.0'))
        
        # Dynamic adjustment
        dynamic_multiplier = self.mempool_pressure_factor * self.network_congestion_factor
        
        # Calculate total fee
        total_fee = (base_fee + size_fee + complexity_fee + output_fee) * priority_multiplier * dynamic_multiplier
        
        # Apply minimum fee
        total_fee = max(total_fee, self.min_relay_fee)
        
        # Round up to 8 decimal places
        return total_fee.quantize(Decimal('0.00000001'), rounding=ROUND_UP)
    
    def calculate_fee_rate(self, tx_size: int, fee_amount: Decimal) -> Decimal:
        """Calculate fee rate (WWC per byte)"""
        if tx_size <= 0:
            return Decimal('0')
        
        return fee_amount / Decimal(tx_size)
    
    def estimate_fee_for_size(self, tx_size: int, target_blocks: int = 6) -> Decimal:
        """Estimate fee for given transaction size and target confirmation"""
        # Base fee rate
        base_rate = self.min_fee_rate
        
        # Adjust based on target blocks
        if target_blocks <= 1:
            multiplier = Decimal('3.0')  # High priority
        elif target_blocks <= 3:
            multiplier = Decimal('2.0')  # Medium priority
        elif target_blocks <= 6:
            multiplier = Decimal('1.0')  # Normal priority
        else:
            multiplier = Decimal('0.5')  # Low priority
        
        # Apply network congestion factor
        adjusted_rate = base_rate * multiplier * self.network_congestion_factor
        
        # Calculate total fee
        estimated_fee = adjusted_rate * Decimal(tx_size)
        
        # Apply minimum fee
        estimated_fee = max(estimated_fee, self.min_relay_fee)
        
        return estimated_fee.quantize(Decimal('0.00000001'), rounding=ROUND_UP)
    
    def update_mempool_pressure(self, mempool_size: int, max_mempool_size: int):
        """Update mempool pressure factor"""
        if max_mempool_size == 0:
            return
        
        utilization = mempool_size / max_mempool_size
        
        if utilization < 0.5:
            self.mempool_pressure_factor = Decimal('0.8')
        elif utilization < 0.8:
            self.mempool_pressure_factor = Decimal('1.0')
        elif utilization < 0.9:
            self.mempool_pressure_factor = Decimal('1.5')
        else:
            self.mempool_pressure_factor = Decimal('2.0')
    
    def update_network_congestion(self, average_block_time: float, target_block_time: float = 600):
        """Update network congestion factor based on block times"""
        if average_block_time == 0:
            return
        
        congestion_ratio = average_block_time / target_block_time
        
        if congestion_ratio < 0.8:
            # Network is fast, lower fees
            self.network_congestion_factor = Decimal('0.8')
        elif congestion_ratio < 1.2:
            # Normal network speed
            self.network_congestion_factor = Decimal('1.0')
        elif congestion_ratio < 2.0:
            # Network is slow, higher fees
            self.network_congestion_factor = Decimal('1.5')
        else:
            # Network is very slow, much higher fees
            self.network_congestion_factor = Decimal('2.5')
    
    def get_fee_statistics(self) -> Dict[str, Any]:
        """Get fee calculation statistics"""
        return {
            'min_relay_fee': str(self.min_relay_fee),
            'min_fee_rate': str(self.min_fee_rate),
            'max_fee_rate': str(self.max_fee_rate),
            'base_fee': str(self.base_fee),
            'mempool_pressure_factor': str(self.mempool_pressure_factor),
            'network_congestion_factor': str(self.network_congestion_factor)
        }


class FeeEstimator:
    """Estimates fees based on historical data and mempool state"""
    
    def __init__(self, history_size: int = 1000):
        self.history_size = history_size
        self.fee_history: deque = deque(maxlen=history_size)
        self.confirmation_history: deque = deque(maxlen=history_size)
        
        # Estimation parameters
        self.decay_factor = 0.95
        self.min_samples = 10
        self.confidence_threshold = 0.8
        
        # Fee rate buckets for estimation
        self.fee_buckets = [
            Decimal('0.00001'),  # 1 sat/byte
            Decimal('0.00002'),  # 2 sat/byte
            Decimal('0.00005'),  # 5 sat/byte
            Decimal('0.0001'),   # 10 sat/byte
            Decimal('0.0002'),   # 20 sat/byte
            Decimal('0.0005'),   # 50 sat/byte
            Decimal('0.001'),    # 100 sat/byte
        ]
    
    def add_fee_sample(self, fee_rate: Decimal, block_height: int, confirmations: int = 0):
        """Add a fee sample to history"""
        sample = FeeRate(
            rate=fee_rate,
            timestamp=time.time(),
            block_height=block_height,
            confirmations=confirmations
        )
        
        self.fee_history.append(sample)
        
        # Add to confirmation history if confirmed
        if confirmations > 0:
            self.confirmation_history.append(sample)
    
    def estimate_fee_rate(self, target_blocks: int = 6) -> FeeEstimate:
        """
        Estimate fee rate for target confirmation time
        
        Args:
            target_blocks: Target number of blocks for confirmation
            
        Returns:
            FeeEstimate with rate, confidence, and timing
        """
        if len(self.confirmation_history) < self.min_samples:
            # Not enough data, use fallback
            return self._fallback_estimate(target_blocks)
        
        # Filter recent confirmations
        current_time = time.time()
        recent_confirmations = [
            sample for sample in self.confirmation_history
            if current_time - sample.timestamp < 3600 * 24  # Last 24 hours
        ]
        
        if len(recent_confirmations) < self.min_samples:
            return self._fallback_estimate(target_blocks)
        
        # Calculate confirmation statistics for each fee bucket
        bucket_stats = self._calculate_bucket_stats(recent_confirmations)
        
        # Find best fee rate for target blocks
        best_rate, confidence = self._find_optimal_rate(bucket_stats, target_blocks)
        
        # Calculate estimated time
        estimated_time = target_blocks * 600  # 10 minutes per block
        
        return FeeEstimate(
            fee_rate=best_rate,
            confidence=confidence,
            target_blocks=target_blocks,
            estimated_time=estimated_time,
            decay_factor=self.decay_factor
        )
    
    def _calculate_bucket_stats(self, confirmations: List[FeeRate]) -> Dict[Decimal, Dict[str, Any]]:
        """Calculate statistics for each fee bucket"""
        bucket_stats = {}
        
        for bucket_rate in self.fee_buckets:
            # Find confirmations with similar fee rates
            similar_fees = [
                sample for sample in confirmations
                if abs(sample.rate - bucket_rate) <= bucket_rate * Decimal('0.1')  # Within 10%
            ]
            
            if similar_fees:
                # Calculate confirmation time statistics
                confirmation_times = [sample.confirmations for sample in similar_fees]
                
                bucket_stats[bucket_rate] = {
                    'count': len(similar_fees),
                    'avg_confirmations': sum(confirmation_times) / len(confirmation_times),
                    'min_confirmations': min(confirmation_times),
                    'max_confirmations': max(confirmation_times),
                    'std_dev': self._calculate_std_dev(confirmation_times)
                }
        
        return bucket_stats
    
    def _find_optimal_rate(self, bucket_stats: Dict[Decimal, Dict[str, Any]], 
                          target_blocks: int) -> Tuple[Decimal, float]:
        """Find optimal fee rate for target confirmation blocks"""
        best_rate = self.fee_buckets[0]  # Start with minimum
        best_confidence = 0.0
        
        for rate, stats in bucket_stats.items():
            avg_confirmations = stats['avg_confirmations']
            
            # Check if this rate meets target
            if avg_confirmations <= target_blocks:
                # Calculate confidence based on how close to target
                deviation = abs(avg_confirmations - target_blocks)
                confidence = max(0.0, 1.0 - (deviation / target_blocks))
                
                # Prefer lower fees with good confidence
                if confidence > best_confidence or (confidence == best_confidence and rate < best_rate):
                    best_rate = rate
                    best_confidence = confidence
        
        return best_rate, best_confidence
    
    def _fallback_estimate(self, target_blocks: int) -> FeeEstimate:
        """Fallback estimation when not enough data"""
        # Use simple heuristic based on target blocks
        if target_blocks <= 1:
            fee_rate = Decimal('0.001')  # 100 sat/byte
        elif target_blocks <= 3:
            fee_rate = Decimal('0.0005')  # 50 sat/byte
        elif target_blocks <= 6:
            fee_rate = Decimal('0.0001')  # 10 sat/byte
        else:
            fee_rate = Decimal('0.00005')  # 5 sat/byte
        
        return FeeEstimate(
            fee_rate=fee_rate,
            confidence=0.5,  # Low confidence
            target_blocks=target_blocks,
            estimated_time=target_blocks * 600,
            decay_factor=self.decay_factor
        )
    
    def _calculate_std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation"""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return math.sqrt(variance)
    
    def get_fee_estimates(self, target_blocks_list: List[int] = None) -> List[FeeEstimate]:
        """Get fee estimates for multiple target blocks"""
        if target_blocks_list is None:
            target_blocks_list = [1, 3, 6, 12, 24]
        
        estimates = []
        for target_blocks in target_blocks_list:
            estimate = self.estimate_fee_rate(target_blocks)
            estimates.append(estimate)
        
        return estimates
    
    def get_fee_statistics(self) -> Dict[str, Any]:
        """Get fee estimation statistics"""
        if not self.fee_history:
            return {
                'total_samples': 0,
                'avg_fee_rate': '0',
                'min_fee_rate': '0',
                'max_fee_rate': '0',
                'confirmation_samples': 0
            }
        
        rates = [sample.rate for sample in self.fee_history]
        
        return {
            'total_samples': len(self.fee_history),
            'confirmation_samples': len(self.confirmation_history),
            'avg_fee_rate': str(sum(rates) / len(rates)),
            'min_fee_rate': str(min(rates)),
            'max_fee_rate': str(max(rates)),
            'oldest_sample': min(sample.timestamp for sample in self.fee_history),
            'newest_sample': max(sample.timestamp for sample in self.fee_history)
        }


class FeeManager:
    """Manages fee calculation and estimation"""
    
    def __init__(self):
        self.calculator = FeeCalculator()
        self.estimator = FeeEstimator()
        
        # Statistics
        self.total_fees_collected = Decimal('0')
        self.total_transactions = 0
        self.average_fee_rate = Decimal('0')
    
    def calculate_transaction_fee(self, tx_size: int, inputs_count: int, outputs_count: int, 
                                priority: str = 'medium') -> Decimal:
        """Calculate transaction fee"""
        fee = self.calculator.calculate_transaction_fee(tx_size, inputs_count, outputs_count, priority)
        
        # Update statistics
        self.total_fees_collected += fee
        self.total_transactions += 1
        
        if self.total_transactions > 0:
            fee_rate = self.calculator.calculate_fee_rate(tx_size, fee)
            self.average_fee_rate = (
                (self.average_fee_rate * (self.total_transactions - 1) + fee_rate) / 
                self.total_transactions
            )
        
        return fee
    
    def estimate_fee_for_confirmation(self, tx_size: int, target_blocks: int = 6) -> Decimal:
        """Estimate fee for target confirmation"""
        estimate = self.estimator.estimate_fee_rate(target_blocks)
        return estimate.fee_rate * Decimal(tx_size)
    
    def add_fee_confirmation(self, fee_rate: Decimal, block_height: int, confirmations: int):
        """Add confirmed fee data to estimator"""
        self.estimator.add_fee_sample(fee_rate, block_height, confirmations)
    
    def update_network_conditions(self, mempool_size: int, max_mempool_size: int, 
                                average_block_time: float):
        """Update network conditions for fee calculation"""
        self.calculator.update_mempool_pressure(mempool_size, max_mempool_size)
        self.calculator.update_network_congestion(average_block_time)
    
    def get_fee_recommendations(self, tx_size: int) -> Dict[str, Any]:
        """Get fee recommendations for different priorities"""
        recommendations = {}
        
        # Low priority (24+ blocks)
        low_fee = self.estimate_fee_for_confirmation(tx_size, 24)
        recommendations['low'] = {
            'fee_rate': str(low_fee / tx_size if tx_size > 0 else 0),
            'total_fee': str(low_fee),
            'target_blocks': 24,
            'estimated_time': 24 * 600  # 4 hours
        }
        
        # Medium priority (6 blocks)
        medium_fee = self.estimate_fee_for_confirmation(tx_size, 6)
        recommendations['medium'] = {
            'fee_rate': str(medium_fee / tx_size if tx_size > 0 else 0),
            'total_fee': str(medium_fee),
            'target_blocks': 6,
            'estimated_time': 6 * 600  # 1 hour
        }
        
        # High priority (1 block)
        high_fee = self.estimate_fee_for_confirmation(tx_size, 1)
        recommendations['high'] = {
            'fee_rate': str(high_fee / tx_size if tx_size > 0 else 0),
            'total_fee': str(high_fee),
            'target_blocks': 1,
            'estimated_time': 600  # 10 minutes
        }
        
        return recommendations
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive fee statistics"""
        return {
            'calculator_stats': self.calculator.get_fee_statistics(),
            'estimator_stats': self.estimator.get_fee_statistics(),
            'manager_stats': {
                'total_fees_collected': str(self.total_fees_collected),
                'total_transactions': self.total_transactions,
                'average_fee_rate': str(self.average_fee_rate)
            }
        }


# Utility functions
def create_fee_manager() -> FeeManager:
    """Create a fee manager instance"""
    return FeeManager()


def calculate_dust_threshold(min_relay_fee: Decimal, tx_size: int) -> Decimal:
    """Calculate dust threshold for transaction outputs"""
    # Dust = 3 * min_relay_fee * tx_size / 1000
    return min_relay_fee * Decimal(3) * Decimal(tx_size) / Decimal(1000)


def is_dust_output(amount: Decimal, dust_threshold: Decimal) -> bool:
    """Check if output amount is dust"""
    return amount < dust_threshold


def optimize_transaction_inputs(inputs: List[Dict], target_amount: Decimal) -> List[Dict]:
    """Optimize transaction inputs to reduce fees"""
    # Sort inputs by amount (largest first)
    sorted_inputs = sorted(inputs, key=lambda x: Decimal(str(x.get('amount', 0))), reverse=True)
    
    # Select minimum number of inputs
    selected_inputs = []
    current_amount = Decimal('0')
    
    for inp in sorted_inputs:
        if current_amount >= target_amount:
            break
        
        selected_inputs.append(inp)
        current_amount += Decimal(str(inp.get('amount', 0)))
    
    return selected_inputs


def estimate_transaction_size(inputs_count: int, outputs_count: int, has_signature: bool = True) -> int:
    """Estimate transaction size"""
    # Base transaction size
    base_size = 10
    
    # Input size (each input ~148 bytes with signature)
    input_size = inputs_count * (148 if has_signature else 40)
    
    # Output size (each output ~34 bytes)
    output_size = outputs_count * 34
    
    return base_size + input_size + output_size
