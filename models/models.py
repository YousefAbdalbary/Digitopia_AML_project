"""
Database models for AML Detection Platform
"""

from datetime import datetime
from bson import ObjectId

class Transaction:
    """Transaction model"""
    
    def __init__(self, data):
        self.id = data.get('_id')
        self.timestamp = data.get('timestamp')
        self.from_bank = data.get('from_bank')
        self.from_account = data.get('from_account')
        self.to_bank = data.get('to_bank')
        self.to_account = data.get('to_account')
        self.amount_received = data.get('amount_received')
        self.receiving_currency = data.get('receiving_currency')
        self.amount_paid = data.get('amount_paid')
        self.payment_currency = data.get('payment_currency')
        self.payment_format = data.get('payment_format')
        self.risk_score = data.get('risk_score', 0.0)
        self.status = data.get('status', 'pending')
        self.created_at = data.get('created_at', datetime.now())
        self.updated_at = data.get('updated_at', datetime.now())
    
    def to_dict(self):
        return {
            '_id': self.id,
            'timestamp': self.timestamp,
            'from_bank': self.from_bank,
            'from_account': self.from_account,
            'to_bank': self.to_bank,
            'to_account': self.to_account,
            'amount_received': self.amount_received,
            'receiving_currency': self.receiving_currency,
            'amount_paid': self.amount_paid,
            'payment_currency': self.payment_currency,
            'payment_format': self.payment_format,
            'risk_score': self.risk_score,
            'status': self.status,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

class Account:
    """Account model"""
    
    def __init__(self, data):
        self.id = data.get('_id')
        self.account_id = data.get('account_id')
        self.name = data.get('name')
        self.type = data.get('type')
        self.bank_id = data.get('bank_id')
        self.country = data.get('country')
        self.status = data.get('status', 'active')
        self.monitoring = data.get('monitoring', True)
        self.risk_score = data.get('risk_score', 0.0)
        self.created_at = data.get('created_at', datetime.now())
        self.updated_at = data.get('updated_at', datetime.now())
    
    def to_dict(self):
        return {
            '_id': self.id,
            'account_id': self.account_id,
            'name': self.name,
            'type': self.type,
            'bank_id': self.bank_id,
            'country': self.country,
            'status': self.status,
            'monitoring': self.monitoring,
            'risk_score': self.risk_score,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

class Alert:
    """Alert model"""
    
    def __init__(self, data):
        self.id = data.get('_id')
        self.transaction_id = data.get('transaction_id')
        self.alert_type = data.get('alert_type')
        self.priority = data.get('priority', 'medium')
        self.status = data.get('status', 'active')
        self.description = data.get('description')
        self.risk_score = data.get('risk_score', 0.0)
        self.assigned_to = data.get('assigned_to')
        self.created_at = data.get('created_at', datetime.now())
        self.updated_at = data.get('updated_at', datetime.now())
    
    def to_dict(self):
        return {
            '_id': self.id,
            'transaction_id': self.transaction_id,
            'alert_type': self.alert_type,
            'priority': self.priority,
            'status': self.status,
            'description': self.description,
            'risk_score': self.risk_score,
            'assigned_to': self.assigned_to,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

class Bank:
    """Bank model"""
    
    def __init__(self, data):
        self.id = data.get('_id')
        self.bank_code = data.get('bank_code')
        self.name = data.get('name')
        self.country = data.get('country')
        self.city = data.get('city')
        self.latitude = data.get('latitude', 0.0)
        self.longitude = data.get('longitude', 0.0)
        self.risk_level = data.get('risk_level', 'low')
        self.created_at = data.get('created_at', datetime.now())
    
    def to_dict(self):
        return {
            '_id': self.id,
            'bank_code': self.bank_code,
            'name': self.name,
            'country': self.country,
            'city': self.city,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'risk_level': self.risk_level,
            'created_at': self.created_at
        }