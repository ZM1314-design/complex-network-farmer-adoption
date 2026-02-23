# 📖 基线模型与强化学习输入数据差异说明

## 🎯 核心问题

**您的问题：** 原始的输入数据（基线模型）和强化学习的输入数据有什么不同？

**答案：** 
- ✅ **数据来源相同**：都使用相同的 `farmer_df`（农户属性DataFrame）
- ⚠️ **使用方式不同**：基线模型直接使用原始字段，强化学习转换为状态向量

---

## 📊 输入数据对比

### 基线模型（TPB）的输入数据

#### 数据来源
```python
# run_experiment.py 第43-44行
generator = FarmerDataGenerator(self.config)
farmer_df = generator.generate_farmer_attributes()
```

#### 直接使用的字段
基线模型在决策时**直接使用** `farmer_df` 中的原始字段：

| 字段 | 用途 | 代码位置 |
|------|------|---------|
| `economic_level` | 计算成本项 | `dynamics.py` 第250-255行 |
| `policy_perception` | 计算政策激励项 | `dynamics.py` 第240行 |
| `risk_tolerance` | 影响决策（间接） | TPB权重中 |
| `fertility`, `soil_structure`, `biological_activity` | 计算质量收益项 | `dynamics.py` 第259-275行 |
| `adoption_state` (邻居) | 计算社会影响项 | `dynamics.py` 第244行 |
| `training_access` | 计算政策激励项 | `dynamics.py` 第240行 |

#### 决策过程
```python
# src/dynamics.py 第377行
prob = self.logit_adoption_probability(idx, subsidy)
# ↓
# 内部调用 compute_utility_tpb
# ↓
# 直接读取 farmer_df 中的字段
U_i = θ_p·S_policy + θ_s·S_social - θ_e·C_cost + θ_q·Q_benefit
```

**特点：**
- ✅ 直接使用原始字段
- ✅ 字段值**直接参与计算**
- ✅ 不需要数据转换

---

### 强化学习（DQN）的输入数据

#### 数据来源
```python
# run_experiment.py 第180-181行
generator = FarmerDataGenerator(self.config)
farmer_df = generator.generate_farmer_attributes()
```

**注意：** 数据来源**完全相同**！

#### 转换为状态向量
强化学习将 `farmer_df` 中的字段**转换**为12维状态向量：

```python
# src/rl_agent.py 第107-164行
def get_state_vector(self, dynamics, G, global_Q: float) -> np.ndarray:
    """
    构建12维状态向量
    """
    state = np.array([
        self.attrs['economic_level'] / 100000,  # s₁: 归一化经济水平
        social_influence,                        # s₂: 计算得到（度中心性）
        self.attrs['policy_perception'],       # s₃: 政策感知度
        self.attrs['risk_tolerance'],           # s₄: 风险偏好
        fertility,                               # s₅: 肥力
        soil_structure,                          # s₆: 颗粒结构
        biological_activity,                     # s₇: 生物活性
        neighbor_adoption,                       # s₈: 计算得到（邻居采纳率）
        global_Q,                                # s₉: 计算得到（全局质量）
        myopia,                                  # s₁₀: 短视性
        education_priority,                      # s₁₁: 教育优先权
        political_voice                          # s₁₂: 话语权
    ], dtype=np.float32)
    return state
```

#### 状态向量组成

| 维度 | 符号 | 数据来源 | 计算方式 |
|------|------|---------|---------|
| s₁ | `income_i` | `farmer_df['economic_level']` | 归一化：`/ 100000` |
| s₂ | `social_i` | **计算得到** | `degree / max_degree` |
| s₃ | `policy_i` | `farmer_df['policy_perception']` | 直接使用 |
| s₄ | `risk_i` | `farmer_df['risk_tolerance']` | 直接使用 |
| s₅ | `F_i` | `farmer_df['fertility']` | 直接使用 |
| s₆ | `S_i` | `farmer_df['soil_structure']` | 直接使用 |
| s₇ | `B_i` | `farmer_df['biological_activity']` | 直接使用 |
| s₈ | `ρ_Ni(t)` | **计算得到** | `mean(neighbors.adoption_state)` |
| s₉ | `Q(t)` | **计算得到** | `dynamics.global_Q` |
| s₁₀ | `δ_i` | `farmer_df['myopia']` | 直接使用 |
| s₁₁ | `E_i` | `farmer_df['education_priority']` | 直接使用 |
| s₁₂ | `V_i` | `farmer_df['political_voice']` | 直接使用 |

**特点：**
- ✅ 转换为固定维度的状态向量（12维）
- ✅ 包含**计算得到的值**（社会影响力、邻居采纳率、全局Q）
- ✅ 需要数据归一化（经济水平）

---

## 🔍 关键差异

### 1. 数据格式

| 对比项 | 基线模型（TPB） | 强化学习（DQN） |
|--------|----------------|----------------|
| **数据格式** | DataFrame（多列） | NumPy数组（12维向量） |
| **字段数量** | 18个字段 | 12个维度 |
| **数据转换** | ❌ 不需要 | ✅ 需要转换 |

---

### 2. 使用的字段

#### 基线模型使用的字段
- `economic_level` - 直接使用
- `policy_perception` - 直接使用
- `risk_tolerance` - 间接使用（影响权重）
- `fertility`, `soil_structure`, `biological_activity` - 直接使用
- `adoption_state` (邻居) - 直接使用
- `training_access` - 直接使用
- 其他字段：间接使用或未使用

#### 强化学习使用的字段
- `economic_level` - 转换为s₁（归一化）
- `policy_perception` - 转换为s₃
- `risk_tolerance` - 转换为s₄
- `fertility`, `soil_structure`, `biological_activity` - 转换为s₅, s₆, s₇
- `myopia` - 转换为s₁₀
- `education_priority` - 转换为s₁₁
- `political_voice` - 转换为s₁₂
- **计算得到的值**：
  - 社会影响力（s₂）- 从网络G计算
  - 邻居采纳率（s₈）- 从网络和采纳状态计算
  - 全局Q（s₉）- 从所有农户质量计算

---

### 3. 数据计算方式

#### 基线模型
```python
# 直接使用原始字段进行计算
S_policy = subsidy * perception * (1 + training * 0.2)
S_social = neighbor_adoption_rate * social_value_base
C_cost = cost_green - subsidy
Q_benefit = Q_normalized * quality_value_base

U_i = θ_p·S_policy + θ_s·S_social - θ_e·C_cost + θ_q·Q_benefit
```

**特点：**
- 字段值**直接参与**TPB效用计算
- 计算过程**透明**（理论公式）
- 不需要数据预处理

#### 强化学习
```python
# 转换为状态向量
state = [
    economic_level / 100000,      # 归一化
    degree / max_degree,          # 计算社会影响力
    policy_perception,             # 直接使用
    risk_tolerance,                # 直接使用
    fertility,                     # 直接使用
    soil_structure,                # 直接使用
    biological_activity,           # 直接使用
    mean(neighbors.adoption_state), # 计算邻居采纳率
    global_Q,                      # 计算全局质量
    myopia,                        # 直接使用
    education_priority,             # 直接使用
    political_voice                # 直接使用
]

# 输入到DQN网络
Q(s, a) = DQN_network(state)
```

**特点：**
- 字段值**转换为**状态向量
- 计算过程**黑盒**（神经网络）
- 需要数据预处理（归一化）

---

## 📈 详细对比表

### 字段使用对比

| 字段名 | 基线模型（TPB） | 强化学习（DQN） | 差异 |
|--------|----------------|----------------|------|
| `economic_level` | ✅ 直接使用 | ✅ 归一化后使用（s₁） | 需要归一化 |
| `policy_perception` | ✅ 直接使用 | ✅ 直接使用（s₃） | 相同 |
| `risk_tolerance` | ⚠️ 间接使用 | ✅ 直接使用（s₄） | RL更直接 |
| `fertility` | ✅ 直接使用 | ✅ 直接使用（s₅） | 相同 |
| `soil_structure` | ✅ 直接使用 | ✅ 直接使用（s₆） | 相同 |
| `biological_activity` | ✅ 直接使用 | ✅ 直接使用（s₇） | 相同 |
| `myopia` | ❌ 未直接使用 | ✅ 直接使用（s₁₀） | RL使用 |
| `education_priority` | ❌ 未直接使用 | ✅ 直接使用（s₁₁） | RL使用 |
| `political_voice` | ❌ 未直接使用 | ✅ 直接使用（s₁₂） | RL使用 |
| **社会影响力** | ⚠️ 间接使用 | ✅ 计算得到（s₂） | RL显式使用 |
| **邻居采纳率** | ✅ 直接使用 | ✅ 计算得到（s₈） | 相同 |
| **全局Q** | ✅ 直接使用 | ✅ 计算得到（s₉） | 相同 |

---

## 💡 关键理解

### 1. 数据来源相同

**两者使用相同的 `farmer_df`：**
```python
# 基线模型
farmer_df = generator.generate_farmer_attributes()

# 强化学习
farmer_df = generator.generate_farmer_attributes()  # 相同的生成器
```

**结论：** ✅ 数据来源**完全相同**

---

### 2. 使用方式不同

#### 基线模型
- **直接使用**原始字段
- 字段值**直接参与**TPB效用计算
- 不需要数据转换

#### 强化学习
- **转换为**12维状态向量
- 字段值**输入到**DQN网络
- 需要数据预处理（归一化、计算衍生值）

---

### 3. 包含的信息不同

#### 基线模型
- 使用**部分字段**（约8-10个）
- 字段值**直接计算**效用
- 不包含**显式的社会影响力**（间接通过邻居采纳率体现）

#### 强化学习
- 使用**更多字段**（12个维度）
- 包含**显式的社会影响力**（度中心性）
- 包含**短视性、教育优先权、话语权**（三个新维度）

---

## 🎯 总结

### 核心差异

| 对比项 | 基线模型（TPB） | 强化学习（DQN） |
|--------|----------------|----------------|
| **数据来源** | ✅ 相同（`farmer_df`） | ✅ 相同（`farmer_df`） |
| **数据格式** | DataFrame（多列） | NumPy数组（12维） |
| **使用方式** | 直接使用原始字段 | 转换为状态向量 |
| **字段数量** | 约8-10个字段 | 12个维度 |
| **数据预处理** | ❌ 不需要 | ✅ 需要（归一化、计算） |
| **包含信息** | 部分字段 | 更多字段（包含新维度） |

---

### 一句话总结

> **数据来源相同**（都是 `farmer_df`），但**使用方式不同**：
> - **基线模型**：直接使用原始字段，通过TPB效用函数计算
> - **强化学习**：转换为12维状态向量，输入到DQN网络
> 
> 强化学习包含**更多信息**（社会影响力、短视性、教育优先权、话语权），并且需要**数据预处理**（归一化、计算衍生值）。

---

## 📝 代码位置

### 基线模型
- **数据生成：** `run_experiment.py` 第43-44行
- **数据使用：** `src/dynamics.py` 第219-294行（`compute_utility_tpb`）

### 强化学习
- **数据生成：** `run_experiment.py` 第180-181行
- **数据转换：** `src/rl_agent.py` 第107-164行（`get_state_vector`）
- **数据使用：** `src/rl_agent.py` 第166-176行（`select_action`）

