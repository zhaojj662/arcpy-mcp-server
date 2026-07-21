# 第8章 大语言模型与空间分析基础

> **4学时（>80分钟） | 对应视频课 L1-L7**
> 
> **前置章节：** 第1-7章（传统GIS空间分析基础）
> 
> **核心服务：** arcpy-mcp-server v2.0（1300+ ArcGIS Pro 工具通过 MCP 协议暴露）

---

## 8.0 arcpy-mcp-server 环境搭建 ※

> ⏱ 预计时间：30分钟
> 
> 本节是全部后续实操的基础。arcpy-mcp-server 是你本地运行的服务，LLM 通过它调用 ArcGIS Pro 的全部工具。

### 8.0.1 前置条件检查

| 条件 | 如何确认 | 备注 |
|------|---------|------|
| Windows 10/11 | Win+R → `winver` | 必修 |
| ArcGIS Pro 3.x | 开始菜单 → ArcGIS Pro | 需有合法授权（高校 Site License 即可） |
| Python 3.9+ | 终端运行 `python --version` | 系统 Python 即可，不需要 arcgispro-py3 环境 |

验证 ArcGIS Pro Python：

```powershell
& "C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" -c "import arcpy; print(arcpy.GetInstallInfo()['Version'])"
# 应输出: 3.0 / 3.1 / 3.2 / 3.3 / 3.4
```

### 8.0.2 安装 arcpy-mcp-server

```powershell
# Step 1: 克隆仓库
git clone https://github.com/zhaojj662/arcpy-mcp-server.git
cd arcpy-mcp-server

# Step 2: 一键安装（安装 openai 等客户端依赖）
install.bat

# Step 3: 启动后台服务
start_server.bat
```

运行后看到 `arcpy-mcp-server v2.0 running on http://127.0.0.1:8765` 即启动成功。

### 8.0.3 验证服务

新开一个终端窗口：

```powershell
# 健康检查
Invoke-RestMethod http://127.0.0.1:8765/health
```

预期输出：

```json
{"status":"ok","server":"arcpy-mcp-server","version":"2.0","tools":1300,"modules":15}
```

```powershell
# 查看所有可用模块
Invoke-RestMethod http://127.0.0.1:8765/modules
```

### 8.0.4 配置 AI 客户端（AutoClaw）

在 AutoClaw 的 MCP Server 管理界面添加：

| 字段 | 值 |
|------|-----|
| Server name | `arcpy` |
| 连接方式 | 本地进程 (stdio) |
| Command | `python` |
| Parameters | `C:\Users\你的用户名\arcpy-mcp-server\bridge\mcp_bridge.py` |

桥接脚本自动将 AutoClaw 的 stdio MCP 协议转发到 `http://127.0.0.1:8765` 的 arcpy 服务。

**配置完成后，AI 自动获得 1300+ GIS 工具的能力。**

### 8.0.5 架构总览

```
┌─────────────┐   stdio JSON-RPC   ┌──────────────┐   HTTP REST   ┌──────────────┐
│  AI 客户端    │◄──────────────────►│ mcp_bridge.py │◄─────────────►│  server.py   │
│  (AutoClaw)  │                    │  (Python 3)   │               │  (arcpy 3.9) │
└─────────────┘                    └──────────────┘               └──────┬───────┘
                                                                        │
                                                                  ┌─────▼──────┐
                                                                  │ ArcGIS Pro │
                                                                  │   3.x      │
                                                                  └────────────┘
```

**关键分离原因：** arcpy 只能运行在 ArcGIS Pro 自带的 Python 3.9 环境中，而 AI 客户端需要标准 MCP stdio 协议。桥接脚本负责两端的协议转换。

### 8.0.6 直接调用 arcpy 服务（不使用 AI 时）

即使不接 AI，也可以直接用 HTTP 调用测试 arcpy 工具：

```powershell
$body = '{"name":"analysis_Buffer","arguments":{"in_features":"C:/GIS-AI-Course/data/roads.shp","out_feature_class":"C:/GIS-AI-Course/results/roads_buf.shp","buffer_distance_or_field":"500 meters"}}'
Invoke-RestMethod -Uri "http://127.0.0.1:8765/call" -Method Post -Body $body -ContentType "application/json"
```

输出示例：

```json
{
  "status": "success",
  "tool": "analysis_Buffer",
  "info": {
    "output": "C:/GIS-AI-Course/results/roads_buf.shp",
    "feature_count": 12,
    "geometry_type": "Polygon",
    "execution_time_seconds": 0.83
  }
}
```

---

## 8.1 大语言模型技术概述 ※

**教学目标**
- 理解 LLM 基本原理与 Transformer 架构
- 掌握 GPT-4o / Claude / DeepSeek / GLM 的选型依据
- 了解 VLM 在 GIS 中的多模态应用
- 认识 LLM 的局限性及应对策略

### 8.1.1 Transformer 与自注意力机制

大语言模型的核心是 2017 年 Google 提出的 Transformer 架构。自注意力（Self-Attention）机制让模型在处理每个词时，同时关注输入序列中的所有其他词。

对于 GIS 场景，这意味着 LLM 能理解复杂的空间描述：

```
"从长春市中心沿人民大街向南5公里，在卫星路交汇处向东2公里，对路口做500米缓冲区"
```

LLM 需要同时关注"人民大街""向南5公里""卫星路""向东2公里""500米缓冲区"等关键信息，理解它们之间的空间拓扑关系——这正是自注意力机制的强项。

### 8.1.2 主流模型对比

| 模型 | 上下文窗口 | 中文能力 | 多模态 | Function Calling | 推荐场景 |
|------|-----------|---------|--------|-----------------|---------|
| GPT-4o | 128K | 优秀 | 支持 | 原生 | 复杂分析、多模态地图识别 |
| Claude 3.5 Sonnet | 200K | 优秀 | 支持 | 原生 | 长文档、大属性表 |
| DeepSeek-V3 | 128K | 优秀 | 纯文本 | 支持 | 低成本批量分析 |
| GLM-4 | 128K | 优秀 | 支持 | 支持 | 国内合规场景 |

### 8.1.3 三种应用范式

| 范式 | 方法 | GIS 场景举例 |
|------|------|------------|
| Zero-Shot | 直接提问，不给示例 | "什么是空间自相关？" |
| Few-Shot | 给 2-3 个示例再提问 | 示范两个 Buffer 分析后再问第三个 |
| 微调 Fine-Tuning | 用 arcpy 文档额外训练 | 让模型更准确理解 arcpy 参数规范 |

**配合 arcpy-mcp-server 时，LLM 自动进入 Function Calling 模式**——无须写示例，它直接读取 MCP Server 暴露的工具 Schema，知道每个工具的参数名称、类型、含义。

### 8.1.4 LLM 的局限与应对

| 局限 | 表现 | 应对（arcpy-mcp-server 内置） |
|------|------|------------------------------|
| 幻觉 | 编造不存在的坐标/地名 | 所有操作由 arcpy 实际执行，结果来自真实数据 |
| 空间推理偏差 | 判断点是否在多边形内不可靠 | `analysis_Intersect` / `analysis_Clip` 由 GIS 引擎精确计算 |
| 坐标精度损失 | 浮点运算不可靠 | arcpy 的精确数值计算 |
| 工具参数错误 | 格式不符合 arcpy 要求 | Server 返回 arcpy 原生错误信息，LLM 可自我修正 |

---

## 8.2 Prompt Engineering 与空间分析应用

**教学目标**
- 掌握 Prompt 设计原则
- 使用 5 种 GIS 场景 Prompt 模板
- 理解 Chain-of-Thought 在空间分析中的价值

### 8.2.1 Prompt 设计三原则

**原则一：角色 + 工具声明**

```
你是 GIS 空间分析助手。你可以调用 arcpy 工具完成以下操作：
- 缓冲区分析 (analysis_Buffer)
- 相交分析 (analysis_Intersect)
- 坡度分析 (ddd_Slope)
- 空间插值 (ga_Kriging, ga_Idw)
- 空间统计 (stats_SpatialAutocorrelation, stats_HotSpots)

所有分析必须通过工具调用执行，不要凭空生成结果。
```

**原则二：输出格式约束**

```
每次工具调用后，请以 JSON 格式报告：
{"step": N, "tool": "工具名", "result": "成功/失败", "details": "具体信息"}
```

**原则三：约束前置**

```
注意事项：
- 所有文件路径使用 C:/GIS-AI-Course/data/ 或 C:/GIS-AI-Course/results/
- 距离单位默认米（meters）
- 工具参数严格遵循 arcpy 规范
```

### 8.2.2 五大 GIS 场景 Prompt 模板

**模板一：缓冲区分析**

```
任务：对 [图层路径] 做 [距离] [单位] 缓冲区分析
工具：analysis_Buffer
参数：
  in_features = "[图层路径]"
  out_feature_class = "C:/GIS-AI-Course/results/[图层名]_buffer_[距离][单位].shp"
  buffer_distance_or_field = "[距离] [单位]"
```

**模板二：叠加分析**

```
任务：将 [图层A] 和 [图层B] 做相交分析
工具：analysis_Intersect
参数：
  in_features = ["[图层A]", "[图层B]"]
  out_feature_class = "C:/GIS-AI-Course/results/intersection.shp"
```

**模板三：空间插值**

```
任务：对 [采样点] 的 [字段] 做 Kriging 插值
工具：ga_Kriging
参数：
  in_features = "[采样点]"
  z_field = "[字段]"
  out_surface_raster = "C:/GIS-AI-Course/results/kriging_result.tif"
```

**模板四：地统计分析**

```
任务：分析 [数据] 的 [字段] 空间自相关性
工具：stats_SpatialAutocorrelation
参数：
  Input_Feature_Class = "[数据]"
  Input_Field = "[字段]"
  Conceptualization_of_Spatial_Relationships = "FIXED_DISTANCE_BAND"
```

**模板五：选址分析（复合）**

```
任务：找适合建 [设施] 的区域
约束：
1. 离 [道路] ≤ [距离A] → analysis_Buffer
2. 离 [居民区] ≤ [距离B] → analysis_Buffer
3. 坡度 < [角度] → ddd_Slope → sa_Reclassify
4. 上述条件取交集 → analysis_Intersect

请按顺序执行每个步骤。
```

### 8.2.3 配合 arcpy-mcp-server 的 Chain-of-Thought

当 AI 通过 MCP 连接 arcpy-mcp-server 后，CoT 由 LLM 在 Function Calling 时自动触发：

```
用户输入：对东北师范大学做 500 米缓冲区

LLM 内部 CoT：
  1. 识别为缓冲区分析任务
  2. 需要知道东北师范大学的位置 → 检查数据目录
  3. 发现已有 nenu.shp（包含东北师范大学坐标）
  4. 调用 analysis_Buffer(in_features="C:/GIS-AI-Course/data/nenu.shp",
     out_feature_class="C:/GIS-AI-Course/results/nenu_buffer_500m.shp",
     buffer_distance_or_field="500 meters")
  5. Server 返回成功 → 向用户报告结果
```

---

## 8.3 MCP 协议与 GIS 工具链集成 ※

**教学目标**
- 理解 MCP 三层架构
- 掌握 arcpy-mcp-server 的工具调用方式
- 理解为何 MCP 优于直接 Function Calling

### 8.3.1 为什么 GIS 需要 MCP

传统问题：LLM 只能"说"，不能"做"。MCP 让 LLM 能调动真实世界的 GIS 引擎。

| 方案 | 流程 | 问题 |
|------|------|------|
| LLM 生成代码 | 用户复制代码 → 手动运行 | 代码可能有 bug，LLM 看不到结果 |
| 直接 Function Calling | LLM → API | 各模型 API 格式不同，工具管理分散 |
| **MCP (arcpy-mcp-server)** | LLM → MCP → arcpy | 统一标准，即插即用，1300+ 工具自动注册 |

### 8.3.2 MCP 工具调用流程（基于 arcpy-mcp-server）

```
1. AI 客户端启动 → 通过 stdio 连接 mcp_bridge.py
2. mcp_bridge.py → HTTP GET /tools → 获取 1300+ 工具列表
3. 用户说"做缓冲区分析" → LLM 从工具列表中匹配 analysis_Buffer
4. LLM 生成 JSON 调用参数
5. mcp_bridge.py → HTTP POST /call → server.py → arcpy → ArcGIS Pro
6. 结果原路返回 → LLM 解读 → 展示给用户
```

### 8.3.3 arcpy-mcp-server 支持的全部模块

| 模块 | 工具数 | 代表性工具 |
|------|--------|-----------|
| analysis | 38 | Buffer, Clip, Intersect, Erase, Union, Thiessen |
| management | 392 | Project, AddField, CalculateField, CreateFeatureclass |
| sa (Spatial Analyst) | 355 | Slope, Aspect, Reclassify, Viewshed, KernelDensity |
| ddd (3D Analyst) | 144 | Slope_3d, Aspect, Contour, Viewshed2, LineOfSight |
| ga (Geostatistical) | 39 | Kriging, Idw, EBK, CrossValidation |
| stats (空间统计) | 44 | SpatialAutocorrelation, HotSpots, ClustersOutliers |
| conversion | 57 | FeatureClassToFeatureClass, JSONToFeatures, KMLToLayer |
| geocoding | 13 | GeocodeAddresses, ReverseGeocode |
| stpm (时空模式) | 16 | CreateSpaceTimeCube, EmergingHotSpotAnalysis |
| cartography | 44 | AggregatePoints, AggregatePolygons, ContourAnnotation |
| nax (Network Analyst) | 61 | Route, ServiceArea, ClosestFacility |
| na | 55 | MakeRouteLayer, MakeServiceAreaLayer |
| edit | 18 | Align, Extend, Trim, Split, Merge |
| server | 18 | CreateMapService, ManageTileCache |
| sharing | 6 | ShareAsWebLayer, ShareAsWebMap |

---

## 8.4 AI 驱动缓冲区分析实战

**教学目标**
- 通过 arcpy-mcp-server 完成首个 AI 驱动的空间分析
- 理解从自然语言到 GIS 执行结果的完整链路

### 8.4.1 创建测试数据

```powershell
# 通过 arcpy-mcp-server 创建点要素（LLM 可以代劳）
```

AI 对话中：

```
"在 C:/GIS-AI-Course/data/ 下创建一个点要素 test_points.shp，
包含三个点：长春市中心(125.32, 43.88)、
净月潭(125.45, 43.79)、南湖公园(125.30, 43.85)"
```

LLM 自动调用 `management_CreateFeatureclass` + `management_AddField` + 插入数据。

### 8.4.2 发起分析

```
"对 test_points.shp 做 500 米缓冲区分析"
```

LLM 自动执行：

```json
POST /call
{
  "name": "analysis_Buffer",
  "arguments": {
    "in_features": "C:/GIS-AI-Course/data/test_points.shp",
    "out_feature_class": "C:/GIS-AI-Course/results/test_buffer.shp",
    "buffer_distance_or_field": "500 meters"
  }
}
```

### 8.4.3 验证结果

在 ArcGIS Pro 中打开 `C:/GIS-AI-Course/results/test_buffer.shp`，确认 3 个缓冲区多边形已正确生成。

### 8.4.4 错误处理演示

```
"对 nonexistent.shp 做缓冲区"
```

LLM 调用后 arcpy-mcp-server 返回：

```json
{"status":"error","message":"ERROR 000732: Dataset nonexistent.shp does not exist","suggestion":"Dataset not found"}
```

LLM 读取错误信息后回复：

```
"数据集 nonexistent.shp 不存在。当前 C:/GIS-AI-Course/data/ 目录中有：
  - test_points.shp
  - nenu.shp
请问你想对哪个文件做分析？"
```

---

## 课堂练习

1. 搭建 arcpy-mcp-server 并完成健康检查
2. 用自然语言指令完成一个缓冲区分析
3. 故意输入错误路径，观察 LLM 的自动纠错过程
4. 查看 `/modules` 和 `/tools` 端点，熟悉可用工具

---


# 第9章 智能空间分析系统构建

> **4学时（>80分钟） | 对应视频课 L8-L16**
>
> **前置：** 第8章（arcpy-mcp-server 已部署并运行）

---

## 9.1 智能工作流引擎

**教学目标**
- 理解 Analysis Chain（Plan → Execute → Observe → Reflect）
- 掌握复合空间分析的自动编排
- 了解 NL2SQL 空间查询

### 9.1.1 Analysis Chain 四步循环

```
Plan:   LLM 拆解用户需求 → 确定需要的工具及执行顺序
Execute: 通过 arcpy-mcp-server 依次调用工具
Observe: 检查每个工具的返回结果
Reflect: 如果失败，分析原因并尝试修正
```

**实际案例（选址分析）**：

```
用户："找适合建医院的区域，离主干道500m内，离居民区1000m内，坡度<5°"

Plan:
  Step 1: analysis_Buffer(roads, roads_buf.shp, "500 meters")
  Step 2: analysis_Buffer(residential, res_buf.shp, "1000 meters")
  Step 3: ddd_Slope(dem.tif, slope.tif)
  Step 4: sa_Reclassify(slope.tif, slope_reclass.tif)
  Step 5: analysis_Intersect([roads_buf, res_buf, slope_reclass], candidates.shp)

Execute: LLM 顺序调用每个工具
Observe: 检查每步返回 {"status":"success"}
Reflect: 如果某步失败（如坐标系不一致），自动插入 management_Project
```

### 9.1.2 中间结果管理

arcpy-mcp-server 自动管理中间数据：

```python
# 所有输出统一写入 results 目录
C:/GIS-AI-Course/results/
  step1_buffer_road.shp
  step2_buffer_res.shp
  step3_slope.tif
  step4_slope_reclass.tif
  final_candidates.shp
```

### 9.1.3 对话式空间查询

通过 geocoding 模块，LLM 可以直接处理地址查询：

```
"地理编码：长春市人民大街5268号"
→ geocoding_GeocodeAddresses → 返回坐标 (125.318, 43.858)

"反向地理编码：(125.326, 43.858) 是什么地方？"
→ geocoding_ReverseGeocode → "东北师范大学"
```

---

## 9.2 AI 驱动的选址分析与空间插值 ※

**教学目标**
- 通过选址分析掌握多工具编排
- 通过空间插值理解 AI 自动方法选择

### 9.2.1 案例一：智能选址分析

**需求**：
```
在长春市找适合建医院的区域：
- 离主干道 ≤ 500m
- 离居民区 ≤ 1000m
- 坡度 < 5°
- 面积 > 2 公顷
```

**LLM 自动执行的完整链路**（通过 arcpy-mcp-server）：

```
Step 1: analysis_Buffer
  in_features = "C:/GIS-AI-Course/data/cc_roads_major.shp"
  out_feature_class = "C:/GIS-AI-Course/results/s1_road_buf.shp"
  buffer_distance_or_field = "500 meters"

Step 2: analysis_Buffer
  in_features = "C:/GIS-AI-Course/data/cc_residential.shp"
  out_feature_class = "C:/GIS-AI-Course/results/s2_res_buf.shp"
  buffer_distance_or_field = "1000 meters"

Step 3: ddd_Slope
  in_raster = "C:/GIS-AI-Course/data/cc_dem_30m.tif"
  out_raster = "C:/GIS-AI-Course/results/s3_slope.tif"

Step 4: sa_Reclassify
  in_raster = "C:/GIS-AI-Course/results/s3_slope.tif"
  remap = "0 5 1;5 90 0"
  out_raster = "C:/GIS-AI-Course/results/s4_slope_reclass.tif"

Step 5: analysis_Intersect
  in_features = ["s1_road_buf.shp", "s2_res_buf.shp"]
  out_feature_class = "C:/GIS-AI-Course/results/s5_candidates.shp"

Step 6: 筛选面积 > 2ha
  management_AddField(添加 Area_ha 字段)
  management_CalculateField(计算面积)
  analysis_Select(筛选 Area_ha > 2)
```

**LLM 生成的选址报告**：

```
选址分析完成。总候选区域 8 个，总面积约 47.3 公顷。
Top 3 推荐：
1. 南关区南部新城地块（12.5 公顷）
2. 朝阳区红旗街东侧（8.2 公顷）
3. 净月区大学城北侧（6.8 公顷）
```

### 9.2.2 案例二：智能空间插值

**需求**：
```
对 air_quality.shp 的 PM25 字段做空间插值，自动选择最优方法
```

**LLM 的自动方法选择逻辑**：

```
Step 1: 数据探查
  management_GetCount → 确认采样点数量
  stats 统计分析 → 检查数据分布（正态/偏态）

Step 2: 方法决策
  采样点 ≥ 30 且正态分布 → ga_Kriging
  采样点 < 30 → ga_Idw (power=2)
  需要光滑表面 → sa_Spline

Step 3: 执行插值
  POST /call {"name":"ga_Kriging","arguments":{...}}

Step 4: 交叉验证
  ga_CrossValidation → 获取 RMSE

Step 5: 对比方法（可选）
  同时执行 ga_Idw → 对比 RMSE → 告知用户哪种方法更优
```

**LLM 的方法对比输出**：

```
Kriging RMSE: 3.42 μg/m³
IDW RMSE:    4.15 μg/m³

Kriging 误差更低（-17.6%），且提供了插值方差估计。
建议采用 Kriging 结果。IDW 的局部极值保留更好，
若关注局部高污染热点，可参考 IDW 结果。
```

---

## 9.3 AI 驱动的地统计与三维可视域 ※

**教学目标**
- 通过地统计案例掌握完整空间统计工作流
- 通过三维可视域案例理解批量三维分析

### 9.3.1 案例三：智能地统计分析

**需求**：
```
分析 crime_points.shp 的犯罪热点空间分布
```

**LLM 通过 arcpy-mcp-server 自动执行**：

```
Step 1: stats_SpatialAutocorrelation（全局 Moran's I）
  Input_Feature_Class = crime_points.shp
  Input_Field = Incident_C
  → 输出 Moran's I = 0.342, Z = 5.67, p < 0.001
  → 结论：显著空间聚集

Step 2: stats_HotSpots（Getis-Ord Gi*）
  Input_Feature_Class = crime_points.shp
  Input_Field = Incident_C
  Output_Feature_Class = hotspot.shp
  → 15 个热点（99%置信）, 8 个冷点

Step 3: stats_ClustersOutliers（Anselin Local Moran's I）
  → 12 个高-高聚类, 2 个高-低异常值

Step 4: sa_KernelDensity（核密度估计）
  → 输出密度栅格

Step 5: stats_IncrementalSpatialAutocorrelation（Ripley's K）
  → 聚集在 200-800m 和 1500-2500m 两个尺度最显著
```

**LLM 自动生成的地统计报告**：

```
犯罪热点分析报告
━━━━━━━━━━━━━━━━━
全局 Moran's I = 0.342 (p < 0.001) → 显著空间聚集

热点区域 (99% 置信):
  - 重庆路商圈 (Gi_Z = 4.23)
  - 火车站周边 (Gi_Z = 3.87)
  - 桂林路夜市 (Gi_Z = 3.45)

多尺度特征:
  - 200-800m 尺度: 街道层面聚集
  - 1500-2500m 尺度: 区域层面聚集

建议: 在热点区域增派巡逻，高-低异常点专题调查
```

### 9.3.2 案例四：智能三维与可视域分析

**需求**：
```
基于 DEM 进行三维地形分析，找到视野最好的瞭望塔位置
```

**LLM 自动执行**：

```
Step 1: ddd_Slope（坡度）
  in_raster = dem.tif → out_raster = slope.tif

Step 2: ddd_Aspect（坡向）
  in_raster = dem.tif → out_raster = aspect.tif

Step 3: ddd_Contour（等高线，20m 间距）
  in_raster = dem.tif
  out_polyline_features = contours.shp
  contour_interval = 20

Step 4: 生成候选观测点网格
  management_CreateFishnet → 500m 间距网格
  management_FeatureToPoint → 提取中心点

Step 5: ddd_Viewshed2（批量视域分析）
  in_raster = dem.tif
  in_observer_features = observer_grid.shp
  out_raster = batch_viewshed.tif

Step 6: 分析结果 → 返回 TOP 3 最佳瞭望塔位置
```

**LLM 自动生成的结论**：

```
视域分析完成 (156 个候选视点)
━━━━━━━━━━━━━━━━━━━━━━━━━━
TOP 1: 观测点 #87 → 可视面积 67.2%
TOP 2: 观测点 #103 → 可视面积 64.8%
TOP 3: 观测点 #42 → 可视面积 63.1%

推荐在 #87 位置建设瞭望塔，可覆盖研究区 2/3 以上面积。
```

---

## 9.4 空间分析 AI Agent 构建

**教学目标**
- 理解 ReAct Agent 架构
- 掌握 arcpy-mcp-server 的工具注册与调用
- 能够构建完整的 AI 空间分析系统

### 9.4.1 ReAct Agent 架构

```
┌─────────────────────────────────────────┐
│              ReAct Agent                 │
│                                          │
│  Plan ──→ Execute ──→ Observe ──→ Reflect│
│    ↑                                    │
│    └──────────── 循环 ──────────────────┘ │
│                                          │
│  通过 arcpy-mcp-server 调用全部工具        │
└─────────────────────────────────────────┘
```

每个循环中：
1. **Plan**：LLM 分析当前状态，决定下一步调用哪个工具
2. **Execute**：通过 MCP → arcpy-mcp-server 执行工具
3. **Observe**：检查返回结果（成功/失败）
4. **Reflect**：如果失败，分析原因（如坐标系不一致），计划修正步骤

### 9.4.2 arcpy-mcp-server 工具自动注册

Agent 启动时自动调用 `/tools` 获取 1300+ 工具的 Schema：

```python
# Agent 伪代码
tools = http_get("/tools")  # 获取全部 1300+ 工具 Schema

# LLM 使用这些 Schema 做 Function Calling
response = llm.chat(
    messages=[{"role": "user", "content": "做缓冲区分析"}],
    tools=tools  # arcpy-mcp-server 提供的工具列表
)
```

### 9.4.3 异常处理与自我修复

arcpy-mcp-server 返回的 arcpy 错误会自动触发修复策略：

| 错误码 | 含义 | LLM 自动修复 |
|--------|------|------------|
| 000732 | 数据集不存在 | 检查 data 目录，建议可用文件 |
| 000725 | 输出已存在 | 自动切换 overwriteOutput 或重命名 |
| 000735 | 参数格式错误 | 从服务器 suggestion 字段读取修正建议 |
| 000210 | 无法创建输出 | 检查 output 目录，自动创建 |
| 000622 | 数据类型不匹配 | 调整参数类型 |

### 9.4.4 复合分析实战：一键选址

用户一句话，Agent 自动完成：

```
"帮我在长春市南部找一个适合建公园的区域"
```

Agent 自动规划并执行（无需人工干预）：

```
Plan:  选址分析 → 需要道路、居民区、DEM 数据
Execute:
  → analysis_Buffer × 2（道路 + 居民区缓冲区）
  → ddd_Slope（坡度）
  → sa_Reclassify（坡度重分类）
  → analysis_Intersect（多图层相交）
  → management_CalculateField（计算面积）
  → analysis_Select（面积筛选）
Observe: 全部步骤成功
Reflect: 无需修正

最终输出:
  候选区域 5 个
  TOP 1: 净月区南侧地块（8.3 公顷，坡度 2.1°）
  TOP 2: 南关区南部新城（6.7 公顷，坡度 3.5°）
```

---

## 课堂练习

1. 使用 arcpy-mcp-server 完成选址分析的 6 个步骤
2. 对给定的气象站数据，分别执行 IDW 和 Kriging 插值并对比
3. 用自然语言指令完成一个包含 5 步以上的复合分析
4. 故意制造路径错误，观察 Agent 的自我修复过程

---

## 课程总结

通过第 8-9 章，学员应掌握：

<div class="rich-metrics">
<div class="rich-metric"><strong>环境部署</strong><br>arcpy-mcp-server 安装与配置</div>
<div class="rich-metric"><strong>LLM 基础</strong><br>Transformer/Prompt/MCP 原理</div>
<div class="rich-metric"><strong>1300+ 工具</strong><br>15 个模块全部可用</div>
<div class="rich-metric"><strong>4 大实战</strong><br>选址·插值·地统计·三维</div>
</div>

**进一步学习方向**：
- GeoLLM（地理空间大模型）前沿进展
- 多 Agent 协作空间分析
- ArcGIS Notebooks 云端分析
- 实时传感器数据 + AI 空间分析

---

## 附录：课程与 arcpy-mcp-server 绑定关系

| 课程内容 | 使用的 arcpy-mcp-server 端点 | 涉及模块 |
|---------|---------------------------|---------|
| 服务安装验证 | GET /health | - |
| 工具发现 | GET /tools, GET /modules | 全部 |
| 缓冲区分析 | POST /call (analysis_Buffer) | analysis |
| 选址分析 | POST /call × 6 | analysis, ddd, sa, management |
| 空间插值 | POST /call (ga_Kriging, ga_Idw) | ga |
| 地统计 | POST /call (stats_*) | stats, sa |
| 三维分析 | POST /call (ddd_*) | ddd, management |
| 地理编码 | POST /call (geocoding_*) | geocoding |
| 数据管理 | POST /call (management_*) | management |

**所有案例均基于 arcpy-mcp-server v2.0 的 HTTP REST API，可直接运行验证。**
