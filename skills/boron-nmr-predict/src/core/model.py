import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import TransformerConv, BatchNorm, global_add_pool

class BoronNMRNet_V3(nn.Module):
    """
    改进版11B NMR预测模型 (多头拼接版本)

    改进点:
    1. 虚拟节点机制 (Virtual Node)
    2. 可学习溶剂Embedding (64维)
    3. 支持注意力权重提取 (可解释性)
    4. 【修改】TransformerConv使用concat=True (多头拼接)
    """

    def __init__(self, node_in_dim, edge_in_dim,
                 num_solvents=11, solvent_dim=64,
                 hidden_dim=256, dropout=0.05, num_heads=4,
                 ml_feature_dim=0, ml_hidden_dim=64):
        super().__init__()

        self.dropout_rate = dropout
        self.hidden_dim = hidden_dim
        self.num_heads = num_heads
        self.head_dim = hidden_dim // num_heads  # 256 / 4 = 64

        # ========================================
        # 1. 编码层
        # ========================================
        self.node_encoder = nn.Linear(node_in_dim, hidden_dim)
        self.edge_encoder = nn.Linear(edge_in_dim, hidden_dim)

        # 溶剂Embedding层
        self.solvent_embedding = nn.Embedding(num_solvents, solvent_dim)

        # 虚拟节点Embedding
        self.virtual_node_encoder = nn.Embedding(1, hidden_dim)

        # ========================================
        # 2. GNN主干 + 虚拟节点更新层
        # concat=True, 每头输出head_dim, 拼接后为hidden_dim
        # ========================================
        self.conv1 = TransformerConv(hidden_dim, self.head_dim, heads=num_heads,
                                     edge_dim=hidden_dim, concat=True)
        self.bn1 = BatchNorm(hidden_dim)

        self.conv2 = TransformerConv(hidden_dim, self.head_dim, heads=num_heads,
                                     edge_dim=hidden_dim, concat=True)
        self.bn2 = BatchNorm(hidden_dim)

        self.conv3 = TransformerConv(hidden_dim, self.head_dim, heads=num_heads,
                                     edge_dim=hidden_dim, concat=True)
        self.bn3 = BatchNorm(hidden_dim)

        # 虚拟节点更新MLP (每层一个)
        self.vn_mlp_list = nn.ModuleList([
            nn.Sequential(
                nn.Linear(hidden_dim, hidden_dim),
                nn.BatchNorm1d(hidden_dim),
                nn.ReLU(),
                nn.Dropout(dropout)
            ) for _ in range(3)
        ])

        # ========================================
        # 3. ML 全局特征编码层 (SHAP Top-20)
        # ========================================
        self.ml_feature_dim = ml_feature_dim
        if ml_feature_dim > 0:
            self.ml_encoder = nn.Sequential(
                nn.Linear(ml_feature_dim, ml_hidden_dim),
                nn.ReLU(),
                nn.Dropout(dropout)
            )
            fusion_dim = hidden_dim + solvent_dim + ml_hidden_dim
        else:
            self.ml_encoder = None
            fusion_dim = hidden_dim + solvent_dim

        # ========================================
        # 4. 预测头
        # ========================================
        self.mlp = nn.Sequential(
            nn.Linear(fusion_dim, 256),
            nn.ReLU(),
            nn.Dropout(self.dropout_rate),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, 1)
        )

    def forward(self, x, edge_index, edge_attr, solvent_ids, mask_b, batch_index,
                ml_global_features=None, return_attention=False):
        """
        前向传播

        参数:
            x: 节点特征 [num_nodes, node_in_dim]
            edge_index: 边索引 [2, num_edges]
            edge_attr: 边特征 [num_edges, edge_in_dim]
            solvent_ids: 溶剂ID [batch_size]
            mask_b: 硼原子掩码 [num_nodes]
            batch_index: 节点所属batch [num_nodes]
            ml_global_features: ML全局特征 [batch_size, ml_feature_dim] (可选)
            return_attention: 是否返回注意力权重 (用于可解释性)

        返回:
            out: 预测的化学位移 [num_b_atoms]
            (可选) attention_weights: 注意力权重
        """
        # ========================================
        # A. 初始编码
        # ========================================
        x = self.node_encoder(x)
        edge_attr = self.edge_encoder(edge_attr)

        # 初始化虚拟节点
        num_graphs = batch_index.max().item() + 1
        virtual_node_feat = self.virtual_node_encoder(
            torch.zeros(num_graphs, dtype=torch.long, device=x.device)
        )  # [num_graphs, hidden_dim]

        # ========================================
        # B. GNN消息传递 + 虚拟节点交互
        # ========================================
        attention_weights = [] if return_attention else None

        # === 第1层 ===
        x_in = x
        x = x + virtual_node_feat[batch_index]  # 虚拟节点 → 真实节点

        if return_attention:
            x, (edge_idx, attn) = self.conv1(x, edge_index, edge_attr,
                                            return_attention_weights=True)
            attention_weights.append((edge_idx, attn))
        else:
            x = self.conv1(x, edge_index, edge_attr)

        x = self.bn1(x)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout_rate, training=self.training)
        x = x + x_in  # 残差

        virtual_node_feat = self.vn_mlp_list[0](
            global_add_pool(x, batch_index) + virtual_node_feat
        )  # 真实节点 → 虚拟节点

        # === 第2层 ===
        x_in = x
        x = x + virtual_node_feat[batch_index]

        if return_attention:
            x, (edge_idx, attn) = self.conv2(x, edge_index, edge_attr,
                                            return_attention_weights=True)
            attention_weights.append((edge_idx, attn))
        else:
            x = self.conv2(x, edge_index, edge_attr)

        x = self.bn2(x)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout_rate, training=self.training)
        x = x + x_in

        virtual_node_feat = self.vn_mlp_list[1](
            global_add_pool(x, batch_index) + virtual_node_feat
        )

        # === 第3层 ===
        x_in = x
        x = x + virtual_node_feat[batch_index]

        if return_attention:
            x, (edge_idx, attn) = self.conv3(x, edge_index, edge_attr,
                                            return_attention_weights=True)
            attention_weights.append((edge_idx, attn))
        else:
            x = self.conv3(x, edge_index, edge_attr)

        x = self.bn3(x)
        x = F.relu(x)
        x = x + x_in

        virtual_node_feat = self.vn_mlp_list[2](
            global_add_pool(x, batch_index) + virtual_node_feat
        )

        # ========================================
        # C. 提取硼原子特征 + 融合溶剂 + ML全局特征
        # ========================================
        b_features = x[mask_b]
        b_batch_idx = batch_index[mask_b]

        # 获取溶剂特征
        solvent_features = self.solvent_embedding(solvent_ids)  # [batch_size, solvent_dim]

        # 确保solvent_features是2维的 (处理batch_size=1的情况)
        if solvent_features.dim() == 1:
            solvent_features = solvent_features.unsqueeze(0)  # [1, solvent_dim]

        b_solvent_features = solvent_features[b_batch_idx]      # [num_b_atoms, solvent_dim]

        # 融合 ML 全局特征 (方案A: 预测头拼接)
        if self.ml_encoder is not None and ml_global_features is not None:
            ml_encoded = self.ml_encoder(ml_global_features)    # [batch_size, ml_hidden_dim]
            if ml_encoded.dim() == 1:
                ml_encoded = ml_encoded.unsqueeze(0)
            b_ml_features = ml_encoded[b_batch_idx]             # [num_b_atoms, ml_hidden_dim]
            combined = torch.cat([b_features, b_solvent_features, b_ml_features], dim=1)
        else:
            combined = torch.cat([b_features, b_solvent_features], dim=1)

        # ========================================
        # D. MLP预测
        # ========================================
        out = self.mlp(combined).squeeze(-1)

        if return_attention:
            return out, attention_weights
        else:
            return out
