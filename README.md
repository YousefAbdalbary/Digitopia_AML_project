
```markdown
# AML Detection with Graph Attention Networks

This project is developed for the Digitopia competition.

## Description
This project implements an Anti-Money Laundering (AML) detection system using a Graph Attention Network (GAT) with PyTorch Geometric (PyG) and PySpark for scalable graph-based analysis, complemented by an AI-powered transaction analysis module (`AIAnalyzer`), a data processing module (`DataProcessor`), a network analysis module (`NetworkAnalyzer`), an advanced pattern analysis module (`AdvancedPatternAnalyzer`), and a risk calculation module (`RiskCalculator`). The GAT model processes transaction data as a graph of accounts (nodes) and transactions (edges), leveraging neighbor sampling. The `AIAnalyzer` uses Isolation Forest for anomaly detection and rule-based risk scoring, the `DataProcessor` handles database operations, dynamic bank location mapping via the REST Countries API, dashboard statistics, geographic cash flow analysis, and account-level reporting, the `NetworkAnalyzer` employs NetworkX for graph construction, centrality metrics, and pattern detection, the `AdvancedPatternAnalyzer` leverages machine learning and statistical techniques for sophisticated pattern detection (e.g., structuring, layering, circular transactions, smurfing, shell companies, and advanced graph-based anomalies), and the `RiskCalculator` computes risk scores based on transaction and account characteristics such as amount, currency, geography, timing, payment method, velocity, patterns, and network connectivity. A Flask-based backend provides API access, and a frontend enables user interaction with analysis results and alerts as of September 29, 2025.

## Table of Contents
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Technologies Used](#technologies-used)
- [Model Details](#model-details)
- [Contributing](#contributing)

## Usage
1. **Train the GAT model**:
   Run the model script to preprocess data, train the GAT model, and save artifacts:
   ```bash
   python models/aml_spark_pyg_neighborloader_full.py
   ```
   This saves the Spark pipeline (`./spark_pipeline_model`), model weights (`./best_gat_neighbor_gpu.pth`), and account-to-index mapping (`./account2idx.json`).

2. **Train the AIAnalyzer model**:
   Use the `AIAnalyzer` class to train on transaction data:
   ```python
   from services.ai_analyzer import AIAnalyzer
   analyzer = AIAnalyzer()
   transactions = pd.read_csv("transactions.csv")
   analyzer.train_model(transactions)
   analyzer.save_model("ai_analyzer_model.pkl")
   ```

3. **Process data with DataProcessor**:
   Use the `DataProcessor` class for database operations and analytics:
   ```python
   from services.data_processor import DataProcessor
   from pymongo import MongoClient
   client = MongoClient("mongodb://localhost:27017/")
   db = client["aml_db"]
   processor = DataProcessor(db)
   dashboard_stats = processor.get_dashboard_stats()
   transactions = processor.get_transactions_with_count({'date_range': '30d'})
   ```

4. **Analyze network with NetworkAnalyzer**:
   Use the `NetworkAnalyzer` class for network-based insights:
   ```python
   from services.network_analyzer import NetworkAnalyzer
   analyzer = NetworkAnalyzer(db)
   network_data = analyzer.get_network_data(focus_account="acc123", depth=2, min_amount=1000)
   connections = analyzer.get_account_connections(account_id="acc123")
   risk_score = analyzer.calculate_network_risk_score(account_id="acc123")
   ```

5. **Analyze patterns with AdvancedPatternAnalyzer**:
   Use the `AdvancedPatternAnalyzer` class for sophisticated pattern detection:
   ```python
   from services.advanced_pattern_analyzer import create_pattern_analyzer
   analyzer = create_pattern_analyzer()
   transactions = list(db.transactions.find())
   patterns = analyzer.analyze_patterns(transactions)
   summary = analyzer.get_pattern_summary(patterns)
   ```

6. **Calculate risk with RiskCalculator**:
   Use the `RiskCalculator` class for risk scoring:
   ```python
   from services.risk_calculator import RiskCalculator
   calculator = RiskCalculator()
   transaction = {'amount_received': 15000, 'receiving_currency': 'USD', 'timestamp': '2025-09-29 10:00:00', 'from_bank': '1001', 'to_bank': '1002', 'payment_format': 'wire'}
   risk_score = calculator.calculate_transaction_risk(transaction)
   explanation = calculator.get_risk_explanation(transaction, risk_score)
   account_risk = calculator.calculate_account_risk(account_id="acc123", db=db)
   batch_risks = calculator.calculate_batch_risk_scores(transactions)
   ```

7. **Run the backend server**:
   Start the Flask application:
   ```bash
   python app.py
   ```
   The API will be available at `http://localhost:5000` (update port in `app.py` if needed). Endpoints may include `/predict` (for GAT predictions), `/analyze` (for AIAnalyzer results), `/network` (for network analysis), `/patterns` (for pattern detection), and `/risk` (for risk scores).

8. **Run the frontend**:
   The frontend files (e.g., `js`, `css`, `templates`, `static`) suggest a web interface. Serve it via the Flask app at `http://localhost:5000`.

## Project Structure
```
PROJECTAML/
├── models/                    # Machine learning models and training scripts
│   ├── __init__.py
│   ├── aml_spark_pyg_neighborloader_full.py  # GAT model script
│   ├── train_model.py
│   └── (other model files)
├── services/                  # Data processing and analysis scripts
│   ├── __init__.py
│   ├── ai_analyzer.py         # AIAnalyzer class for anomaly detection
│   ├── data_processor.py      # DataProcessor class for database and analytics
│   ├── network_analyzer.py    # NetworkAnalyzer class for graph analysis
│   ├── advanced_pattern_analyzer.py  # AdvancedPatternAnalyzer class for pattern detection
│   ├── risk_calculator.py     # RiskCalculator class for risk scoring
│   ├── pattern_analyzer.py
│   └── risk_calculator.py
├── __pycache__/               # Python bytecode cache
├── static/                    # Static frontend assets
│   ├── js/
│   ├── css/
│   ├── favicon.svg
│   └── logo.png
├── templates/                 # HTML templates for Flask
├── tests/                     # Test files
├── uploads/                   # Directory for uploaded files
├── app.py                     # Flask application entry point
├── config.py                  # Configuration settings
├── README.md                  # This file
```

## Technologies Used
- **Model**: PyTorch, PyTorch Geometric (GATConv, NeighborLoader), scikit-learn
- **Data Processing**: PySpark (for feature engineering and pipeline), Pandas
- **Network Analysis**: NetworkX
- **Backend**: Flask
- **Frontend**: HTML, CSS, JavaScript (served via Flask templates)
- **Database**: MongoDB (via PyMongo)
- **API**: requests
- **Hardware**: GPU (optional, via CUDA) or CPU
- **Others**: NumPy, JSON, Pickle

## Model Details
- **GAT Model**:
  - **Data**: Transactions as a graph (accounts as nodes, transactions as edges with attributes like amount and currency).
  - **Feature Engineering**: Spark-based preprocessing (e.g., timestamp features, aggregated account stats), vector assembly, and scaling.
  - **Architecture**: GAT with two `GATConv` layers (head count configurable).
- **AIAnalyzer**:
  - **Method**: Isolation Forest for anomaly detection, DBSCAN for clustering, rule-based risk scoring.
  - **Patterns**: Detects rapid-fire, circular, and structuring transactions.
- **NetworkAnalyzer**:
  - **Method**: NetworkX-based graph analysis with centrality metrics (betweenness, closeness, PageRank).
  - **Patterns**: Identifies hubs, cycles, isolated clusters, high-velocity accounts, and structuring.
- **AdvancedPatternAnalyzer**:
  - **Method**: Machine learning (Isolation Forest, DBSCAN) and statistical techniques (Gini coefficient, centrality metrics).
  - **Patterns**: Detects structuring, layering, circular transactions, smurfing, shell companies, and advanced graph-based anomalies (e.g., betweenness exploitation, eigenvector dominance).
- **RiskCalculator**:
  - **Method**: Weighted scoring based on amount, currency, geography, timing, payment method, velocity, patterns, and network connectivity.
  - **Features**: Transaction-level and account-level risk scoring with detailed explanations.

## Contributing
Contributions are welcome! Please fork the repository and submit pull requests with your changes.
```


