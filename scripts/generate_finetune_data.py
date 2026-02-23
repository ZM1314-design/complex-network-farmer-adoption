import json
import random

def generate_dataset():
    data = []
    
    # 1. 核心数值结论（Model Specific Knowledge）
    knowledge_pairs = [
        {
            "instruction": "本研究中识别出的政策补贴临界阈值是多少？",
            "output": "在现实校准的补贴区间（0-500元/亩）内，政策补贴呈现S型非线性特征。Sigmoid拟合得到的连续临界点约为 483.4 元/亩，而逾渗意义上的结构临界点约为 485 元/亩。"
        },
        {
            "instruction": "在现实基线情景下（补贴105元/亩），系统的演化结果如何？",
            "output": "在现实平均补贴（105元/亩）下，由于远低于临界阈值，单一补贴工具无法触发系统级扩散。系统会迅速陷入“低采纳—低质量锁定（lock-in trap）”，终态采纳率收敛至0，耕地质量也衰减至0。"
        },
        {
            "instruction": "强化学习（DQN）策略相比传统基线模型有何优势？",
            "output": "在相同的现实补贴约束下，DQN通过多智能体协作学习，成功跨越了低采纳陷阱。实验显示，RL策略的终态采纳率达到约 94.33%，平均奖励约 47.89，且将全局耕地质量推向 1.0，显著优于基线。"
        },
        {
            "instruction": "网络结构对绿色施肥技术扩散有什么影响？",
            "output": "研究发现网络具有显著的异质性。Hub节点（高度中心性）和桥接节点（高介数中心性）具有结构性杠杆效应。对这些关键节点进行定向干预（如培训或声誉激励），比平均化补贴具有更高的系统效率。"
        }
    ]
    
    # 2. 场景推演（Simulation Logic）
    # 生成一些基于论文逻辑的合成问答
    scenarios = [
        ("补贴300元", "低于临界点483.4元，预计采纳率较低，系统可能无法突破锁定。"),
        ("补贴550元", "高于临界点483.4元，位于高效区，预计能触发系统级扩散，实现高采纳率。"),
        ("仅有技术培训", "虽然成本效益比最高（1.42），但单靠培训可能难以在大范围引发质变，建议与补贴组合使用。"),
        ("组合政策（补贴+声誉）", "存在显著的协同效应（Synergy），能在较低财政成本下实现比单一高补贴更好的扩散效果。")
    ]
    
    for cond, res in scenarios:
        knowledge_pairs.append({
            "instruction": f"如果在仿真中采用{cond}，预期结果会怎样？",
            "output": f"根据双曲几何网络模型的实验结论：{res}"
        })

    # 3. 基础定义（Domain Knowledge）
    definitions = [
        ("TPB模型", "计划行为理论（TPB）包含态度、主观规范（社会影响）和感知行为控制（成本/技术门槛），本研究用其构建农户的效用函数。"),
        ("双曲几何网络", "用于模拟农户社交网络，能同时重现真实网络的无标度特性（度分布）和高聚集特性（社区结构）。")
    ]
    
    for term, desc in definitions:
        knowledge_pairs.append({
            "instruction": f"请解释本研究中的{term}是什么？",
            "output": desc
        })
        
    # 格式化为通用的 Instruction Tuning 格式
    formatted_data = []
    for item in knowledge_pairs:
        # 增加一些多样性模板
        formatted_data.append({
            "instruction": item["instruction"],
            "input": "",
            "output": item["output"]
        })

    # 写入文件
    with open('complex_network_thesis_dataset.jsonl', 'w', encoding='utf-8') as f:
        for entry in formatted_data:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
            
    print(f"成功生成数据集：complex_network_thesis_dataset.jsonl，共 {len(formatted_data)} 条数据")

if __name__ == "__main__":
    generate_dataset()
