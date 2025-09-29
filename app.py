from flask import Flask, render_template, request, jsonify, session, redirect, url_for, make_response
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
import json
from bson import ObjectId
from config import config
from services.data_processor import DataProcessor
from services.ai_analyzer import AIAnalyzer
from services.network_analyzer import NetworkAnalyzer
from services.risk_calculator import RiskCalculator

app = Flask(__name__)
app.config.from_object(config['development'])

# MongoDB connection
client = MongoClient(app.config['MONGO_URI'])
db = client[app.config['MONGO_DBNAME']]

# Initialize services
data_processor = DataProcessor(db)
ai_analyzer = AIAnalyzer()
network_analyzer = NetworkAnalyzer(db)
risk_calculator = RiskCalculator()

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/favicon.ico')
def favicon():
    """Serve favicon"""
    from flask import send_from_directory
    try:
        return send_from_directory(os.path.join(app.root_path, 'static'), 
                                   'favicon.ico', 
                                   mimetype='image/vnd.microsoft.icon')
    except:
        # Fallback to SVG favicon if .ico doesn't exist
        return send_from_directory(os.path.join(app.root_path, 'static'), 
                                   'favicon.svg', 
                                   mimetype='image/svg+xml')

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/network')
def network_graph():
    """Network graph page"""
    transaction_id = request.args.get('transaction')
    return render_template('network.html', transaction_id=transaction_id)

@app.route('/cash-flow')
def cash_flow():
    """Multi-currency cash flow page"""
    return render_template('cash_flow.html')

@app.route('/alerts')
def alerts():
    """Alerts page"""
    return render_template('alerts.html')

@app.route('/accounts')
def accounts():
    """Account analysis page"""
    return render_template('accounts.html')

@app.route('/upload')
def upload_page():
    """Dataset upload page"""
    return render_template('upload.html')

@app.route('/reports')
def reports():
    """Reports page"""
    return render_template('reports.html')

# Account API endpoints
@app.route('/api/accounts/recent-high-risk')
def get_recent_high_risk_accounts():
    """Get recent high-risk accounts"""
    try:
        limit = int(request.args.get('limit', 10))
        accounts = data_processor.get_recent_high_risk_accounts(limit)
        return jsonify(accounts)
    except Exception as e:
        print(f"Error getting recent high-risk accounts: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/accounts/summary')
def get_accounts_summary():
    """Get accounts summary statistics"""
    try:
        summary = data_processor.get_accounts_summary()
        return jsonify(summary)
    except Exception as e:
        print(f"Error getting accounts summary: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/accounts/search')
def search_accounts():
    """Search accounts based on filters"""
    try:
        filters = {
            'query': request.args.get('query', ''),
            'type': request.args.get('type', 'all'),
            'risk_level': request.args.get('risk_level', 'all'),
            'country': request.args.get('country', 'all')
        }
        
        accounts = data_processor.search_accounts(filters)
        return jsonify(accounts)
    except Exception as e:
        print(f"Error searching accounts: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/accounts/<account_id>/details')
def get_account_details(account_id):
    """Get detailed account information"""
    try:
        # Use the same approach as search_accounts to get account data
        filters = {'query': account_id}
        accounts = data_processor.search_accounts(filters)
        
        # Find the specific account
        account = None
        for acc in accounts:
            if acc['account_id'] == account_id:
                account = acc
                break
        
        if not account:
            return jsonify({'error': 'Account not found'}), 404
        
        # Get additional details by querying transactions directly
        transactions = list(db.transactions.find({
            '$or': [
                {'from_account': account_id},
                {'to_account': account_id}
            ]
        }).sort('timestamp', -1).limit(10))
        
        # Enhance account data with recent transactions
        account['recent_transactions'] = [
            {
                'transaction_id': str(t.get('_id')),
                'timestamp': t.get('timestamp'),
                'amount': t.get('amount_received', 0),
                'from_account': t.get('from_account'),
                'to_account': t.get('to_account'),
                'currency': t.get('receiving_currency'),
                'risk_score': t.get('risk_score', 0)
            } for t in transactions
        ]
        
        return jsonify(account)
        
    except Exception as e:
        print(f"Error getting account details: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/accounts/<account_id>/analyze', methods=['POST'])
def analyze_account(account_id):
    """Analyze account for suspicious patterns"""
    try:
        analysis = data_processor.analyze_account(account_id)
        return jsonify(analysis)
    except Exception as e:
        print(f"Error analyzing account: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/accounts/<account_id>/flag', methods=['POST'])
def flag_account(account_id):
    """Flag an account for review"""
    try:
        # You can implement actual flagging logic here
        # For now, just return success
        return jsonify({
            'account_id': account_id,
            'flagged': True,
            'flagged_at': datetime.now().isoformat(),
            'message': 'Account flagged for review'
        })
    except Exception as e:
        print(f"Error flagging account: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/accounts/<account_id>/report', methods=['POST'])
def generate_account_report(account_id):
    """Generate comprehensive report for an account"""
    try:
        report_data = data_processor.generate_account_report(account_id)
        return jsonify(report_data)
    except Exception as e:
        print(f"Error generating report for account {account_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/debug/accounts')
def debug_accounts():
    """Debug endpoint to check actual account data"""
    try:
        # Get some sample transactions to see actual field names
        sample_transactions = list(db.transactions.find({}).limit(10))
        accounts = list(set([t.get('from_account') for t in sample_transactions if t.get('from_account')]))
        
        return jsonify({
            'sample_transactions': [
                {
                    'from_account': t.get('from_account'),
                    'to_account': t.get('to_account'),
                    'amount': t.get('amount_received'),
                    'keys': list(t.keys())
                } for t in sample_transactions[:3]
            ],
            'unique_accounts': accounts[:10]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API Routes
@app.route('/api/dashboard/stats')
def dashboard_stats():
    """Get dashboard statistics"""
    try:
        stats = data_processor.get_dashboard_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/volume-trends')
def get_volume_trends():
    """Get transaction volume trends over time"""
    try:
        period = request.args.get('period', '7d')  # Default to 7 days
        trends = data_processor.get_transaction_volume_trends(period)
        return jsonify(trends)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/transactions')
def get_transactions():
    """Get transactions with optional filters"""
    try:
        filters = {
            'start_date': request.args.get('start_date'),
            'end_date': request.args.get('end_date'),
            'currency': request.args.get('currency'),
            'risk_level': request.args.get('risk_level'),
            'limit': int(request.args.get('limit', 100))
        }
        transactions = data_processor.get_transactions(filters)
        return jsonify(transactions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/transactions/<transaction_id>')
def get_transaction_details(transaction_id):
    """Get single transaction details"""
    try:
        print(f"Getting transaction details for ID: {transaction_id}")
        transaction = data_processor.get_transaction_by_id(transaction_id)
        
        if transaction:
            return jsonify(transaction)
        else:
            return jsonify({'error': 'Transaction not found'}), 404
            
    except Exception as e:
        print(f"Error getting transaction details: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/transactions/<transaction_id>/flag', methods=['POST'])
def flag_transaction(transaction_id):
    """Flag a transaction as suspicious"""
    try:
        print(f"Flagging transaction ID: {transaction_id}")
        result = data_processor.flag_transaction(transaction_id)
        
        if result:
            return jsonify({'message': 'Transaction flagged successfully'})
        else:
            return jsonify({'error': 'Failed to flag transaction'}), 400
            
    except Exception as e:
        print(f"Error flagging transaction: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/network/graph')
def network_graph_data():
    """Get network graph data"""
    try:
        account_id = request.args.get('account_id')
        depth = int(request.args.get('depth', 2))
        graph_data = network_analyzer.get_network_graph(account_id, depth)
        return jsonify(graph_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cash-flow/map')
def cash_flow_map():
    """Get geographic cash flow data for map with enhanced filtering"""
    try:
        # Get filter parameters
        currency = request.args.get('currency', 'ALL')
        time_period = request.args.get('time_period', '30d')
        min_amount = float(request.args.get('min_amount', 0))
        risk_level = request.args.get('risk_level', 'all')
        
        print(f"Map API called with filters: currency={currency}, period={time_period}, min_amount={min_amount}, risk={risk_level}")
        
        # Get map data with filters
        map_data = data_processor.get_geographic_flow_data(
            currency=currency,
            time_period=time_period,
            min_amount=min_amount,
            risk_level=risk_level
        )
        
        return jsonify(map_data)
    except Exception as e:
        print(f"Error in cash_flow_map: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/cash-flow/overview')
def cash_flow_overview():
    """Get cash flow overview data"""
    try:
        currency = request.args.get('currency', 'all')
        date_range = request.args.get('date_range', '30d')
        
        # Get basic cash flow statistics
        overview_data = data_processor.get_cash_flow_overview(currency, date_range)
        return jsonify(overview_data)
    except Exception as e:
        print(f"Error in cash_flow_overview: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/cash-flow/multi-currency')
def multi_currency_flow():
    """Get multi-currency cash flow data"""
    try:
        account_id = request.args.get('account_id')
        flow_data = data_processor.get_multi_currency_flow(account_id)
        return jsonify(flow_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts')
def get_alerts():
    """Get alerts with pagination"""
    try:
        # Get filter parameters
        status = request.args.get('status', 'all')
        priority = request.args.get('priority', 'all') 
        alert_type = request.args.get('type', 'all')
        search = request.args.get('search', '')
        date_filter = request.args.get('date', '')
        
        # Get pagination parameters
        offset = int(request.args.get('offset', 0))
        limit = int(request.args.get('limit', 20))
        
        # Get all alerts based on filters
        if status == 'all':
            status = None
        if priority == 'all':
            priority = None
            
        alerts = data_processor.get_alerts(status, priority)
        
        # Filter by type if specified
        if alert_type and alert_type != 'all':
            alerts = [alert for alert in alerts if alert.get('type') == alert_type]
        
        # Filter by search term if specified
        if search:
            search_lower = search.lower()
            alerts = [alert for alert in alerts if 
                     search_lower in alert.get('description', '').lower() or
                     search_lower in alert.get('title', '').lower() or
                     search_lower in alert.get('account_id', '').lower()]
        
        # Filter by date if specified
        if date_filter:
            try:
                filter_date = datetime.strptime(date_filter, '%Y-%m-%d')
                next_day = filter_date + timedelta(days=1)
                alerts = [alert for alert in alerts if 
                         filter_date <= datetime.fromisoformat(alert.get('created_at', '').replace('Z', '+00:00')) < next_day]
            except (ValueError, TypeError):
                pass  # Invalid date format, skip filtering
        
        # Apply pagination
        total_alerts = len(alerts)
        paginated_alerts = alerts[offset:offset + limit]
        has_more = offset + limit < total_alerts
        
        return jsonify({
            'alerts': paginated_alerts,
            'has_more': has_more,
            'total': total_alerts,
            'offset': offset,
            'limit': limit
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts/<alert_id>', methods=['GET'])
def get_alert_details(alert_id):
    """Get single alert details"""
    try:
        alert = data_processor.get_alert_by_id(alert_id)
        if alert:
            return jsonify(alert)
        else:
            return jsonify({'error': 'Alert not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts/<alert_id>', methods=['PUT'])
def update_alert(alert_id):
    """Update alert status"""
    try:
        data = request.get_json()
        status = data.get('status')
        notes = data.get('notes')
        
        success = data_processor.update_alert_status(alert_id, status, notes)
        
        if success:
            return jsonify({'success': True, 'message': 'Alert updated successfully'})
        else:
            return jsonify({'success': False, 'message': 'Alert not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts/<alert_id>/resolve', methods=['POST'])
def resolve_alert(alert_id):
    """Resolve an alert"""
    try:
        data = request.get_json() or {}
        notes = data.get('notes', '')
        
        success = data_processor.update_alert_status(alert_id, 'resolved', notes)
        
        if success:
            return jsonify({'success': True, 'message': 'Alert resolved successfully'})
        else:
            return jsonify({'success': False, 'message': 'Alert not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts/<alert_id>/investigate', methods=['POST'])
def investigate_alert(alert_id):
    """Start investigation for an alert"""
    try:
        data = request.get_json() or {}
        notes = data.get('notes', '')
        
        success = data_processor.update_alert_status(alert_id, 'investigating', notes)
        
        if success:
            return jsonify({'success': True, 'message': 'Investigation started successfully'})
        else:
            return jsonify({'success': False, 'message': 'Alert not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts/<alert_id>/dismiss', methods=['POST'])
def dismiss_alert(alert_id):
    """Dismiss an alert"""
    try:
        data = request.get_json() or {}
        notes = data.get('notes', '')
        
        success = data_processor.update_alert_status(alert_id, 'dismissed', notes)
        
        if success:
            return jsonify({'success': True, 'message': 'Alert dismissed successfully'})
        else:
            return jsonify({'success': False, 'message': 'Alert not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts/<alert_id>/read', methods=['POST'])
def mark_alert_read(alert_id):
    """Mark an alert as read"""
    try:
        success = data_processor.mark_alert_read(alert_id)
        
        if success:
            return jsonify({'success': True, 'message': 'Alert marked as read'})
        else:
            return jsonify({'success': False, 'message': 'Alert not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts/generate', methods=['POST'])  
def generate_alerts():
    """Manually trigger alert generation"""
    try:
        data_processor.generate_alerts_from_transactions()
        return jsonify({'success': True, 'message': 'Alerts generated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/account/<account_id>')
def get_account_analysis(account_id):
    """Get detailed account analysis"""
    try:
        analysis = data_processor.get_account_analysis(account_id)
        return jsonify(analysis)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_dataset():
    """Upload and process transaction dataset"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file or not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Please upload CSV, XLSX, or XLS files.'}), 400
        
        # Create uploads directory if it doesn't exist
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # Save the uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Process the uploaded file
        result = data_processor.process_uploaded_file(filepath)
        
        if not result.get('success', False):
            return jsonify({
                'error': result.get('error', 'Failed to process file'),
                'details': result.get('details', [])
            }), 400
        
        # Get options from request
        run_analysis = request.form.get('run_analysis', 'false').lower() == 'true'
        generate_alerts = request.form.get('generate_alerts', 'false').lower() == 'true'
        
        ai_result = {'suspicious_count': 0, 'alerts_generated': 0}
        
        # Run AI analysis if requested
        if run_analysis and result.get('transaction_ids'):
            try:
                ai_result = ai_analyzer.analyze_transactions(result['transaction_ids'], db)
            except Exception as ai_error:
                print(f"AI Analysis error: {ai_error}")
                ai_result = {'suspicious_count': 0, 'alerts_generated': 0, 'error': str(ai_error)}
        
        # Calculate statistics
        stats = data_processor.get_dashboard_stats()
        
        # Clean up uploaded file after processing
        try:
            os.remove(filepath)
        except Exception as cleanup_error:
            print(f"Warning: Could not remove uploaded file: {cleanup_error}")
        
        return jsonify({
            'success': True,
            'message': 'File uploaded and processed successfully',
            'filename': filename,
            'records_processed': result.get('processed_records', 0),
            'transaction_ids': result.get('transaction_ids', []),
            'suspicious_count': ai_result.get('suspicious_count', 0),
            'alerts_generated': ai_result.get('alerts_generated', 0),
            'errors': result.get('errors', []),
            'average_risk': result.get('average_risk', 0),
            'total_volume': result.get('total_volume', 0),
            'currencies_found': result.get('currencies_found', []),
            'ai_analysis_enabled': run_analysis,
            'alert_generation_enabled': generate_alerts
        })
    
    except Exception as e:
        print(f"Upload error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/uploads/recent')
def get_recent_uploads():
    """Get recent file uploads"""
    try:
        # For now, return mock data since we don't store upload history
        # In production, you'd want to store upload metadata in the database
        recent_uploads = [
            {
                '_id': 'upload_001',
                'filename': 'transactions_sample.csv',
                'upload_date': datetime.now() - timedelta(hours=2),
                'records_processed': 1500,
                'suspicious_count': 45,
                'status': 'completed'
            },
            {
                '_id': 'upload_002', 
                'filename': 'monthly_data.xlsx',
                'upload_date': datetime.now() - timedelta(days=1),
                'records_processed': 3200,
                'suspicious_count': 87,
                'status': 'completed'
            }
        ]
        
        return jsonify(recent_uploads)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analyze', methods=['POST'])
def run_ai_analysis():
    """Run AI analysis on transactions"""
    try:
        data = request.get_json()
        transaction_ids = data.get('transaction_ids', [])
        
        if not transaction_ids:
            # Analyze all recent transactions
            transaction_ids = data_processor.get_recent_transaction_ids()
        
        result = ai_analyzer.analyze_transactions(transaction_ids, db)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/risk/calculate', methods=['POST'])
def calculate_risk():
    """Calculate risk score for a transaction or account"""
    try:
        data = request.get_json()
        transaction_data = data.get('transaction_data')
        account_id = data.get('account_id')
        
        if transaction_data:
            risk_score = risk_calculator.calculate_transaction_risk(transaction_data)
        elif account_id:
            risk_score = risk_calculator.calculate_account_risk(account_id)
        else:
            return jsonify({'error': 'No data provided for risk calculation'}), 400
        
        return jsonify({'risk_score': risk_score})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/network/data')
def get_network_data():
    """Get network analysis data"""
    try:
        focus_account = request.args.get('focus_account', '')
        depth = int(request.args.get('depth', 2))
        min_amount = float(request.args.get('min_amount', 1000))
        risk_level = request.args.get('risk_level', 'all')
        
        # Get network data
        network_data = network_analyzer.get_network_data(
            focus_account=focus_account,
            depth=depth,
            min_amount=min_amount,
            risk_level=risk_level
        )
        
        return jsonify(network_data)
    
    except Exception as e:
        print(f"Error getting network data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/network/patterns', methods=['POST'])
def analyze_patterns():
    """Analyze AML patterns in transaction data"""
    try:
        from services.pattern_analyzer import create_pattern_analyzer
        
        # Get filter parameters from request
        data = request.get_json() if request.is_json else {}
        
        focus_account = data.get('focus_account', '')
        depth = int(data.get('depth', 2))
        min_amount = float(data.get('min_amount', 1000))
        risk_level = data.get('risk_level', 'all')
        
        print(f"Pattern analysis request with filters: {data}")
        
        # Get transactions based on filters
        filters = {
            'focus_account': focus_account,
            'min_amount': min_amount,
            'risk_level': risk_level,
            'limit': 1000  # Limit for performance
        }
        
        # Get transactions from database
        transactions = data_processor.get_transactions_for_analysis(filters)
        
        if not transactions:
            return jsonify({
                'results': [],
                'summary': {
                    'total_patterns': 0,
                    'message': 'No transactions found matching the criteria'
                },
                'debug_info': {
                    'database_query': filters,
                    'total_transactions_in_db': data_processor.transactions.count_documents({})
                }
            })
        
        print(f"Analyzing {len(transactions)} transactions for patterns")
        
        # Debug: Show sample transaction data
        if transactions:
            sample_tx = transactions[0]
            print(f"Sample transaction fields: {list(sample_tx.keys())}")
            print(f"Sample source: '{sample_tx.get('source', 'MISSING')}'")
            print(f"Sample target: '{sample_tx.get('target', 'MISSING')}'")
        
        # Create pattern analyzer and run analysis
        analyzer = create_pattern_analyzer()
        patterns = analyzer.analyze_patterns(transactions)
        
        # Convert patterns to serializable format
        pattern_results = []
        for pattern in patterns:
            pattern_results.append({
                'type': pattern.pattern_type.value,
                'severity': pattern.risk_level.value,
                'confidence': round(pattern.confidence, 3),
                'description': pattern.description,
                'affected_accounts': pattern.affected_accounts,
                'transaction_ids': pattern.transaction_ids,
                'evidence': pattern.evidence,
                'recommendation': pattern.recommendation,
                'timestamp': pattern.timestamp.isoformat()
            })
        
        # Get summary
        summary = analyzer.get_pattern_summary(patterns)
        
        print(f"Pattern analysis completed. Found {len(pattern_results)} patterns")
        
        return jsonify({
            'results': pattern_results,
            'summary': summary,
            'analysis_info': {
                'transactions_analyzed': len(transactions),
                'filters_applied': filters,
                'analysis_timestamp': datetime.now().isoformat()
            },
            'debug_info': {
                'sample_transaction_keys': list(transactions[0].keys()) if transactions else [],
                'sample_source': transactions[0].get('source', 'MISSING') if transactions else 'NO_TRANSACTIONS',
                'sample_target': transactions[0].get('target', 'MISSING') if transactions else 'NO_TRANSACTIONS',
                'empty_sources': sum(1 for tx in transactions if not tx.get('source') or tx.get('source') == ''),
                'empty_targets': sum(1 for tx in transactions if not tx.get('target') or tx.get('target') == '')
            }
        })
    
    except ImportError as e:
        print(f"Import error: {e}")
        return jsonify({'error': 'Pattern analysis module not available'}), 500
    except Exception as e:
        print(f"Error analyzing patterns: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/cash-flow/transactions')
def get_cash_flow_transactions():
    """Get cash flow transactions"""
    try:
        filters = {
            'account_filter': request.args.get('account_filter', ''),
            'currency': request.args.get('currency', 'all'),
            'date_range': request.args.get('date_range', '30d'),
            'search': request.args.get('search', ''),
            'page': int(request.args.get('page', 1)),
            'per_page': int(request.args.get('per_page', 50))
        }
        
        print(f"Cash flow transactions request with filters: {filters}")
        
        # Get transactions with pagination and total count
        result = data_processor.get_transactions_with_count(filters)
        
        return jsonify({
            'transactions': result['transactions'],
            'total_count': result['total_count'],
            'page': filters['page'],
            'per_page': filters['per_page'],
            'total_pages': (result['total_count'] + filters['per_page'] - 1) // filters['per_page']
        })
    
    except Exception as e:
        print(f"Error getting cash flow transactions: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts/stats')
def get_alerts_stats():
    """Get alerts statistics"""
    try:
        # Get recent alerts
        alerts = list(db.alerts.find().sort('timestamp', -1).limit(100))
        
        # Calculate stats
        active_alerts = len([alert for alert in alerts if alert.get('status') == 'active'])
        high_priority = len([alert for alert in alerts if alert.get('priority') == 'high'])
        
        # Calculate resolved today
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        resolved_today = len([
            alert for alert in alerts 
            if alert.get('status') == 'resolved' and 
            alert.get('updated_at', datetime.min) >= today
        ])
        
        # Use data processor for comprehensive stats
        stats = data_processor.get_alert_statistics()
        
        # Get recent alerts for display
        recent_alerts = data_processor.get_alerts('active', None)
        
        return jsonify({
            'active_alerts': stats['active_alerts'],
            'high_priority': stats['high_priority'],
            'resolved_today': stats['resolved_today'],
            'avg_response_time': f"{stats['avg_response_time']}h",
            'alerts': [
                {
                    '_id': alert['_id'],
                    'type': alert.get('type', 'SUSPICIOUS TRANSACTION'),
                    'description': alert.get('description', ''),
                    'priority': alert.get('priority', 'medium'),
                    'status': alert.get('status', 'active'),
                    'timestamp': alert.get('created_at', datetime.now().isoformat())
                }
                for alert in recent_alerts[:10]  # Return only first 10
            ]
        })
    
    except Exception as e:
        print(f"Error getting alerts stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts/mark-all-read', methods=['POST'])
def mark_all_alerts_read():
    """Mark all alerts as read"""
    try:
        # Update all unread alerts to read status
        result = db.alerts.update_many(
            {'read': {'$ne': True}},
            {
                '$set': {
                    'read': True,
                    'read_at': datetime.now()
                }
            }
        )
        
        return jsonify({
            'success': True,
            'count': result.modified_count,
            'message': f'Marked {result.modified_count} alerts as read'
        })
        
    except Exception as e:
        print(f"Error marking all alerts as read: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts/export', methods=['GET'])
def export_alerts():
    """Export alerts to CSV"""
    try:
        # Get filter parameters
        status = request.args.get('status', 'all')
        priority = request.args.get('priority', 'all')
        alert_type = request.args.get('type', 'all')
        search = request.args.get('search', '')
        date_filter = request.args.get('date', '')
        
        # Build query filters
        query = {}
        
        if status != 'all':
            query['status'] = status
            
        if priority != 'all':
            query['priority'] = priority
            
        if alert_type != 'all':
            query['type'] = alert_type
            
        if search:
            query['$or'] = [
                {'description': {'$regex': search, '$options': 'i'}},
                {'account_id': {'$regex': search, '$options': 'i'}},
                {'type': {'$regex': search, '$options': 'i'}}
            ]
            
        if date_filter:
            try:
                filter_date = datetime.strptime(date_filter, '%Y-%m-%d')
                next_day = filter_date + timedelta(days=1)
                query['created_at'] = {
                    '$gte': filter_date,
                    '$lt': next_day
                }
            except ValueError:
                pass
        
        # Get alerts from database
        alerts = list(db.alerts.find(query).sort('created_at', -1))
        
        # Create CSV content
        import io
        import csv
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'ID', 'Type', 'Description', 'Priority', 'Status', 
            'Account ID', 'Amount', 'Currency', 'Risk Score',
            'Created At', 'Updated At', 'Read Status'
        ])
        
        # Write data rows
        for alert in alerts:
            writer.writerow([
                str(alert.get('_id', '')),
                alert.get('type', ''),
                alert.get('description', ''),
                alert.get('priority', ''),
                alert.get('status', ''),
                alert.get('account_id', ''),
                alert.get('amount', ''),
                alert.get('currency', ''),
                alert.get('risk_score', ''),
                alert.get('created_at', ''),
                alert.get('updated_at', ''),
                'Read' if alert.get('read') else 'Unread'
            ])
        
        # Create response
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = 'attachment; filename=alerts_export.csv'
        
        return response
        
    except Exception as e:
        print(f"Error exporting alerts: {e}")
        return jsonify({'error': str(e)}), 500

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)