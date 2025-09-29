import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import math

class RiskCalculator:
    """Calculate risk scores for transactions and accounts"""
    
    def __init__(self):
        self.risk_weights = {
            'amount': 0.25,
            'frequency': 0.20,
            'geography': 0.15,
            'currency': 0.15,
            'timing': 0.10,
            'network': 0.15
        }
        
        self.currency_risk_scores = {
            'USD': 0.1, 'EUR': 0.1, 'GBP': 0.1, 'CHF': 0.1,
            'JPY': 0.2, 'CAD': 0.15, 'AUD': 0.15, 'SGD': 0.2,
            'CNY': 0.3, 'RUB': 0.4, 'INR': 0.25, 'BRL': 0.3,
            'BTC': 0.9, 'ETH': 0.8, 'XMR': 0.95, 'LTC': 0.7
        }
        
        self.high_risk_countries = {
            'AF', 'BY', 'CF', 'CD', 'CU', 'ER', 'GN', 'GW', 'HT', 'IR',
            'IQ', 'LB', 'LY', 'ML', 'MM', 'NI', 'KP', 'SO', 'SS', 'SD',
            'SY', 'UZ', 'VE', 'YE', 'ZW'
        }
    
    def calculate_transaction_risk(self, transaction):
        """Calculate risk score for a single transaction"""
        try:
            risk_components = {}
            
            # Amount-based risk
            risk_components['amount'] = self._calculate_amount_risk(transaction)
            
            # Currency risk
            risk_components['currency'] = self._calculate_currency_risk(transaction)
            
            # Geography risk
            risk_components['geography'] = self._calculate_geography_risk(transaction)
            
            # Timing risk
            risk_components['timing'] = self._calculate_timing_risk(transaction)
            
            # Payment method risk
            risk_components['payment_method'] = self._calculate_payment_method_risk(transaction)
            
            # Calculate weighted total
            total_risk = 0
            for component, score in risk_components.items():
                weight = self.risk_weights.get(component, 0.1)
                total_risk += score * weight
            
            # Apply additional risk factors
            total_risk = self._apply_additional_risk_factors(transaction, total_risk)
            
            return min(max(total_risk, 0.0), 1.0)
        
        except Exception as e:
            print(f"Error calculating transaction risk: {e}")
            return 0.0
    
    def _calculate_amount_risk(self, transaction):
        """Calculate risk based on transaction amount"""
        try:
            amount = float(transaction.get('amount_received', 0))
            
            # Risk thresholds
            if amount >= 1000000:  # 1M+
                return 0.9
            elif amount >= 100000:  # 100K+
                return 0.7
            elif amount >= 50000:   # 50K+
                return 0.5
            elif amount >= 10000:   # 10K+ (reporting threshold)
                return 0.3
            elif amount >= 9500:    # Just below reporting threshold (structuring)
                return 0.8
            elif amount < 100:      # Very small amounts (testing)
                return 0.4
            else:
                return 0.1
        
        except:
            return 0.0
    
    def _calculate_currency_risk(self, transaction):
        """Calculate risk based on currency type"""
        try:
            receiving_currency = transaction.get('receiving_currency', 'USD')
            payment_currency = transaction.get('payment_currency', 'USD')
            
            receiving_risk = self.currency_risk_scores.get(receiving_currency, 0.5)
            payment_risk = self.currency_risk_scores.get(payment_currency, 0.5)
            
            # Higher risk if currencies are different (conversion)
            if receiving_currency != payment_currency:
                conversion_risk = 0.2
            else:
                conversion_risk = 0.0
            
            return max(receiving_risk, payment_risk) + conversion_risk
        
        except:
            return 0.0
    
    def _calculate_geography_risk(self, transaction):
        """Calculate risk based on geographic factors"""
        try:
            # This would typically use bank location data
            # For now, we'll use a simplified approach based on bank codes
            
            from_bank = str(transaction.get('from_bank', ''))
            to_bank = str(transaction.get('to_bank', ''))
            
            # If banks are very different (potentially different countries)
            if from_bank and to_bank:
                bank_distance = abs(int(from_bank) - int(to_bank)) if from_bank.isdigit() and to_bank.isdigit() else 0
                
                if bank_distance > 1000:  # Likely cross-border
                    return 0.6
                elif bank_distance > 100:  # Likely different regions
                    return 0.3
                else:
                    return 0.1
            
            return 0.2  # Default moderate risk
        
        except:
            return 0.0
    
    def _calculate_timing_risk(self, transaction):
        """Calculate risk based on transaction timing"""
        try:
            timestamp = transaction.get('timestamp')
            if not timestamp:
                return 0.0
            
            # Convert to datetime if string
            if isinstance(timestamp, str):
                timestamp = pd.to_datetime(timestamp)
            
            # Weekend transactions (higher risk)
            if timestamp.weekday() >= 5:  # Saturday = 5, Sunday = 6
                weekend_risk = 0.3
            else:
                weekend_risk = 0.0
            
            # Night transactions (higher risk)
            hour = timestamp.hour
            if hour < 6 or hour > 22:
                night_risk = 0.2
            else:
                night_risk = 0.0
            
            # Holiday periods (would need holiday calendar)
            # For now, just basic timing risk
            
            return weekend_risk + night_risk
        
        except:
            return 0.0
    
    def _calculate_payment_method_risk(self, transaction):
        """Calculate risk based on payment method"""
        try:
            payment_format = transaction.get('payment_format', '').lower()
            
            risk_scores = {
                'cash': 0.8,
                'cryptocurrency': 0.9,
                'wire': 0.4,
                'ach': 0.2,
                'check': 0.3,
                'credit_card': 0.1,
                'debit_card': 0.1,
                'electronic': 0.2,
                'online': 0.3
            }
            
            for method, risk in risk_scores.items():
                if method in payment_format:
                    return risk
            
            return 0.2  # Default risk for unknown methods
        
        except:
            return 0.0
    
    def _apply_additional_risk_factors(self, transaction, base_risk):
        """Apply additional risk factors"""
        try:
            additional_risk = 0
            
            # Round number detection
            amount = float(transaction.get('amount_received', 0))
            if amount > 0 and amount % 1000 == 0:
                additional_risk += 0.1
            
            # Exact amount matching (potential structuring)
            amount_paid = float(transaction.get('amount_paid', 0))
            if abs(amount - amount_paid) < 0.01:  # Exactly matching amounts
                additional_risk += 0.1
            
            # Very high precision amounts (unusual)
            if amount > 100 and (amount * 100) % 1 != 0:  # Has cents
                decimal_places = len(str(amount).split('.')[-1]) if '.' in str(amount) else 0
                if decimal_places > 2:
                    additional_risk += 0.05
            
            return min(base_risk + additional_risk, 1.0)
        
        except:
            return base_risk
    
    def calculate_account_risk(self, account_id, db=None):
        """Calculate overall risk score for an account"""
        try:
            if db is None:
                return 0.0
            
            # Get account transactions from last 90 days
            start_date = datetime.now() - timedelta(days=90)
            
            transactions = list(db.transactions.find({
                '$or': [
                    {'from_account': account_id},
                    {'to_account': account_id}
                ],
                'timestamp': {'$gte': start_date}
            }))
            
            if not transactions:
                return 0.0
            
            risk_factors = {
                'transaction_risk': 0,
                'velocity_risk': 0,
                'pattern_risk': 0,
                'network_risk': 0
            }
            
            # Average transaction risk
            transaction_risks = []
            for t in transactions:
                t_risk = self.calculate_transaction_risk(t)
                transaction_risks.append(t_risk)
            
            risk_factors['transaction_risk'] = np.mean(transaction_risks) if transaction_risks else 0
            
            # Velocity risk
            risk_factors['velocity_risk'] = self._calculate_velocity_risk(transactions, account_id)
            
            # Pattern risk
            risk_factors['pattern_risk'] = self._calculate_pattern_risk(transactions, account_id)
            
            # Network risk (simplified)
            risk_factors['network_risk'] = self._calculate_network_risk_simple(transactions, account_id)
            
            # Weighted total
            weights = {
                'transaction_risk': 0.4,
                'velocity_risk': 0.2,
                'pattern_risk': 0.2,
                'network_risk': 0.2
            }
            
            total_risk = sum(risk_factors[factor] * weights[factor] for factor in risk_factors)
            
            return min(max(total_risk, 0.0), 1.0)
        
        except Exception as e:
            print(f"Error calculating account risk: {e}")
            return 0.0
    
    def _calculate_velocity_risk(self, transactions, account_id):
        """Calculate risk based on transaction velocity"""
        try:
            if len(transactions) < 2:
                return 0.0
            
            # Sort by timestamp
            df = pd.DataFrame(transactions)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            
            # Calculate time differences
            time_diffs = df['timestamp'].diff().dt.total_seconds().dropna()
            
            # Risk factors
            velocity_risk = 0
            
            # Very fast transactions (< 5 minutes apart)
            fast_transactions = (time_diffs < 300).sum()
            if fast_transactions > 0:
                velocity_risk += min(fast_transactions * 0.1, 0.5)
            
            # High frequency (many transactions per day)
            days_active = (df['timestamp'].max() - df['timestamp'].min()).days + 1
            transactions_per_day = len(transactions) / days_active
            
            if transactions_per_day > 20:
                velocity_risk += 0.6
            elif transactions_per_day > 10:
                velocity_risk += 0.3
            elif transactions_per_day > 5:
                velocity_risk += 0.1
            
            return min(velocity_risk, 1.0)
        
        except:
            return 0.0
    
    def _calculate_pattern_risk(self, transactions, account_id):
        """Calculate risk based on suspicious patterns"""
        try:
            pattern_risk = 0
            
            # Amount patterns
            amounts = [float(t.get('amount_received', 0)) for t in transactions]
            
            if len(amounts) > 5:
                # Check for structuring (similar amounts)
                amount_std = np.std(amounts)
                amount_mean = np.mean(amounts)
                
                if amount_mean > 5000 and amount_std / amount_mean < 0.1:
                    pattern_risk += 0.4  # Very consistent amounts
                
                # Check for round numbers
                round_numbers = sum(1 for amt in amounts if amt > 1000 and amt % 1000 == 0)
                if round_numbers / len(amounts) > 0.7:
                    pattern_risk += 0.2
            
            # Currency patterns
            currencies = [t.get('receiving_currency', 'USD') for t in transactions]
            unique_currencies = len(set(currencies))
            
            if unique_currencies > 5:
                pattern_risk += 0.2  # Many different currencies
            
            # Timing patterns
            timestamps = [pd.to_datetime(t.get('timestamp')) for t in transactions if t.get('timestamp')]
            
            if len(timestamps) > 10:
                hours = [ts.hour for ts in timestamps]
                night_transactions = sum(1 for h in hours if h < 6 or h > 22)
                
                if night_transactions / len(timestamps) > 0.5:
                    pattern_risk += 0.3  # Mostly night transactions
            
            return min(pattern_risk, 1.0)
        
        except:
            return 0.0
    
    def _calculate_network_risk_simple(self, transactions, account_id):
        """Simplified network risk calculation"""
        try:
            # Count unique counterparties
            counterparties = set()
            
            for t in transactions:
                if t.get('from_account') == account_id:
                    counterparties.add(t.get('to_account'))
                else:
                    counterparties.add(t.get('from_account'))
            
            # Risk based on number of counterparties
            num_counterparties = len(counterparties)
            
            if num_counterparties > 100:
                return 0.8
            elif num_counterparties > 50:
                return 0.5
            elif num_counterparties > 20:
                return 0.3
            elif num_counterparties < 2:
                return 0.4  # Suspicious if only one counterparty
            else:
                return 0.1
        
        except:
            return 0.0
    
    def calculate_batch_risk_scores(self, transactions):
        """Calculate risk scores for a batch of transactions"""
        try:
            risk_scores = []
            
            for transaction in transactions:
                risk_score = self.calculate_transaction_risk(transaction)
                risk_scores.append(risk_score)
            
            return risk_scores
        
        except Exception as e:
            print(f"Error calculating batch risk scores: {e}")
            return [0.0] * len(transactions)
    
    def get_risk_explanation(self, transaction, risk_score):
        """Generate human-readable explanation for risk score"""
        try:
            explanations = []
            
            # Amount factors
            amount = float(transaction.get('amount_received', 0))
            if amount >= 50000:
                explanations.append(f"High transaction amount: ${amount:,.2f}")
            elif 9500 <= amount < 10000:
                explanations.append(f"Amount just below reporting threshold: ${amount:,.2f}")
            
            # Currency factors
            currency = transaction.get('receiving_currency', 'USD')
            if currency in ['BTC', 'ETH', 'XMR']:
                explanations.append(f"High-risk cryptocurrency: {currency}")
            elif currency not in ['USD', 'EUR', 'GBP', 'CHF']:
                explanations.append(f"Non-major currency: {currency}")
            
            # Timing factors
            timestamp = transaction.get('timestamp')
            if timestamp:
                if isinstance(timestamp, str):
                    timestamp = pd.to_datetime(timestamp)
                
                if timestamp.weekday() >= 5:
                    explanations.append("Weekend transaction")
                
                if timestamp.hour < 6 or timestamp.hour > 22:
                    explanations.append("Night-time transaction")
            
            # Payment method
            payment_format = transaction.get('payment_format', '').lower()
            if 'cash' in payment_format:
                explanations.append("Cash transaction")
            elif 'crypto' in payment_format:
                explanations.append("Cryptocurrency transaction")
            
            # Round number
            if amount > 1000 and amount % 1000 == 0:
                explanations.append("Round number amount")
            
            if not explanations:
                explanations.append("Low risk transaction")
            
            return {
                'risk_score': risk_score,
                'risk_level': 'High' if risk_score > 0.7 else 'Medium' if risk_score > 0.3 else 'Low',
                'explanations': explanations
            }
        
        except Exception as e:
            print(f"Error generating risk explanation: {e}")
            return {
                'risk_score': risk_score,
                'risk_level': 'Unknown',
                'explanations': ['Error generating explanation']
            }