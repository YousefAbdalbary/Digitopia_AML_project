import networkx as nx
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict

class NetworkAnalyzer:
    """Network analysis for transaction relationships and patterns"""
    
    def __init__(self, db):
        self.db = db
        self.transactions = db.transactions
        self.accounts = db.accounts
    
    def get_network_graph(self, focus_account=None, depth=2, min_amount=0):
        """Generate network graph data for visualization"""
        try:
            # Build query based on focus account and depth
            if focus_account:
                # Get transactions involving the focus account
                base_query = {
                    '$or': [
                        {'from_account': focus_account},
                        {'to_account': focus_account}
                    ]
                }
                
                if min_amount > 0:
                    base_query['amount_received'] = {'$gte': min_amount}
                
                transactions = list(self.transactions.find(base_query))
                
                # Expand to connected accounts if depth > 1
                if depth > 1:
                    connected_accounts = set()
                    for t in transactions:
                        connected_accounts.add(t['from_account'])
                        connected_accounts.add(t['to_account'])
                    
                    # Get transactions between connected accounts
                    expanded_query = {
                        '$or': [
                            {'from_account': {'$in': list(connected_accounts)}},
                            {'to_account': {'$in': list(connected_accounts)}}
                        ]
                    }
                    
                    if min_amount > 0:
                        expanded_query['amount_received'] = {'$gte': min_amount}
                    
                    additional_transactions = list(self.transactions.find(expanded_query))
                    
                    # Combine and deduplicate
                    all_transactions = transactions + additional_transactions
                    seen_ids = set()
                    transactions = []
                    for t in all_transactions:
                        if t['_id'] not in seen_ids:
                            transactions.append(t)
                            seen_ids.add(t['_id'])
            else:
                # Get recent high-value transactions if no focus account
                query = {
                    'timestamp': {'$gte': datetime.now() - timedelta(days=30)},
                    'amount_received': {'$gte': max(min_amount, 1000)}
                }
                transactions = list(self.transactions.find(query).limit(500))
            
            # Build network graph
            G = nx.DiGraph()
            
            # Track account statistics
            account_stats = defaultdict(lambda: {
                'total_sent': 0,
                'total_received': 0,
                'transaction_count': 0,
                'risk_scores': [],
                'currencies': set(),
                'banks': set()
            })
            
            # Add edges and collect account stats
            for transaction in transactions:
                from_acc = transaction['from_account']
                to_acc = transaction['to_account']
                amount = transaction['amount_received']
                risk_score = transaction.get('risk_score', 0)
                currency = transaction['receiving_currency']
                timestamp = transaction['timestamp']
                
                # Add edge with transaction data
                if G.has_edge(from_acc, to_acc):
                    # Update existing edge
                    edge_data = G[from_acc][to_acc]
                    edge_data['total_amount'] += amount
                    edge_data['transaction_count'] += 1
                    edge_data['risk_scores'].append(risk_score)
                    edge_data['currencies'].add(currency)
                    if timestamp > edge_data['last_transaction']:
                        edge_data['last_transaction'] = timestamp
                else:
                    # Create new edge
                    G.add_edge(from_acc, to_acc, **{
                        'total_amount': amount,
                        'transaction_count': 1,
                        'risk_scores': [risk_score],
                        'currencies': {currency},
                        'last_transaction': timestamp,
                        'transaction_ids': [str(transaction['_id'])]
                    })
                
                # Update account statistics
                account_stats[from_acc]['total_sent'] += amount
                account_stats[from_acc]['transaction_count'] += 1
                account_stats[from_acc]['risk_scores'].append(risk_score)
                account_stats[from_acc]['currencies'].add(currency)
                account_stats[from_acc]['banks'].add(transaction['from_bank'])
                
                account_stats[to_acc]['total_received'] += amount
                account_stats[to_acc]['transaction_count'] += 1
                account_stats[to_acc]['risk_scores'].append(risk_score)
                account_stats[to_acc]['currencies'].add(currency)
                account_stats[to_acc]['banks'].add(transaction['to_bank'])
            
            # Calculate network metrics
            centrality_metrics = self.calculate_centrality_metrics(G)
            
            # Prepare nodes data
            nodes = []
            for account in G.nodes():
                stats = account_stats[account]
                centrality = centrality_metrics.get(account, {})
                
                # Get account details from database
                account_info = self.accounts.find_one({'account_id': account})
                
                node = {
                    'id': account,
                    'label': account[:8] + '...' if len(account) > 8 else account,
                    'total_sent': stats['total_sent'],
                    'total_received': stats['total_received'],
                    'net_flow': stats['total_received'] - stats['total_sent'],
                    'transaction_count': stats['transaction_count'],
                    'avg_risk_score': np.mean(stats['risk_scores']) if stats['risk_scores'] else 0,
                    'max_risk_score': max(stats['risk_scores']) if stats['risk_scores'] else 0,
                    'currencies': list(stats['currencies']),
                    'bank_count': len(stats['banks']),
                    'betweenness_centrality': centrality.get('betweenness', 0),
                    'closeness_centrality': centrality.get('closeness', 0),
                    'pagerank': centrality.get('pagerank', 0),
                    'in_degree': G.in_degree(account),
                    'out_degree': G.out_degree(account),
                    'is_focus': account == focus_account
                }
                
                # Add account info if available
                if account_info:
                    node.update({
                        'account_name': account_info.get('name', 'Unknown'),
                        'account_type': account_info.get('type', 'Unknown'),
                        'country': account_info.get('country', 'Unknown')
                    })
                
                # Determine node size and color based on activity
                total_activity = stats['total_sent'] + stats['total_received']
                node['size'] = min(max(total_activity / 10000, 10), 100)  # Scale node size
                
                # Color based on risk score
                avg_risk = node['avg_risk_score']
                if avg_risk > 0.7:
                    node['color'] = '#ff4444'  # High risk - red
                elif avg_risk > 0.4:
                    node['color'] = '#ffaa44'  # Medium risk - orange
                else:
                    node['color'] = '#44aa44'  # Low risk - green
                
                nodes.append(node)
            
            # Prepare edges data
            edges = []
            for from_acc, to_acc, edge_data in G.edges(data=True):
                avg_risk = np.mean(edge_data['risk_scores']) if edge_data['risk_scores'] else 0
                
                edge = {
                    'from': from_acc,
                    'to': to_acc,
                    'total_amount': edge_data['total_amount'],
                    'transaction_count': edge_data['transaction_count'],
                    'avg_risk_score': avg_risk,
                    'max_risk_score': max(edge_data['risk_scores']) if edge_data['risk_scores'] else 0,
                    'currencies': list(edge_data['currencies']),
                    'last_transaction': edge_data['last_transaction'].isoformat() if hasattr(edge_data['last_transaction'], 'isoformat') else str(edge_data['last_transaction']),
                    'transaction_ids': edge_data.get('transaction_ids', [])
                }
                
                # Edge width based on amount
                edge['width'] = min(max(edge_data['total_amount'] / 5000, 1), 10)
                
                # Edge color based on risk
                if avg_risk > 0.7:
                    edge['color'] = '#ff4444'
                elif avg_risk > 0.4:
                    edge['color'] = '#ffaa44'
                else:
                    edge['color'] = '#888888'
                
                edges.append(edge)
            
            # Detect suspicious patterns
            patterns = self.detect_network_patterns(G, account_stats)
            
            return {
                'nodes': nodes,
                'edges': edges,
                'patterns': patterns,
                'network_stats': {
                    'total_nodes': len(nodes),
                    'total_edges': len(edges),
                    'total_transactions': len(transactions),
                    'focus_account': focus_account,
                    'depth': depth
                }
            }
        
        except Exception as e:
            print(f"Error generating network graph: {e}")
            return {'nodes': [], 'edges': [], 'patterns': []}
    
    def calculate_centrality_metrics(self, G):
        """Calculate various centrality metrics for the network"""
        try:
            metrics = {}
            
            # Only calculate if graph has nodes
            if len(G.nodes()) == 0:
                return metrics
            
            # Betweenness centrality
            try:
                betweenness = nx.betweenness_centrality(G)
                for node in betweenness:
                    if node not in metrics:
                        metrics[node] = {}
                    metrics[node]['betweenness'] = betweenness[node]
            except:
                pass
            
            # Closeness centrality
            try:
                closeness = nx.closeness_centrality(G)
                for node in closeness:
                    if node not in metrics:
                        metrics[node] = {}
                    metrics[node]['closeness'] = closeness[node]
            except:
                pass
            
            # PageRank
            try:
                pagerank = nx.pagerank(G)
                for node in pagerank:
                    if node not in metrics:
                        metrics[node] = {}
                    metrics[node]['pagerank'] = pagerank[node]
            except:
                pass
            
            return metrics
        
        except Exception as e:
            print(f"Error calculating centrality metrics: {e}")
            return {}
    
    def detect_network_patterns(self, G, account_stats):
        """Detect suspicious patterns in the transaction network"""
        try:
            patterns = []
            
            # Pattern 1: Hub accounts (high degree centrality)
            degree_centrality = nx.degree_centrality(G)
            high_degree_threshold = 0.1  # Top 10% by degree
            
            for account, centrality in degree_centrality.items():
                if centrality > high_degree_threshold:
                    patterns.append({
                        'type': 'hub_account',
                        'account': account,
                        'description': f"Hub account with high connectivity (centrality: {centrality:.3f})",
                        'risk_level': 'medium',
                        'metric_value': centrality
                    })
            
            # Pattern 2: Cycles (potential money laundering cycles)
            try:
                cycles = list(nx.simple_cycles(G))
                for cycle in cycles[:10]:  # Limit to first 10 cycles
                    if len(cycle) >= 3:  # Only cycles of 3+ accounts
                        patterns.append({
                            'type': 'cycle',
                            'accounts': cycle,
                            'description': f"Transaction cycle detected involving {len(cycle)} accounts",
                            'risk_level': 'high',
                            'cycle_length': len(cycle)
                        })
            except:
                pass  # Skip if cycle detection fails
            
            # Pattern 3: Isolated clusters
            try:
                components = list(nx.weakly_connected_components(G))
                for component in components:
                    if 3 <= len(component) <= 10:  # Small isolated groups
                        total_internal_amount = 0
                        for node in component:
                            for neighbor in component:
                                if G.has_edge(node, neighbor):
                                    total_internal_amount += G[node][neighbor]['total_amount']
                        
                        patterns.append({
                            'type': 'isolated_cluster',
                            'accounts': list(component),
                            'description': f"Isolated cluster of {len(component)} accounts",
                            'risk_level': 'medium',
                            'cluster_size': len(component),
                            'internal_amount': total_internal_amount
                        })
            except:
                pass
            
            # Pattern 4: High-velocity accounts
            for account, stats in account_stats.items():
                if stats['transaction_count'] > 50 and len(stats['currencies']) > 3:
                    patterns.append({
                        'type': 'high_velocity',
                        'account': account,
                        'description': f"High-velocity account: {stats['transaction_count']} transactions across {len(stats['currencies'])} currencies",
                        'risk_level': 'medium',
                        'transaction_count': stats['transaction_count'],
                        'currency_count': len(stats['currencies'])
                    })
            
            # Pattern 5: Structuring patterns (consistent amounts)
            for from_acc, to_acc, edge_data in G.edges(data=True):
                if edge_data['transaction_count'] > 5:
                    # Get individual transaction amounts for this edge
                    edge_transactions = list(self.transactions.find({
                        'from_account': from_acc,
                        'to_account': to_acc
                    }))
                    
                    amounts = [t['amount_received'] for t in edge_transactions]
                    if len(amounts) > 5:
                        # Check for similar amounts (potential structuring)
                        amount_std = np.std(amounts)
                        amount_mean = np.mean(amounts)
                        
                        if amount_std / amount_mean < 0.1:  # Low variation
                            patterns.append({
                                'type': 'structuring',
                                'from_account': from_acc,
                                'to_account': to_acc,
                                'description': f"Potential structuring: {len(amounts)} similar amounts",
                                'risk_level': 'high',
                                'transaction_count': len(amounts),
                                'amount_consistency': 1 - (amount_std / amount_mean)
                            })
            
            return patterns
        
        except Exception as e:
            print(f"Error detecting network patterns: {e}")
            return []
    
    def get_account_connections(self, account_id, max_connections=50):
        """Get direct connections for a specific account"""
        try:
            # Get outgoing connections
            outgoing = list(self.transactions.aggregate([
                {'$match': {'from_account': account_id}},
                {'$group': {
                    '_id': '$to_account',
                    'total_sent': {'$sum': '$amount_paid'},
                    'transaction_count': {'$sum': 1},
                    'avg_risk_score': {'$avg': '$risk_score'},
                    'currencies': {'$addToSet': '$payment_currency'},
                    'last_transaction': {'$max': '$timestamp'}
                }},
                {'$sort': {'total_sent': -1}},
                {'$limit': max_connections}
            ]))
            
            # Get incoming connections
            incoming = list(self.transactions.aggregate([
                {'$match': {'to_account': account_id}},
                {'$group': {
                    '_id': '$from_account',
                    'total_received': {'$sum': '$amount_received'},
                    'transaction_count': {'$sum': 1},
                    'avg_risk_score': {'$avg': '$risk_score'},
                    'currencies': {'$addToSet': '$receiving_currency'},
                    'last_transaction': {'$max': '$timestamp'}
                }},
                {'$sort': {'total_received': -1}},
                {'$limit': max_connections}
            ]))
            
            # Format connections
            connections = {
                'outgoing': [],
                'incoming': []
            }
            
            for conn in outgoing:
                connections['outgoing'].append({
                    'account_id': conn['_id'],
                    'total_amount': conn['total_sent'],
                    'transaction_count': conn['transaction_count'],
                    'avg_risk_score': conn['avg_risk_score'],
                    'currencies': conn['currencies'],
                    'last_transaction': conn['last_transaction'].isoformat() if hasattr(conn['last_transaction'], 'isoformat') else str(conn['last_transaction']),
                    'connection_type': 'sent_to'
                })
            
            for conn in incoming:
                connections['incoming'].append({
                    'account_id': conn['_id'],
                    'total_amount': conn['total_received'],
                    'transaction_count': conn['transaction_count'],
                    'avg_risk_score': conn['avg_risk_score'],
                    'currencies': conn['currencies'],
                    'last_transaction': conn['last_transaction'].isoformat() if hasattr(conn['last_transaction'], 'isoformat') else str(conn['last_transaction']),
                    'connection_type': 'received_from'
                })
            
            return connections
        
        except Exception as e:
            print(f"Error getting account connections: {e}")
            return {'outgoing': [], 'incoming': []}
    
    def calculate_network_risk_score(self, account_id):
        """Calculate overall network risk score for an account"""
        try:
            connections = self.get_account_connections(account_id)
            
            risk_factors = {
                'high_risk_connections': 0,
                'connection_diversity': 0,
                'volume_concentration': 0,
                'currency_diversity': 0
            }
            
            all_connections = connections['outgoing'] + connections['incoming']
            
            if not all_connections:
                return 0.0
            
            # High-risk connections
            high_risk_count = sum(1 for conn in all_connections if conn['avg_risk_score'] > 0.7)
            risk_factors['high_risk_connections'] = min(high_risk_count / len(all_connections), 1.0)
            
            # Connection diversity (many small vs few large connections)
            amounts = [conn['total_amount'] for conn in all_connections]
            if amounts:
                amount_std = np.std(amounts)
                amount_mean = np.mean(amounts)
                risk_factors['volume_concentration'] = min(amount_std / (amount_mean + 1), 1.0)
            
            # Currency diversity
            all_currencies = set()
            for conn in all_connections:
                all_currencies.update(conn['currencies'])
            risk_factors['currency_diversity'] = min(len(all_currencies) / 10, 1.0)
            
            # Connection count (too many connections can be suspicious)
            connection_count_risk = min(len(all_connections) / 100, 1.0)
            
            # Weighted risk score
            weights = {
                'high_risk_connections': 0.4,
                'volume_concentration': 0.2,
                'currency_diversity': 0.2,
                'connection_count': 0.2
            }
            
            network_risk = (
                risk_factors['high_risk_connections'] * weights['high_risk_connections'] +
                risk_factors['volume_concentration'] * weights['volume_concentration'] +
                risk_factors['currency_diversity'] * weights['currency_diversity'] +
                connection_count_risk * weights['connection_count']
            )
            
            return min(network_risk, 1.0)
        
        except Exception as e:
            print(f"Error calculating network risk score: {e}")
            return 0.0
    
    def get_network_data(self, focus_account='', depth=2, min_amount=1000, risk_level='all'):
        """Get network data for API endpoint"""
        try:
            print(f"Getting network data: focus={focus_account}, depth={depth}, min_amount={min_amount}, risk={risk_level}")
            
            # Build query based on focus account and depth
            if focus_account:
                # Start with transactions directly involving focus account
                base_query = {
                    '$or': [
                        {'from_account': focus_account},
                        {'to_account': focus_account}
                    ]
                }
                
                # Add filters
                if min_amount > 0:
                    base_query['amount_received'] = {'$gte': min_amount}
                
                if risk_level != 'all':
                    if risk_level == 'high':
                        base_query['risk_score'] = {'$gte': 0.7}
                    elif risk_level == 'medium':
                        base_query['risk_score'] = {'$gte': 0.4, '$lt': 0.7}
                    elif risk_level == 'low':
                        base_query['risk_score'] = {'$lt': 0.4}
                
                transactions = list(self.transactions.find(base_query).limit(500))
                
                # Expand to connected accounts based on depth
                if depth > 1:
                    connected_accounts = set([focus_account])
                    for t in transactions:
                        connected_accounts.add(t['from_account'])
                        connected_accounts.add(t['to_account'])
                    
                    # For each additional depth level
                    for level in range(2, depth + 1):
                        # Get transactions involving connected accounts
                        expanded_query = {
                            '$or': [
                                {'from_account': {'$in': list(connected_accounts)}},
                                {'to_account': {'$in': list(connected_accounts)}}
                            ]
                        }
                        
                        if min_amount > 0:
                            expanded_query['amount_received'] = {'$gte': min_amount}
                        
                        if risk_level != 'all':
                            if risk_level == 'high':
                                expanded_query['risk_score'] = {'$gte': 0.7}
                            elif risk_level == 'medium':
                                expanded_query['risk_score'] = {'$gte': 0.4, '$lt': 0.7}
                            elif risk_level == 'low':
                                expanded_query['risk_score'] = {'$lt': 0.4}
                        
                        additional_transactions = list(self.transactions.find(expanded_query).limit(300))
                        
                        # Add new accounts to connected set
                        for t in additional_transactions:
                            connected_accounts.add(t['from_account'])
                            connected_accounts.add(t['to_account'])
                        
                        # Combine with existing transactions (avoid duplicates)
                        existing_ids = {str(t['_id']) for t in transactions}
                        for t in additional_transactions:
                            if str(t['_id']) not in existing_ids:
                                transactions.append(t)
                                existing_ids.add(str(t['_id']))
                        
                        print(f"Depth {level}: {len(additional_transactions)} additional transactions, {len(connected_accounts)} total accounts")
                
                print(f"Final result for focus '{focus_account}' at depth {depth}: {len(transactions)} transactions")
                        
            else:
                # No focus account - get recent high-value transactions
                query = {
                    'timestamp': {'$gte': datetime.now() - timedelta(days=30)}
                }
                
                if min_amount > 0:
                    query['amount_received'] = {'$gte': min_amount}
                
                if risk_level != 'all':
                    if risk_level == 'high':
                        query['risk_score'] = {'$gte': 0.7}
                    elif risk_level == 'medium':
                        query['risk_score'] = {'$gte': 0.4, '$lt': 0.7}
                    elif risk_level == 'low':
                        query['risk_score'] = {'$lt': 0.4}
                
                # Limit based on depth (more depth = more transactions)
                limit = min(1000, 200 * depth)
                transactions = list(self.transactions.find(query).limit(limit))
                print(f"No focus account - found {len(transactions)} recent transactions")
            
            print(f"Found {len(transactions)} transactions matching criteria")
            
            # Build network
            nodes = {}
            edges = []
            
            for transaction in transactions:
                from_acc = transaction['from_account']
                to_acc = transaction['to_account']
                amount = transaction['amount_received']
                risk_score = transaction.get('risk_score', 0)
                
                # Add nodes
                if from_acc not in nodes:
                    nodes[from_acc] = {
                        'id': from_acc,
                        'type': 'account',
                        'total_sent': 0,
                        'total_received': 0,
                        'transaction_count': 0,
                        'avg_risk_score': 0,
                        'risk_scores': []
                    }
                
                if to_acc not in nodes:
                    nodes[to_acc] = {
                        'id': to_acc,
                        'type': 'account',
                        'total_sent': 0,
                        'total_received': 0,
                        'transaction_count': 0,
                        'avg_risk_score': 0,
                        'risk_scores': []
                    }
                
                # Update node stats
                nodes[from_acc]['total_sent'] += amount
                nodes[from_acc]['transaction_count'] += 1
                nodes[from_acc]['risk_scores'].append(risk_score)
                
                nodes[to_acc]['total_received'] += amount
                nodes[to_acc]['transaction_count'] += 1
                nodes[to_acc]['risk_scores'].append(risk_score)

                # Add edge
                edges.append({
                    'source': from_acc,
                    'target': to_acc,
                    'amount': amount,
                    'to_bank': transaction['to_bank'],
                    'from_bank': transaction['from_bank'],
                    'risk_score': risk_score,
                    'currency': transaction['receiving_currency'],
                    'timestamp': transaction['timestamp'].isoformat() if isinstance(transaction['timestamp'], datetime) else str(transaction['timestamp']),
                    'transaction_id': str(transaction['_id'])
                })
            
            # Calculate average risk scores for nodes
            for node in nodes.values():
                if node['risk_scores']:
                    node['avg_risk_score'] = np.mean(node['risk_scores'])
                    
                    # Determine risk level
                    if node['avg_risk_score'] >= 0.7:
                        node['risk_level'] = 'high'
                    elif node['avg_risk_score'] >= 0.4:
                        node['risk_level'] = 'medium'
                    else:
                        node['risk_level'] = 'low'
                else:
                    node['avg_risk_score'] = 0
                    node['risk_level'] = 'low'
                
                # Clean up temporary data
                del node['risk_scores']
            
            nodes_list = list(nodes.values())
            
            # Calculate stats
            high_risk_count = len([n for n in nodes_list if n['risk_level'] == 'high'])
           
            result = {
                'nodes': nodes_list,
                'edges': edges,
                'stats': {
                    'nodes': len(nodes_list),
                    'edges': len(edges),
                    'transactions': len(transactions),
                    'high_risk': high_risk_count
                },
                'patterns': []  # Could add pattern detection here
            }
            
            print(f"Returning network data: {len(nodes_list)} nodes, {len(edges)} edges")
            return result
            
        except Exception as e:
            print(f"Error getting network data: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                'nodes': [],
                'edges': [],
                'stats': {'nodes': 0, 'edges': 0, 'transactions': 0, 'high_risk': 0},
                'patterns': []
            }