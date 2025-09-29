"""
Advanced AML Pattern Analysis Module
This module provides sophisticated pattern detection for Anti-Money Laundering (AML) analysis
using modern machine learning and statistical techniques.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging
from collections import defaultdict, Counter
import networkx as nx
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_similarity
from scipy import stats
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components, shortest_path
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PatternType(Enum):
    """Enumeration of different AML pattern types"""
    STRUCTURING = "structuring"
    LAYERING = "layering"
    CIRCULAR_TRANSACTIONS = "circular_transactions"
    RAPID_MOVEMENT = "rapid_movement"
    VELOCITY_ANOMALY = "velocity_anomaly"
    ROUND_AMOUNT = "round_amount"
    SMURFING = "smurfing"
    SHELL_COMPANY = "shell_company"
    UNUSUAL_GEOGRAPHY = "unusual_geography"
    TIME_ANOMALY = "time_anomaly"
    GRAPH_CENTRALITY_ANOMALY = "graph_centrality_anomaly"
    BRIDGE_ACCOUNT = "bridge_account"
    HUB_ACCOUNT = "hub_account"
    ISOLATED_CLUSTER = "isolated_cluster"
    FLOW_CONCENTRATION = "flow_concentration"
    NETWORK_DENSITY_ANOMALY = "network_density_anomaly"
    BETWEENNESS_EXPLOITATION = "betweenness_exploitation"
    EIGENVECTOR_DOMINANCE = "eigenvector_dominance"
    COMMUNITY_ISOLATION = "community_isolation"
    GRAPH_DIAMETER_ANOMALY = "graph_diameter_anomaly"

class RiskLevel(Enum):
    """Risk severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class PatternResult:
    """Data class for pattern analysis results"""
    pattern_type: PatternType
    risk_level: RiskLevel
    confidence: float
    description: str
    affected_accounts: List[str]
    transaction_ids: List[str]
    evidence: Dict[str, Any]
    recommendation: str
    timestamp: datetime

class AdvancedPatternAnalyzer:
    """
    Advanced Pattern Analyzer for AML Detection
    
    This class implements sophisticated algorithms to detect various money laundering patterns
    including structuring, layering, circular transactions, and other suspicious activities.
    """
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.isolation_forest = IsolationForest(contamination=0.1, random_state=42)
        self.dbscan = DBSCAN(eps=0.5, min_samples=3)
        self.patterns_cache = {}
        
        # Threshold configurations
        self.thresholds = {
            'structuring_amount': 10000,  # Just below reporting threshold
            'structuring_frequency': 5,   # Number of transactions in timeframe
            'circular_path_length': 3,    # Minimum path length for circular detection
            'rapid_movement_hours': 24,   # Time window for rapid movement
            'velocity_multiplier': 3,     # Standard deviations for velocity anomaly
            'round_amount_threshold': 0.8, # Percentage of round amounts to flag
            'geography_distance_km': 1000,  # Unusual geographic distance
            'time_anomaly_hours': [22, 6],  # Unusual transaction hours
            
            # Advanced graph-based thresholds
            'centrality_percentile': 95,   # Top percentile for centrality anomalies
            'betweenness_threshold': 0.1,  # Betweenness centrality threshold
            'eigenvector_threshold': 0.1,  # Eigenvector centrality threshold
            'clustering_coeff_threshold': 0.8,  # Local clustering coefficient
            'bridge_score_threshold': 0.7,  # Bridge account detection
            'hub_degree_threshold': 10,    # Minimum degree for hub detection
            'flow_concentration_ratio': 0.8,  # Flow concentration threshold
            'community_modularity_threshold': 0.3,  # Community isolation threshold
            'diameter_anomaly_threshold': 2.0,  # Graph diameter anomaly multiplier
            'density_anomaly_threshold': 3.0   # Network density standard deviations
        }
    
    def analyze_patterns(self, transactions: List[Dict], accounts: List[Dict] = None) -> List[PatternResult]:
        """
        Main method to analyze all patterns in the transaction data
        
        Args:
            transactions: List of transaction dictionaries
            accounts: Optional list of account information
            
        Returns:
            List of PatternResult objects containing detected patterns
        """
        logger.info(f"Starting pattern analysis on {len(transactions)} transactions")
        
        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(transactions)
        
        if df.empty:
            logger.warning("No transactions provided for analysis")
            return []
        
        logger.info(f"DataFrame columns: {df.columns.tolist()}")
        logger.info(f"Sample data:\n{df.head(2)}")
        
        # Handle different column name formats
        column_mappings = {
            'source': ['source', 'sender_account', 'Sender_account', 'from_account'],
            'target': ['target', 'receiver_account', 'Receiver_account', 'to_account'],
            'amount': ['amount', 'Amount', 'amount_received', 'transaction_amount'],
            'timestamp': ['timestamp', 'Date', 'date', 'transaction_date', 'Time']
        }
        
        # Map columns to standard names
        for standard_name, possible_names in column_mappings.items():
            if standard_name not in df.columns:
                for possible_name in possible_names:
                    if possible_name in df.columns:
                        df[standard_name] = df[possible_name]
                        logger.info(f"Mapped column '{possible_name}' to '{standard_name}'")
                        break
        
        # Ensure required columns exist
        required_columns = ['amount', 'timestamp', 'source', 'target']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.error(f"Missing required columns: {missing_columns}")
            return []
        
        # Convert timestamp to datetime if it's not already
        if 'timestamp' in df.columns:
            try:
                # Handle different timestamp formats
                if 'Date' in df.columns and 'Time' in df.columns:
                    # Combine Date and Time columns
                    df['timestamp'] = pd.to_datetime(df['Date'] + ' ' + df['Time'], errors='coerce')
                else:
                    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
                
                # Remove rows with invalid timestamps
                invalid_timestamps = df['timestamp'].isna().sum()
                if invalid_timestamps > 0:
                    logger.warning(f"Found {invalid_timestamps} invalid timestamps, removing them")
                    df = df.dropna(subset=['timestamp'])
                
                df = df.sort_values('timestamp')
                logger.info(f"Timestamp range: {df['timestamp'].min()} to {df['timestamp'].max()}")
            except Exception as e:
                logger.error(f"Error processing timestamps: {e}")
                return []
        
        results = []
        
        # Run all pattern detection methods
        try:
            results.extend(self._detect_structuring(df))
            results.extend(self._detect_layering(df))
            results.extend(self._detect_circular_transactions(df))
            results.extend(self._detect_rapid_movement(df))
            results.extend(self._detect_velocity_anomalies(df))
            results.extend(self._detect_round_amounts(df))
            results.extend(self._detect_smurfing(df))
            results.extend(self._detect_time_anomalies(df))
            results.extend(self._detect_geographic_anomalies(df))
            results.extend(self._detect_shell_companies(df, accounts))
            
            # Advanced graph-based detection methods
            results.extend(self._detect_graph_centrality_anomalies(df))
            results.extend(self._detect_bridge_accounts(df))
            results.extend(self._detect_hub_accounts(df))
            results.extend(self._detect_isolated_clusters(df))
            results.extend(self._detect_flow_concentration(df))
            results.extend(self._detect_network_density_anomalies(df))
            results.extend(self._detect_betweenness_exploitation(df))
            results.extend(self._detect_eigenvector_dominance(df))
            results.extend(self._detect_community_isolation(df))
            results.extend(self._detect_graph_diameter_anomalies(df))
            
        except Exception as e:
            logger.error(f"Error during pattern analysis: {str(e)}")
        
        # Sort results by risk level and confidence
        results.sort(key=lambda x: (x.risk_level.value, -x.confidence), reverse=True)
        
        logger.info(f"Pattern analysis completed. Found {len(results)} suspicious patterns")
        return results
    
    def _detect_structuring(self, df: pd.DataFrame) -> List[PatternResult]:
        """Detect structuring patterns (breaking large amounts into smaller ones)"""
        patterns = []
        threshold = self.thresholds['structuring_amount']
        frequency = self.thresholds['structuring_frequency']
        
        # Group by account and look for multiple transactions just below threshold
        for account in df['source'].unique():
            account_txns = df[df['source'] == account].copy()
            
            # Look for transactions just below the threshold within short time windows
            below_threshold = account_txns[
                (account_txns['amount'] < threshold) & 
                (account_txns['amount'] > threshold * 0.7)  # Between 70-100% of threshold
            ]
            
            if len(below_threshold) >= frequency:
                # Check if these transactions occurred within a short time window
                time_groups = []
                for _, group in below_threshold.groupby(pd.Grouper(key='timestamp', freq='D')):
                    if len(group) >= 3:  # 3 or more transactions in a day
                        time_groups.append(group)
                
                if time_groups:
                    total_amount = sum(group['amount'].sum() for group in time_groups)
                    confidence = min(0.95, len(below_threshold) / 10 * 0.8)
                    
                    risk_level = RiskLevel.HIGH if confidence > 0.8 else RiskLevel.MEDIUM
                    
                    patterns.append(PatternResult(
                        pattern_type=PatternType.STRUCTURING,
                        risk_level=risk_level,
                        confidence=confidence,
                        description=f"Account {account} conducted {len(below_threshold)} transactions just below ${threshold:,.2f} threshold, totaling ${total_amount:,.2f}",
                        affected_accounts=[account],
                        transaction_ids=below_threshold['transaction_id'].tolist() if 'transaction_id' in below_threshold.columns else [],
                        evidence={
                            'transaction_count': len(below_threshold),
                            'total_amount': total_amount,
                            'average_amount': below_threshold['amount'].mean(),
                            'time_span_days': (below_threshold['timestamp'].max() - below_threshold['timestamp'].min()).days
                        },
                        recommendation="Investigate for potential structuring to avoid reporting requirements",
                        timestamp=datetime.now()
                    ))
        
        return patterns
    
    def _detect_layering(self, df: pd.DataFrame) -> List[PatternResult]:
        """Detect layering patterns (complex transaction chains)"""
        patterns = []
        
        # Build transaction network
        G = nx.DiGraph()
        for _, row in df.iterrows():
            G.add_edge(row['source'], row['target'], 
                      amount=row['amount'], 
                      timestamp=row['timestamp'])
        
        # Find complex paths (potential layering)
        for node in G.nodes():
            # Find all paths of length 3+ starting from this node
            try:
                for target in G.nodes():
                    if node != target:
                        paths = list(nx.all_simple_paths(G, node, target, cutoff=6))
                        for path in paths:
                            if len(path) >= 4:  # Path length 4+ indicates complex layering
                                # Calculate total amount through this path
                                path_amounts = []
                                for i in range(len(path) - 1):
                                    edge_data = G[path[i]][path[i+1]]
                                    path_amounts.append(edge_data['amount'])
                                
                                if path_amounts and len(set(path)) == len(path):  # No repeated nodes
                                    confidence = min(0.9, len(path) / 8 * 0.7)
                                    risk_level = RiskLevel.HIGH if len(path) >= 5 else RiskLevel.MEDIUM
                                    
                                    patterns.append(PatternResult(
                                        pattern_type=PatternType.LAYERING,
                                        risk_level=risk_level,
                                        confidence=confidence,
                                        description=f"Complex transaction chain detected: {' → '.join(path[:3])}... ({len(path)} accounts involved)",
                                        affected_accounts=path,
                                        transaction_ids=[],
                                        evidence={
                                            'path_length': len(path),
                                            'total_amount': sum(path_amounts),
                                            'path': path,
                                            'amounts': path_amounts
                                        },
                                        recommendation="Investigate complex transaction chain for potential layering activity",
                                        timestamp=datetime.now()
                                    ))
                                    
                                    # Limit results to avoid overwhelming output
                                    if len(patterns) >= 10:
                                        return patterns
            except Exception as e:
                logger.debug(f"Error analyzing paths from {node}: {str(e)}")
                continue
        
        return patterns
    
    def _detect_circular_transactions(self, df: pd.DataFrame) -> List[PatternResult]:
        """Detect circular transaction patterns"""
        patterns = []
        
        # Build directed graph
        G = nx.DiGraph()
        transaction_map = {}
        
        for idx, row in df.iterrows():
            edge_id = f"{row['source']}_{row['target']}_{idx}"
            G.add_edge(row['source'], row['target'], 
                      amount=row['amount'], 
                      timestamp=row['timestamp'],
                      edge_id=edge_id)
            transaction_map[edge_id] = row
        
        # Find strongly connected components (potential circular flows)
        try:
            cycles = list(nx.simple_cycles(G))
            
            for cycle in cycles:
                if len(cycle) >= self.thresholds['circular_path_length']:
                    # Calculate cycle properties
                    cycle_amounts = []
                    cycle_times = []
                    
                    for i in range(len(cycle)):
                        source = cycle[i]
                        target = cycle[(i + 1) % len(cycle)]
                        
                        if G.has_edge(source, target):
                            edge_data = G[source][target]
                            cycle_amounts.append(edge_data['amount'])
                            cycle_times.append(edge_data['timestamp'])
                    
                    if cycle_amounts:
                        total_amount = sum(cycle_amounts)
                        time_span = (max(cycle_times) - min(cycle_times)).total_seconds() / 3600  # hours
                        
                        confidence = min(0.95, len(cycle) / 6 * 0.8)
                        risk_level = RiskLevel.CRITICAL if len(cycle) >= 5 else RiskLevel.HIGH
                        
                        patterns.append(PatternResult(
                            pattern_type=PatternType.CIRCULAR_TRANSACTIONS,
                            risk_level=risk_level,
                            confidence=confidence,
                            description=f"Circular transaction pattern detected involving {len(cycle)} accounts with total amount ${total_amount:,.2f}",
                            affected_accounts=cycle,
                            transaction_ids=[],
                            evidence={
                                'cycle_length': len(cycle),
                                'total_amount': total_amount,
                                'time_span_hours': time_span,
                                'cycle_path': cycle,
                                'amounts': cycle_amounts
                            },
                            recommendation="Investigate circular flow pattern for potential money laundering",
                            timestamp=datetime.now()
                        ))
        except Exception as e:
            logger.debug(f"Error detecting circular transactions: {str(e)}")
        
        return patterns
    
    def _detect_rapid_movement(self, df: pd.DataFrame) -> List[PatternResult]:
        """Detect rapid movement of funds"""
        patterns = []
        time_window = timedelta(hours=self.thresholds['rapid_movement_hours'])
        
        # Group by amount ranges to find similar amounts moving quickly
        for _, group in df.groupby(df['amount'].round(-3)):  # Group by thousands
            if len(group) >= 3:
                group_sorted = group.sort_values('timestamp')
                
                for i in range(len(group_sorted) - 2):
                    window_transactions = group_sorted.iloc[i:i+3]
                    time_diff = window_transactions['timestamp'].max() - window_transactions['timestamp'].min()
                    
                    if time_diff <= time_window:
                        accounts_involved = set(window_transactions['source']).union(set(window_transactions['target']))
                        total_amount = window_transactions['amount'].sum()
                        
                        confidence = min(0.9, len(accounts_involved) / 5 * 0.7)
                        risk_level = RiskLevel.HIGH if len(accounts_involved) >= 4 else RiskLevel.MEDIUM
                        
                        patterns.append(PatternResult(
                            pattern_type=PatternType.RAPID_MOVEMENT,
                            risk_level=risk_level,
                            confidence=confidence,
                            description=f"Rapid movement of ${total_amount:,.2f} through {len(accounts_involved)} accounts within {time_diff.total_seconds()/3600:.1f} hours",
                            affected_accounts=list(accounts_involved),
                            transaction_ids=window_transactions['transaction_id'].tolist() if 'transaction_id' in window_transactions.columns else [],
                            evidence={
                                'accounts_count': len(accounts_involved),
                                'total_amount': total_amount,
                                'time_span_hours': time_diff.total_seconds() / 3600,
                                'transaction_count': len(window_transactions)
                            },
                            recommendation="Investigate rapid fund movement pattern",
                            timestamp=datetime.now()
                        ))
        
        return patterns
    
    def _detect_velocity_anomalies(self, df: pd.DataFrame) -> List[PatternResult]:
        """Detect unusual transaction velocity patterns"""
        patterns = []
        
        # Calculate transaction velocity for each account
        account_velocities = {}
        
        for account in set(df['source']).union(set(df['target'])):
            account_txns = df[(df['source'] == account) | (df['target'] == account)]
            
            if len(account_txns) >= 5:  # Need sufficient data
                # Calculate daily transaction counts
                daily_counts = account_txns.groupby(account_txns['timestamp'].dt.date).size()
                
                if len(daily_counts) >= 3:  # Need at least 3 days of data
                    mean_velocity = daily_counts.mean()
                    std_velocity = daily_counts.std()
                    
                    if std_velocity > 0:
                        # Find anomalous days
                        anomalous_days = daily_counts[
                            daily_counts > mean_velocity + self.thresholds['velocity_multiplier'] * std_velocity
                        ]
                        
                        if len(anomalous_days) > 0:
                            max_velocity_day = anomalous_days.idxmax()
                            max_velocity = anomalous_days.max()
                            
                            confidence = min(0.9, (max_velocity - mean_velocity) / mean_velocity * 0.5)
                            risk_level = RiskLevel.HIGH if max_velocity > mean_velocity * 5 else RiskLevel.MEDIUM
                            
                            patterns.append(PatternResult(
                                pattern_type=PatternType.VELOCITY_ANOMALY,
                                risk_level=risk_level,
                                confidence=confidence,
                                description=f"Account {account} showed unusual transaction velocity: {max_velocity} transactions on {max_velocity_day} (normal: {mean_velocity:.1f})",
                                affected_accounts=[account],
                                transaction_ids=[],
                                evidence={
                                    'normal_velocity': mean_velocity,
                                    'anomalous_velocity': max_velocity,
                                    'anomalous_date': str(max_velocity_day),
                                    'velocity_ratio': max_velocity / mean_velocity
                                },
                                recommendation="Investigate unusual transaction velocity pattern",
                                timestamp=datetime.now()
                            ))
        
        return patterns
    
    def _detect_round_amounts(self, df: pd.DataFrame) -> List[PatternResult]:
        """Detect suspicious round amount patterns"""
        patterns = []
        
        # Define round amounts (ending in multiple zeros)
        df['is_round'] = df['amount'].apply(lambda x: x % 1000 == 0 and x >= 1000)
        
        for account in df['source'].unique():
            account_txns = df[df['source'] == account]
            
            if len(account_txns) >= 5:  # Need sufficient transactions
                round_ratio = account_txns['is_round'].mean()
                
                if round_ratio >= self.thresholds['round_amount_threshold']:
                    round_txns = account_txns[account_txns['is_round']]
                    total_round_amount = round_txns['amount'].sum()
                    
                    confidence = min(0.85, round_ratio * 0.9)
                    risk_level = RiskLevel.MEDIUM if round_ratio >= 0.9 else RiskLevel.LOW
                    
                    patterns.append(PatternResult(
                        pattern_type=PatternType.ROUND_AMOUNT,
                        risk_level=risk_level,
                        confidence=confidence,
                        description=f"Account {account} has {round_ratio*100:.1f}% round amount transactions (${total_round_amount:,.2f} total)",
                        affected_accounts=[account],
                        transaction_ids=round_txns['transaction_id'].tolist() if 'transaction_id' in round_txns.columns else [],
                        evidence={
                            'round_ratio': round_ratio,
                            'round_transaction_count': len(round_txns),
                            'total_round_amount': total_round_amount,
                            'total_transactions': len(account_txns)
                        },
                        recommendation="Investigate high frequency of round amount transactions",
                        timestamp=datetime.now()
                    ))
        
        return patterns
    
    def _detect_smurfing(self, df: pd.DataFrame) -> List[PatternResult]:
        """Detect smurfing patterns (multiple small transactions to avoid detection)"""
        patterns = []
        
        # Look for coordinated small transactions from multiple sources to same target
        for target in df['target'].value_counts().head(20).index:  # Top 20 recipients
            target_txns = df[df['target'] == target]
            
            # Group by day and look for multiple small transactions
            daily_groups = target_txns.groupby(target_txns['timestamp'].dt.date)
            
            for date, day_txns in daily_groups:
                if len(day_txns) >= 5:  # Multiple transactions in one day
                    unique_sources = day_txns['source'].nunique()
                    total_amount = day_txns['amount'].sum()
                    avg_amount = day_txns['amount'].mean()
                    
                    # Check if transactions are small but numerous from different sources
                    if unique_sources >= 3 and avg_amount < 5000 and len(day_txns) >= 5:
                        confidence = min(0.9, (unique_sources * len(day_txns)) / 50 * 0.8)
                        risk_level = RiskLevel.HIGH if unique_sources >= 5 else RiskLevel.MEDIUM
                        
                        patterns.append(PatternResult(
                            pattern_type=PatternType.SMURFING,
                            risk_level=risk_level,
                            confidence=confidence,
                            description=f"Potential smurfing detected: {len(day_txns)} small transactions from {unique_sources} sources to {target} on {date}, totaling ${total_amount:,.2f}",
                            affected_accounts=[target] + day_txns['source'].unique().tolist(),
                            transaction_ids=day_txns['transaction_id'].tolist() if 'transaction_id' in day_txns.columns else [],
                            evidence={
                                'transaction_count': len(day_txns),
                                'unique_sources': unique_sources,
                                'total_amount': total_amount,
                                'average_amount': avg_amount,
                                'date': str(date)
                            },
                            recommendation="Investigate coordinated small transactions pattern",
                            timestamp=datetime.now()
                        ))
        
        return patterns
    
    def _detect_time_anomalies(self, df: pd.DataFrame) -> List[PatternResult]:
        """Detect unusual timing patterns"""
        patterns = []
        
        if 'timestamp' not in df.columns:
            return patterns
        
        # Extract hour from timestamp
        df['hour'] = df['timestamp'].dt.hour
        unusual_hours = set(range(self.thresholds['time_anomaly_hours'][0], 24)).union(
            set(range(0, self.thresholds['time_anomaly_hours'][1] + 1))
        )
        
        # Find accounts with high proportion of unusual hour transactions
        for account in df['source'].unique():
            account_txns = df[df['source'] == account]
            
            if len(account_txns) >= 10:  # Need sufficient transactions
                unusual_txns = account_txns[account_txns['hour'].isin(unusual_hours)]
                unusual_ratio = len(unusual_txns) / len(account_txns)
                
                if unusual_ratio >= 0.3:  # 30% or more transactions at unusual hours
                    total_unusual_amount = unusual_txns['amount'].sum()
                    
                    confidence = min(0.8, unusual_ratio * 0.9)
                    risk_level = RiskLevel.MEDIUM if unusual_ratio >= 0.5 else RiskLevel.LOW
                    
                    patterns.append(PatternResult(
                        pattern_type=PatternType.TIME_ANOMALY,
                        risk_level=risk_level,
                        confidence=confidence,
                        description=f"Account {account} conducts {unusual_ratio*100:.1f}% of transactions during unusual hours (${total_unusual_amount:,.2f})",
                        affected_accounts=[account],
                        transaction_ids=unusual_txns['transaction_id'].tolist() if 'transaction_id' in unusual_txns.columns else [],
                        evidence={
                            'unusual_ratio': unusual_ratio,
                            'unusual_transaction_count': len(unusual_txns),
                            'total_unusual_amount': total_unusual_amount,
                            'most_common_hour': unusual_txns['hour'].mode().iloc[0] if len(unusual_txns) > 0 else None
                        },
                        recommendation="Investigate transactions occurring at unusual hours",
                        timestamp=datetime.now()
                    ))
        
        return patterns
    
    def _detect_geographic_anomalies(self, df: pd.DataFrame) -> List[PatternResult]:
        """Detect unusual geographic patterns (placeholder - would need geographic data)"""
        patterns = []
        
        # This would require actual geographic data for source/target locations
        # For now, we'll look for patterns in bank codes or location identifiers
        
        if 'from_bank' in df.columns and 'to_bank' in df.columns:
            # Look for unusual international patterns
            international_txns = df[df['from_bank'] != df['to_bank']]
            
            if len(international_txns) > 0:
                # Group by account and check for high international activity
                for account in df['source'].unique():
                    account_txns = df[df['source'] == account]
                    account_international = international_txns[international_txns['source'] == account]
                    
                    if len(account_txns) >= 5 and len(account_international) >= 3:
                        international_ratio = len(account_international) / len(account_txns)
                        
                        if international_ratio >= 0.5:  # 50% or more international
                            unique_countries = account_international['to_bank'].nunique()
                            total_international_amount = account_international['amount'].sum()
                            
                            confidence = min(0.7, international_ratio * unique_countries / 10)
                            risk_level = RiskLevel.MEDIUM if unique_countries >= 3 else RiskLevel.LOW
                            
                            patterns.append(PatternResult(
                                pattern_type=PatternType.UNUSUAL_GEOGRAPHY,
                                risk_level=risk_level,
                                confidence=confidence,
                                description=f"Account {account} shows high international activity: {international_ratio*100:.1f}% to {unique_countries} countries (${total_international_amount:,.2f})",
                                affected_accounts=[account],
                                transaction_ids=account_international['transaction_id'].tolist() if 'transaction_id' in account_international.columns else [],
                                evidence={
                                    'international_ratio': international_ratio,
                                    'unique_countries': unique_countries,
                                    'total_international_amount': total_international_amount,
                                    'countries': account_international['to_bank'].unique().tolist()
                                },
                                recommendation="Investigate high international transaction activity",
                                timestamp=datetime.now()
                            ))
        
        return patterns
    
    def _detect_shell_companies(self, df: pd.DataFrame, accounts: List[Dict] = None) -> List[PatternResult]:
        """Detect potential shell company patterns"""
        patterns = []
        
        if not accounts:
            return patterns
        
        # Convert accounts to DataFrame
        accounts_df = pd.DataFrame(accounts)
        
        # Look for accounts with high transaction volume but low variety
        transaction_stats = df.groupby('source').agg({
            'amount': ['count', 'sum', 'mean', 'std'],
            'target': 'nunique',
            'timestamp': ['min', 'max']
        }).round(2)
        
        transaction_stats.columns = ['tx_count', 'total_amount', 'avg_amount', 'amount_std', 'unique_targets', 'first_tx', 'last_tx']
        transaction_stats = transaction_stats.reset_index()
        
        for _, row in transaction_stats.iterrows():
            account = row['source']
            
            # Shell company indicators:
            # 1. High transaction volume
            # 2. Low number of unique counterparties
            # 3. Short operational period
            # 4. Round amounts
            
            if row['tx_count'] >= 10 and row['unique_targets'] <= 3:
                operational_days = (row['last_tx'] - row['first_tx']).days + 1
                
                # Calculate shell company score
                shell_score = 0
                evidence = {}
                
                # High volume, few counterparties
                if row['tx_count'] >= 20 and row['unique_targets'] <= 2:
                    shell_score += 0.3
                    evidence['concentrated_activity'] = True
                
                # Short operational period with high activity
                if operational_days <= 30 and row['tx_count'] >= 15:
                    shell_score += 0.2
                    evidence['short_operational_period'] = operational_days
                
                # High proportion of round amounts
                account_txns = df[df['source'] == account]
                round_amounts = account_txns[account_txns['amount'] % 1000 == 0]
                if len(round_amounts) / len(account_txns) >= 0.7:
                    shell_score += 0.2
                    evidence['high_round_amounts'] = len(round_amounts) / len(account_txns)
                
                # Very regular amounts (low standard deviation)
                if row['amount_std'] < row['avg_amount'] * 0.1:
                    shell_score += 0.2
                    evidence['regular_amounts'] = True
                
                if shell_score >= 0.4:  # Threshold for shell company suspicion
                    confidence = min(0.9, shell_score)
                    risk_level = RiskLevel.HIGH if shell_score >= 0.7 else RiskLevel.MEDIUM
                    
                    patterns.append(PatternResult(
                        pattern_type=PatternType.SHELL_COMPANY,
                        risk_level=risk_level,
                        confidence=confidence,
                        description=f"Account {account} exhibits shell company characteristics: {row['tx_count']} transactions to only {row['unique_targets']} counterparties in {operational_days} days",
                        affected_accounts=[account],
                        transaction_ids=account_txns['transaction_id'].tolist() if 'transaction_id' in account_txns.columns else [],
                        evidence={
                            'shell_score': shell_score,
                            'transaction_count': int(row['tx_count']),
                            'unique_counterparties': int(row['unique_targets']),
                            'operational_days': operational_days,
                            'total_amount': float(row['total_amount']),
                            **evidence
                        },
                        recommendation="Investigate for potential shell company activity",
                        timestamp=datetime.now()
                    ))
        
        return patterns
    
    def _build_transaction_graph(self, df: pd.DataFrame, weighted: bool = True) -> nx.DiGraph:
        """Build a weighted directed graph from transaction data"""
        G = nx.DiGraph()
        
        # Add edges with weights and attributes
        for _, row in df.iterrows():
            source = str(row['source']).strip() if row['source'] else None
            target = str(row['target']).strip() if row['target'] else None
            amount = row['amount']
            timestamp = row['timestamp']
            
            # Skip if source or target is empty
            if not source or not target or source == '' or target == '' or source == 'nan' or target == 'nan':
                logger.debug(f"Skipping transaction with empty source ({source}) or target ({target})")
                continue
            
            if G.has_edge(source, target):
                # Aggregate multiple transactions between same accounts
                G[source][target]['weight'] += amount
                G[source][target]['count'] += 1
                G[source][target]['amounts'].append(amount)
                G[source][target]['timestamps'].append(timestamp)
            else:
                G.add_edge(source, target, 
                          weight=amount if weighted else 1,
                          count=1,
                          amounts=[amount],
                          timestamps=[timestamp])
        
        return G
    
    def _calculate_graph_metrics(self, G: nx.DiGraph) -> Dict[str, Any]:
        """Calculate comprehensive graph metrics"""
        metrics = {}
        
        try:
            # Basic graph properties
            metrics['num_nodes'] = G.number_of_nodes()
            metrics['num_edges'] = G.number_of_edges()
            metrics['density'] = nx.density(G)
            
            # Convert to undirected for some metrics
            G_undirected = G.to_undirected()
            
            # Centrality measures
            metrics['betweenness_centrality'] = nx.betweenness_centrality(G, weight='weight')
            metrics['closeness_centrality'] = nx.closeness_centrality(G, distance='weight')
            metrics['eigenvector_centrality'] = nx.eigenvector_centrality(G, weight='weight', max_iter=1000)
            metrics['pagerank'] = nx.pagerank(G, weight='weight')
            
            # Degree centralities
            metrics['in_degree_centrality'] = nx.in_degree_centrality(G)
            metrics['out_degree_centrality'] = nx.out_degree_centrality(G)
            
            # Clustering and community structure
            metrics['clustering_coefficient'] = nx.clustering(G_undirected, weight='weight')
            metrics['transitivity'] = nx.transitivity(G_undirected)
            
            # Path metrics
            if nx.is_weakly_connected(G):
                metrics['diameter'] = nx.diameter(G_undirected)
                metrics['average_path_length'] = nx.average_shortest_path_length(G_undirected, weight='weight')
            else:
                # For disconnected graphs, calculate for largest component
                largest_cc = max(nx.weakly_connected_components(G), key=len)
                subgraph = G.subgraph(largest_cc).to_undirected()
                if len(subgraph) > 1:
                    metrics['diameter'] = nx.diameter(subgraph)
                    metrics['average_path_length'] = nx.average_shortest_path_length(subgraph, weight='weight')
            
            # Community detection using modularity
            communities = nx.community.greedy_modularity_communities(G_undirected, weight='weight')
            metrics['num_communities'] = len(communities)
            metrics['modularity'] = nx.community.modularity(G_undirected, communities, weight='weight')
            metrics['communities'] = communities
            
        except Exception as e:
            logger.debug(f"Error calculating graph metrics: {str(e)}")
            
        return metrics
    
    def _detect_graph_centrality_anomalies(self, df: pd.DataFrame) -> List[PatternResult]:
        """Detect accounts with anomalous centrality measures"""
        patterns = []
        
        try:
            G = self._build_transaction_graph(df)
            metrics = self._calculate_graph_metrics(G)
            
            if not metrics:
                return patterns
            
            # Analyze betweenness centrality anomalies
            betweenness = metrics.get('betweenness_centrality', {})
            if betweenness:
                threshold = np.percentile(list(betweenness.values()), self.thresholds['centrality_percentile'])
                
                for account, centrality in betweenness.items():
                    if centrality > threshold and centrality > self.thresholds['betweenness_threshold']:
                        confidence = min(0.9, centrality * 2)
                        risk_level = RiskLevel.HIGH if centrality > 0.2 else RiskLevel.MEDIUM
                        
                        patterns.append(PatternResult(
                            pattern_type=PatternType.GRAPH_CENTRALITY_ANOMALY,
                            risk_level=risk_level,
                            confidence=confidence,
                            description=f"Account {account} shows high betweenness centrality ({centrality:.3f}), indicating potential intermediary role in money flows",
                            affected_accounts=[account],
                            transaction_ids=[],
                            evidence={
                                'betweenness_centrality': centrality,
                                'centrality_rank': sorted(betweenness.values(), reverse=True).index(centrality) + 1,
                                'total_accounts': len(betweenness),
                                'threshold': threshold
                            },
                            recommendation="Investigate account's role as potential financial intermediary",
                            timestamp=datetime.now()
                        ))
            
        except Exception as e:
            logger.debug(f"Error detecting centrality anomalies: {str(e)}")
        
        return patterns
    
    def _detect_bridge_accounts(self, df: pd.DataFrame) -> List[PatternResult]:
        """Detect bridge accounts that connect otherwise disconnected components"""
        patterns = []
        
        try:
            G = self._build_transaction_graph(df)
            G_undirected = G.to_undirected()
            
            # Find bridges (edges whose removal increases number of connected components)
            bridges = list(nx.bridges(G_undirected))
            
            if bridges:
                # Find accounts that appear in multiple bridges
                bridge_accounts = defaultdict(int)
                for bridge in bridges:
                    bridge_accounts[bridge[0]] += 1
                    bridge_accounts[bridge[1]] += 1
                
                for account, bridge_count in bridge_accounts.items():
                    if bridge_count >= 2:  # Account appears in multiple bridges
                        # Calculate bridge score
                        account_edges = list(G.in_edges(account)) + list(G.out_edges(account))
                        total_flow = sum(G[u][v]['weight'] for u, v in account_edges if G.has_edge(u, v))
                        
                        confidence = min(0.95, bridge_count / len(bridges) * 0.8)
                        risk_level = RiskLevel.HIGH if bridge_count >= 3 else RiskLevel.MEDIUM
                        
                        patterns.append(PatternResult(
                            pattern_type=PatternType.BRIDGE_ACCOUNT,
                            risk_level=risk_level,
                            confidence=confidence,
                            description=f"Account {account} acts as bridge in {bridge_count} critical connections, controlling ${total_flow:,.2f} in flows",
                            affected_accounts=[account],
                            transaction_ids=[],
                            evidence={
                                'bridge_count': bridge_count,
                                'total_bridges': len(bridges),
                                'total_flow_controlled': total_flow,
                                'bridge_ratio': bridge_count / len(bridges)
                            },
                            recommendation="Investigate bridge account's role in network connectivity",
                            timestamp=datetime.now()
                        ))
        
        except Exception as e:
            logger.debug(f"Error detecting bridge accounts: {str(e)}")
        
        return patterns
    
    def _detect_hub_accounts(self, df: pd.DataFrame) -> List[PatternResult]:
        """Detect hub accounts with unusually high connectivity"""
        patterns = []
        
        try:
            G = self._build_transaction_graph(df)
            
            # Calculate degree statistics
            degrees = dict(G.degree())
            if not degrees:
                return patterns
            
            degree_values = list(degrees.values())
            mean_degree = np.mean(degree_values)
            std_degree = np.std(degree_values)
            
            # Find accounts with exceptionally high degree
            for account, degree in degrees.items():
                if degree >= self.thresholds['hub_degree_threshold'] and degree > mean_degree + 2 * std_degree:
                    
                    # Calculate additional hub metrics
                    in_degree = G.in_degree(account)
                    out_degree = G.out_degree(account)
                    
                    # Calculate total flow through this hub
                    total_inflow = sum(G[u][account]['weight'] for u in G.predecessors(account))
                    total_outflow = sum(G[account][v]['weight'] for v in G.successors(account))
                    
                    confidence = min(0.9, degree / max(degree_values) * 0.8)
                    risk_level = RiskLevel.HIGH if degree > mean_degree + 3 * std_degree else RiskLevel.MEDIUM
                    
                    patterns.append(PatternResult(
                        pattern_type=PatternType.HUB_ACCOUNT,
                        risk_level=risk_level,
                        confidence=confidence,
                        description=f"Account {account} is a major hub with {degree} connections ({in_degree} in, {out_degree} out), processing ${total_inflow + total_outflow:,.2f}",
                        affected_accounts=[account],
                        transaction_ids=[],
                        evidence={
                            'total_degree': degree,
                            'in_degree': in_degree,
                            'out_degree': out_degree,
                            'total_inflow': total_inflow,
                            'total_outflow': total_outflow,
                            'degree_z_score': (degree - mean_degree) / std_degree if std_degree > 0 else 0
                        },
                        recommendation="Investigate hub account's role in transaction network",
                        timestamp=datetime.now()
                    ))
        
        except Exception as e:
            logger.debug(f"Error detecting hub accounts: {str(e)}")
        
        return patterns
    
    def _detect_isolated_clusters(self, df: pd.DataFrame) -> List[PatternResult]:
        """Detect isolated clusters that may indicate layering schemes"""
        patterns = []
        
        try:
            G = self._build_transaction_graph(df)
            G_undirected = G.to_undirected()
            
            # Find connected components
            components = list(nx.connected_components(G_undirected))
            
            # Analyze components for suspicious patterns
            for component in components:
                if len(component) >= 3:  # Focus on components with 3+ accounts
                    subgraph = G.subgraph(component)
                    
                    # Calculate component metrics
                    total_flow = sum(data['weight'] for _, _, data in subgraph.edges(data=True))
                    density = nx.density(subgraph)
                    
                    # Check if component is highly isolated (few external connections)
                    external_connections = 0
                    for node in component:
                        external_connections += len([n for n in G.neighbors(node) if n not in component])
                    
                    isolation_ratio = 1 - (external_connections / (len(component) * (len(G.nodes()) - len(component))))
                    
                    if isolation_ratio > 0.8 and density > 0.5:  # Highly isolated and dense
                        confidence = min(0.9, isolation_ratio * density)
                        risk_level = RiskLevel.HIGH if len(component) >= 5 else RiskLevel.MEDIUM
                        
                        patterns.append(PatternResult(
                            pattern_type=PatternType.ISOLATED_CLUSTER,
                            risk_level=risk_level,
                            confidence=confidence,
                            description=f"Isolated cluster of {len(component)} accounts with high internal density ({density:.2f}) and ${total_flow:,.2f} in flows",
                            affected_accounts=list(component),
                            transaction_ids=[],
                            evidence={
                                'cluster_size': len(component),
                                'cluster_density': density,
                                'total_flow': total_flow,
                                'isolation_ratio': isolation_ratio,
                                'external_connections': external_connections
                            },
                            recommendation="Investigate isolated cluster for potential layering scheme",
                            timestamp=datetime.now()
                        ))
        
        except Exception as e:
            logger.debug(f"Error detecting isolated clusters: {str(e)}")
        
        return patterns
    
    def _detect_flow_concentration(self, df: pd.DataFrame) -> List[PatternResult]:
        """Detect unusual concentration of transaction flows"""
        patterns = []
        
        try:
            G = self._build_transaction_graph(df)
            
            # Calculate flow concentration for each account
            for account in G.nodes():
                # Get all flows through this account
                inflows = [(u, G[u][account]['weight']) for u in G.predecessors(account)]
                outflows = [(G[account][v]['weight'], v) for v in G.successors(account)]
                
                if len(inflows) >= 2 and len(outflows) >= 2:
                    # Calculate Gini coefficient for flow concentration
                    inflow_amounts = [amount for _, amount in inflows]
                    outflow_amounts = [amount for amount, _ in outflows]
                    
                    inflow_gini = self._calculate_gini_coefficient(inflow_amounts)
                    outflow_gini = self._calculate_gini_coefficient(outflow_amounts)
                    
                    # High Gini coefficient indicates concentration
                    if inflow_gini > self.thresholds['flow_concentration_ratio'] or outflow_gini > self.thresholds['flow_concentration_ratio']:
                        total_flow = sum(inflow_amounts) + sum(outflow_amounts)
                        
                        confidence = min(0.9, max(inflow_gini, outflow_gini))
                        risk_level = RiskLevel.HIGH if max(inflow_gini, outflow_gini) > 0.9 else RiskLevel.MEDIUM
                        
                        patterns.append(PatternResult(
                            pattern_type=PatternType.FLOW_CONCENTRATION,
                            risk_level=risk_level,
                            confidence=confidence,
                            description=f"Account {account} shows high flow concentration (Gini: in={inflow_gini:.2f}, out={outflow_gini:.2f}) with ${total_flow:,.2f} total flow",
                            affected_accounts=[account],
                            transaction_ids=[],
                            evidence={
                                'inflow_gini': inflow_gini,
                                'outflow_gini': outflow_gini,
                                'total_inflow': sum(inflow_amounts),
                                'total_outflow': sum(outflow_amounts),
                                'num_inflow_sources': len(inflows),
                                'num_outflow_targets': len(outflows)
                            },
                            recommendation="Investigate concentrated flow patterns for potential funnel account",
                            timestamp=datetime.now()
                        ))
        
        except Exception as e:
            logger.debug(f"Error detecting flow concentration: {str(e)}")
        
        return patterns
    
    def _detect_network_density_anomalies(self, df: pd.DataFrame) -> List[PatternResult]:
        """Detect anomalies in local network density"""
        patterns = []
        
        try:
            G = self._build_transaction_graph(df)
            G_undirected = G.to_undirected()
            
            # Calculate local clustering coefficient for each node
            clustering_coeffs = nx.clustering(G_undirected, weight='weight')
            
            if not clustering_coeffs:
                return patterns
            
            # Find accounts with unusually high local clustering
            coeff_values = list(clustering_coeffs.values())
            mean_clustering = np.mean(coeff_values)
            std_clustering = np.std(coeff_values)
            
            for account, coeff in clustering_coeffs.items():
                if coeff > self.thresholds['clustering_coeff_threshold'] and coeff > mean_clustering + self.thresholds['density_anomaly_threshold'] * std_clustering:
                    
                    # Get neighbors and their interconnections
                    neighbors = list(G_undirected.neighbors(account))
                    neighbor_subgraph = G_undirected.subgraph(neighbors + [account])
                    
                    total_flow = sum(G_undirected[u][v]['weight'] for u, v in neighbor_subgraph.edges() if G_undirected.has_edge(u, v))
                    
                    confidence = min(0.85, coeff * 0.9)
                    risk_level = RiskLevel.MEDIUM if coeff > 0.9 else RiskLevel.LOW
                    
                    patterns.append(PatternResult(
                        pattern_type=PatternType.NETWORK_DENSITY_ANOMALY,
                        risk_level=risk_level,
                        confidence=confidence,
                        description=f"Account {account} shows unusually high local network density (clustering={coeff:.3f}) with {len(neighbors)} interconnected neighbors",
                        affected_accounts=[account] + neighbors,
                        transaction_ids=[],
                        evidence={
                            'clustering_coefficient': coeff,
                            'num_neighbors': len(neighbors),
                            'total_local_flow': total_flow,
                            'clustering_z_score': (coeff - mean_clustering) / std_clustering if std_clustering > 0 else 0
                        },
                        recommendation="Investigate dense local network for potential coordinated activity",
                        timestamp=datetime.now()
                    ))
        
        except Exception as e:
            logger.debug(f"Error detecting network density anomalies: {str(e)}")
        
        return patterns
    
    def _detect_betweenness_exploitation(self, df: pd.DataFrame) -> List[PatternResult]:
        """Detect accounts exploiting betweenness positions for control"""
        patterns = []
        
        try:
            G = self._build_transaction_graph(df)
            
            # Calculate betweenness centrality
            betweenness = nx.betweenness_centrality(G, weight='weight')
            
            if not betweenness:
                return patterns
            
            # Find accounts with high betweenness that process large volumes
            for account, centrality in betweenness.items():
                if centrality > self.thresholds['betweenness_threshold']:
                    
                    # Calculate flow control metrics
                    shortest_paths_through = 0
                    total_controlled_flow = 0
                    
                    # Estimate flow controlled by this account
                    for source in G.nodes():
                        for target in G.nodes():
                            if source != target and source != account and target != account:
                                try:
                                    paths = list(nx.all_shortest_paths(G, source, target, weight='weight'))
                                    paths_through_account = [p for p in paths if account in p]
                                    if paths_through_account:
                                        shortest_paths_through += len(paths_through_account)
                                        # Add flow estimate
                                        if G.has_edge(source, target):
                                            total_controlled_flow += G[source][target]['weight']
                                except nx.NetworkXNoPath:
                                    continue
                    
                    if shortest_paths_through > 5:  # Account controls multiple paths
                        confidence = min(0.95, centrality * 2)
                        risk_level = RiskLevel.HIGH if centrality > 0.2 else RiskLevel.MEDIUM
                        
                        patterns.append(PatternResult(
                            pattern_type=PatternType.BETWEENNESS_EXPLOITATION,
                            risk_level=risk_level,
                            confidence=confidence,
                            description=f"Account {account} exploits betweenness position (centrality={centrality:.3f}) controlling {shortest_paths_through} critical paths",
                            affected_accounts=[account],
                            transaction_ids=[],
                            evidence={
                                'betweenness_centrality': centrality,
                                'paths_controlled': shortest_paths_through,
                                'estimated_controlled_flow': total_controlled_flow,
                                'control_ratio': shortest_paths_through / len(G.nodes()) if len(G.nodes()) > 0 else 0
                            },
                            recommendation="Investigate account's strategic position for potential flow control",
                            timestamp=datetime.now()
                        ))
        
        except Exception as e:
            logger.debug(f"Error detecting betweenness exploitation: {str(e)}")
        
        return patterns
    
    def _detect_eigenvector_dominance(self, df: pd.DataFrame) -> List[PatternResult]:
        """Detect accounts with dominant eigenvector centrality indicating influence"""
        patterns = []
        
        try:
            # Debug: Print data info
            logger.info(f"DataFrame shape: {df.shape}")
            logger.info(f"Columns: {df.columns.tolist()}")
            logger.info(f"Sample source values: {df['source'].unique()[:5] if 'source' in df.columns else 'NO SOURCE COLUMN'}")
            logger.info(f"Sample target values: {df['target'].unique()[:5] if 'target' in df.columns else 'NO TARGET COLUMN'}")
            
            # Check for empty account IDs
            if 'source' in df.columns and 'target' in df.columns:
                empty_sources = df['source'].isna() | (df['source'] == '') | (df['source'].str.strip() == '')
                empty_targets = df['target'].isna() | (df['target'] == '') | (df['target'].str.strip() == '')
                
                logger.info(f"Empty sources: {empty_sources.sum()}")
                logger.info(f"Empty targets: {empty_targets.sum()}")
                
                # Filter out rows with empty account IDs
                valid_df = df[~(empty_sources | empty_targets)].copy()
                logger.info(f"Valid transactions after filtering: {len(valid_df)}")
                
                if len(valid_df) == 0:
                    logger.warning("No valid transactions after filtering empty account IDs")
                    return patterns
                
                df = valid_df
            
            G = self._build_transaction_graph(df)
            
            # Calculate eigenvector centrality
            eigenvector = nx.eigenvector_centrality(G, weight='weight', max_iter=1000)
            
            if not eigenvector:
                return patterns
            
            # Find accounts with high eigenvector centrality
            max_centrality = max(eigenvector.values())
            
            for account, centrality in eigenvector.items():
                # Skip empty account IDs
                if not account or account == '' or str(account).strip() == '':
                    continue
                    
                if centrality > self.thresholds['eigenvector_threshold'] and centrality > max_centrality * 0.5:
                    
                    # Calculate influence metrics
                    connected_accounts = list(G.predecessors(account)) + list(G.successors(account))
                    high_centrality_connections = sum(1 for acc in connected_accounts if eigenvector.get(acc, 0) > np.mean(list(eigenvector.values())))
                    
                    total_flow = sum(G[u][account]['weight'] for u in G.predecessors(account)) + \
                                sum(G[account][v]['weight'] for v in G.successors(account))
                    
                    confidence = min(0.9, centrality / max_centrality * 0.8)
                    risk_level = RiskLevel.HIGH if centrality > max_centrality * 0.8 else RiskLevel.MEDIUM
                    
                    patterns.append(PatternResult(
                        pattern_type=PatternType.EIGENVECTOR_DOMINANCE,
                        risk_level=risk_level,
                        confidence=confidence,
                        description=f"ACCOUNT ID: {account} shows dominant influence (eigenvector={centrality:.3f}) with connections to {high_centrality_connections} other influential accounts",
                        affected_accounts=[account],
                        transaction_ids=[],
                        evidence={
                            'account_id': str(account),
                            'eigenvector_centrality': centrality,
                            'relative_dominance': centrality / max_centrality,
                            'influential_connections': high_centrality_connections,
                            'total_connections': len(connected_accounts),
                            'total_flow': total_flow,
                            'connected_account_ids': [str(acc) for acc in connected_accounts]
                        },
                        recommendation=f"Investigate account ID {account}'s dominant influence in transaction network",
                        timestamp=datetime.now()
                    ))
        
        except Exception as e:
            logger.debug(f"Error detecting eigenvector dominance: {str(e)}")
        
        return patterns
    
    def _detect_community_isolation(self, df: pd.DataFrame) -> List[PatternResult]:
        """Detect communities that are isolated from the main network"""
        patterns = []
        
        try:
            G = self._build_transaction_graph(df)
            G_undirected = G.to_undirected()
            
            # Detect communities using modularity-based method
            communities = nx.community.greedy_modularity_communities(G_undirected, weight='weight')
            
            if len(communities) <= 1:
                return patterns
            
            # Calculate modularity
            modularity = nx.community.modularity(G_undirected, communities, weight='weight')
            
            if modularity > self.thresholds['community_modularity_threshold']:
                # Analyze each community for isolation
                for i, community in enumerate(communities):
                    if len(community) >= 3:  # Focus on communities with 3+ accounts
                        
                        # Calculate external connections
                        external_edges = 0
                        internal_flow = 0
                        external_flow = 0
                        
                        for node in community:
                            for neighbor in G_undirected.neighbors(node):
                                if neighbor not in community:
                                    external_edges += 1
                                    if G.has_edge(node, neighbor):
                                        external_flow += G[node][neighbor]['weight']
                                    if G.has_edge(neighbor, node):
                                        external_flow += G[neighbor][node]['weight']
                                else:
                                    if G.has_edge(node, neighbor):
                                        internal_flow += G[node][neighbor]['weight']
                        
                        # Calculate isolation metrics
                        total_possible_external = len(community) * (len(G.nodes()) - len(community))
                        isolation_ratio = 1 - (external_edges / total_possible_external) if total_possible_external > 0 else 1
                        
                        if isolation_ratio > 0.7:  # Highly isolated community
                            confidence = min(0.9, isolation_ratio * 0.8)
                            risk_level = RiskLevel.HIGH if isolation_ratio > 0.9 else RiskLevel.MEDIUM
                            
                            patterns.append(PatternResult(
                                pattern_type=PatternType.COMMUNITY_ISOLATION,
                                risk_level=risk_level,
                                confidence=confidence,
                                description=f"Isolated community of {len(community)} accounts with {isolation_ratio:.2f} isolation ratio and ${internal_flow:,.2f} internal flow",
                                affected_accounts=list(community),
                                transaction_ids=[],
                                evidence={
                                    'community_size': len(community),
                                    'isolation_ratio': isolation_ratio,
                                    'internal_flow': internal_flow,
                                    'external_flow': external_flow,
                                    'modularity': modularity,
                                    'external_connections': external_edges
                                },
                                recommendation="Investigate isolated community for potential closed-loop laundering",
                                timestamp=datetime.now()
                            ))
        
        except Exception as e:
            logger.debug(f"Error detecting community isolation: {str(e)}")
        
        return patterns
    
    def _detect_graph_diameter_anomalies(self, df: pd.DataFrame) -> List[PatternResult]:
        """Detect anomalies in graph diameter that may indicate layering"""
        patterns = []
        
        try:
            G = self._build_transaction_graph(df)
            G_undirected = G.to_undirected()
            
            # Analyze connected components
            components = list(nx.connected_components(G_undirected))
            
            for component in components:
                if len(component) >= 4:  # Need sufficient nodes
                    subgraph = G_undirected.subgraph(component)
                    
                    # Calculate diameter and other path metrics
                    diameter = nx.diameter(subgraph)
                    avg_path_length = nx.average_shortest_path_length(subgraph, weight='weight')
                    
                    # Expected diameter for random graph of same size
                    expected_diameter = np.log(len(component)) / np.log(np.log(len(component)))
                    
                    # Check if diameter is unusually large (indicating potential layering)
                    if diameter > expected_diameter * self.thresholds['diameter_anomaly_threshold']:
                        
                        # Find longest paths in the component
                        longest_paths = []
                        for source in component:
                            for target in component:
                                if source != target:
                                    try:
                                        path_length = nx.shortest_path_length(subgraph, source, target, weight='weight')
                                        if path_length == diameter:
                                            longest_paths.append((source, target))
                                    except nx.NetworkXNoPath:
                                        continue
                        
                        # Calculate total flow in component
                        total_flow = sum(data['weight'] for _, _, data in G.subgraph(component).edges(data=True))
                        
                        confidence = min(0.9, (diameter / expected_diameter - 1) * 0.5)
                        risk_level = RiskLevel.HIGH if diameter > expected_diameter * 3 else RiskLevel.MEDIUM
                        
                        patterns.append(PatternResult(
                            pattern_type=PatternType.GRAPH_DIAMETER_ANOMALY,
                            risk_level=risk_level,
                            confidence=confidence,
                            description=f"Component with {len(component)} accounts shows unusual diameter ({diameter}) suggesting complex layering paths",
                            affected_accounts=list(component),
                            transaction_ids=[],
                            evidence={
                                'actual_diameter': diameter,
                                'expected_diameter': expected_diameter,
                                'diameter_ratio': diameter / expected_diameter,
                                'avg_path_length': avg_path_length,
                                'component_size': len(component),
                                'total_flow': total_flow,
                                'longest_paths_count': len(longest_paths)
                            },
                            recommendation="Investigate component with unusual diameter for complex layering schemes",
                            timestamp=datetime.now()
                        ))
        
        except Exception as e:
            logger.debug(f"Error detecting graph diameter anomalies: {str(e)}")
        
        return patterns
    
    def _calculate_gini_coefficient(self, values: List[float]) -> float:
        """Calculate Gini coefficient for inequality measurement"""
        if not values or len(values) == 0:
            return 0.0
        
        # Sort values
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        # Calculate Gini coefficient
        cumsum = np.cumsum(sorted_values)
        return (n + 1 - 2 * sum(cumsum) / cumsum[-1]) / n if cumsum[-1] > 0 else 0.0
    
    def get_pattern_summary(self, patterns: List[PatternResult]) -> Dict[str, Any]:
        """Generate a summary of detected patterns"""
        if not patterns:
            return {
                'total_patterns': 0,
                'risk_distribution': {},
                'pattern_types': {},
                'recommendations': []
            }
        
        risk_counts = Counter([p.risk_level.value for p in patterns])
        pattern_counts = Counter([p.pattern_type.value for p in patterns])
        
        # Generate top recommendations
        high_risk_patterns = [p for p in patterns if p.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]]
        recommendations = []
        
        if high_risk_patterns:
            recommendations.append("Immediate investigation required for high-risk patterns")
            recommendations.append("Consider filing suspicious activity reports (SARs)")
            recommendations.append("Enhanced monitoring of flagged accounts")
        
        return {
            'total_patterns': len(patterns),
            'risk_distribution': dict(risk_counts),
            'pattern_types': dict(pattern_counts),
            'high_risk_count': len(high_risk_patterns),
            'average_confidence': np.mean([p.confidence for p in patterns]),
            'affected_accounts': len(set().union(*[p.affected_accounts for p in patterns])),
            'recommendations': recommendations,
            'analysis_timestamp': datetime.now().isoformat()
        }

# Factory function to create analyzer instance
def create_pattern_analyzer() -> AdvancedPatternAnalyzer:
    """Factory function to create a new pattern analyzer instance"""
    return AdvancedPatternAnalyzer()