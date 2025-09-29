import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
from datetime import datetime, timedelta
import pickle
import os

class AIAnalyzer:
    """AI-powered transaction analysis for AML detection"""
    
    def __init__(self):
        self.isolation_forest = IsolationForest(contamination=0.1, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_columns = [
            'amount_received', 'amount_paid', 'hour', 'day_of_week',
            'amount_ratio', 'bank_distance', 'currency_risk'
        ]
    
    def extract_features(self, transactions):
        """Extract features from transactions for ML analysis"""
        try:
            df = pd.DataFrame(transactions)
            
            # Convert timestamp if it's a string
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df['hour'] = df['timestamp'].dt.hour
                df['day_of_week'] = df['timestamp'].dt.dayofweek
            else:
                df['hour'] = 12  # Default values
                df['day_of_week'] = 1
            
            # Amount-based features
            df['amount_ratio'] = df['amount_paid'] / (df['amount_received'] + 1e-6)
            df['log_amount_received'] = np.log1p(df['amount_received'])
            df['log_amount_paid'] = np.log1p(df['amount_paid'])
            
            # Bank distance (simplified - using bank codes)
            df['bank_distance'] = abs(df['from_bank'].astype(int, errors='ignore').fillna(0) - 
                                    df['to_bank'].astype(int, errors='ignore').fillna(0))
            
            # Currency risk (simplified mapping)
            currency_risk_map = {
                'USD': 0.1, 'EUR': 0.1, 'GBP': 0.1, 'CHF': 0.1,
                'JPY': 0.2, 'CAD': 0.2, 'AUD': 0.2,
                'BTC': 0.9, 'ETH': 0.8, 'XMR': 0.95
            }
            df['currency_risk'] = df['receiving_currency'].map(currency_risk_map).fillna(0.5)
            
            # Round-number detection
            df['is_round_number'] = ((df['amount_received'] % 1000) == 0).astype(int)
            
            # Weekend/night transactions (higher risk)
            df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
            df['is_night'] = ((df['hour'] < 6) | (df['hour'] > 22)).astype(int)
            
            # Select feature columns that exist
            available_features = [col for col in self.feature_columns if col in df.columns]
            feature_matrix = df[available_features].fillna(0)
            
            return feature_matrix, df
        
        except Exception as e:
            print(f"Error extracting features: {e}")
            return pd.DataFrame(), pd.DataFrame()
    
    def train_model(self, transactions):
        """Train the AI model on transaction data"""
        try:
            features, _ = self.extract_features(transactions)
            
            if features.empty:
                print("No features extracted for training")
                return False
            
            # Scale features
            features_scaled = self.scaler.fit_transform(features)
            
            # Train isolation forest
            self.isolation_forest.fit(features_scaled)
            self.is_trained = True
            
            print(f"Model trained on {len(features)} transactions")
            return True
        
        except Exception as e:
            print(f"Error training model: {e}")
            return False
    
    def predict_anomalies(self, transactions):
        """Predict anomalies in transactions"""
        try:
            if not self.is_trained:
                # Train on the provided data first
                self.train_model(transactions)
            
            features, df = self.extract_features(transactions)
            
            if features.empty:
                return []
            
            # Scale features
            features_scaled = self.scaler.transform(features)
            
            # Predict anomalies (-1 for anomaly, 1 for normal)
            anomaly_predictions = self.isolation_forest.predict(features_scaled)
            anomaly_scores = self.isolation_forest.decision_function(features_scaled)
            
            # Convert to risk scores (0-1, where 1 is highest risk)
            risk_scores = 1 - (anomaly_scores - anomaly_scores.min()) / (anomaly_scores.max() - anomaly_scores.min() + 1e-6)
            
            # Apply additional rule-based risk factors
            risk_scores = self.apply_rule_based_risk(df, risk_scores)
            
            return risk_scores.tolist()
        
        except Exception as e:
            print(f"Error predicting anomalies: {e}")
            return []
    
    def apply_rule_based_risk(self, df, base_risk_scores):
        """Apply rule-based risk adjustments"""
        try:
            risk_scores = base_risk_scores.copy()
            
            # High amount transactions
            high_amount_threshold = df['amount_received'].quantile(0.95)
            high_amount_mask = df['amount_received'] > high_amount_threshold
            risk_scores[high_amount_mask] = np.minimum(risk_scores[high_amount_mask] + 0.2, 1.0)
            
            # Round number transactions
            if 'is_round_number' in df.columns:
                round_number_mask = df['is_round_number'] == 1
                risk_scores[round_number_mask] = np.minimum(risk_scores[round_number_mask] + 0.1, 1.0)
            
            # Weekend/night transactions
            if 'is_weekend' in df.columns and 'is_night' in df.columns:
                unusual_time_mask = (df['is_weekend'] == 1) | (df['is_night'] == 1)
                risk_scores[unusual_time_mask] = np.minimum(risk_scores[unusual_time_mask] + 0.05, 1.0)
            
            # High currency risk
            if 'currency_risk' in df.columns:
                high_currency_risk_mask = df['currency_risk'] > 0.7
                risk_scores[high_currency_risk_mask] = np.minimum(risk_scores[high_currency_risk_mask] + 0.15, 1.0)
            
            # Unusual amount ratios
            if 'amount_ratio' in df.columns:
                unusual_ratio_mask = (df['amount_ratio'] < 0.5) | (df['amount_ratio'] > 2.0)
                risk_scores[unusual_ratio_mask] = np.minimum(risk_scores[unusual_ratio_mask] + 0.1, 1.0)
            
            return risk_scores
        
        except Exception as e:
            print(f"Error applying rule-based risk: {e}")
            return base_risk_scores
    
    def analyze_transactions(self, transaction_ids, database=None):
        """Analyze transactions and generate alerts"""
        try:
            if database is None:
                print("Database connection required for analysis")
                return {'error': 'No database connection'}
            
            # Fetch transactions from database
            from bson import ObjectId
            object_ids = [ObjectId(tid) for tid in transaction_ids if ObjectId.is_valid(tid)]
            
            transactions_cursor = database.transactions.find({'_id': {'$in': object_ids}})
            transactions = list(transactions_cursor)
            
            if not transactions:
                return {'message': 'No transactions found for analysis'}
            
            # Convert datetime objects to strings for processing
            for t in transactions:
                if 'timestamp' in t and hasattr(t['timestamp'], 'isoformat'):
                    t['timestamp'] = t['timestamp'].isoformat()
            
            # Predict risk scores
            risk_scores = self.predict_anomalies(transactions)
            
            # Update transactions with risk scores
            suspicious_count = 0
            alerts_generated = 0
            
            for i, (transaction, risk_score) in enumerate(zip(transactions, risk_scores)):
                # Update transaction in database
                database.transactions.update_one(
                    {'_id': transaction['_id']},
                    {
                        '$set': {
                            'risk_score': risk_score,
                            'analyzed_at': datetime.now(),
                            'status': 'analyzed'
                        }
                    }
                )
                
                # Generate alert for high-risk transactions
                if risk_score > 0.7:
                    suspicious_count += 1
                    
                    alert = {
                        'transaction_id': str(transaction['_id']),
                        'alert_type': 'suspicious_transaction',
                        'risk_score': risk_score,
                        'priority': 'high' if risk_score > 0.9 else 'medium',
                        'description': f"High-risk transaction detected (Risk Score: {risk_score:.3f})",
                        'from_account': transaction.get('from_account'),
                        'to_account': transaction.get('to_account'),
                        'amount': transaction.get('amount_received'),
                        'currency': transaction.get('receiving_currency'),
                        'status': 'active',
                        'created_at': datetime.now(),
                        'assigned_to': None
                    }
                    
                    database.alerts.insert_one(alert)
                    alerts_generated += 1
            
            return {
                'analyzed_transactions': len(transactions),
                'suspicious_count': suspicious_count,
                'alerts_generated': alerts_generated,
                'avg_risk_score': np.mean(risk_scores) if risk_scores else 0
            }
        
        except Exception as e:
            print(f"Error analyzing transactions: {e}")
            return {'error': str(e)}
    
    def detect_transaction_patterns(self, transactions):
        """Detect suspicious patterns in transaction networks"""
        try:
            df = pd.DataFrame(transactions)
            
            if df.empty:
                return []
            
            patterns = []
            
            # Pattern 1: Rapid fire transactions
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df_sorted = df.sort_values('timestamp')
                
                for account in df['from_account'].unique():
                    account_txns = df_sorted[df_sorted['from_account'] == account]
                    
                    if len(account_txns) > 5:
                        time_diffs = account_txns['timestamp'].diff().dt.total_seconds()
                        rapid_fire = (time_diffs < 300).sum()  # Less than 5 minutes
                        
                        if rapid_fire > 3:
                            patterns.append({
                                'type': 'rapid_fire',
                                'account': account,
                                'description': f"Account made {rapid_fire} transactions within 5 minutes",
                                'risk_level': 'high'
                            })
            
            # Pattern 2: Circular transactions
            for account in df['from_account'].unique():
                sent_to = df[df['from_account'] == account]['to_account'].tolist()
                received_from = df[df['to_account'] == account]['from_account'].tolist()
                
                circular = set(sent_to).intersection(set(received_from))
                if circular:
                    patterns.append({
                        'type': 'circular',
                        'account': account,
                        'description': f"Circular transactions detected with {len(circular)} accounts",
                        'risk_level': 'medium'
                    })
            
            # Pattern 3: Structuring (amounts just below reporting threshold)
            threshold = 10000  # Common AML reporting threshold
            structuring_amounts = df[
                (df['amount_received'] > threshold * 0.8) & 
                (df['amount_received'] < threshold)
            ]
            
            for account in structuring_amounts['from_account'].unique():
                account_structuring = structuring_amounts[structuring_amounts['from_account'] == account]
                if len(account_structuring) > 2:
                    patterns.append({
                        'type': 'structuring',
                        'account': account,
                        'description': f"Potential structuring: {len(account_structuring)} transactions near threshold",
                        'risk_level': 'high'
                    })
            
            return patterns
        
        except Exception as e:
            print(f"Error detecting patterns: {e}")
            return []
    
    def save_model(self, filepath):
        """Save trained model to file"""
        try:
            model_data = {
                'isolation_forest': self.isolation_forest,
                'scaler': self.scaler,
                'is_trained': self.is_trained,
                'feature_columns': self.feature_columns
            }
            
            with open(filepath, 'wb') as f:
                pickle.dump(model_data, f)
            
            print(f"Model saved to {filepath}")
            return True
        
        except Exception as e:
            print(f"Error saving model: {e}")
            return False
    
    def load_model(self, filepath):
        """Load trained model from file"""
        try:
            if not os.path.exists(filepath):
                print(f"Model file not found: {filepath}")
                return False
            
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)
            
            self.isolation_forest = model_data['isolation_forest']
            self.scaler = model_data['scaler']
            self.is_trained = model_data['is_trained']
            self.feature_columns = model_data['feature_columns']
            
            print(f"Model loaded from {filepath}")
            return True
        
        except Exception as e:
            print(f"Error loading model: {e}")
            return False