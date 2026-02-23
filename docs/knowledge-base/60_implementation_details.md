# 完整技术实现细节（从数据到输出的全链路）

> **文档目标**：逐行代码级别解析从数据处理→模型训练→输出的每一个环节，包括维度变换、单位统一、参数流转等所有技术细节。

---

## 目录

1. [数据处理阶段](#1-数据处理阶段)
2. [输入数据维度](#2-输入数据维度)
3. [模型搭建](#3-模型搭建)
4. [模型训练](#4-模型训练)
5. [参数与指标](#5-参数与指标)
6. [单位统一](#6-单位统一)
7. [输出阶段](#7-输出阶段)

---

## 1. 数据处理阶段

### 1.1 配置文件读取（入口）

**代码位置**：`src/data_generator.py:197-201`

```python
def load_config(config_path: str = 'config.yaml') -> Dict:
    """加载配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config
```

**输入**：
- `config.yaml`（YAML格式）

**输出**：
- Python字典（嵌套结构）

**数据流转**：
```yaml
# config.yaml 原始格式
network:
  num_farmers: 300
  
# yaml.safe_load() 后
{
  'network': {
    'num_farmers': 300,
    ...
  },
  'farmer': {...},
  ...
}
```

---

### 1.2 农户属性生成（核心数据源）

**代码位置**：`src/data_generator.py:18-170`

#### 1.2.1 经济水平生成

**代码**：
```python
# 第27-35行
economic = np.maximum(
    np.random.normal(
        farmer_config['economic_mean'],      # μ = 50000
        farmer_config['economic_std'],       # σ = 20000
        self.num_farmers                     # N = 300
    ),
    0  # 确保非负
)
```

**维度变化**：
- 输入：配置参数（标量）
  - `economic_mean`: 50000（元/年）
  - `economic_std`: 20000（元/年）
  - `num_farmers`: 300（个）
- 处理：
  1. `np.random.normal(50000, 20000, 300)` → shape=(300,)，值域(-∞,+∞)
  2. `np.maximum(..., 0)` → shape=(300,)，值域[0,+∞)
- 输出：1维NumPy数组
  - shape: (300,)
  - dtype: float64
  - 单位: 元/年
  - 统计量示例：mean≈50000, std≈20000, min≈0, max≈120000

**为什么这样设计**：
- 正态分布模拟真实收入分布（中间多、两端少）
- `np.maximum(..., 0)`处理负值（经济水平不能为负）
- ⚠️**隐性逻辑**：没有上界截断，极端高收入（>10万）可能导致后续RL状态归一化失真

---

#### 1.2.2 教育程度生成

**代码**：
```python
# 第38-42行
education = np.random.choice(
    farmer_config['education_levels'],  # [0, 1, 2, 3]
    size=self.num_farmers,              # 300
    p=[0.3, 0.4, 0.2, 0.1]             # 概率分布（硬编码）
)
```

**维度变化**：
- 输入：
  - 候选值：[0, 1, 2, 3]（小学/初中/高中/大专+）
  - 概率：[0.3, 0.4, 0.2, 0.1]
  - 样本量：300
- 输出：
  - shape: (300,)
  - dtype: int64
  - 值域: {0, 1, 2, 3}
  - 分布示例：0出现90次(30%)，1出现120次(40%)，2出现60次(20%)，3出现30次(10%)

**⚠️关键隐性逻辑**：
- 概率`[0.3, 0.4, 0.2, 0.1]`在代码中硬编码，**不在config.yaml中**
- 修改配置文件的`education_levels`只能改变取值范围，无法改变概率分布
- **对结论的影响**：70%低教育(0+1)决定了"教育优先权奖励"的实际覆盖面

---

#### 1.2.3 短视性与折扣因子生成

**代码**：
```python
# 第64-71行
myopia = np.random.uniform(
    farmer_config['myopia_range'][0],  # 0.1
    farmer_config['myopia_range'][1],  # 0.9
    self.num_farmers                   # 300
)
discount_factor = 1.0 / (1.0 + myopia)
```

**维度变化与公式映射**：

| 变量 | 符号 | 公式 | 输入范围 | 输出范围 | 单位 |
|------|------|------|----------|----------|------|
| 短视性 | δᵢ | U(0.1,0.9) | [0.1, 0.9] | [0.1, 0.9] | 无量纲 |
| 折扣因子 | γᵢ | 1/(1+δᵢ) | [0.1, 0.9] | [0.53, 0.91] | 无量纲 |

**数学关系**：
```
δᵢ=0.1 → γᵢ=1/1.1=0.91 (远见型农户，重视长期收益)
δᵢ=0.5 → γᵢ=1/1.5=0.67 (中等)
δᵢ=0.9 → γᵢ=1/1.9=0.53 (短视型农户，只看眼前)
```

**在RL中的作用**：
- `γᵢ`作为个性化折扣因子：`target_q = reward + γᵢ * max_next_q`
- 短视农户(γ<0.6)倾向立即奖励（可能采纳传统施肥因为成本低）
- 远见农户(γ>0.8)重视长期收益（愿意投资绿色施肥）

---

#### 1.2.4 三维土壤质量生成

**代码**：
```python
# 第113-138行
# 三个维度的质量（正态分布，带随机性）
fertility = np.random.normal(initial_fertility, 0.1, self.num_farmers)
fertility = np.clip(fertility, 0, 1)

soil_structure = np.random.normal(initial_structure, 0.1, self.num_farmers)
soil_structure = np.clip(soil_structure, 0, 1)

biological_activity = np.random.normal(initial_biological, 0.1, self.num_farmers)
biological_activity = np.clip(biological_activity, 0, 1)

# 计算综合质量（加权平均）
quality_weights = {
    'fertility': 0.4,
    'soil_structure': 0.3,
    'biological_activity': 0.3
}
land_quality = (
    0.4 * fertility +
    0.3 * soil_structure +
    0.3 * biological_activity
)
```

**维度结构**：

| 维度 | 变量名 | 初始值μ | 标准差σ | 值域 | 权重 | 物理意义 |
|------|--------|---------|---------|------|------|----------|
| 肥力 | fertility | 0.5 | 0.1 | [0,1] | 0.4 | 短期产量 |
| 颗粒结构 | soil_structure | 0.5 | 0.1 | [0,1] | 0.3 | 长期稳定性 |
| 生物活性 | biological_activity | 0.5 | 0.1 | [0,1] | 0.3 | 可持续性 |
| **综合质量** | land_quality | - | - | [0,1] | - | 加权平均 |

**生成后数据形状**：
```python
fertility.shape           # (300,)
soil_structure.shape      # (300,)
biological_activity.shape # (300,)
land_quality.shape        # (300,)
```

**为什么需要三维**：
- **单一质量的局限**：无法区分"肥力高但结构差"与"肥力低但结构好"
- **三维的优势**：
  1. 绿色施肥对三维影响不同（见`dynamics.py:40-161`）
  2. 传统施肥短期提升肥力但损害结构和生物活性
  3. 更真实反映土壤健康的多维性质

---

### 1.3 最终DataFrame结构

**输出DataFrame结构**：

| 列名 | dtype | 值域 | 单位 | 作用 |
|------|-------|------|------|------|
| farmer_id | int64 | [0,299] | - | 唯一标识符 |
| economic_level | float64 | [0,∞) | 元/年 | 决策效用、RL状态 |
| education | int64 | {0,1,2,3} | - | 影响教育优先权 |
| risk_tolerance | float64 | [0,1] | - | RL状态 |
| env_awareness | float64 | [0,1] | - | 预留 |
| myopia | float64 | [0.1,0.9] | - | 计算折扣因子 |
| discount_factor | float64 | [0.53,0.91] | - | RL个性化γᵢ |
| adoption_state | int64 | {0,1} | - | 采纳状态 |
| fertility | float64 | [0,1] | - | 三维质量 |
| soil_structure | float64 | [0,1] | - | 三维质量 |
| biological_activity | float64 | [0,1] | - | 三维质量 |
| land_quality | float64 | [0,1] | - | 综合质量 |
| education_priority | float64 | [0,1] | - | RL奖励λ₄ |
| political_voice | float64 | [0,1] | - | RL奖励λ₅ |
| x, y, z | float64 | [-1,1] | - | 双曲空间坐标 |
| policy_perception | float64 | [0.3,0.7] | - | 政策感知度 |
| training_access | int64 | {0,1} | - | 培训状态 |

**总计**：行数300，列数19，内存约45KB

---

## 2. 输入数据维度

### 2.1 RL状态空间维度（12维）

**代码位置**：`src/rl_agent.py:107-164`

```python
state = np.array([
    self.attrs['economic_level'] / 100000,  # [0] 经济水平（归一化）
    social_influence,                       # [1] 度中心性
    self.attrs['policy_perception'],        # [2] 政策感知
    self.attrs['risk_tolerance'],           # [3] 风险偏好
    fertility,                              # [4] 肥力
    soil_structure,                         # [5] 颗粒结构
    biological_activity,                    # [6] 生物活性
    neighbor_adoption,                      # [7] 邻居采纳率
    global_Q,                               # [8] 全局质量
    myopia,                                 # [9] 短视性
    education_priority,                     # [10] 教育优先权
    political_voice                         # [11] 话语权
], dtype=np.float32)
```

**详细维度表**：

| 索引 | 维度名 | 值域 | 单位 | 物理意义 |
|------|--------|------|------|----------|
| 0 | 经济水平 | [0,∞) | 无量纲 | 归一化经济能力 |
| 1 | 度中心性 | [0,1] | 无量纲 | 社会影响力 |
| 2 | 政策感知 | [0.3,0.7] | 无量纲 | 政策敏感度 |
| 3 | 风险偏好 | [0,1] | 无量纲 | 风险态度 |
| 4 | 肥力 | [0,1] | 无量纲 | 短期产量 |
| 5 | 颗粒结构 | [0,1] | 无量纲 | 长期稳定性 |
| 6 | 生物活性 | [0,1] | 无量纲 | 可持续性 |
| 7 | 邻居采纳率 | [0,1] | 无量纲 | 社会压力 |
| 8 | 全局质量 | [0,1] | 无量纲 | 宏观环境 |
| 9 | 短视性 | [0.1,0.9] | 无量纲 | 时间偏好 |
| 10 | 教育优先权 | [0,1] | 无量纲 | 教育激励 |
| 11 | 话语权 | [0,1] | 无量纲 | 参政激励 |

---

## 3. 模型搭建

### 3.1 DQN网络结构

**代码位置**：`src/rl_agent.py:14-26`

```python
class DQNetwork(nn.Module):
    def __init__(self, state_dim: int, action_dim: int, hidden_dim: int = 128):
        super(DQNetwork, self).__init__()
        self.fc1 = nn.Linear(state_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, action_dim)
    
    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        return self.fc3(x)
```

**网络架构**：

```
输入层(12) → 隐藏层1(64) → 隐藏层2(64) → 输出层(2)
            ReLU          ReLU          Linear

参数量：
- fc1: 12×64 + 64 = 832
- fc2: 64×64 + 64 = 4160
- fc3: 64×2 + 2 = 130
总计：5122个参数
```

---

## 4. 模型训练

### 4.1 训练循环结构

```python
for episode in range(50):
    dynamics.reset_states()
    
    for step in range(60):
        # 获取状态 → 选择动作 → 更新环境 → 计算奖励 → 存储经验 → 训练
        avg_reward = mas.step(subsidy, training=True)
    
    if episode % 5 == 0:
        mas.update_all_target_networks()
    
    mas.decay_all_epsilon()
```

---

## 5. 参数与指标

### 5.1 RL超参数

| 参数 | 值 | 作用 |
|------|-----|------|
| hidden_dim | 64 | 隐藏层维度 |
| learning_rate | 0.001 | 学习率 |
| batch_size | 128 | 批量大小 |
| memory_size | 5000 | 回放池容量 |
| target_update | 5 | 目标网络更新周期 |

---

## 6. 单位统一

### 6.1 单位转换策略

**核心原则**：所有效用/奖励项统一为"元"

```python
# 社会影响：0-1 → 元
S_social = neighbor_adoption_rate * 1000.0  # 基准1000元

# 质量收益：0-1 → 元
Q_benefit = Q_normalized * 5000.0  # 基准5000元
```

---

## 7. 输出阶段

### 7.1 输出文件

| 文件 | 格式 | 内容 |
|------|------|------|
| results/rl_training_history.csv | CSV | 训练过程数据 |
| models/agent_0_final.pth | PyTorch | 模型权重 |
| figures/training_curves.png | PNG | 训练曲线图 |
| results/results_summary.json | JSON | 最终结果摘要 |

---

## 总结：完整数据流

```
config.yaml → FarmerDataGenerator(300×19) → NetworkBuilder(2400边) 
→ AdoptionDynamics → RL训练(12维状态→DQN→动作→奖励) 
→ 输出(CSV/PNG/JSON/PTH)
```
