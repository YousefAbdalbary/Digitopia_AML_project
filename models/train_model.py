# file: aml_spark_pyg_neighborloader_full.py
import os
import json
import numpy as np
from typing import List, Dict

# Spark
from pyspark.sql import SparkSession, functions as F, types as T
from pyspark.ml import Pipeline
from pyspark.ml.feature import StringIndexer, VectorAssembler, StandardScaler
from pyspark.ml.functions import vector_to_array

# Torch + PyG
import torch
import torch.nn as nn
import torch.nn.functional as F_torch
from torch_geometric.data import Data
from torch_geometric.nn import GATConv, Linear
from torch_geometric.loader import NeighborLoader

# sklearn
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, f1_score

# ---------------------------
# CONFIG
# ---------------------------
CSV_PATH = "/kaggle/input/synthetic-transaction-monitoring-dataset-aml"   # <<< عدّل هنا
PIPELINE_DIR = "./spark_pipeline_model"
MODEL_PATH = "./best_gat_neighbor_gpu.pth"
MAPPING_PATH = "./account2idx.json"
NUM_EPOCHS = 50        # عدد الإبوكات الثابت
BATCH_SIZE = 1024
VAL_BATCH_SIZE = 2048
TEST_BATCH_SIZE = 2048
NUM_NEIGHBORS = [20, 20]  # sampling neighbors per hop
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
PIN_MEMORY = True  # لتحسين نسخ الذاكرة لو الجهاز يدعم
# ---------------------------

def main():
    # ---------------------------
    # 1) Spark session
    # ---------------------------
    spark = SparkSession.builder \
        .appName("AML-NeighborLoader-GPU-Full") \
        .config("spark.driver.memory", "16g") \
        .config("spark.executor.memory", "8g") \
        .getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    # ---------------------------
    # 2) Read CSV (schema)
    # ---------------------------
    schema = T.StructType([
        T.StructField("Time", T.StringType(), True),
        T.StructField("Date", T.StringType(), True),
        T.StructField("Sender_account", T.StringType(), True),
        T.StructField("Receiver_account", T.StringType(), True),
        T.StructField("Amount", T.DoubleType(), True),
        T.StructField("Payment_currency", T.StringType(), True),
        T.StructField("Received_currency", T.StringType(), True),
        T.StructField("Sender_bank_location", T.StringType(), True),
        T.StructField("Receiver_bank_location", T.StringType(), True),
        T.StructField("Payment_type", T.StringType(), True),
        T.StructField("Is_laundering", T.IntegerType(), True),
        T.StructField("Laundering_type", T.StringType(), True)
    ])
    df = spark.read.csv(CSV_PATH, header=True, schema=schema)

    # ---------------------------
    # 3) Feature engineering (Spark)
    # ---------------------------
    df = df.withColumn("timestamp", F.to_timestamp(F.concat_ws(" ", F.col("Date"), F.col("Time")), "yyyy-MM-dd HH:mm:ss"))
    df = df.withColumn("hour", F.hour("timestamp").cast("int"))
    df = df.withColumn("weekday", F.dayofweek("timestamp").cast("int"))
    df = df.withColumn("amount_log", F.log1p(F.col("Amount")))

    # sender/receiver aggregated features
    sender_aggs = df.groupBy("Sender_account").agg(
        F.count("*").alias("sender_tx_count"),
        F.mean("Amount").alias("sender_amt_mean"),
        F.stddev("Amount").alias("sender_amt_std"),
        F.countDistinct("Receiver_account").alias("sender_unique_receivers"),
        F.mean("hour").alias("sender_avg_hour")
    )

    receiver_aggs = df.groupBy("Receiver_account").agg(
        F.count("*").alias("receiver_tx_count"),
        F.mean("Amount").alias("receiver_amt_mean"),
        F.stddev("Amount").alias("receiver_amt_std"),
        F.countDistinct("Sender_account").alias("receiver_unique_senders"),
        F.mean("hour").alias("receiver_avg_hour")
    ).withColumnRenamed("Receiver_account", "Receiver_acc_for_join")

    df = df.join(sender_aggs, on="Sender_account", how="left") \
           .join(receiver_aggs, df["Receiver_account"] == F.col("Receiver_acc_for_join"), how="left") \
           .drop("Receiver_acc_for_join")

    # ---------------------------
    # 4) Encoding + assemble + scale (Spark pipeline)
    # ---------------------------
    cat_cols = ["Payment_currency", "Received_currency", "Sender_bank_location", "Receiver_bank_location", "Payment_type", "Laundering_type"]
    num_cols = ["Amount", "amount_log", "hour", "weekday",
                "sender_tx_count","sender_amt_mean","sender_amt_std","sender_unique_receivers","sender_avg_hour",
                "receiver_tx_count","receiver_amt_mean","receiver_amt_std","receiver_unique_senders","receiver_avg_hour"]

    indexers = [StringIndexer(inputCol=c, outputCol=f"{c}_idx", handleInvalid="keep") for c in cat_cols]
    indexed_cols = [f"{c}_idx" for c in cat_cols]

    assembler = VectorAssembler(inputCols=indexed_cols + num_cols, outputCol="features_vec", handleInvalid="keep")
    scaler = StandardScaler(inputCol="features_vec", outputCol="features_scaled", withMean=True, withStd=True)

    pipeline = Pipeline(stages=indexers + [assembler, scaler])
    pipeline_model = pipeline.fit(df)

    # save pipeline
    try:
        pipeline_model.write().overwrite().save(PIPELINE_DIR)
    except Exception:
        import shutil
        if os.path.exists(PIPELINE_DIR):
            shutil.rmtree(PIPELINE_DIR)
        pipeline_model.write().save(PIPELINE_DIR)

    df_feat = pipeline_model.transform(df)

    # ---------------------------
    # 5) vector -> array and explode features (dynamic dim)
    # ---------------------------
    df_feat = df_feat.withColumn("features_array", vector_to_array("features_scaled"))
    dim = int(df_feat.select(F.size("features_array").alias("dim")).first()["dim"])
    print(f"Feature dimension = {dim}")

    for i in range(dim):
        df_feat = df_feat.withColumn(f"f_{i}", F.col("features_array").getItem(i))

    # fill nulls for edge attrs and indexed cols
    df_feat = df_feat.fillna({"amount_log": 0.0})
    for c in indexed_cols:
        df_feat = df_feat.fillna({c: -1.0})

    # ---------------------------
    # 6) per-account node features (sender & receiver averaged)
    # ---------------------------
    sender_exprs = [F.avg(f"f_{i}").alias(f"sender_f_{i}") for i in range(dim)]
    receiver_exprs = [F.avg(f"f_{i}").alias(f"receiver_f_{i}") for i in range(dim)]

    sender_feats = df_feat.groupBy("Sender_account").agg(*sender_exprs).na.fill(0.0).withColumnRenamed("Sender_account", "account_sender")
    receiver_feats = df_feat.groupBy("Receiver_account").agg(*receiver_exprs).na.fill(0.0).withColumnRenamed("Receiver_account", "account_receiver")

    accounts_df = df_feat.select("Sender_account").union(df_feat.select("Receiver_account")).distinct().withColumnRenamed("Sender_account", "account")
    joined = accounts_df.join(sender_feats.withColumnRenamed("account_sender","account"), on="account", how="left") \
                        .join(receiver_feats.withColumnRenamed("account_receiver","account"), on="account", how="left")

    for i in range(dim):
        joined = joined.withColumn(f"sender_f_{i}", F.coalesce(F.col(f"sender_f_{i}"), F.lit(0.0)))
        joined = joined.withColumn(f"receiver_f_{i}", F.coalesce(F.col(f"receiver_f_{i}"), F.lit(0.0)))
        joined = joined.withColumn(f"node_f_{i}", ((F.col(f"sender_f_{i}") + F.col(f"receiver_f_{i}")) / 2.0))

    node_features_df = joined.select("account", *[f"node_f_{i}" for i in range(dim)]).na.fill(0.0)

    # ---------------------------
    # 7) edges RDD with attributes
    # ---------------------------
    edge_cols = ["amount_log"] + indexed_cols
    for c in edge_cols:
        if c not in df_feat.columns:
            df_feat = df_feat.withColumn(c, F.lit(0.0))

    edges_rdd = df_feat.select("Sender_account","Receiver_account", *edge_cols).distinct().rdd \
        .map(lambda r: (r["Sender_account"], r["Receiver_account"], [float(r[c]) if r[c] is not None else 0.0 for c in edge_cols]))

    # ---------------------------
    # 8) collect accounts & mapping
    # ---------------------------
    accounts = node_features_df.select("account").rdd.map(lambda r: r["account"]).collect()
    account2idx = {acc: i for i, acc in enumerate(accounts)}
    n_nodes = len(accounts)
    print(f"Number of nodes (accounts): {n_nodes}")
    with open(MAPPING_PATH, "w") as f:
        json.dump(account2idx, f)

    # ---------------------------
    # 9) build edge_index & edge_attr
    # ---------------------------
    edge_tuples = edges_rdd.map(lambda t: (account2idx.get(t[0], None), account2idx.get(t[1], None), t[2])) \
                           .filter(lambda x: x[0] is not None and x[1] is not None).collect()

    if len(edge_tuples) == 0:
        raise RuntimeError("No edges found after mapping to account indices. Check account mapping.")

    edge_src = [int(e[0]) for e in edge_tuples]
    edge_dst = [int(e[1]) for e in edge_tuples]
    edge_attrs = [e[2] for e in edge_tuples]

    edge_index = torch.tensor([edge_src, edge_dst], dtype=torch.long)
    edge_attr = torch.tensor(np.array(edge_attrs, dtype=np.float32), dtype=torch.float) if len(edge_attrs)>0 else None

    # ---------------------------
    # 10) build node feature tensor x
    # ---------------------------
    node_feat_map = node_features_df.rdd.map(lambda r: (r["account"], [float(r[f"node_f_{i}"]) for i in range(dim)])).collectAsMap()
    X_list = [node_feat_map.get(acc, [0.0]*dim) for acc in accounts]
    x = torch.tensor(np.array(X_list, dtype=np.float32), dtype=torch.float)

    # ---------------------------
    # 11) build label tensor y (account-level)
    # ---------------------------
    labels_map = df_feat.filter(F.col("Is_laundering")==1).select("Sender_account","Receiver_account").rdd \
                .flatMap(lambda r: [r["Sender_account"], r["Receiver_account"]]).map(lambda a: (a,1)).collectAsMap()
    y_list = [int(labels_map.get(acc, 0)) for acc in accounts]
    y = torch.tensor(np.array(y_list, dtype=np.int64), dtype=torch.long)

    # ---------------------------
    # 12) create PyG Data (on CPU for NeighborLoader sampling)
    # ---------------------------
    data = Data(x=x, edge_index=edge_index, edge_attr=edge_attr, y=y)

    # create stratified train/val/test splits
    node_idx = np.arange(n_nodes)
    if len(np.unique(y_list)) > 1:
        train_idx, test_idx = train_test_split(node_idx, test_size=0.2, stratify=y_list, random_state=42)
        train_idx, val_idx = train_test_split(train_idx, test_size=0.125, stratify=[y_list[i] for i in train_idx], random_state=42)
    else:
        train_idx = node_idx[:int(0.7*n_nodes)]
        val_idx = node_idx[int(0.7*n_nodes):int(0.8*n_nodes)]
        test_idx = node_idx[int(0.8*n_nodes):]

    data.train_mask = torch.zeros(n_nodes, dtype=torch.bool)
    data.val_mask   = torch.zeros(n_nodes, dtype=torch.bool)
    data.test_mask  = torch.zeros(n_nodes, dtype=torch.bool)
    data.train_mask[train_idx] = True
    data.val_mask[val_idx] = True
    data.test_mask[test_idx] = True

    # ---------------------------
    # 13) model definition (GAT)
    # ---------------------------
    class GATNet(nn.Module):
        def __init__(self, in_channels, edge_dim=None, hidden_channels=128, out_channels=1, heads=4, dropout=0.5):  ### تعديل لتحسين الدقة: زيادة hidden_channels، تقليل dropout، إضافة edge_dim
            super().__init__()
            self.conv1 = GATConv(in_channels, hidden_channels, heads=heads, dropout=dropout, edge_dim=edge_dim)
            self.conv2 = GATConv(hidden_channels * heads, max(8, hidden_channels//4), heads=1, concat=False, dropout=dropout, edge_dim=edge_dim)
            self.lin = Linear(max(8, hidden_channels//4), out_channels)

        def forward(self, x, edge_index, edge_attr=None):
            x = F_torch.dropout(x, p=0.5, training=self.training)  ### تعديل لتحسين الدقة: تقليل dropout إلى 0.5
            x = F_torch.elu(self.conv1(x, edge_index, edge_attr))  ### تعديل لتحسين الدقة: تمرير edge_attr
            x = F_torch.dropout(x, p=0.5, training=self.training)
            x = F_torch.elu(self.conv2(x, edge_index, edge_attr))  ### تعديل لتحسين الدقة: تمرير edge_attr
            x = self.lin(x).squeeze(-1)
            return x

    # ### تعديل لتحسين الدقة: تمرير edge_dim إلى النموذج
    edge_dim = edge_attr.size(1) if edge_attr is not None else None
    model = GATNet(in_channels=x.size(1), edge_dim=edge_dim, hidden_channels=128).to(DEVICE)

    # ---------------------------
    # 14) NeighborLoader (sampling on CPU)
    # ---------------------------
    train_loader = NeighborLoader(data, input_nodes=data.train_mask, num_neighbors=NUM_NEIGHBORS,
                                  batch_size=BATCH_SIZE, shuffle=True)
    val_loader   = NeighborLoader(data, input_nodes=data.val_mask, num_neighbors=NUM_NEIGHBORS,
                                  batch_size=VAL_BATCH_SIZE, shuffle=False)
    test_loader  = NeighborLoader(data, input_nodes=data.test_mask, num_neighbors=NUM_NEIGHBORS,
                                  batch_size=TEST_BATCH_SIZE, shuffle=False)

    # ---------------------------
    # 15) Training loop (WITH early stopping) with GPU compute  ### تعديل لتحسين الدقة: إضافة early stopping
    # ---------------------------
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=5e-4)
    pos = int(data.y.sum().item())
    neg = data.num_nodes - pos
    pos_weight = torch.tensor((neg / pos) if pos > 0 else 1.0).to(DEVICE)
    criterion = torch.nn.BCEWithLogitsLoss(pos_weight=pos_weight)

    best_val_auc = -1.0
    patience = 10  ### تعديل لتحسين الدقة: إضافة patience لـ early stopping
    epochs_no_improve = 0

    for epoch in range(1, NUM_EPOCHS + 1):
        model.train()
        total_loss = 0.0
        total_examples = 0

        for batch in train_loader:
            # keep batch.n_id on CPU, move batch.x and batch.edge_index to GPU
            batch_n_id = batch.n_id  # CPU tensor of global node indices
            seed_num = batch.batch_size if hasattr(batch, "batch_size") else batch.n_id.size(0)

            batch_x = batch.x.to(DEVICE, non_blocking=PIN_MEMORY)
            batch_edge_index = batch.edge_index.to(DEVICE, non_blocking=PIN_MEMORY)
            batch_edge_attr = batch.edge_attr.to(DEVICE, non_blocking=PIN_MEMORY) if hasattr(batch, "edge_attr") and batch.edge_attr is not None else None

            optimizer.zero_grad()
            logits = model(batch_x, batch_edge_index, batch_edge_attr)

            seed_nid = batch_n_id[:seed_num].cpu()  # ensure CPU indices
            labels = data.y[seed_nid].to(DEVICE).float()
            preds = logits[:seed_num]
            loss = criterion(preds, labels)
            loss.backward()
            optimizer.step()

            total_loss += loss.item() * seed_num
            total_examples += int(seed_num)

        train_loss = total_loss / max(1, total_examples)

        # validation
        model.eval()
        ys, ps = [], []
        with torch.no_grad():
            for batch in val_loader:
                batch_n_id = batch.n_id
                seed_num = batch.batch_size if hasattr(batch, "batch_size") else batch.n_id.size(0)

                batch_x = batch.x.to(DEVICE, non_blocking=PIN_MEMORY)
                batch_edge_index = batch.edge_index.to(DEVICE, non_blocking=PIN_MEMORY)
                batch_edge_attr = batch.edge_attr.to(DEVICE, non_blocking=PIN_MEMORY) if hasattr(batch, "edge_attr") and batch.edge_attr is not None else None

                logits = model(batch_x, batch_edge_index, batch_edge_attr)
                seed_nid = batch_n_id[:seed_num].cpu()
                labels = data.y[seed_nid].cpu().numpy()
                prob = torch.sigmoid(logits[:seed_num]).cpu().numpy()

                ys.append(labels); ps.append(prob)

        if len(ys) > 0:
            ys = np.concatenate(ys); ps = np.concatenate(ps)
            val_auc = roc_auc_score(ys, ps) if len(np.unique(ys)) > 1 else 0.0
            val_f1 = f1_score(ys, (ps > 0.5).astype(int), zero_division=0)
        else:
            val_auc, val_f1 = 0.0, 0.0

        print(f"Epoch {epoch:03d} | TrainLoss {train_loss:.4f} | ValAUC {val_auc:.4f} | ValF1 {val_f1:.4f}")

        # save best model and early stopping  ### تعديل لتحسين الدقة: إضافة early stopping
        if val_auc > best_val_auc:
            best_val_auc = val_auc
            torch.save(model.state_dict(), MODEL_PATH)
            epochs_no_improve = 0
        else:
            epochs_no_improve += 1

        if epochs_no_improve >= patience:
            print(f"Early stopping at epoch {epoch}")
            break

    # ---------------------------
    # 16) Load best model and final test evaluation
    # ---------------------------
    if os.path.exists(MODEL_PATH):
        model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
    model.eval()

    ys, ps = [], []
    with torch.no_grad():
        for batch in test_loader:
            batch_n_id = batch.n_id
            seed_num = batch.batch_size if hasattr(batch, "batch_size") else batch.n_id.size(0)

            batch_x = batch.x.to(DEVICE, non_blocking=PIN_MEMORY)
            batch_edge_index = batch.edge_index.to(DEVICE, non_blocking=PIN_MEMORY)
            batch_edge_attr = batch.edge_attr.to(DEVICE, non_blocking=PIN_MEMORY) if hasattr(batch, "edge_attr") and batch.edge_attr is not None else None

            logits = model(batch_x, batch_edge_index, batch_edge_attr)
            seed_nid = batch_n_id[:seed_num].cpu()
            labels = data.y[seed_nid].cpu().numpy()
            prob = torch.sigmoid(logits[:seed_num]).cpu().numpy()

            ys.append(labels); ps.append(prob)

    if len(ys) > 0:
        ys = np.concatenate(ys); ps = np.concatenate(ps)
        test_auc = roc_auc_score(ys, ps) if len(np.unique(ys)) > 1 else 0.0
        test_f1 = f1_score(ys, (ps > 0.5).astype(int), zero_division=0)
    else:
        test_auc, test_f1 = 0.0, 0.0

    print(f"Final Test AUC = {test_auc:.4f} | Test F1 = {test_f1:.4f}")

    # ---------------------------
    # 17) Save mapping & pipeline (already saved pipeline earlier)
    # ---------------------------
    with open(MAPPING_PATH, "w") as f:
        json.dump(account2idx, f)
    print(f"Saved model -> {MODEL_PATH}, mapping -> {MAPPING_PATH}, pipeline -> {PIPELINE_DIR}")

    # ---------------------------
    # 18) Prediction helpers (GPU inference)
    # ---------------------------
    def predict_existing_accounts(account_list: List[str]) -> Dict[str, float]:
        model.eval()
        with torch.no_grad():
            logits = model(data.x.to(DEVICE), data.edge_index.to(DEVICE), data.edge_attr.to(DEVICE) if data.edge_attr is not None else None)
            probs = torch.sigmoid(logits).cpu().numpy()
        out = {}
        for acc in account_list:
            idx = account2idx.get(acc, None)
            out[acc] = float(probs[idx]) if idx is not None else None
        return out

    def predict_with_new_transactions(new_df_spark) -> Dict[str, float]:
        # transform and aggregate same as training; then append nodes & edges temporarily to run inference
        new_feat = pipeline_model.transform(new_df_spark)
        new_feat = new_feat.withColumn("features_array", vector_to_array("features_scaled"))
        for i in range(dim):
            new_feat = new_feat.withColumn(f"f_{i}", F.col("features_array").getItem(i))

        sender_new = new_feat.groupBy("Sender_account").agg(*[F.avg(f"f_{i}").alias(f"sender_f_{i}") for i in range(dim)]).na.fill(0.0)
        receiver_new = new_feat.groupBy("Receiver_account").agg(*[F.avg(f"f_{i}").alias(f"receiver_f_{i}") for i in range(dim)]).na.fill(0.0).withColumnRenamed("Receiver_account","account")
        new_accounts_df = new_feat.select("Sender_account").union(new_feat.select("Receiver_account")).distinct().withColumnRenamed("Sender_account","account")
        joined_new = new_accounts_df.join(sender_new.withColumnRenamed("Sender_account","account"), on="account", how="left") \
                                    .join(receiver_new.withColumnRenamed("account","account"), on="account", how="left")

        for i in range(dim):
            joined_new = joined_new.withColumn(f"sender_f_{i}", F.coalesce(F.col(f"sender_f_{i}"), F.lit(0.0)))
            joined_new = joined_new.withColumn(f"receiver_f_{i}", F.coalesce(F.col(f"receiver_f_{i}"), F.lit(0.0)))

        node_new_df = joined_new.select("account", *[((F.col(f"sender_f_{i}") + F.col(f"receiver_f_{i}"))/2.0).alias(f"node_f_{i}") for i in range(dim)]).na.fill(0.0)
        new_map = node_new_df.rdd.map(lambda r: (r["account"], [float(r[f"node_f_{i}"]) for i in range(dim)])).collectAsMap()

        existing_accounts = set(accounts)
        appended_accounts = [acc for acc in new_map.keys() if acc not in existing_accounts]

        new_X_list = [new_map[acc] for acc in appended_accounts] if len(appended_accounts) > 0 else []
        if len(new_X_list) > 0:
            new_X_arr = np.array(new_X_list, dtype=np.float32)
            x_combined = torch.cat([data.x.cpu(), torch.tensor(new_X_arr, dtype=torch.float)], dim=0).to(DEVICE)
        else:
            x_combined = data.x.to(DEVICE)

        base_count = len(accounts)
        appended_index_map = {acc: base_count + i for i, acc in enumerate(appended_accounts)}
        def map_idx(a):
            if a in account2idx:
                return account2idx[a]
            elif a in appended_index_map:
                return appended_index_map[a]
            else:
                return None

        new_edges = new_feat.select("Sender_account","Receiver_account").distinct().rdd \
                    .map(lambda r: (map_idx(r["Sender_account"]), map_idx(r["Receiver_account"]))) \
                    .filter(lambda x: x[0] is not None and x[1] is not None).collect()

        if len(new_edges) > 0:
            new_src = [int(e[0]) for e in new_edges]
            new_dst = [int(e[1]) for e in new_edges]
            edge_src_comb = torch.cat([data.edge_index[0].cpu(), torch.tensor(new_src, dtype=torch.long)], dim=0).to(DEVICE)
            edge_dst_comb = torch.cat([data.edge_index[1].cpu(), torch.tensor(new_dst, dtype=torch.long)], dim=0).to(DEVICE)
            edge_index_comb = torch.stack([edge_src_comb, edge_dst_comb], dim=0).to(DEVICE)
        else:
            edge_index_comb = data.edge_index.to(DEVICE)

        model.eval()
        with torch.no_grad():
            logits_comb = model(x_combined, edge_index_comb, data.edge_attr.to(DEVICE) if data.edge_attr is not None else None)
            probs_comb = torch.sigmoid(logits_comb).cpu().numpy()

        out = {}
        for acc in new_map.keys():
            if acc in account2idx:
                out[acc] = float(probs_comb[account2idx[acc]])
            else:
                idx = appended_index_map[acc]
                out[acc] = float(probs_comb[idx])
        return out

    # return helpers so user can import them if running from main
    return {
        "spark_session": spark,
        "pipeline_model": pipeline_model,
        "model": model,
        "data": data,
        "account2idx": account2idx,
        "predict_existing_accounts": predict_existing_accounts,
        "predict_with_new_transactions": predict_with_new_transactions
    }

if __name__ == "__main__":
    artifacts = main()
    print("Done. Artifacts keys:", list(artifacts.keys()))