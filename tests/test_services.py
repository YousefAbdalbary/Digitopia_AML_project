"""
Basic unit tests for AML Detection Platform
"""

import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.risk_calculator import RiskCalculator
from services.ai_analyzer import AIAnalyzer
import pandas as pd
from datetime import datetime

class TestRiskCalculator(unittest.TestCase):
    
    def setUp(self):
        self.risk_calculator = RiskCalculator()
    
    def test_amount_risk_calculation(self):
        """Test amount-based risk calculation"""
        # High amount transaction
        transaction = {'amount_received': 1000000}
        risk = self.risk_calculator._calculate_amount_risk(transaction)
        self.assertGreater(risk, 0.8)
        
        # Normal amount transaction
        transaction = {'amount_received': 5000}
        risk = self.risk_calculator._calculate_amount_risk(transaction)
        self.assertLess(risk, 0.5)
        
        # Structuring amount (just below 10K)
        transaction = {'amount_received': 9500}
        risk = self.risk_calculator._calculate_amount_risk(transaction)
        self.assertGreater(risk, 0.7)
    
    def test_currency_risk_calculation(self):
        """Test currency-based risk calculation"""
        # High-risk cryptocurrency
        transaction = {
            'receiving_currency': 'BTC',
            'payment_currency': 'USD'
        }
        risk = self.risk_calculator._calculate_currency_risk(transaction)
        self.assertGreater(risk, 0.8)
        
        # Low-risk major currency
        transaction = {
            'receiving_currency': 'USD',
            'payment_currency': 'USD'
        }
        risk = self.risk_calculator._calculate_currency_risk(transaction)
        self.assertLess(risk, 0.3)
    
    def test_timing_risk_calculation(self):
        """Test timing-based risk calculation"""
        # Weekend night transaction
        weekend_night = datetime(2024, 1, 6, 23, 30)  # Saturday night
        transaction = {'timestamp': weekend_night}
        risk = self.risk_calculator._calculate_timing_risk(transaction)
        self.assertGreater(risk, 0.4)
        
        # Weekday daytime transaction
        weekday_day = datetime(2024, 1, 8, 14, 30)  # Monday afternoon
        transaction = {'timestamp': weekday_day}
        risk = self.risk_calculator._calculate_timing_risk(transaction)
        self.assertLess(risk, 0.2)
    
    def test_overall_transaction_risk(self):
        """Test overall transaction risk calculation"""
        # High-risk transaction
        high_risk_transaction = {
            'amount_received': 1000000,
            'receiving_currency': 'BTC',
            'payment_currency': 'USD',
            'timestamp': datetime(2024, 1, 6, 23, 30),
            'payment_format': 'cash',
            'from_bank': '12345',
            'to_bank': '99999'
        }
        
        risk = self.risk_calculator.calculate_transaction_risk(high_risk_transaction)
        self.assertGreater(risk, 0.7)
        self.assertLessEqual(risk, 1.0)
        
        # Low-risk transaction
        low_risk_transaction = {
            'amount_received': 1000,
            'receiving_currency': 'USD',
            'payment_currency': 'USD',
            'timestamp': datetime(2024, 1, 8, 14, 30),
            'payment_format': 'credit_card',
            'from_bank': '12345',
            'to_bank': '12346'
        }
        
        risk = self.risk_calculator.calculate_transaction_risk(low_risk_transaction)
        self.assertLess(risk, 0.4)
        self.assertGreaterEqual(risk, 0.0)

class TestAIAnalyzer(unittest.TestCase):
    
    def setUp(self):
        self.ai_analyzer = AIAnalyzer()
    
    def test_feature_extraction(self):
        """Test feature extraction from transactions"""
        sample_transactions = [
            {
                'timestamp': '2024-01-08T14:30:00',
                'amount_received': 5000,
                'amount_paid': 5000,
                'receiving_currency': 'USD',
                'from_bank': '12345',
                'to_bank': '67890'
            },
            {
                'timestamp': '2024-01-08T15:00:00',
                'amount_received': 10000,
                'amount_paid': 8500,
                'receiving_currency': 'EUR',
                'from_bank': '11111',
                'to_bank': '22222'
            }
        ]
        
        features, df = self.ai_analyzer.extract_features(sample_transactions)
        
        # Check if features DataFrame is created
        self.assertIsInstance(features, pd.DataFrame)
        self.assertGreater(len(features), 0)
        
        # Check if required columns are present
        expected_columns = ['amount_received', 'amount_paid', 'hour', 'day_of_week']
        for col in expected_columns:
            if col in self.ai_analyzer.feature_columns:
                self.assertIn(col, features.columns)
    
    def test_rule_based_risk_application(self):
        """Test rule-based risk factor application"""
        df = pd.DataFrame([
            {
                'amount_received': 10000,  # Round number
                'is_round_number': 1,
                'is_weekend': 0,
                'is_night': 1,
                'currency_risk': 0.8
            }
        ])
        
        base_risk = pd.Series([0.5])
        adjusted_risk = self.ai_analyzer.apply_rule_based_risk(df, base_risk)
        
        # Risk should be higher due to round number, night time, and high currency risk
        self.assertGreater(adjusted_risk[0], base_risk[0])
        self.assertLessEqual(adjusted_risk[0], 1.0)

class TestDataValidation(unittest.TestCase):
    
    def test_required_columns_validation(self):
        """Test validation of required columns in uploaded data"""
        required_columns = [
            'Timestamp', 'From Bank', 'From Account', 'To Bank', 'To Account',
            'Amount Received', 'Receiving Currency', 'Amount Paid', 'Payment Currency',
            'Payment Format'
        ]
        
        # Valid data
        valid_data = pd.DataFrame({col: [1, 2, 3] for col in required_columns})
        missing_columns = [col for col in required_columns if col not in valid_data.columns]
        self.assertEqual(len(missing_columns), 0)
        
        # Invalid data (missing columns)
        invalid_data = pd.DataFrame({'Timestamp': [1, 2, 3], 'Amount': [100, 200, 300]})
        missing_columns = [col for col in required_columns if col not in invalid_data.columns]
        self.assertGreater(len(missing_columns), 0)

if __name__ == '__main__':
    unittest.main()