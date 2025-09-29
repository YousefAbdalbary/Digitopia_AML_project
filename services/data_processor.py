import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from bson import ObjectId
import json
import requests
import re

class DataProcessor:
    """Handles data processing and database operations"""
    
    def __init__(self, db):
        self.db = db
        self.transactions = db.transactions
        self.accounts = db.accounts
        self.alerts = db.alerts
        self.banks = db.banks
        self.bank_countries = db.bank_countries  # New collection for bank country mappings
        self.country_cache = {}  # Cache for country coordinates
        self._country_cache = {}  # Cache for country coordinates
        self._bank_country_cache = {}  # Cache for bank-to-country mapping
        
        # Country code mapping
        self._country_code_mappings = {
            'US': 'US', 'USA': 'US', 'UNITED STATES': 'US',
            'UK': 'GB', 'UNITED KINGDOM': 'GB', 'BRITAIN': 'GB', 'ENGLAND': 'GB',
            'CANADA': 'CA', 'CA': 'CA',
            'GERMANY': 'DE', 'DE': 'DE', 'DEUTSCHLAND': 'DE',
            'FRANCE': 'FR', 'FR': 'FR',
            'SWITZERLAND': 'CH', 'CH': 'CH',
            'SPAIN': 'ES', 'ES': 'ES',
            'ITALY': 'IT', 'IT': 'IT',
            'NETHERLANDS': 'NL', 'NL': 'NL',
            'JAPAN': 'JP', 'JP': 'JP',
            'CHINA': 'CN', 'CN': 'CN',
            'INDIA': 'IN', 'IN': 'IN',
            'AUSTRALIA': 'AU', 'AU': 'AU'
        }
    
    def _cache_bank_country(self, bank_name, country_code):
        """Cache bank country mapping in memory"""
        try:
            # Update in-memory cache
            self._bank_country_cache[bank_name] = country_code
            
        except Exception as e:
            print(f"Error caching bank country for {bank_name}: {e}")
    
    def _fetch_country_coordinates(self, country_code):
        """Fetch country coordinates using REST Countries API with caching"""
        if country_code in self._country_cache:
            return self._country_cache[country_code]
        
        try:
            # Use REST Countries API
            response = requests.get(
                f'https://restcountries.com/v3.1/alpha/{country_code}',
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0 and 'latlng' in data[0]:
                    coordinates = {
                        'lat': data[0]['latlng'][0],
                        'lng': data[0]['latlng'][1],
                        'country': data[0].get('name', {}).get('common', country_code)
                    }
                    self._country_cache[country_code] = coordinates
                    return coordinates
        
        except Exception as e:
            print(f"Error fetching coordinates for {country_code}: {e}")
            
        # Use a simple default for unknown countries
        coordinates = {
            'lat': 0, 'lng': 0, 'country': country_code
        }
        
        self._country_cache[country_code] = coordinates
        return coordinates
    
    def _get_bank_location(self, bank_name):
        """Get dynamic bank location based on bank location string"""
        if bank_name in self._bank_country_cache:
            return self._bank_country_cache[bank_name]
        
        bank_name_upper = bank_name.upper().strip()
        
        # Get country code from the location string
        country_code = self._country_code_mappings.get(bank_name_upper, bank_name_upper)
        if country_code == bank_name_upper and len(country_code) != 2:
            country_code = 'Unknown'
            
        # Get coordinates for the country
        coordinates = self._fetch_country_coordinates(country_code)
        
        # Create location object
        location = {
            'country': coordinates['country'],
            'lat': coordinates['lat'],
            'lng': coordinates['lng'],
            'id': country_code,
            'bank_name': bank_name
        }
        
        # Cache the result
        self._bank_country_cache[bank_name] = location
        
        return location
    
    def get_dashboard_stats(self):
        """Get main dashboard statistics"""
        try:
            # Get current date ranges
            today = datetime.now()
            last_30_days = today - timedelta(days=30)
            
            # Count suspicious transactions
            suspicious_count = self.transactions.count_documents({
                'risk_score': {'$gte': 0.7},
                'timestamp': {'$gte': last_30_days}
            })
            
            # Count monitored accounts
            monitored_accounts = self.accounts.count_documents({
                'status': 'active',
                'monitoring': True
            })
            
            # Calculate daily risk rate
            today_start = today.replace(hour=0, minute=0, second=0, microsecond=0)
            today_transactions = self.transactions.count_documents({
                'timestamp': {'$gte': today_start}
            })
            today_suspicious = self.transactions.count_documents({
                'timestamp': {'$gte': today_start},
                'risk_score': {'$gte': 0.7}
            })
            
            daily_risk_rate = (today_suspicious / today_transactions * 100) if today_transactions > 0 else 0
            
            # Calculate cash flow volume
            pipeline = [
                {'$match': {'timestamp': {'$gte': last_30_days}}},
                {'$group': {
                    '_id': '$receiving_currency',
                    'total_volume': {'$sum': '$amount_received'}
                }}
            ]
            
            cash_flow_data = list(self.transactions.aggregate(pipeline))
            total_volume = sum([item['total_volume'] for item in cash_flow_data])
            
            # Risk distribution
            risk_distribution = {
                'low': self.transactions.count_documents({'risk_score': {'$lt': 0.3}}),
                'medium': self.transactions.count_documents({'risk_score': {'$gte': 0.3, '$lt': 0.7}}),
                'high': self.transactions.count_documents({'risk_score': {'$gte': 0.7}})
            }
            
            return {
                'suspicious_transactions': suspicious_count,
                'monitored_accounts': monitored_accounts,
                'daily_risk_rate': round(daily_risk_rate, 2),
                'cash_flow_volume': total_volume,
                'risk_distribution': risk_distribution,
                'currency_breakdown': cash_flow_data
            }
        
        except Exception as e:
            print(f"Error getting dashboard stats: {e}")
            return {}
    
    def get_transactions(self, filters):
        """Get transactions with filters"""
        try:
            query = {}
            
            print(f"Getting transactions with filters: {filters}")
            
            # Date range filter
            if filters.get('date_range'):
                days = int(filters['date_range'].replace('d', ''))
                start_date = datetime.now() - timedelta(days=days)
                query['timestamp'] = {'$gte': start_date}
                print(f"Added date filter: from {start_date}")
            elif filters.get('start_date') and filters.get('end_date'):
                start_date = datetime.fromisoformat(filters['start_date'])
                end_date = datetime.fromisoformat(filters['end_date'])
                query['timestamp'] = {'$gte': start_date, '$lte': end_date}
            
            # Currency filter
            if filters.get('currency') and filters['currency'] != 'all':
                # Try both possible currency field names
                query['$or'] = [
                    {'receiving_currency': filters['currency']},
                    {'currency_type': filters['currency']}
                ]
                print(f"Added currency filter: {filters['currency']}")
            
            # Account filter
            if filters.get('account_filter'):
                query['$or'] = query.get('$or', []) + [
                    {'sender_account': {'$regex': filters['account_filter'], '$options': 'i'}},
                    {'receiver_account': {'$regex': filters['account_filter'], '$options': 'i'}}
                ]
                print(f"Added account filter: {filters['account_filter']}")
            
            # Search filter
            if filters.get('search'):
                search_regex = {'$regex': filters['search'], '$options': 'i'}
                query['$or'] = query.get('$or', []) + [
                    {'from_bank': search_regex},
                    {'to_bank': search_regex},
                    {'transaction_id': search_regex}
                ]
                print(f"Added search filter: {filters['search']}")
            
            # Risk level filter
            if filters.get('risk_level'):
                if filters['risk_level'] == 'low':
                    query['risk_score'] = {'$lt': 0.3}
                elif filters['risk_level'] == 'medium':
                    query['risk_score'] = {'$gte': 0.3, '$lt': 0.7}
                elif filters['risk_level'] == 'high':
                    query['risk_score'] = {'$gte': 0.7}
            
            # Debug: Check total count
            total_count = self.transactions.count_documents(query)
            print(f"Query: {query}")
            print(f"Found {total_count} matching transactions")
            
            # Pagination
            page = filters.get('page', 1)
            per_page = filters.get('per_page', 50)
            skip = (page - 1) * per_page
            
            transactions = list(self.transactions.find(query).skip(skip).limit(per_page))
            
            # Convert ObjectId to string for JSON serialization
            for transaction in transactions:
                transaction['_id'] = str(transaction['_id'])
                if 'timestamp' in transaction:
                    transaction['timestamp'] = transaction['timestamp'].isoformat()
            
            print(f"Returning {len(transactions)} transactions")
            return transactions
        
        except Exception as e:
            print(f"Error getting transactions: {e}")
            return []
    
    def get_transactions_with_count(self, filters):
        """Get transactions with total count for pagination"""
        try:
            query = {}
            
            print(f"Getting transactions with count for filters: {filters}")
            
            # First, let's see what fields exist in sample transaction
            sample = self.transactions.find_one()
            if sample:
                print(f"Sample transaction fields: {list(sample.keys())}")
            
            # Get total count without filters first
            total_all = self.transactions.count_documents({})
            print(f"Total transactions in database: {total_all}")
            
            # Date range filter
            if filters.get('date_range'):
                days = int(filters['date_range'].replace('d', ''))
                start_date = datetime.now() - timedelta(days=days)
                query['timestamp'] = {'$gte': start_date}
                print(f"Added date filter: from {start_date}")
            
            # For now, let's start with no other filters to see if we get data
            
            # Get total count with current filters
            total_count = self.transactions.count_documents(query)
            print(f"Query: {query}")
            print(f"Total matching transactions: {total_count}")
            
            # Pagination
            page = filters.get('page', 1)
            per_page = filters.get('per_page', 50)
            skip = (page - 1) * per_page
            
            transactions = list(self.transactions.find(query).skip(skip).limit(per_page))
            
            # Convert ObjectId to string for JSON serialization
            for transaction in transactions:
                transaction['_id'] = str(transaction['_id'])
                if 'timestamp' in transaction:
                    transaction['timestamp'] = transaction['timestamp'].isoformat()
            
            print(f"Returning {len(transactions)} transactions out of {total_count} total")
            
            return {
                'transactions': transactions,
                'total_count': total_count
            }
        
        except Exception as e:
            print(f"Error getting transactions with count: {e}")
            return {'transactions': [], 'total_count': 0}
    
    def get_transaction_by_id(self, transaction_id):
        """Get single transaction by ID"""
        try:
            from bson import ObjectId
            
            print(f"Looking for transaction with ID: {transaction_id}")
            
            # Try to convert to ObjectId
            try:
                object_id = ObjectId(transaction_id)
                transaction = self.transactions.find_one({'_id': object_id})
            except:
                # If ObjectId conversion fails, try as string
                transaction = self.transactions.find_one({'_id': transaction_id})
            
            if transaction:
                # Convert ObjectId to string for JSON serialization
                transaction['_id'] = str(transaction['_id'])
                if 'timestamp' in transaction:
                    transaction['timestamp'] = transaction['timestamp'].isoformat()
                
                # Show some transaction info for debugging
                print(f"Found transaction: ID={transaction['_id']}")
                if 'sender_account' in transaction:
                    print(f"  From: {transaction['sender_account']} -> To: {transaction.get('receiver_account', 'N/A')}")
                if 'amount_received' in transaction:
                    print(f"  Amount: {transaction['amount_received']} {transaction.get('receiving_currency', 'N/A')}")
                return transaction
            else:
                print("Transaction not found")
                return None
                
        except Exception as e:
            print(f"Error getting transaction by ID: {e}")
            return None
    
    def flag_transaction(self, transaction_id):
        """Flag a transaction as suspicious"""
        try:
            from bson import ObjectId
            
            print(f"Flagging transaction with ID: {transaction_id}")
            
            # Try to convert to ObjectId
            try:
                object_id = ObjectId(transaction_id)
                result = self.transactions.update_one(
                    {'_id': object_id},
                    {
                        '$set': {
                            'flagged': True,
                            'flagged_at': datetime.now(),
                            'flag_reason': 'User flagged as suspicious'
                        }
                    }
                )
            except:
                # If ObjectId conversion fails, try as string
                result = self.transactions.update_one(
                    {'_id': transaction_id},
                    {
                        '$set': {
                            'flagged': True,
                            'flagged_at': datetime.now(),
                            'flag_reason': 'User flagged as suspicious'
                        }
                    }
                )
            
            if result.modified_count > 0:
                print(f"Successfully flagged transaction")
                return True
            else:
                print("Transaction not found or already flagged")
                return False
                
        except Exception as e:
            print(f"Error flagging transaction: {e}")
            return False
    
    def get_transactions_for_analysis(self, filters):
        """Get transactions formatted for pattern analysis"""
        try:
            query = {}
            
            print(f"Getting transactions for pattern analysis with filters: {filters}")
            
            # Focus account filter
            if filters.get('focus_account'):
                focus_account = filters['focus_account']
                query['$or'] = [
                    {'sender_account': focus_account},
                    {'receiver_account': focus_account}
                ]
            
            # Minimum amount filter
            if filters.get('min_amount'):
                min_amount = float(filters['min_amount'])
                query['amount_received'] = {'$gte': min_amount}
            
            # Risk level filter
            if filters.get('risk_level') and filters['risk_level'] != 'all':
                risk_level = filters['risk_level']
                if risk_level == 'high':
                    query['risk_score'] = {'$gte': 0.7}
                elif risk_level == 'medium':
                    query['risk_score'] = {'$gte': 0.3, '$lt': 0.7}
                elif risk_level == 'low':
                    query['risk_score'] = {'$lt': 0.3}
            
            # Limit for performance
            limit = filters.get('limit', 1000)
            
            print(f"Analysis query: {query}")
            
            # Get transactions from database
            transactions_cursor = self.transactions.find(query).limit(limit).sort('timestamp', -1)
            transactions = list(transactions_cursor)
            
            print(f"Found {len(transactions)} transactions for analysis")
            
            # Transform data for pattern analyzer
            formatted_transactions = []
            
            for txn in transactions:
                try:
                    # Create standardized transaction format
                    formatted_txn = {
                        'transaction_id': str(txn.get('_id', '')),
                        'source': txn.get('from_account', ''),
                        'target': txn.get('to_account', ''),
                        'amount': float(txn.get('amount_received', 0)),
                        'currency': txn.get('receiving_currency', 'USD'),
                        'timestamp': txn.get('timestamp', datetime.now()),
                        'risk_score': float(txn.get('risk_score', 0)),
                        'from_bank': txn.get('from_bank', ''),
                        'to_bank': txn.get('to_bank', ''),
                        'payment_format': txn.get('payment_format', ''),
                        'is_laundering': txn.get('is_laundering', 0)
                    }
                    
                    # Ensure timestamp is datetime object
                    if isinstance(formatted_txn['timestamp'], str):
                        formatted_txn['timestamp'] = datetime.fromisoformat(formatted_txn['timestamp'].replace('Z', '+00:00'))
                    
                    formatted_transactions.append(formatted_txn)
                    
                except Exception as e:
                    print(f"Error formatting transaction {txn.get('_id', 'unknown')}: {e}")
                    continue
            
            print(f"Successfully formatted {len(formatted_transactions)} transactions for analysis")
            return formatted_transactions
            
        except Exception as e:
            print(f"Error getting transactions for analysis: {e}")
            return []
    
    def get_cash_flow_overview(self, currency='all', date_range='30d'):
        """Get cash flow overview statistics with detailed breakdown"""
        try:
            # Calculate date range
            days = int(date_range.replace('d', ''))
            start_date = datetime.now() - timedelta(days=days)
            
            # Build match conditions
            match_conditions = {'timestamp': {'$gte': start_date}}
            
            if currency != 'all':
                match_conditions['currency_type'] = currency
            
            print(f"Getting cash flow overview with filters: currency={currency}, date_range={date_range}")
            
            # Get basic statistics
            basic_stats = self._get_basic_stats(match_conditions)
            
            # Get currency breakdown
            currency_breakdown = self._get_currency_breakdown(match_conditions)
            
            # Get trends data
            trends = self._get_trends_data(match_conditions, days)
            
            # Get risk analysis
            risk_analysis = self._get_risk_analysis(match_conditions)
            
            # Get top flows
            top_flows = self._get_top_flows(match_conditions)
            
            return {
                **basic_stats,
                'currency_breakdown': currency_breakdown,
                'trends': trends,
                'risk_analysis': risk_analysis,
                'top_flows': top_flows
            }
                
        except Exception as e:
            print(f"Error getting cash flow overview: {e}")
            return {}
    
    def _get_basic_stats(self, match_conditions):
        """Get basic transaction statistics"""
        try:
            pipeline = [
                {'$match': match_conditions},
                {
                    '$group': {
                        '_id': None,
                        'total_transactions': {'$sum': 1},
                        'total_amount': {'$sum': '$amount_received'},
                        'avg_amount': {'$avg': '$amount_received'},
                        'max_amount': {'$max': '$amount_received'},
                        'min_amount': {'$min': '$amount_received'},
                        'avg_risk_score': {'$avg': '$risk_score'},
                        'high_risk_count': {
                            '$sum': {
                                '$cond': [{'$gte': ['$risk_score', 0.7]}, 1, 0]
                            }
                        }
                    }
                }
            ]
            
            results = list(self.transactions.aggregate(pipeline))
            
            if results:
                stats = results[0]
                del stats['_id']
                return stats
            else:
                return {
                    'total_transactions': 0,
                    'total_amount': 0,
                    'avg_amount': 0,
                    'max_amount': 0,
                    'min_amount': 0,
                    'avg_risk_score': 0,
                    'high_risk_count': 0
                }
        except Exception as e:
            print(f"Error getting basic stats: {e}")
            return {}
    
    def _get_currency_breakdown(self, match_conditions):
        """Get currency breakdown for pie chart"""
        try:
            pipeline = [
                {'$match': match_conditions},
                {
                    '$group': {
                        '_id': {'$ifNull': ['$currency_type', '$receiving_currency']},
                        'amount': {'$sum': '$amount_received'},
                        'count': {'$sum': 1}
                    }
                },
                {'$sort': {'amount': -1}}
            ]
            
            results = list(self.transactions.aggregate(pipeline))
            
            return [{
                'currency': result['_id'] or 'Unknown',
                'amount': result['amount'],
                'count': result['count']
            } for result in results]
            
        except Exception as e:
            print(f"Error getting currency breakdown: {e}")
            return []
    
    def _get_trends_data(self, match_conditions, days):
        """Get trends data for line chart"""
        try:
            pipeline = [
                {'$match': match_conditions},
                {
                    '$group': {
                        '_id': {
                            '$dateToString': {
                                'format': '%Y-%m-%d',
                                'date': '$timestamp'
                            }
                        },
                        'amount': {'$sum': '$amount_received'},
                        'count': {'$sum': 1}
                    }
                },
                {'$sort': {'_id': 1}}
            ]
            
            results = list(self.transactions.aggregate(pipeline))
            
            return [{
                'date': result['_id'],
                'amount': result['amount'],
                'count': result['count']
            } for result in results]
            
        except Exception as e:
            print(f"Error getting trends data: {e}")
            return []
    
    def _get_risk_analysis(self, match_conditions):
        """Get risk analysis breakdown"""
        try:
            pipeline = [
                {'$match': match_conditions},
                {
                    '$group': {
                        '_id': {
                            '$switch': {
                                'branches': [
                                    {'case': {'$gte': ['$risk_score', 0.7]}, 'then': 'high'},
                                    {'case': {'$gte': ['$risk_score', 0.4]}, 'then': 'medium'}
                                ],
                                'default': 'low'
                            }
                        },
                        'count': {'$sum': 1},
                        'amount': {'$sum': '$amount_received'}
                    }
                }
            ]
            
            results = list(self.transactions.aggregate(pipeline))
            
            risk_data = {'low': 0, 'medium': 0, 'high': 0}
            for result in results:
                risk_data[result['_id']] = {
                    'count': result['count'],
                    'amount': result['amount']
                }
            
            return risk_data
            
        except Exception as e:
            print(f"Error getting risk analysis: {e}")
            return {}
    
    def _get_top_flows(self, match_conditions, limit=5):
        """Get top cash flows"""
        try:
            pipeline = [
                {'$match': match_conditions},
                {
                    '$group': {
                        '_id': {
                            'from_bank': '$from_bank',
                            'to_bank': '$to_bank'
                        },
                        'total_amount': {'$sum': '$amount_received'},
                        'count': {'$sum': 1},
                        'avg_risk': {'$avg': '$risk_score'}
                    }
                },
                {'$sort': {'total_amount': -1}},
                {'$limit': limit}
            ]
            
            results = list(self.transactions.aggregate(pipeline))
            
            return [{
                'from_bank': result['_id']['from_bank'],
                'to_bank': result['_id']['to_bank'],
                'amount': result['total_amount'],
                'count': result['count'],
                'avg_risk': result['avg_risk']
            } for result in results]
            
        except Exception as e:
            print(f"Error getting top flows: {e}")
            return []
    
    def get_geographic_flow_data(self, currency='USD', time_period='30d', min_amount=0, risk_level='all'):
        """Get geographic cash flow data for map visualization with enhanced filtering"""
        try:
            # Calculate date range
            days = int(time_period.replace('d', ''))
            start_date = datetime.now() - timedelta(days=days)
            
            # Dynamic bank location detection (no hardcoding)
            print(f"Processing geographic flow data - currency: {currency}, period: {time_period}, min_amount: {min_amount}, risk_level: {risk_level}")
            
            # Debug: Check total transactions
            total_transactions = self.transactions.count_documents({})
            print(f"Total transactions in database: {total_transactions}")
            
            # Debug: Sample transaction fields
            sample_transaction = self.transactions.find_one({})
            if sample_transaction:
                print(f"Sample transaction fields: {list(sample_transaction.keys())}")
            
            # Build match conditions
            match_conditions = {'timestamp': {'$gte': start_date}}
            
            # Add minimum amount filter
            if min_amount > 0:
                match_conditions['amount_received'] = {'$gte': min_amount}
                print(f"Added minimum amount filter: {min_amount}")
            
            # Add risk level filter
            if risk_level != 'all':
                if risk_level == 'high':
                    match_conditions['risk_score'] = {'$gte': 0.7}
                elif risk_level == 'medium':
                    match_conditions['risk_score'] = {'$gte': 0.4, '$lt': 0.7}
                elif risk_level == 'low':
                    match_conditions['risk_score'] = {'$lt': 0.4}
                print(f"Added risk level filter: {risk_level}")
            
            # Handle currency filter
            if currency.upper() not in ['ALL', 'ALL CURRENCIES']:
                match_conditions['receiving_currency'] = currency
            else:
                print("Processing ALL currencies - no currency filter applied")
            
            print(f"Match conditions: {match_conditions}")
            
            # Aggregate transactions by country pairs
            pipeline = [
                {'$match': match_conditions},
                {
                    '$group': {
                        '_id': {
                            'from_bank': '$from_bank',
                            'to_bank': '$to_bank'
                        },
                        'total_amount': {'$sum': '$amount_received'},
                        'transaction_count': {'$sum': 1},
                        'avg_risk_score': {'$avg': '$risk_score'},
                        'max_risk_score': {'$max': '$risk_score'}
                    }
                }
            ]
            
            flows_data = list(self.transactions.aggregate(pipeline))
            print(f"Found {len(flows_data)} flow aggregations")
            
            # Debug: Print first few flows
            if flows_data:
                print(f"Sample flow data: {flows_data[0]}")
            
            # Group by countries
            country_volumes = {}
            country_flows = []
            
            for flow in flows_data:
                from_bank = flow['_id']['from_bank']
                to_bank = flow['_id']['to_bank']
                
                print(f"Processing flow from {from_bank} to {to_bank}")
                
                # Get dynamic bank locations
                from_location = self._get_bank_location(from_bank)
                to_location = self._get_bank_location(to_bank)
                
                print(f"From location: {from_location}")
                print(f"To location: {to_location}")
                
                if from_location and to_location:
                    from_country = from_location['id']
                    to_country = to_location['id']
                    
                    # Update country volumes
                    if from_country not in country_volumes:
                        country_volumes[from_country] = {
                            'id': from_country,
                            'lat': from_location['lat'],
                            'lng': from_location['lng'],
                            'volume': 0,
                            'risk': 0,
                            'transaction_count': 0
                        }
                    
                    if to_country not in country_volumes:
                        country_volumes[to_country] = {
                            'id': to_country,
                            'lat': to_location['lat'],
                            'lng': to_location['lng'],
                            'volume': 0,
                            'risk': 0,
                            'transaction_count': 0
                        }
                    
                    # Add volumes
                    volume_millions = flow['total_amount'] / 1000000
                    country_volumes[from_country]['volume'] += volume_millions
                    country_volumes[to_country]['volume'] += volume_millions
                    
                    print(f"Added volume {volume_millions}M to {from_country} and {to_country}")
                    
                    # Update risk scores (weighted average)
                    current_risk = country_volumes[from_country]['risk']
                    current_count = country_volumes[from_country]['transaction_count']
                    new_count = current_count + flow['transaction_count']
                    
                    if new_count > 0:
                        country_volumes[from_country]['risk'] = (
                            (current_risk * current_count + flow['avg_risk_score'] * flow['transaction_count']) / new_count
                        )
                        country_volumes[from_country]['transaction_count'] = new_count
                    
                    # Create flow if significant 
                    if flow['total_amount'] > 10000:  # Much lower threshold for visibility
                        # For same-country flows, use bank names instead of country codes
                        if from_country == to_country:
                            flow_source = f"{from_country}_{from_bank}".replace(' ', '_')[:10]
                            flow_target = f"{to_country}_{to_bank}".replace(' ', '_')[:10]
                        else:
                            flow_source = from_country
                            flow_target = to_country
                            
                        country_flows.append({
                            'source': flow_source,
                            'target': flow_target,
                            'amount': flow['total_amount'],
                            'risk': flow['avg_risk_score'],
                            'from_bank': from_bank,
                            'to_bank': to_bank
                        })
                else:
                    print(f"Skipping flow due to missing location data: {from_bank} -> {to_bank}")
            
            # Convert to lists
            nodes = list(country_volumes.values())
            
            print(f"Generated {len(nodes)} nodes before filtering")
            print(f"Generated {len(country_flows)} flows")
            
            # Debug: Show node volumes before filtering
            for node in nodes:
                print(f"Node {node['id']}: volume = {node['volume']}M")
            
            # Filter out small volumes (reduce filter to catch more data)
            nodes = [node for node in nodes if node['volume'] > 0.01]  # Reduced minimum to 0.01M volume (10K)
            
            print(f"Generated {len(nodes)} nodes after filtering")
            
            # Debug: Show filtered node volumes
            for node in nodes:
                print(f"Filtered Node {node['id']}: volume = {node['volume']}M")
            
            # Log the actual data results without fallback
            print(f"Generated {len(nodes)} final nodes from real data")
            print(f"Generated {len(country_flows)} final flows from real data")
            
            # Calculate total volume properly
            total_volume = sum([node['volume'] for node in nodes]) if nodes else 0
            
            result = {
                'nodes': nodes,
                'flows': country_flows,
                'currency': currency,
                'time_period': time_period,
                'total_volume': total_volume,
                'total_flows': len(country_flows)
            }
            
            print(f"Final result: nodes={len(nodes)}, flows={len(country_flows)}, volume={total_volume}")
            return result
        
        except Exception as e:
            print(f"Error getting geographic flow data: {e}")
            import traceback
            traceback.print_exc()
            # Return empty data structure on error - no hardcoded fallback
            return {
                'nodes': [],
                'flows': [],
                'currency': currency if 'currency' in locals() else 'USD',
                'time_period': time_period if 'time_period' in locals() else '30d',
                'total_volume': 0,
                'total_flows': 0,
                'error': str(e)
            }
    
    def get_multi_currency_flow(self, account_id=None):
        """Get multi-currency cash flow data"""
        try:
            query = {}
            if account_id:
                query = {'$or': [
                    {'from_account': account_id},
                    {'to_account': account_id}
                ]}
            
            # Get currency breakdown
            pipeline = [
                {'$match': query},
                {'$group': {
                    '_id': '$receiving_currency',
                    'total_received': {'$sum': '$amount_received'},
                    'total_paid': {'$sum': '$amount_paid'},
                    'transaction_count': {'$sum': 1},
                    'avg_risk_score': {'$avg': '$risk_score'}
                }}
            ]
            
            currency_data = list(self.transactions.aggregate(pipeline))
            
            # Get recent transactions
            recent_transactions = list(self.transactions.find(query).sort('timestamp', -1).limit(50))
            
            for transaction in recent_transactions:
                transaction['_id'] = str(transaction['_id'])
                transaction['timestamp'] = transaction['timestamp'].isoformat()
            
            return {
                'currency_breakdown': currency_data,
                'recent_transactions': recent_transactions,
                'account_id': account_id
            }
        
        except Exception as e:
            print(f"Error getting multi-currency flow: {e}")
            return {}
    
    def get_alerts(self, status='active', priority=None):
        """Get alerts with filters based on real analysis"""
        try:
            # Always ensure we have up-to-date alerts based on latest analysis
            self.update_alerts_from_analysis()
            
            # Build query for filtering
            query = {}
            if status and status != 'all':
                query['status'] = status
            if priority and priority != 'all':
                query['priority'] = priority
            
            alerts = list(self.alerts.find(query).sort('created_at', -1).limit(100))
            
            # Convert ObjectId and datetime to strings
            for alert in alerts:
                alert['_id'] = str(alert['_id'])
                if 'created_at' in alert:
                    alert['created_at'] = alert['created_at'].isoformat()
                if 'updated_at' in alert:
                    alert['updated_at'] = alert['updated_at'].isoformat()
            
            return alerts
        
        except Exception as e:
            print(f"Error getting alerts: {e}")
            return []
    
    def get_alert_by_id(self, alert_id):
        """Get a single alert by ID"""
        try:
            from bson import ObjectId
            alert = self.alerts.find_one({'_id': ObjectId(alert_id)})
            
            if alert:
                alert['_id'] = str(alert['_id'])
                if 'created_at' in alert:
                    alert['created_at'] = alert['created_at'].isoformat()
                if 'updated_at' in alert:
                    alert['updated_at'] = alert['updated_at'].isoformat()
                return alert
            
            return None
        except Exception as e:
            print(f"Error getting alert by ID {alert_id}: {e}")
            return None
    
    def generate_alerts_from_transactions(self):
        """Generate alerts from recent high-risk transactions"""
        try:
            # Get recent high-risk transactions
            start_date = datetime.now() - timedelta(days=30)
            
            high_risk_transactions = list(self.transactions.find({
                'timestamp': {'$gte': start_date},
                'risk_score': {'$gte': 0.7}
            }).sort('timestamp', -1).limit(20))
            
            # Generate alerts for high-risk transactions
            for transaction in high_risk_transactions:
                # Check if alert already exists for this transaction
                existing_alert = self.alerts.find_one({
                    'transaction_id': str(transaction['_id']),
                    'type': 'high_risk_transaction'
                })
                
                if not existing_alert:
                    # Get country information from bank location
                    from_bank = transaction.get('from_bank', '').strip().upper()
                    to_bank = transaction.get('to_bank', '').strip().upper()
                    from_country = self._country_code_mappings.get(from_bank, 'Unknown')
                    to_country = self._country_code_mappings.get(to_bank, 'Unknown')
                    
                    # Determine priority based on risk score and amount
                    if transaction['risk_score'] >= 0.9 or transaction.get('amount_received', 0) >= 500000:
                        priority = 'high'
                    elif transaction['risk_score'] >= 0.8 or transaction.get('amount_received', 0) >= 100000:
                        priority = 'medium'
                    else:
                        priority = 'low'
                    
                    # Create alert
                    alert = {
                        'title': f'High Risk Transaction Detected',
                        'description': f'Transaction of ${transaction.get("amount_received", 0):,.2f} from {transaction.get("from_bank", "Unknown")} ({from_country}) to {transaction.get("to_bank", "Unknown")} ({to_country}) has risk score of {transaction["risk_score"]:.1%}',
                        'type': 'high_risk_transaction',
                        'priority': priority,
                        'status': 'active',
                        'transaction_id': str(transaction['_id']),
                        'account_id': transaction.get('from_account', ''),
                        'amount': transaction.get('amount_received', 0),
                        'currency': transaction.get('receiving_currency', 'USD'),
                        'risk_score': transaction['risk_score'],
                        'from_country': from_country,
                        'to_country': to_country,
                        'created_at': datetime.now(),
                        'updated_at': datetime.now(),
                        'source': 'automated_detection'
                    }
                    
                    self.alerts.insert_one(alert)
                    print(f"Generated alert for transaction {transaction['_id']}")
            
            # Generate alerts for unusual patterns
            self._generate_pattern_alerts()
            
            print(f"Alert generation completed")
            
        except Exception as e:
            print(f"Error generating alerts: {e}")
    
    def _generate_pattern_alerts(self):
        """Generate alerts for unusual transaction patterns"""
        try:
            start_date = datetime.now() - timedelta(days=7)
            
            # Find accounts with sudden volume increases
            pipeline = [
                {'$match': {'timestamp': {'$gte': start_date}}},
                {'$group': {
                    '_id': '$from_account',
                    'total_amount': {'$sum': '$amount_received'},
                    'transaction_count': {'$sum': 1},
                    'avg_risk': {'$avg': '$risk_score'},
                    'banks': {'$addToSet': '$from_bank'}
                }},
                {'$match': {
                    '$or': [
                        {'total_amount': {'$gte': 1000000}},  # High volume
                        {'transaction_count': {'$gte': 50}},  # High frequency
                        {'avg_risk': {'$gte': 0.6}}  # High average risk
                    ]
                }},
                {'$limit': 10}
            ]
            
            suspicious_accounts = list(self.transactions.aggregate(pipeline))
            
            for account_data in suspicious_accounts:
                account_id = account_data['_id']
                
                # Check if alert already exists
                existing_alert = self.alerts.find_one({
                    'account_id': account_id,
                    'type': 'suspicious_pattern',
                    'created_at': {'$gte': start_date}
                })
                
                if not existing_alert:
                    # Determine alert type and priority
                    if account_data['total_amount'] >= 1000000:
                        alert_type = 'high_volume_pattern'
                        priority = 'high'
                        description = f'Account {account_id} has unusually high transaction volume: ${account_data["total_amount"]:,.2f} in the last 7 days'
                    elif account_data['transaction_count'] >= 50:
                        alert_type = 'high_frequency_pattern'
                        priority = 'medium'
                        description = f'Account {account_id} has high transaction frequency: {account_data["transaction_count"]} transactions in 7 days'
                    else:
                        alert_type = 'high_risk_pattern'
                        priority = 'medium'
                        description = f'Account {account_id} has consistently high risk scores: {account_data["avg_risk"]:.1%} average risk'
                    
                    # Get country information for the banks involved
                    countries = []
                    for bank in account_data['banks']:
                        bank_upper = bank.strip().upper() if bank else ''
                        country = self._country_code_mappings.get(bank_upper, 'Unknown')
                        if country != 'Unknown':
                            countries.append(country)
                    
                    alert = {
                        'title': 'Suspicious Transaction Pattern',
                        'description': description,
                        'type': alert_type,
                        'priority': priority,
                        'status': 'active',
                        'account_id': account_id,
                        'pattern_data': {
                            'total_amount': account_data['total_amount'],
                            'transaction_count': account_data['transaction_count'],
                            'avg_risk': account_data['avg_risk'],
                            'countries_involved': list(set(countries))
                        },
                        'created_at': datetime.now(),
                        'updated_at': datetime.now(),
                        'source': 'pattern_analysis'
                    }
                    
                    self.alerts.insert_one(alert)
                    print(f"Generated pattern alert for account {account_id}")
            
        except Exception as e:
            print(f"Error generating pattern alerts: {e}")
    
    def update_alerts_from_analysis(self):
        """Update alerts based on real-time analysis of transactions"""
        try:
            # Check if we need to refresh alerts (e.g., every hour)
            last_update = self.alerts.find_one({}, sort=[('created_at', -1)])
            if last_update and 'created_at' in last_update:
                time_since_update = datetime.now() - last_update['created_at']
                if time_since_update.total_seconds() < 3600:  # Less than 1 hour
                    return  # Skip update if recent alerts exist
            
            self.generate_real_alerts_from_analysis()
        
        except Exception as e:
            print(f"Error updating alerts: {e}")
    
    def generate_real_alerts_from_analysis(self):
        """Generate real alerts based on risk analysis and pattern detection"""
        try:
            print("Analyzing transactions and generating real alerts...")
            
            # Clear existing alerts to avoid duplicates
            self.alerts.delete_many({})
            print("Cleared existing alerts from database")
            
            # Import analysis services
            from services.risk_calculator import RiskCalculator
            from services.pattern_analyzer import create_pattern_analyzer
            from services.network_analyzer import NetworkAnalyzer
            
            # Initialize analyzers
            risk_calculator = RiskCalculator()
            pattern_analyzer = create_pattern_analyzer()
            network_analyzer = NetworkAnalyzer(self.db)
            
            # Get all transactions for analysis
            all_transactions = list(self.transactions.find({}).sort('timestamp', -1).limit(1000))
            
            if not all_transactions:
                print("No transactions found in database. Cannot generate real alerts.")
                return
            
            print(f"Analyzing {len(all_transactions)} transactions...")
            
            alerts_created = 0
            
            # 1. Analyze High Risk Transactions
            print("Analyzing high risk transactions...")
            for transaction in all_transactions:
                try:
                    # Calculate risk score using RiskCalculator
                    risk_score = risk_calculator.calculate_transaction_risk(transaction)
                    
                    # Update transaction with calculated risk score
                    self.transactions.update_one(
                        {'_id': transaction['_id']},
                        {'$set': {'risk_score': risk_score}}
                    )
                    
                    # Generate alert for high risk transactions
                    if risk_score >= 0.8:
                        priority = 'high'
                        alert_type = 'high_risk_transaction'
                        title = 'High Risk Transaction Detected'
                        description = f'Transaction {str(transaction["_id"])} flagged with risk score {risk_score:.2f}'
                        
                    elif risk_score >= 0.6:
                        priority = 'medium'
                        alert_type = 'medium_risk_transaction'
                        title = 'Medium Risk Transaction Detected'
                        description = f'Transaction {str(transaction["_id"])} flagged with risk score {risk_score:.2f}'
                        
                    else:
                        continue  # Skip low risk transactions
                    
                    # Create alert
                    alert = self._create_alert(
                        title=title,
                        description=description,
                        alert_type=alert_type,
                        priority=priority,
                        transaction=transaction,
                        risk_score=risk_score,
                        evidence={'calculated_risk_score': risk_score}
                    )
                    
                    self.alerts.insert_one(alert)
                    alerts_created += 1
                    
                except Exception as e:
                    print(f"Error analyzing transaction {transaction.get('_id')}: {e}")
                    continue
            
            print(f"Created {alerts_created} risk-based alerts")
            
            # 2. Analyze Patterns using Pattern Analyzer
            print("Analyzing suspicious patterns...")
            try:
                # Convert transactions to DataFrame for pattern analysis
                df_transactions = pd.DataFrame(all_transactions)
                
                # Run pattern analysis
                pattern_results = pattern_analyzer.analyze_patterns(df_transactions)
                
                for pattern_result in pattern_results:
                    try:
                        # Determine priority based on risk level
                        if pattern_result.risk_level.value == 'critical':
                            priority = 'high'
                        elif pattern_result.risk_level.value == 'high':
                            priority = 'high'
                        elif pattern_result.risk_level.value == 'medium':
                            priority = 'medium'
                        else:
                            priority = 'low'
                        
                        # Create alert for detected pattern
                        alert = self._create_alert(
                            title=f"Suspicious Pattern: {pattern_result.pattern_type.value.replace('_', ' ').title()}",
                            description=pattern_result.description,
                            alert_type='suspicious_pattern',
                            priority=priority,
                            transaction=None,  # Pattern may involve multiple transactions
                            risk_score=pattern_result.confidence,
                            evidence={
                                'pattern_type': pattern_result.pattern_type.value,
                                'confidence': pattern_result.confidence,
                                'affected_accounts': pattern_result.affected_accounts,
                                'transaction_ids': pattern_result.transaction_ids,
                                'evidence': pattern_result.evidence
                            }
                        )
                        
                        # Add pattern-specific fields
                        alert['affected_accounts'] = pattern_result.affected_accounts
                        alert['related_transactions'] = pattern_result.transaction_ids
                        
                        self.alerts.insert_one(alert)
                        alerts_created += 1
                        
                    except Exception as e:
                        print(f"Error creating pattern alert: {e}")
                        continue
                        
            except Exception as e:
                print(f"Error in pattern analysis: {e}")
            
            # 3. Analyze Network Anomalies
            print("Analyzing network anomalies...")
            try:
                # Get network data for analysis
                network_data = network_analyzer.get_network_data(depth=2, min_amount=1000)
                
                if network_data and network_data.get('nodes'):
                    # Analyze for suspicious network patterns
                    suspicious_accounts = []
                    
                    for node in network_data['nodes']:
                        # Check for accounts with unusually high transaction counts
                        if node.get('transaction_count', 0) > 50:
                            suspicious_accounts.append({
                                'account': node['id'],
                                'reason': 'High transaction volume',
                                'transaction_count': node['transaction_count'],
                                'risk_level': node.get('avg_risk_score', 0)
                            })
                        
                        # Check for accounts with high risk scores
                        if node.get('avg_risk_score', 0) > 0.7:
                            suspicious_accounts.append({
                                'account': node['id'],
                                'reason': 'High average risk score',
                                'avg_risk_score': node['avg_risk_score'],
                                'transaction_count': node.get('transaction_count', 0)
                            })
                    
                    # Create alerts for suspicious accounts
                    for suspicious in suspicious_accounts:
                        priority = 'high' if suspicious.get('avg_risk_score', 0) > 0.8 else 'medium'
                        
                        alert = self._create_alert(
                            title=f"Network Anomaly: {suspicious['reason']}",
                            description=f"Account {suspicious['account']} shows {suspicious['reason'].lower()}",
                            alert_type='network_anomaly',
                            priority=priority,
                            transaction=None,
                            risk_score=suspicious.get('avg_risk_score', suspicious.get('transaction_count', 0) / 100),
                            evidence=suspicious
                        )
                        
                        alert['account_id'] = suspicious['account']
                        
                        self.alerts.insert_one(alert)
                        alerts_created += 1
                        
            except Exception as e:
                print(f"Error in network analysis: {e}")
            
            print(f"Successfully generated {alerts_created} real alerts based on analysis")
            
        except Exception as e:
            print(f"Error generating real alerts: {e}")
    
    def _create_alert(self, title, description, alert_type, priority, transaction=None, risk_score=0.0, evidence=None):
        """Helper method to create alert document"""
        alert = {
            'title': title,
            'description': description,
            'type': alert_type,
            'priority': priority,
            'status': 'active',  # All new alerts start as active
            'risk_score': risk_score,
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'source': 'real_analysis',
            'read': False,
            'evidence': evidence or {},
            'notes': []
        }
        
        # Add transaction-specific fields if transaction is provided
        if transaction:
            alert.update({
                'transaction_id': str(transaction['_id']),
                'account_id': transaction.get('from_account'),
                'amount': transaction.get('amount_received'),
                'currency': transaction.get('receiving_currency', 'USD'),
                'from_country': transaction.get('from_country', 'Unknown'),
                'to_country': transaction.get('to_country', 'Unknown')
            })
        
        return alert
    
    def get_alert_statistics(self):
        """Get alert statistics for dashboard"""
        try:
            today = datetime.now()
            today_start = today.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Count active alerts
            active_alerts = self.alerts.count_documents({'status': 'active'})
            
            # Count high priority alerts
            high_priority = self.alerts.count_documents({
                'status': 'active',
                'priority': 'high'
            })
            
            # Count resolved today
            resolved_today = self.alerts.count_documents({
                'status': 'resolved',
                'updated_at': {'$gte': today_start}
            })
            
            # Calculate average response time (simplified)
            resolved_alerts = list(self.alerts.find({
                'status': 'resolved',
                'resolved_at': {'$exists': True}
            }).limit(100))
            
            response_times = []
            for alert in resolved_alerts:
                if 'resolved_at' in alert and 'created_at' in alert:
                    response_time = (alert['resolved_at'] - alert['created_at']).total_seconds() / 3600  # hours
                    response_times.append(response_time)
            
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            return {
                'active_alerts': active_alerts,
                'high_priority': high_priority,
                'resolved_today': resolved_today,
                'avg_response_time': round(avg_response_time, 1)
            }
        
        except Exception as e:
            print(f"Error getting alert statistics: {e}")
            return {
                'active_alerts': 0,
                'high_priority': 0,
                'resolved_today': 0,
                'avg_response_time': 0
            }
    
    def update_alert_status(self, alert_id, status, notes=None):
        """Update alert status"""
        try:
            from bson import ObjectId
            
            update_data = {
                'status': status,
                'updated_at': datetime.now()
            }
            
            if status == 'resolved':
                update_data['resolved_at'] = datetime.now()
            
            if notes:
                update_data['notes'] = notes
            
            result = self.alerts.update_one(
                {'_id': ObjectId(alert_id)},
                {'$set': update_data}
            )
            
            return result.modified_count > 0
        
        except Exception as e:
            print(f"Error updating alert status: {e}")
            return False
    
    def mark_alert_read(self, alert_id):
        """Mark an alert as read"""
        try:
            from bson import ObjectId
            
            result = self.alerts.update_one(
                {'_id': ObjectId(alert_id)},
                {'$set': {'read': True, 'read_at': datetime.now()}}
            )
            
            return result.modified_count > 0
        
        except Exception as e:
            print(f"Error marking alert as read: {e}")
            return False
    
    def get_account_analysis(self, account_id):
        """Get detailed account analysis"""
        try:
            # Get account info
            account = self.accounts.find_one({'account_id': account_id})
            if not account:
                return {'error': 'Account not found'}
            
            # Get transaction history
            transactions = list(self.transactions.find({
                '$or': [
                    {'from_account': account_id},
                    {'to_account': account_id}
                ]
            }).sort('timestamp', -1).limit(100))
            
            # Calculate statistics
            total_received = sum([t['amount_received'] for t in transactions if t['to_account'] == account_id])
            total_sent = sum([t['amount_paid'] for t in transactions if t['from_account'] == account_id])
            avg_risk_score = np.mean([t['risk_score'] for t in transactions]) if transactions else 0
            
            # Get currency breakdown
            currencies = {}
            for t in transactions:
                curr = t['receiving_currency']
                if curr not in currencies:
                    currencies[curr] = {'received': 0, 'sent': 0, 'count': 0}
                
                if t['to_account'] == account_id:
                    currencies[curr]['received'] += t['amount_received']
                else:
                    currencies[curr]['sent'] += t['amount_paid']
                currencies[curr]['count'] += 1
            
            # Convert ObjectIds and dates
            account['_id'] = str(account['_id'])
            for transaction in transactions:
                transaction['_id'] = str(transaction['_id'])
                transaction['timestamp'] = transaction['timestamp'].isoformat()
            
            return {
                'account': account,
                'transactions': transactions,
                'statistics': {
                    'total_received': total_received,
                    'total_sent': total_sent,
                    'transaction_count': len(transactions),
                    'avg_risk_score': round(avg_risk_score, 3),
                    'currencies': currencies
                }
            }
        
        except Exception as e:
            print(f"Error getting account analysis: {e}")
            return {'error': str(e)}
    
    def process_uploaded_file(self, filepath):
        """Process uploaded transaction file with comprehensive validation and risk scoring"""
        try:
            # Read file based on extension
            if filepath.endswith('.csv'):
                try:
                    df = pd.read_csv(filepath, encoding='utf-8')
                except UnicodeDecodeError:
                    df = pd.read_csv(filepath, encoding='latin-1')
            elif filepath.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(filepath)
            else:
                return {
                    'success': False,
                    'error': 'Unsupported file format. Please upload CSV, XLSX, or XLS files.'
                }
            
            # Check if dataframe is empty
            if df.empty:
                return {
                    'success': False,
                    'error': 'The uploaded file is empty or contains no data.'
                }
            
            print(f"Loaded file with {len(df)} rows and columns: {list(df.columns)}")
            
            # Define required columns with flexible matching (supporting both old and new formats)
            # Note: amount_paid is optional for new format as it uses single Amount column
            required_columns_map = {
                'timestamp': ['Timestamp', 'Date', 'Transaction Date', 'Time', 'DateTime'],
                'from_bank': ['From Bank', 'Sender Bank', 'Source Bank', 'Originating Bank', 'Sender_bank_location'],
                'from_account': ['From Account', 'Sender Account', 'Source Account', 'From Acc', 'Sender_account'],
                'to_bank': ['To Bank', 'Receiver Bank', 'Destination Bank', 'Receiving Bank', 'Receiver_bank_location'],
                'to_account': ['To Account', 'Receiver Account', 'Destination Account', 'To Acc', 'Receiver_account'],
                'amount_received': ['Amount Received', 'Amount', 'Transaction Amount', 'Received Amount'],
                'receiving_currency': ['Receiving Currency', 'Currency', 'Curr', 'CCY', 'Received_currency'],
                'payment_currency': ['Payment Currency', 'Pay Currency', 'Send Currency', 'Payment_currency'],
                'payment_format': ['Payment Format', 'Payment Type', 'Transaction Type', 'Method', 'Payment_type']
            }
            
            # Optional columns (not required for new format)
            optional_columns_map = {
                'amount_paid': ['Amount Paid', 'Paid Amount', 'Amount Sent', 'Send Amount']
            }
            
            # Map required columns
            column_mapping = {}
            missing_fields = []
            
            for field, possible_names in required_columns_map.items():
                found = False
                for col_name in df.columns:
                    if col_name in possible_names:
                        column_mapping[field] = col_name
                        found = True
                        break
                
                if not found:
                    # Try case-insensitive partial matching
                    for col_name in df.columns:
                        for possible in possible_names:
                            if possible.lower() in col_name.lower() or col_name.lower() in possible.lower():
                                column_mapping[field] = col_name
                                found = True
                                break
                        if found:
                            break
                
                if not found:
                    missing_fields.append(field)

            # Map optional columns
            for field, possible_names in optional_columns_map.items():
                found = False
                for col_name in df.columns:
                    if col_name in possible_names:
                        column_mapping[field] = col_name
                        found = True
                        break
                
                if not found:
                    # Try case-insensitive partial matching
                    for col_name in df.columns:
                        for possible in possible_names:
                            if possible.lower() in col_name.lower() or col_name.lower() in possible.lower():
                                column_mapping[field] = col_name
                                found = True
                                break
                        if found:
                            break
            
            if missing_fields:
                return {
                    'success': False,
                    'error': f'Missing required columns for fields: {missing_fields}',
                    'details': f'Available columns: {list(df.columns)}',
                    'required_fields': required_columns_map
                }
            
            print(f"Column mapping: {column_mapping}")
            
            # Process and validate data
            transaction_ids = []
            processed_records = 0
            errors = []
            total_volume = 0
            currencies_found = set()
            risk_scores = []
            
            for index, row in df.iterrows():
                try:
                    # Parse timestamp - handle both single timestamp and separate Date/Time columns
                    try:
                        # Check if we have separate Date and Time columns
                        if 'Date' in df.columns and 'Time' in df.columns:
                            date_str = str(row['Date']).strip()
                            time_str = str(row['Time']).strip()
                            datetime_str = f"{date_str} {time_str}"
                            timestamp = pd.to_datetime(datetime_str)
                        else:
                            timestamp = pd.to_datetime(row[column_mapping['timestamp']])
                        
                        if pd.isna(timestamp):
                            timestamp = datetime.now()
                    except:
                        timestamp = datetime.now()
                        errors.append(f"Row {index + 1}: Invalid timestamp, using current time")
                    
                    # Parse amounts - handle both single Amount column and separate received/paid amounts
                    try:
                        # Check if we have a single Amount column (new format)
                        if 'Amount' in df.columns:
                            amount_received = float(str(row['Amount']).replace(',', '').replace('$', ''))
                            amount_paid = amount_received  # Same amount for both
                        else:
                            # Use the old format with separate amounts
                            amount_received = float(str(row[column_mapping['amount_received']]).replace(',', '').replace('$', ''))
                        
                        if amount_received <= 0:
                            errors.append(f"Row {index + 1}: Invalid amount: {amount_received}")
                            continue
                    except:
                        errors.append(f"Row {index + 1}: Could not parse amount")
                        continue
                    
                    # Handle amount_paid if not set above
                    if 'Amount' not in df.columns and 'amount_paid' in column_mapping:
                        try:
                            amount_paid = float(str(row[column_mapping['amount_paid']]).replace(',', '').replace('$', ''))
                            if amount_paid <= 0:
                                amount_paid = amount_received  # Default to received amount
                        except:
                            amount_paid = amount_received
                    elif 'Amount' not in df.columns:
                        # If no amount_paid column, use received amount
                        amount_paid = amount_received
                    
                    # Get currencies
                    receiving_currency = str(row[column_mapping['receiving_currency']]).upper().strip()
                    payment_currency = str(row[column_mapping['payment_currency']]).upper().strip()
                    
                    if receiving_currency not in ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'CNY', 'INR']:
                        receiving_currency = 'USD'  # Default to USD
                    
                    if payment_currency not in ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'CNY', 'INR']:
                        payment_currency = receiving_currency
                    
                    currencies_found.add(receiving_currency)
                    currencies_found.add(payment_currency)
                    
                    # Calculate basic risk score
                    risk_score = self._calculate_basic_risk_score(
                        amount_received, receiving_currency, payment_currency, 
                        str(row[column_mapping['payment_format']]), timestamp
                    )
                    
                    # Create transaction document
                    transaction = {
                        'timestamp': timestamp,
                        'from_bank': str(row[column_mapping['from_bank']]).strip(),
                        'from_account': str(row[column_mapping['from_account']]).strip(),
                        'to_bank': str(row[column_mapping['to_bank']]).strip(),
                        'to_account': str(row[column_mapping['to_account']]).strip(),
                        'amount_received': round(amount_received, 2),
                        'receiving_currency': receiving_currency,
                        'amount_paid': round(amount_paid, 2),
                        'payment_currency': payment_currency,
                        'payment_format': str(row[column_mapping['payment_format']]).strip(),
                        'risk_score': round(risk_score, 3),
                        'processed_at': datetime.now(),
                        'status': 'completed',
                        'source': 'file_upload',
                        'created_at': datetime.now(),
                        'updated_at': datetime.now()
                    }
                    
                    # Insert into database
                    result = self.transactions.insert_one(transaction)
                    transaction_ids.append(str(result.inserted_id))
                    processed_records += 1
                    total_volume += amount_received
                    risk_scores.append(risk_score)
                    
                except Exception as row_error:
                    errors.append(f"Row {index + 1}: {str(row_error)}")
            
            if processed_records == 0:
                return {
                    'success': False,
                    'error': 'No valid transactions could be processed from the file',
                    'details': errors
                }
            
            # Calculate statistics
            average_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0
            
            return {
                'success': True,
                'processed_records': processed_records,
                'transaction_ids': transaction_ids,
                'errors': errors,
                'total_volume': round(total_volume, 2),
                'average_risk': round(average_risk, 3),
                'currencies_found': list(currencies_found),
                'high_risk_count': len([r for r in risk_scores if r >= 0.7]),
                'column_mapping': column_mapping
            }
        
        except Exception as e:
            print(f"Error processing file: {e}")
            return {
                'success': False,
                'error': f'File processing failed: {str(e)}',
                'details': []
            }
    
    def _calculate_basic_risk_score(self, amount, receiving_currency, payment_currency, payment_format, timestamp):
        """Calculate a basic risk score for uploaded transactions"""
        try:
            risk_score = 0.1  # Base risk
            
            # Amount-based risk
            if amount > 100000:
                risk_score += 0.4
            elif amount > 50000:
                risk_score += 0.2
            elif amount > 10000:
                risk_score += 0.1
            
            # Currency risk
            if receiving_currency != 'USD':
                risk_score += 0.1
            if receiving_currency != payment_currency:
                risk_score += 0.15
            
            # Payment format risk
            payment_format_lower = payment_format.lower()
            if 'crypto' in payment_format_lower or 'bitcoin' in payment_format_lower:
                risk_score += 0.3
            elif 'cash' in payment_format_lower:
                risk_score += 0.2
            elif 'wire' in payment_format_lower:
                risk_score += 0.1
            
            # Time-based risk (transactions outside business hours)
            if hasattr(timestamp, 'hour'):
                hour = timestamp.hour
                if hour < 6 or hour > 22:  # Outside business hours
                    risk_score += 0.1
                
                # Weekend transactions
                if timestamp.weekday() >= 5:
                    risk_score += 0.05
            
            # Random factor for ML training diversity
            import random
            risk_score += random.uniform(-0.05, 0.05)
            
            return min(max(risk_score, 0.0), 1.0)  # Clamp between 0 and 1
            
        except Exception as e:
            print(f"Error calculating risk score: {e}")
            return 0.5  # Default moderate risk
    
    def get_transaction_volume_trends(self, period='7d'):
        """Get transaction volume trends over time periods"""
        try:
            now = datetime.now()
            
            # Determine date range and grouping based on period
            if period == '24h':
                start_date = now - timedelta(hours=24)
                group_format = '%Y-%m-%d %H:00:00'
                intervals = 24
            elif period == '7d':
                start_date = now - timedelta(days=7)
                group_format = '%Y-%m-%d'
                intervals = 7
            elif period == '30d':
                start_date = now - timedelta(days=30)
                group_format = '%Y-%m-%d'
                intervals = 30
            else:
                start_date = now - timedelta(days=7)
                group_format = '%Y-%m-%d'
                intervals = 7
            
            # MongoDB aggregation pipeline
            pipeline = [
                {
                    '$match': {
                        'timestamp': {'$gte': start_date}
                    }
                },
                {
                    '$group': {
                        '_id': {
                            '$dateToString': {
                                'format': group_format,
                                'date': '$timestamp'
                            }
                        },
                        'total_volume': {'$sum': '$amount_received'},
                        'transaction_count': {'$sum': 1},
                        'avg_amount': {'$avg': '$amount_received'},
                        'max_amount': {'$max': '$amount_received'},
                        'min_amount': {'$min': '$amount_received'}
                    }
                },
                {
                    '$sort': {'_id': 1}
                }
            ]
            
            results = list(self.transactions.aggregate(pipeline))
            
            # Create complete time series with zero values for missing periods
            volume_data = {}
            for result in results:
                volume_data[result['_id']] = {
                    'volume': result['total_volume'],
                    'count': result['transaction_count'],
                    'avg_amount': result['avg_amount'],
                    'max_amount': result['max_amount'],
                    'min_amount': result['min_amount']
                }
            
            # Fill in missing time periods with zero values
            time_series = []
            for i in range(intervals):
                if period == '24h':
                    current_time = now - timedelta(hours=intervals-1-i)
                    time_key = current_time.strftime('%Y-%m-%d %H:00:00')
                    label = current_time.strftime('%H:00')
                else:
                    current_time = now - timedelta(days=intervals-1-i)
                    time_key = current_time.strftime('%Y-%m-%d')
                    if period == '7d':
                        label = current_time.strftime('%a')  # Mon, Tue, etc.
                    else:
                        label = current_time.strftime('%m/%d')  # MM/DD
                
                if time_key in volume_data:
                    data_point = volume_data[time_key]
                else:
                    data_point = {
                        'volume': 0,
                        'count': 0,
                        'avg_amount': 0,
                        'max_amount': 0,
                        'min_amount': 0
                    }
                
                time_series.append({
                    'label': label,
                    'date': time_key,
                    'volume': data_point['volume'],
                    'count': data_point['count'],
                    'avg_amount': data_point['avg_amount'],
                    'max_amount': data_point['max_amount'],
                    'min_amount': data_point['min_amount']
                })
            
            return {
                'success': True,
                'data': time_series,
                'period': period,
                'total_volume': sum([point['volume'] for point in time_series]),
                'total_transactions': sum([point['count'] for point in time_series]),
                'avg_volume_per_period': sum([point['volume'] for point in time_series]) / len(time_series) if time_series else 0
            }
            
        except Exception as e:
            print(f"Error getting transaction volume trends: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': [],
                'period': period
            }
    
    def get_recent_transaction_ids(self, days=7):
        """Get recent transaction IDs for analysis"""
        try:
            start_date = datetime.now() - timedelta(days=days)
            transactions = self.transactions.find(
                {'timestamp': {'$gte': start_date}},
                {'_id': 1}
            )
            return [str(t['_id']) for t in transactions]
        
        except Exception as e:
            print(f"Error getting recent transaction IDs: {e}")
            return []
    
    def get_recent_high_risk_accounts(self, limit=10):
        """Get recent high-risk accounts"""
        try:
            # Get accounts with high risk scores from recent transactions
            start_date = datetime.now() - timedelta(days=30)
            
            pipeline = [
                {'$match': {
                    'timestamp': {'$gte': start_date},
                    'risk_score': {'$gte': 0.3},  # Lower threshold to get more results
                    'from_account': {'$ne': None, '$exists': True}  # Filter out null accounts
                }},
                {'$group': {
                    '_id': '$from_account',
                    'risk_score': {'$avg': '$risk_score'},
                    'total_amount': {'$sum': '$amount_received'},
                    'transaction_count': {'$sum': 1},
                    'last_transaction': {'$max': '$timestamp'},
                    'currencies': {'$addToSet': '$receiving_currency'},
                    'to_banks': {'$addToSet': '$to_bank'}
                }},
                {'$sort': {'risk_score': -1}},
                {'$limit': limit}
            ]
            
            accounts = list(self.transactions.aggregate(pipeline))
            
            # Filter and format accounts
            formatted_accounts = []
            for account in accounts:
                if account['_id']:  # Only process accounts with valid IDs
                    # Try to get country from bank info
                    country = 'Unknown'
                    if account['to_banks']:
                        for bank in account['to_banks']:
                            if bank:
                                bank_upper = bank.strip().upper() if bank else ''
                                detected_country = self._country_code_mappings.get(bank_upper, 'Unknown')
                                if detected_country != 'Unknown':
                                    country = detected_country
                                    break
                    
                    formatted_account = {
                        'account_id': account['_id'],
                        'risk_score': round(account['risk_score'], 3),
                        'total_amount': account['total_amount'],
                        'total_sent': account['total_amount'],  # For compatibility
                        'transaction_count': account['transaction_count'],
                        'last_transaction': account['last_transaction'].isoformat(),
                        'currencies': account['currencies'],
                        'to_banks': account['to_banks'],
                        'account_type': 'Individual',
                        'country': country
                    }
                    formatted_accounts.append(formatted_account)
            
            return formatted_accounts
            
        except Exception as e:
            print(f"Error getting recent high-risk accounts: {e}")
            return []
    
    def search_accounts(self, filters):
        """Search accounts based on filters"""
        try:
            # Build the match query
            match_query = {}
            
            # Date range - last 30 days
            start_date = datetime.now() - timedelta(days=30)
            match_query['timestamp'] = {'$gte': start_date}
            
            # Text search in account IDs
            if filters.get('query'):
                query = filters['query']
                match_query['$or'] = [
                    {'from_account': {'$regex': query, '$options': 'i'}},
                    {'to_account': {'$regex': query, '$options': 'i'}}
                ]
            
            # Risk level filter
            if filters.get('risk_level') and filters['risk_level'] != 'all':
                if filters['risk_level'] == 'high':
                    match_query['risk_score'] = {'$gte': 0.7}
                elif filters['risk_level'] == 'medium':
                    match_query['risk_score'] = {'$gte': 0.4, '$lt': 0.7}
                elif filters['risk_level'] == 'low':
                    match_query['risk_score'] = {'$lt': 0.4}
            
            # Build aggregation pipeline
            pipeline = [
                {'$match': match_query},
                {'$group': {
                    '_id': '$from_account',
                    'risk_score': {'$avg': '$risk_score'},
                    'total_sent': {'$sum': '$amount_received'},
                    'transaction_count': {'$sum': 1},
                    'last_transaction': {'$max': '$timestamp'},
                    'currencies': {'$addToSet': '$receiving_currency'},
                    'banks': {'$addToSet': '$from_bank'},
                    'countries': {'$addToSet': '$from_country'}
                }},
                {'$match': {
                    '_id': {'$ne': None, '$exists': True}  # Filter out null accounts
                }},
                {'$sort': {'risk_score': -1}},
                {'$limit': 50}  # Limit results
            ]
            
            accounts = list(self.transactions.aggregate(pipeline))
            
            # Format results
            formatted_accounts = []
            for account in accounts:
                # Better country detection
                country = 'Unknown'
                if account['countries'] and account['countries'][0]:
                    country = account['countries'][0]
                elif account['banks']:
                    # Try to detect from bank names
                    for bank in account['banks']:
                        if bank:
                            bank_upper = bank.strip().upper() if bank else ''
                            detected_country = self._country_code_mappings.get(bank_upper, 'Unknown')
                            if detected_country != 'Unknown':
                                country = detected_country
                                break
                
                formatted_account = {
                    'account_id': account['_id'],
                    'risk_score': round(account['risk_score'], 3),
                    'total_sent': account['total_sent'],
                    'total_amount': account['total_sent'],  # Add for compatibility
                    'transaction_count': account['transaction_count'],
                    'last_transaction': account['last_transaction'].isoformat() if account['last_transaction'] else None,
                    'currencies': list(account['currencies']),
                    'banks': list(account['banks']),
                    'countries': list(account['countries']),
                    'account_type': 'Individual',  # Default type
                    'country': country
                }
                formatted_accounts.append(formatted_account)
            
            return formatted_accounts
            
        except Exception as e:
            print(f"Error searching accounts: {e}")
            return []
    
    def get_account_details(self, account_id):
        """Get detailed account information"""
        try:
            # Debug: print what we're looking for
            print(f"Looking for account: {account_id}")
            
            # Get account transactions - try multiple field names
            transactions = list(self.transactions.find({
                '$or': [
                    {'from_account': account_id},
                    {'to_account': account_id},
                    {'sender_account': account_id},
                    {'receiver_account': account_id}
                ]
            }).sort('timestamp', -1).limit(100))
            
            print(f"Found {len(transactions)} transactions for account {account_id}")
            
            if not transactions:
                # Try a broader search to see if account exists at all
                all_transactions_with_account = list(self.transactions.find({
                    '$or': [
                        {'from_account': {'$regex': account_id, '$options': 'i'}},
                        {'to_account': {'$regex': account_id, '$options': 'i'}},
                        {'sender_account': {'$regex': account_id, '$options': 'i'}},
                        {'receiver_account': {'$regex': account_id, '$options': 'i'}}
                    ]
                }).limit(5))
                print(f"Broader search found {len(all_transactions_with_account)} transactions")
                if all_transactions_with_account:
                    print(f"Sample matches: {[t.get('from_account') for t in all_transactions_with_account]}")
                return None
            
            # Calculate statistics
            total_sent = sum(t['amount_received'] for t in transactions if t.get('from_account') == account_id)
            total_received = sum(t['amount_received'] for t in transactions if t.get('to_account') == account_id)
            avg_risk = sum(t.get('risk_score', 0) for t in transactions) / len(transactions)
            
            # Get unique counterparties
            counterparties = set()
            for t in transactions:
                if t.get('from_account') == account_id:
                    counterparties.add(t.get('to_account'))
                else:
                    counterparties.add(t.get('from_account'))
            
            return {
                'account_id': account_id,
                'total_sent': total_sent,
                'total_received': total_received,
                'net_flow': total_received - total_sent,
                'transaction_count': len(transactions),
                'avg_risk_score': avg_risk,
                'counterparties_count': len(counterparties),
                'recent_transactions': transactions[:10],  # Last 10 transactions
                'currencies': list(set(t.get('receiving_currency') for t in transactions if t.get('receiving_currency'))),
                'banks': list(set(t.get('from_bank') for t in transactions if t.get('from_bank')))
            }
            
        except Exception as e:
            print(f"Error getting account details: {e}")
            return None
    
    def analyze_account(self, account_id):
        """Analyze account for suspicious patterns"""
        try:
            # Get account transactions
            transactions = list(self.transactions.find({
                '$or': [
                    {'from_account': account_id},
                    {'to_account': account_id}
                ]
            }).sort('timestamp', -1))
            
            if not transactions:
                return {'patterns': [], 'risk_score': 0, 'recommendations': []}
            
            patterns = []
            risk_factors = []
            
            # Pattern 1: High transaction frequency
            if len(transactions) > 50:
                patterns.append({
                    'type': 'high_frequency',
                    'description': 'High transaction frequency detected',
                    'severity': 'medium',
                    'count': len(transactions)
                })
                risk_factors.append(0.3)
            
            # Pattern 2: Large amounts
            large_amounts = [t for t in transactions if t.get('amount_received', 0) > 100000]
            if large_amounts:
                patterns.append({
                    'type': 'large_amounts',
                    'description': 'Large transaction amounts detected',
                    'severity': 'high',
                    'count': len(large_amounts)
                })
                risk_factors.append(0.4)
            
            # Pattern 3: High risk transactions
            high_risk = [t for t in transactions if t.get('risk_score', 0) > 0.7]
            if high_risk:
                patterns.append({
                    'type': 'high_risk_transactions',
                    'description': 'High risk transactions detected',
                    'severity': 'high',
                    'count': len(high_risk)
                })
                risk_factors.append(0.5)
            
            # Calculate overall risk score
            overall_risk = sum(risk_factors) / 3 if risk_factors else 0
            
            recommendations = []
            if overall_risk > 0.6:
                recommendations.append('Consider enhanced due diligence procedures')
                recommendations.append('Monitor for unusual transaction patterns')
            
            # Calculate transaction statistics
            incoming_transactions = [t for t in transactions if t.get('to_account') == account_id]
            outgoing_transactions = [t for t in transactions if t.get('from_account') == account_id]
            total_amount = sum([t.get('amount_received', 0) for t in transactions])
            avg_amount = total_amount / len(transactions) if transactions else 0
            
            return {
                'account_id': account_id,
                'patterns': patterns,
                'risk_score': min(overall_risk, 1.0),
                'recommendations': recommendations,
                'analysis_date': datetime.now().isoformat(),
                'transaction_stats': {
                    'total_count': len(transactions),
                    'incoming_count': len(incoming_transactions),
                    'outgoing_count': len(outgoing_transactions),
                    'avg_amount': avg_amount,
                    'total_amount': total_amount
                }
            }
            
        except Exception as e:
            print(f"Error analyzing account: {e}")
            return {'patterns': [], 'risk_score': 0, 'recommendations': []}
    
    def get_accounts_summary(self):
        """Get accounts summary statistics"""
        try:
            start_date = datetime.now() - timedelta(days=30)
            
            # Total accounts
            total_accounts = self.transactions.distinct('from_account')
            
            # High risk accounts
            high_risk_accounts = list(self.transactions.aggregate([
                {'$match': {
                    'timestamp': {'$gte': start_date},
                    'risk_score': {'$gte': 0.7}
                }},
                {'$group': {'_id': '$from_account'}},
                {'$count': 'count'}
            ]))
            
            # Flagged accounts (assuming we have a flagged field)
            flagged_accounts = list(self.transactions.aggregate([
                {'$match': {'flagged': True}},
                {'$group': {'_id': '$from_account'}},
                {'$count': 'count'}
            ]))
            
            return {
                'total_accounts': len(total_accounts),
                'high_risk_accounts': high_risk_accounts[0]['count'] if high_risk_accounts else 0,
                'flagged_accounts': flagged_accounts[0]['count'] if flagged_accounts else 0,
                'period': '30 days'
            }
            
        except Exception as e:
            print(f"Error getting accounts summary: {e}")
            return {
                'total_accounts': 0,
                'high_risk_accounts': 0,
                'flagged_accounts': 0,
                'period': '30 days'
            }
    
    def generate_account_report(self, account_id):
        """Generate comprehensive report for an account"""
        try:
            # Get account details and analysis
            account_details = self.get_account_details(account_id)
            account_analysis = self.analyze_account(account_id)
            
            if not account_details:
                return {'error': 'Account not found'}
            
            # Get additional statistics
            transactions = list(self.transactions.find({
                '$or': [
                    {'from_account': account_id},
                    {'to_account': account_id},
                    {'sender_account': account_id},
                    {'receiver_account': account_id}
                ]
            }).sort('timestamp', -1))
            
            # Calculate additional metrics
            total_incoming = sum(t.get('amount_received', 0) for t in transactions if t.get('receiver_account') == account_id or t.get('to_account') == account_id)
            total_outgoing = sum(t.get('amount_received', 0) for t in transactions if t.get('sender_account') == account_id or t.get('from_account') == account_id)
            
            # Get unique counterparties
            counterparties = set()
            for t in transactions:
                if t.get('sender_account') == account_id and t.get('receiver_account'):
                    counterparties.add(t.get('receiver_account'))
                elif t.get('receiver_account') == account_id and t.get('sender_account'):
                    counterparties.add(t.get('sender_account'))
                elif t.get('from_account') == account_id and t.get('to_account'):
                    counterparties.add(t.get('to_account'))
                elif t.get('to_account') == account_id and t.get('from_account'):
                    counterparties.add(t.get('from_account'))
            
            # Generate report
            report = {
                'account_id': account_id,
                'generated_at': datetime.now().isoformat(),
                'account_details': account_details,
                'risk_analysis': account_analysis,
                'transaction_summary': {
                    'total_transactions': len(transactions),
                    'total_incoming': total_incoming,
                    'total_outgoing': total_outgoing,
                    'net_flow': total_incoming - total_outgoing,
                    'unique_counterparties': len(counterparties),
                    'date_range': {
                        'from': min(t['timestamp'] for t in transactions).isoformat() if transactions else None,
                        'to': max(t['timestamp'] for t in transactions).isoformat() if transactions else None
                    }
                },
                'risk_indicators': {
                    'high_risk_transactions': len([t for t in transactions if t.get('risk_score', 0) > 0.7]),
                    'large_transactions': len([t for t in transactions if t.get('amount_received', 0) > 100000]),
                    'suspicious_patterns': account_analysis.get('patterns', []) if account_analysis else []
                },
                'recommendations': self._generate_recommendations(account_details, account_analysis, transactions)
            }
            
            return report
            
        except Exception as e:
            print(f"Error generating report for account {account_id}: {e}")
            return {'error': str(e)}
    
    def _generate_recommendations(self, account_details, analysis, transactions):
        """Generate recommendations based on account analysis"""
        recommendations = []
        
        if not account_details or not analysis:
            return recommendations
        
        risk_score = analysis.get('risk_score', 0)
        
        if risk_score > 0.7:
            recommendations.append("HIGH PRIORITY: Account requires immediate investigation due to high risk score")
        elif risk_score > 0.4:
            recommendations.append("MEDIUM PRIORITY: Account should be monitored closely")
        
        if analysis.get('patterns'):
            if 'large_amounts' in [p.get('type') for p in analysis.get('patterns', [])]:
                recommendations.append("Monitor for unusual large transaction patterns")
            if 'high_risk_transactions' in [p.get('type') for p in analysis.get('patterns', [])]:
                recommendations.append("Review high-risk transaction counterparties")
        
        high_risk_count = len([t for t in transactions if t.get('risk_score', 0) > 0.7])
        if high_risk_count > 5:
            recommendations.append(f"Account has {high_risk_count} high-risk transactions - review transaction history")
        
        if len(transactions) > 100:
            recommendations.append("High transaction volume - ensure adequate monitoring")
        
        return recommendations
    
    def get_account_details(self, account_id):
        """Get detailed account information"""
        try:
            # Get account transactions
            transactions = list(self.transactions.find(
                {'$or': [
                    {'sender_account': account_id},
                    {'receiver_account': account_id}
                ]},
                {'_id': 1, 'timestamp': 1, 'amount_received': 1, 'risk_score': 1, 'sender_account': 1, 'receiver_account': 1}
            ).sort('timestamp', -1).limit(50))
            
            if not transactions:
                return None
            
            # Calculate statistics
            total_sent = sum(t['amount_received'] for t in transactions if t.get('sender_account') == account_id)
            total_received = sum(t['amount_received'] for t in transactions if t.get('receiver_account') == account_id)
            avg_risk = sum(t['risk_score'] for t in transactions) / len(transactions)
            
            # Convert timestamps
            for t in transactions:
                t['_id'] = str(t['_id'])
                t['timestamp'] = t['timestamp'].isoformat()
            
            return {
                'account_id': account_id,
                'total_sent': total_sent,
                'total_received': total_received,
                'transaction_count': len(transactions),
                'avg_risk_score': avg_risk,
                'recent_transactions': transactions
            }
            
        except Exception as e:
            print(f"Error getting account details: {e}")
            return None