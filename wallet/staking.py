# wallet/staking.py
import time
import json
import hashlib
from typing import Dict, List, Optional, Tuple
from core.blockchain import Blockchain
from core.transaction import Transaction


class StakingPool:
    """Delegated staking pool implementation"""
    
    def __init__(self, pool_address: str, commission_rate: float = 0.05):
        self.pool_address = pool_address
        self.commission_rate = commission_rate  # 5% commission
        
        # Staking state
        self.delegators: Dict[str, Dict] = {}  # delegator_address -> delegation_info
        self.validators: Dict[str, Dict] = {}  # validator_address -> validator_info
        self.total_staked = 0.0
        self.active_validators = []
        
        # Pool statistics
        self.pool_stats = {
            "total_rewards": 0.0,
            "total_commission": 0.0,
            "epoch_rewards": {},
            "uptime": time.time()
        }
        
        print(f"🏊 Staking pool created: {pool_address}")
        print(f"💰 Commission rate: {commission_rate * 100:.1f}%")
    
    def delegate_stake(self, delegator_address: str, amount: float, validator_address: str) -> bool:
        """
        Delegate stake to a validator
        
        Args:
            delegator_address: Address of delegator
            amount: Amount to stake
            validator_address: Address of validator to delegate to
        """
        if amount <= 0:
            print("❌ Stake amount must be positive")
            return False
        
        # Check if validator exists
        if validator_address not in self.validators:
            print(f"❌ Validator {validator_address} not found")
            return False
        
        # Update delegator's stake
        if delegator_address not in self.delegators:
            self.delegators[delegator_address] = {
                "total_staked": 0.0,
                "delegations": {},
                "rewards_earned": 0.0,
                "join_time": time.time()
            }
        
        # Add or update delegation
        delegations = self.delegators[delegator_address]["delegations"]
        if validator_address in delegations:
            delegations[validator_address] += amount
        else:
            delegations[validator_address] = amount
        
        self.delegators[delegator_address]["total_staked"] += amount
        self.total_staked += amount
        
        # Update validator stake
        self.validators[validator_address]["total_delegated"] += amount
        
        print(f"✅ Stake delegated:")
        print(f"   Delegator: {delegator_address[:16]}...")
        print(f"   Validator: {validator_address[:16]}...")
        print(f"   Amount: {amount:.8f} WWC")
        print(f"   Total pool stake: {self.total_staked:.8f} WWC")
        
        return True
    
    def undelegate_stake(self, delegator_address: str, validator_address: str, amount: float) -> bool:
        """
        Undelegate stake from validator
        
        Args:
            delegator_address: Address of delegator
            validator_address: Address of validator
            amount: Amount to undelegate
        """
        if delegator_address not in self.delegators:
            print(f"❌ Delegator {delegator_address} not found")
            return False
        
        delegations = self.delegators[delegator_address]["delegations"]
        current_stake = delegations.get(validator_address, 0.0)
        
        if amount > current_stake:
            print(f"❌ Cannot undelegate more than staked: {amount} > {current_stake}")
            return False
        
        # Update delegation
        delegations[validator_address] -= amount
        self.delegators[delegator_address]["total_staked"] -= amount
        self.total_staked -= amount
        
        # Update validator
        self.validators[validator_address]["total_delegated"] -= amount
        
        # Remove delegation if zero
        if delegations[validator_address] == 0:
            del delegations[validator_address]
        
        print(f"✅ Stake undelegated:")
        print(f"   Delegator: {delegator_address[:16]}...")
        print(f"   Validator: {validator_address[:16]}...")
        print(f"   Amount: {amount:.8f} WWC")
        print(f"   Remaining stake: {self.total_staked:.8f} WWC")
        
        return True
    
    def add_validator(self, validator_address: str, commission_rate: float = 0.10) -> bool:
        """
        Add a validator to the pool
        
        Args:
            validator_address: Address of validator
            commission_rate: Validator's commission rate (10% default)
        """
        if validator_address in self.validators:
            print(f"⚠️ Validator {validator_address} already exists")
            return False
        
        self.validators[validator_address] = {
            "address": validator_address,
            "commission_rate": commission_rate,
            "total_delegated": 0.0,
            "rewards_earned": 0.0,
            "join_time": time.time(),
            "status": "active",
            "performance_score": 100.0  # Start with perfect score
        }
        
        print(f"✅ Validator added:")
        print(f"   Address: {validator_address[:16]}...")
        print(f"   Commission: {commission_rate * 100:.1f}%")
        
        return True
    
    def remove_validator(self, validator_address: str) -> bool:
        """Remove a validator from the pool"""
        if validator_address not in self.validators:
            print(f"❌ Validator {validator_address} not found")
            return False
        
        # Force undelegate all stakes
        validator = self.validators[validator_address]
        total_delegated = validator["total_delegated"]
        
        if total_delegated > 0:
            print(f"⚠️ Force undelegating {total_delegated:.8f} WWC from validator")
        
        self.total_staked -= total_delegated
        
        # Remove validator
        del self.validators[validator_address]
        
        if validator_address in self.active_validators:
            self.active_validators.remove(validator_address)
        
        print(f"✅ Validator removed: {validator_address[:16]}...")
        return True
    
    def calculate_rewards(self, epoch_duration: int = 86400) -> Dict[str, float]:
        """
        Calculate rewards for all participants
        
        Args:
            epoch_duration: Duration of epoch in seconds (default 24 hours)
        """
        total_rewards = self.total_staked * 0.05  # 5% annual staking reward
        epoch_rewards = total_rewards * (epoch_duration / 31536000)  # Convert to epoch reward
        
        rewards_distribution = {}
        
        # Calculate validator rewards
        for validator_addr, validator in self.validators.items():
            if validator["total_delegated"] > 0:
                # Validator gets commission + share of rewards
                validator_share = (validator["total_delegated"] / self.total_staked) * epoch_rewards
                commission = validator_share * validator["commission_rate"]
                validator_reward = validator_share - commission
                
                rewards_distribution[validator_addr] = validator_reward
                
                # Track pool commission
                self.pool_stats["total_commission"] += commission
        
        # Calculate delegator rewards (net of validator commissions)
        for delegator_addr, delegator in self.delegators.items():
            delegator_reward = 0.0
            
            for validator_addr, stake_amount in delegator["delegations"].items():
                if stake_amount > 0 and validator_addr in rewards_distribution:
                    # Delegator gets rewards minus validator commission
                    validator_commission = rewards_distribution[validator_addr] * self.validators[validator_addr]["commission_rate"]
                    net_reward = (stake_amount / self.validators[validator_addr]["total_delegated"]) * (rewards_distribution[validator_addr] - validator_commission)
                    delegator_reward += net_reward
            
            if delegator_reward > 0:
                rewards_distribution[delegator_addr] = delegator_reward
        
        # Update statistics
        self.pool_stats["total_rewards"] += epoch_rewards
        current_epoch = int(time.time() / epoch_duration)
        self.pool_stats["epoch_rewards"][str(current_epoch)] = epoch_rewards
        
        print(f"💰 Epoch rewards calculated:")
        print(f"   Total rewards: {epoch_rewards:.8f} WWC")
        print(f"   Participants: {len(rewards_distribution)}")
        
        return rewards_distribution
    
    def select_active_validators(self, max_validators: int = 21) -> List[str]:
        """
        Select top validators for active set based on stake and performance
        
        Args:
            max_validators: Maximum number of active validators
        """
        # Score validators by stake and performance
        validator_scores = []
        
        for validator_addr, validator in self.validators.items():
            if validator["total_delegated"] > 0:
                # Calculate composite score
                stake_score = validator["total_delegated"]
                performance_score = validator["performance_score"]
                commission_penalty = 1.0 - validator["commission_rate"]  # Lower commission = higher score
                
                composite_score = stake_score * performance_score * commission_penalty
                
                validator_scores.append((composite_score, validator_addr))
        
        # Sort by score and select top validators
        validator_scores.sort(reverse=True)
        selected = [addr for score, addr in validator_scores[:max_validators]]
        
        self.active_validators = selected
        
        print(f"🎯 Selected {len(selected)} active validators:")
        for i, validator_addr in enumerate(selected[:5]):  # Show top 5
            validator = self.validators[validator_addr]
            print(f"   {i+1}. {validator_addr[:16]}... ({validator['total_delegated']:.2f} WWC)")
        
        if len(selected) > 5:
            print(f"   ... and {len(selected)-5} more validators")
        
        return selected
    
    def update_validator_performance(self, validator_address: str, performance_change: float):
        """
        Update validator performance score
        
        Args:
            validator_address: Address of validator
            performance_change: Performance change (-1.0 to 1.0)
        """
        if validator_address not in self.validators:
            print(f"❌ Validator {validator_address} not found")
            return
        
        current_score = self.validators[validator_address]["performance_score"]
        new_score = max(0.0, min(100.0, current_score + performance_change))
        
        self.validators[validator_address]["performance_score"] = new_score
        
        print(f"📊 Validator performance updated:")
        print(f"   Address: {validator_address[:16]}...")
        print(f"   Score: {current_score:.1f} → {new_score:.1f}")
    
    def get_delegator_info(self, delegator_address: str) -> Optional[Dict]:
        """Get information about a delegator"""
        return self.delegators.get(delegator_address)
    
    def get_validator_info(self, validator_address: str) -> Optional[Dict]:
        """Get information about a validator"""
        return self.validators.get(validator_address)
    
    def get_pool_stats(self) -> Dict:
        """Get pool statistics"""
        uptime = time.time() - self.pool_stats["uptime"]
        
        return {
            "pool_address": self.pool_address,
            "commission_rate": self.commission_rate,
            "total_staked": self.total_staked,
            "total_delegators": len(self.delegators),
            "total_validators": len(self.validators),
            "active_validators": len(self.active_validators),
            "total_rewards": self.pool_stats["total_rewards"],
            "total_commission": self.pool_stats["total_commission"],
            "uptime_hours": uptime / 3600,
            "epochs_completed": len(self.pool_stats["epoch_rewards"])
        }
    
    def export_state(self, filename: str):
        """Export pool state to file"""
        state = {
            "pool_address": self.pool_address,
            "commission_rate": self.commission_rate,
            "delegators": self.delegators,
            "validators": self.validators,
            "active_validators": self.active_validators,
            "pool_stats": self.pool_stats,
            "export_time": time.time()
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(state, f, indent=2)
            print(f"📁 Pool state exported to {filename}")
        except Exception as e:
            print(f"❌ Export failed: {e}")


class StakingManager:
    """High-level staking management"""
    
    def __init__(self, blockchain: Blockchain):
        self.blockchain = blockchain
        self.pools: Dict[str, StakingPool] = {}
        self.current_epoch = 0
        self.epoch_duration = 86400  # 24 hours
        
        # Staking parameters
        self.min_stake_amount = 1.0
        self.max_validators_per_pool = 21
        self.unbonding_period = 7 * 86400  # 7 days
        
        print("🏊 Staking manager initialized")
    
    def create_pool(self, pool_address: str, commission_rate: float = 0.05) -> StakingPool:
        """Create a new staking pool"""
        if pool_address in self.pools:
            print(f"⚠️ Pool {pool_address} already exists")
            return self.pools[pool_address]
        
        pool = StakingPool(pool_address, commission_rate)
        self.pools[pool_address] = pool
        
        print(f"✅ Staking pool created: {pool_address}")
        return pool
    
    def process_epoch(self):
        """Process staking epoch and distribute rewards"""
        self.current_epoch += 1
        epoch_start = time.time()
        
        print(f"🌅 Processing staking epoch {self.current_epoch}")
        
        # Process rewards for each pool
        total_epoch_rewards = 0.0
        
        for pool_addr, pool in self.pools.items():
            # Select active validators
            active_validators = pool.select_active_validators(self.max_validators_per_pool)
            
            # Calculate rewards
            rewards = pool.calculate_rewards(self.epoch_duration)
            total_epoch_rewards += sum(rewards.values())
            
            # Create reward transactions
            self._create_reward_transactions(rewards, pool_addr)
        
        # Create staking block
        if total_epoch_rewards > 0:
            self._create_staking_block(total_epoch_rewards, epoch_start)
        
        print(f"✅ Epoch {self.current_epoch} completed:")
        print(f"   Total rewards distributed: {total_epoch_rewards:.8f} WWC")
        print(f"   Next epoch in: {self.epoch_duration/3600:.1f} hours")
    
    def _create_reward_transactions(self, rewards: Dict[str, float], pool_address: str):
        """Create transactions for reward distribution"""
        for recipient_addr, reward_amount in rewards.items():
            if reward_amount > 0.00000001:  # Dust threshold
                # Create reward transaction
                tx = Transaction(
                    inputs=[],  # Coinbase-like transaction for rewards
                    outputs=[{
                        "address": recipient_addr,
                        "amount": reward_amount
                    }]
                )
                
                # Add to mempool for inclusion in staking block
                self.blockchain.mempool.add_transaction(tx)
    
    def _create_staking_block(self, total_rewards: float, epoch_start: float):
        """Create special staking block for epoch"""
        # Create staking transaction
        staking_tx = Transaction(
            inputs=[],
            outputs=[{
                "address": "STAKING_TREASURY",
                "amount": total_rewards
            }]
        )
        
        # Create staking block
        staking_block = self.blockchain.create_block("STAKING_VALIDATOR")
        
        # Add staking transaction
        staking_block.transactions.insert(0, staking_tx)
        
        # Mine staking block (simplified - in production would be more complex)
        staking_block.mine()
        
        # Add to blockchain
        self.blockchain.add_block(staking_block)
        
        print(f"⛏️ Staking block created: #{staking_block.index}")
        print(f"   Rewards: {total_rewards:.8f} WWC")
    
    def delegate_to_pool(self, pool_address: str, delegator_address: str, 
                      amount: float, validator_address: str) -> bool:
        """Delegate stake to a specific pool"""
        if pool_address not in self.pools:
            print(f"❌ Pool {pool_address} not found")
            return False
        
        return self.pools[pool_address].delegate_stake(delegator_address, amount, validator_address)
    
    def get_staking_info(self, address: str) -> Dict:
        """Get staking information for an address"""
        info = {
            "address": address,
            "total_staked": 0.0,
            "pools": [],
            "rewards_earned": 0.0
        }
        
        # Check all pools for this address
        for pool_addr, pool in self.pools.items():
            # Check as delegator
            delegator_info = pool.get_delegator_info(address)
            if delegator_info:
                info["total_staked"] += delegator_info["total_staked"]
                info["rewards_earned"] += delegator_info["rewards_earned"]
                info["pools"].append({
                    "pool_address": pool_addr,
                    "staked": delegator_info["total_staked"],
                    "delegations": delegator_info["delegations"]
                })
            
            # Check as validator
            validator_info = pool.get_validator_info(address)
            if validator_info:
                info["pools"].append({
                    "pool_address": pool_addr,
                    "role": "validator",
                    "total_delegated": validator_info["total_delegated"],
                    "commission_rate": validator_info["commission_rate"],
                    "performance_score": validator_info["performance_score"]
                })
        
        return info
    
    def get_system_stats(self) -> Dict:
        """Get overall staking system statistics"""
        total_staked = sum(pool.total_staked for pool in self.pools.values())
        total_delegators = sum(len(pool.delegators) for pool in self.pools.values())
        total_validators = sum(len(pool.validators) for pool in self.pools.values())
        total_active_validators = sum(len(pool.active_validators) for pool in self.pools.values())
        
        return {
            "current_epoch": self.current_epoch,
            "total_pools": len(self.pools),
            "total_staked": total_staked,
            "total_delegators": total_delegators,
            "total_validators": total_validators,
            "total_active_validators": total_active_validators,
            "epoch_duration_hours": self.epoch_duration / 3600,
            "min_stake": self.min_stake_amount,
            "unbonding_period_days": self.unbonding_period / 86400
        }


# Utility functions
def calculate_staking_apy(stake_amount: float, annual_reward_rate: float = 0.05) -> float:
    """Calculate APY for staking"""
    return annual_reward_rate * 100


def estimate_staking_rewards(stake_amount: float, days: int, apr: float = 0.05) -> float:
    """Estimate staking rewards for a period"""
    daily_rate = apr / 365
    return stake_amount * daily_rate * days


def create_staking_contract(pool_address: str, rules: Dict) -> Dict:
    """Create staking contract rules"""
    return {
        "contract_type": "staking",
        "pool_address": pool_address,
        "rules": rules,
        "created_at": time.time(),
        "version": "1.0"
    }
