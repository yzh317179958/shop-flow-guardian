# Fiido 专业级客服坐席工作台 - 开发周期文档

> **文档编号**: ENTERPRISE-WORKBENCH-LIFECYCLE
> **文档版本**: v2.0 🔄 **闭环架构优化版**
> **优先级**: P0（企业级基础设施）
> **状态**: 📋 规划中
> **创建时间**: 2025-12-02
> **最后更新**: 2025-12-02
> **核心理念**: **客户-AI客服-后端-坐席工作台 四位一体闭环设计**

---

## 📋 目录

1. [概述与目标](#1-概述与目标)
   - 1.1 业务背景
   - 1.2 项目现状（v3.4.0）
   - 1.3 标杆参考
   - **⭐ 1.4 闭环业务流程核心理念**
2. [当前系统分析](#2-当前系统分析)
3. [标杆对比与差距](#3-标杆对比与差距)
4. [开发周期规划](#4-开发周期规划)
5. [技术架构设计](#5-技术架构设计)
   - **⭐ 5.1 闭环架构设计**
   - 5.2 系统架构图
   - 5.3 核心模块设计
   - **⭐ 5.4 数据流与事件流**
6. [数据与权限设计](#6-数据与权限设计)
7. [后续建议](#7-后续建议)

---

## 1. 概述与目标

### 1.1 业务背景

Fiido是跨境电商独立站，客服系统需要覆盖:

- **多渠道**: 在线聊天、邮件工单、电话记录、社交媒体
- **多场景**: 售前咨询、售后工单、SLA追踪、跨语言沟通
- **多角色**: 普通坐席、技术支持、主管、VIP专员
- **合规要求**: 存证归档、数据可视化、审计日志

### 1.2 项目现状（v3.4.0）

**已完成功能**（L1-2-Part1 工单核心）:
- ✅ 基础工单生命周期（创建→处理→解决→关闭→重开）
- ✅ 手动创建工单（`/api/tickets/manual`）
- ✅ 工单分配/转派（`/api/tickets/{id}/assign`）
- ✅ SLA 监控（`/api/tickets/sla-summary`, `/api/tickets/sla-alerts`）
- ✅ 搜索筛选（关键词、多维度筛选）
- ✅ 导出 CSV（`/api/tickets/export`）

**待开发功能**（缺口分析）:
- ❌ 智能分配算法（技能匹配、负载均衡）
- ❌ 批量操作（批量分配、批量关闭）
- ❌ 工单模板（快速创建常见工单）
- ❌ 导出 Excel/PDF（多格式报表）
- ❌ 内部协作功能（评论、@提醒、附件共享）
- ❌ 自动化规则（自动分配、自动回复、工作流）
- ❌ SLA 可视化面板（实时监控、趋势图表）
- ❌ 权限矩阵强化（分层审核、操作日志）

### 1.3 标杆参考

从**聚水潭、拼多多坐席工作台**等专业产品中提炼的共性规律:

**设计理念**:
1. **全链路视图 + 实时监控面板**: 同时显示队列、SLA、工单趋势
2. **自动化策略 + 权限矩阵**: 按技能/负载自动派单、分层审核与日志
3. **多数据出口**: 导出多格式、API/BI、自动报表
4. **异常预警与回溯**: SLA超时、情绪预警、操作审计
5. **增量迭代原则**: 功能拆分为可验证子任务，每步不破坏既有流程

### ⭐ 1.4 闭环业务流程核心理念

**核心原则**: 系统不是独立组件的组合，而是 **客户-AI客服-后端-坐席工作台** 四位一体的闭环业务流程。

#### 1.4.1 闭环流程设计哲学

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  传统设计 ❌                  闭环设计 ✅                     │
│  ┌──────┐                    ┌──────────────────────┐       │
│  │ 客户 │                    │                      │       │
│  └──┬───┘                    │   客户 ←─────┐       │       │
│     │                        │    ↓         │       │       │
│  ┌──▼────┐                   │  AI客服 ─────┤       │       │
│  │AI客服 │                   │    ↓         │       │       │
│  └──┬────┘                   │   后端 ──────┤       │       │
│     │                        │    ↓         │       │       │
│  ┌──▼────┐                   │ 坐席工作台 ──┘       │       │
│  │ 后端  │                   │                      │       │
│  └──┬────┘                   │  实时双向事件流       │       │
│     │                        │  统一状态管理         │       │
│  ┌──▼──────┐                 │  端到端追踪          │       │
│  │坐席工作台│                 └──────────────────────┘       │
│  └─────────┘                                                │
│                                                              │
│  问题：单向、割裂、延迟        优势：闭环、实时、一致         │
└──────────────────────────────────────────────────────────────┘
```

#### 1.4.2 完整用户旅程示例

**场景: 客户咨询 → AI处理 → 人工升级 → 解决问题**

```
┌─────────────────────────────────────────────────────────────┐
│ 阶段1: 客户发起咨询                                          │
├─────────────────────────────────────────────────────────────┤
│ 客户端 (Vue)       → 发送消息 "我的电池续航只有20公里"       │
│ 后端 (backend.py)  → POST /api/chat (携带 session_name)     │
│ Coze API          → AI 分析并回复                            │
│ 客户端            ← SSE 流式接收 AI 回复                      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 阶段2: AI 判断需要人工介入                                   │
├─────────────────────────────────────────────────────────────┤
│ 后端 (regulator.py) → 检测关键词"电池"/"续航"触发升级         │
│ 后端 (session_state.py) → 状态: bot_active → pending_manual │
│ 后端 (smart_assignment.py) → 智能分配:                      │
│   - 获取在线坐席列表                                          │
│   - 技能匹配("电池专家"标签)                                  │
│   - 负载均衡(选择当前工单数最少坐席)                          │
│   - 历史服务记录(优先分配给之前服务过的坐席)                  │
│ 后端 → 创建会话工单: POST /api/sessions/{id}/ticket         │
│ 坐席工作台 ← SSE 推送通知: 新会话待接入                       │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 阶段3: 坐席接入处理                                          │
├─────────────────────────────────────────────────────────────┤
│ 坐席工作台 → 点击"接入会话"按钮                               │
│ 后端 ← PUT /api/sessions/{id}/assign (分配坐席)             │
│ 后端 (session_state.py) → 状态: pending_manual → manual_live│
│ 后端 → SSE 推送到客户端: "坐席正在接入..."                    │
│ 客户端 ← 显示"人工客服【李客服】为您服务"                      │
│ 坐席工作台 ← 加载完整会话历史 + 客户画像                       │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 阶段4: 双向实时通信                                          │
├─────────────────────────────────────────────────────────────┤
│ 坐席工作台 → 发送消息"请问您充电时是否充满?"                  │
│ 后端 ← POST /api/manual/messages                            │
│ 后端 → SSE 推送到客户端(延迟 < 100ms)                        │
│ 客户端 → 回复"充满了，但续航还是很短"                          │
│ 后端 ← POST /api/chat (manual_live 状态下直接转发)          │
│ 坐席工作台 ← SSE 推送客户回复(延迟 < 100ms)                  │
│                                                              │
│ [关键]: 双向 SSE 事件流保证实时性                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 阶段5: 工单处理与SLA追踪                                     │
├─────────────────────────────────────────────────────────────┤
│ 坐席工作台 → 添加内部备注"@王技术 需要现场检测"               │
│ 后端 ← POST /api/tickets/{id}/comments                      │
│ 后端 (automation_engine.py) → 检测 @提醒，推送通知            │
│ 坐席工作台(王技术) ← SSE 通知"李客服提到了你"                 │
│                                                              │
│ 后端 (sla_timer.py) → 实时计算剩余时效                       │
│   - 首次响应时效(FRT): 剩余 8分钟(目标10分钟)                 │
│   - 解决时效(RT): 剩余 6.5小时(目标8小时)                     │
│ 坐席工作台 ← SSE 推送 SLA 状态更新(每分钟)                    │
│ 坐席工作台 → 显示倒计时"⚠️ 剩余 8分钟需首次响应"              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 阶段6: 问题解决与闭环                                        │
├─────────────────────────────────────────────────────────────┤
│ 坐席工作台 → 标记工单"已解决"                                 │
│ 后端 ← PATCH /api/tickets/{id} (status: resolved)           │
│ 后端 (sla_timer.py) → 记录 resolved_at 时间戳                │
│ 后端 (audit_log.py) → 记录操作日志                           │
│ 后端 (automation_engine.py) → 触发自动回复规则:              │
│   "您的问题已解决，7天内未反馈将自动关闭"                      │
│ 客户端 ← SSE 推送公开回复                                     │
│                                                              │
│ 坐席工作台 → 点击"结束会话"                                   │
│ 后端 ← PUT /api/sessions/{id}/end                           │
│ 后端 (session_state.py) → 状态: manual_live → bot_active    │
│ 客户端 ← SSE 推送"会话已结束，AI客服继续为您服务"              │
│                                                              │
│ [闭环完成]: 客户问题解决，工单归档，AI恢复服务                  │
└─────────────────────────────────────────────────────────────┘
```

#### 1.4.3 闭环设计的三大支柱

**支柱1: 统一状态管理**

所有组件共享同一份会话状态(`session_state`)，任何变更实时同步:

```python
# 后端 (src/session_state.py) - 状态真实来源
class SessionState:
    session_name: str
    status: SessionStatus          # bot_active | pending_manual | manual_live
    assigned_agent: str | None     # 当前处理坐席
    customer_email: str
    conversation_id: str           # Coze 会话ID
    ticket_id: str | None          # 关联工单ID
    tags: List[str]                # 会话标签
    sla_status: SLAStatus          # SLA状态

# 状态变更时，通过 SSE 同步到:
# - 客户端 (显示"人工接入中"/"AI服务中")
# - 坐席工作台 (会话列表实时更新)
# - SLA 监控面板 (实时倒计时)
```

**支柱2: 事件驱动通信**

所有关键操作触发 SSE 事件，实现组件间解耦:

```python
# 事件类型定义
SSE_EVENTS = {
    # 客户端事件
    "ai_message": "AI回复消息",
    "manual_message": "人工回复消息",
    "status_change": "会话状态变更",
    "agent_typing": "坐席正在输入",

    # 坐席工作台事件
    "new_session": "新会话待接入",
    "session_assigned": "会话已分配",
    "customer_replied": "客户回复",
    "sla_alert": "SLA超时预警",
    "mention_notification": "@提醒通知",
    "ticket_updated": "工单更新",
}
```

**支柱3: 端到端追踪**

每个用户请求从客户端到后端到AI到坐席工作台，全链路可追踪:

```python
# 请求追踪ID (在客户端发起时生成)
trace_id = f"{session_name}_{timestamp}_{uuid4()}"

# 贯穿整个调用链
logger.info(f"[{trace_id}] 客户发送消息: {message}")
logger.info(f"[{trace_id}] 调用 Coze API")
logger.info(f"[{trace_id}] AI 回复完成，耗时 {duration}s")
logger.info(f"[{trace_id}] 触发人工升级规则")
logger.info(f"[{trace_id}] 分配给坐席: {agent_id}")
logger.info(f"[{trace_id}] 坐席接入成功")
```

#### 1.4.4 闭环设计对开发的指导

**指导原则1: 前后端同步开发**

每个功能增量必须同时考虑前后端实现:

```
❌ 错误方式:
增量1-1: 开发后端智能分配API
增量1-2: 开发前端调用智能分配API

✅ 正确方式:
增量1-1: 智能分配闭环实现
  - 后端: smart_assignment.py 算法 + /api/sessions/{id}/assign
  - 后端: SSE 推送"新会话"事件到坐席工作台
  - 前端: Dashboard.vue 接收 SSE，显示新会话通知
  - 前端: 点击"接入"按钮调用 assign API
  - 验证: 客户端看到"人工接入中"，坐席工作台显示会话详情
```

**指导原则2: 数据一致性优先**

任何数据变更，优先保证后端 Redis 状态正确，再通过 SSE 同步到前端:

```python
# ✅ 正确流程
@app.post("/api/tickets/{id}/assign")
async def assign_ticket(ticket_id: str, agent_id: str):
    # 1. 更新后端状态(真实来源)
    ticket = await ticket_store.get(ticket_id)
    ticket.assigned_to = agent_id
    ticket.status = "in_progress"
    await ticket_store.save(ticket)

    # 2. 推送 SSE 事件到前端
    await notify_agent(agent_id, {"type": "ticket_assigned", "ticket_id": ticket_id})

    # 3. 前端接收 SSE，自动刷新工单列表
```

**指导原则3: 失败自愈机制**

闭环设计要求任何环节失败不影响整体:

```python
# 示例: SSE 推送失败不影响业务逻辑
try:
    await sse_queues[session_name].put(event)
except Exception as e:
    logger.warning(f"SSE 推送失败: {e}")
    # 不阻塞主流程，客户端会通过定时刷新同步状态

# 示例: 智能分配失败，降级到手动分配
try:
    assigned_agent = await smart_assignment_engine.assign(session_name)
except Exception as e:
    logger.error(f"智能分配失败: {e}")
    # 降级: 通知所有在线坐席，等待手动接入
    await broadcast_to_agents({"type": "manual_assign_required"})
```

---

## 2. 当前系统分析

### 2.1 已有能力清单

| 功能模块 | 实现程度 | API端点 | 前端组件 | 备注 |
|---------|---------|---------|---------|------|
| 工单CRUD | ✅ 100% | `/api/tickets`, `/api/tickets/{id}` | `TicketList.vue` | 基础功能完整 |
| 状态流转 | ✅ 90% | `/api/tickets/{id}` PATCH | 状态机已实现 | 缺少自动流转 |
| 重开与归档 | ✅ 100% | `/api/tickets/{id}/reopen`, `/archive` | - | 已落地 |
| 手动创建 | ✅ 100% | `/api/tickets/manual` | `CreateTicket.vue` | 支持客户信息 |
| 从会话创建 | ✅ 100% | `/api/sessions/{id}/ticket` | `SessionDetail.vue` | 自动填充信息 |
| 分配/转派 | ✅ 100% | `/api/tickets/{id}/assign` | - | 手动分配 |
| 搜索 | ✅ 80% | `/api/tickets/search` | `TicketSearch.vue` | 关键词搜索 |
| 高级筛选 | ✅ 90% | `/api/tickets/filter` POST | `TicketFilter.vue` | 多维度组合 |
| CSV导出 | ✅ 100% | `/api/tickets/export` | - | 限制10000条 |
| SLA监控 | ✅ 70% | `/api/tickets/sla-summary`, `/sla-alerts` | - | 无可视化面板 |
| 评论系统 | ✅ 50% | `/api/tickets/{id}/comments` | - | 仅API，无UI |

**数据持久化**:
- Redis（TTL 30天）: 活跃工单
- 无长期存储: 归档工单需要数据库（MySQL/PostgreSQL）

### 2.2 核心缺口分析

#### 2.2.1 功能缺口

| 缺口类别 | 具体问题 | 业务影响 | 优先级 |
|---------|---------|---------|-------|
| **智能分配** | 手动分配效率低 | 响应时间慢50% | 🔴 P0 |
| **批量操作** | 无法批量处理工单 | 重复劳动多 | 🔴 P0 |
| **工单模板** | 创建重复工单耗时 | 效率低30% | 🟡 P1 |
| **多格式导出** | 只有CSV，无Excel/PDF | 报表不美观 | 🟡 P1 |
| **协作功能** | 无内部评论、@提醒 | 团队协作差 | 🔴 P0 |
| **自动化** | 无自动回复、自动流转 | 重复工作多60% | 🔴 P0 |
| **SLA可视化** | 无仪表盘、趋势图 | 管理盲区 | 🔴 P0 |
| **权限细化** | 坐席权限粗糙 | 合规风险 | 🟡 P1 |

#### 2.2.2 性能缺口

| 性能指标 | 当前值 | 目标值 | 差距 |
|---------|-------|-------|------|
| 工单搜索响应时间 | ~800ms (10000条) | < 500ms | ❌ 37.5%慢 |
| 导出10000条工单 | ~60s (CSV) | < 30s | ❌ 100%慢 |
| 自动分配算法 | 无 | < 100ms | ❌ 缺失 |
| SLA状态更新频率 | 无实时 | 每分钟 | ❌ 缺失 |

#### 2.2.3 数据缺口

- **无长期存储**: 归档工单超过30天后无法查询
- **无BI集成**: 无法对接数据分析平台
- **无审计日志**: 操作记录不完整

---

## 3. 标杆对比与差距

### 3.1 功能对比表

| 功能点 | Fiido当前 | Zendesk | 聚水潭 | 拼多多坐席 | 差距 |
|-------|----------|---------|--------|-----------|-----|
| **全链路视图** | ❌ | ✅ | ✅ | ✅ | 缺少实时监控面板 |
| **智能分配** | ❌ | ✅ 技能+负载 | ✅ AI推荐 | ✅ 负载均衡 | 完全缺失 |
| **批量操作** | ❌ | ✅ 50+操作 | ✅ 10+操作 | ✅ 批量分配 | 完全缺失 |
| **工单模板** | ❌ | ✅ 自定义 | ✅ 行业模板 | ✅ 预设模板 | 完全缺失 |
| **导出格式** | CSV | CSV/Excel/PDF | Excel/PDF | Excel | 缺Excel/PDF |
| **内部协作** | ❌ | ✅ 评论/@提醒 | ✅ 群聊协作 | ✅ @提醒 | 无UI实现 |
| **自动化** | ❌ | ✅ 50+规则 | ✅ 20+规则 | ✅ 工作流 | 完全缺失 |
| **SLA可视化** | 仅API | ✅ 仪表盘 | ✅ 实时监控 | ✅ 趋势图 | 无前端面板 |
| **权限矩阵** | 基础 | ✅ 细粒度 | ✅ 分层审核 | ✅ 操作日志 | 粗糙 |
| **多语言** | ❌ | ✅ 50+语言 | ✅ 自动翻译 | ✅ 实时翻译 | 完全缺失 |
| **情绪识别** | ❌ | ✅ AI分析 | ✅ 预警 | ✅ 升级规则 | 完全缺失 |

**总结**: Fiido当前功能完整度约**40%**（9/22功能点），与标杆差距显著。

### 3.2 关键差距分析

**差距1: 自动化能力缺失**
- 标杆产品自动化率 > 70%，Fiido为 0%
- 影响: 重复性工作多，坐席效率低60%

**差距2: 实时监控能力不足**
- 标杆产品有实时监控面板，Fiido仅有API
- 影响: 管理者无法快速决策

**差距3: 协作体验差**
- 标杆产品支持@提醒、群聊，Fiido无UI
- 影响: 复杂问题处理慢70%

**差距4: 数据出口单一**
- 标杆产品支持Excel/PDF/BI，Fiido仅CSV
- 影响: 报表不美观，无法对接BI

---

## 4. 开发周期规划

### 4.1 总体规划原则

**核心原则**（严格遵守 `CLAUDE.md` 铁律0）:
1. **小步快跑**: 每个增量 < 2小时开发量、< 5个文件修改
2. **频繁验证**: 每个增量独立测试、提交、打tag
3. **不破坏现有**: 所有新功能不影响核心对话和会话功能
4. **回归测试**: 每次提交后必须运行 `tests/regression_test.sh`

**开发策略**:
- **影子发布**: 新功能默认关闭，通过feature flag控制
- **A/B测试**: 部分坐席先试用新功能
- **数据兼容**: 新字段设置默认值，兼容旧数据

### 4.2 周期划分（4个阶段）

| 周期 | 目标 | 工期 | 验收标准 |
|-----|------|------|---------|
| **周期1** | 智能分配与批量操作 | 2周 | 自动分配成功率>90%，批量操作支持5+操作 |
| **周期2** | 协作功能与工单模板 | 2周 | 内部评论可用，@提醒实时推送，5+模板 |
| **周期3** | SLA可视化与自动化 | 3周 | SLA面板实时更新，10+自动化规则 |
| **周期4** | 多格式导出与权限强化 | 2周 | Excel/PDF导出，操作日志完整 |

**总工期**: 9周（约2.5个月）

---

## 4.3 周期1: 智能分配与批量操作（2周）

### 目标

实现智能分配算法和批量操作功能，提升工单处理效率50%。

### 增量列表（6个增量）

#### 增量1-1: 坐席技能标签系统（<2小时）

**功能描述**:
- 为坐席添加技能标签（如"电池专家"、"物流专员"）
- 支持技能等级（初级、中级、高级）

**文件修改**（< 5个）:
- `src/agent_auth.py`: 添加 `skills` 字段到 `Agent` 模型
- `backend.py`: 新增 `/api/agents/{id}/skills` PUT 接口
- `agent-workbench/src/types/agent.ts`: 更新类型定义

**数据模型**:
```typescript
interface AgentSkills {
  category: string       // 技能分类: "product", "logistics", "tech"
  level: "junior" | "intermediate" | "senior"
  tags: string[]         // 具体标签: ["battery", "motor"]
}
```

**验证要点**:
- [ ] 管理员可为坐席添加技能标签
- [ ] 技能标签存储到Redis/数据库
- [ ] 回归测试通过

**提交**:
```bash
git commit -m "feat: 坐席技能标签系统 v3.5.1"
git tag v3.5.1
```

---

#### 增量1-2: 智能分配算法核心逻辑（<2小时）

**功能描述**:
- 实现技能匹配 + 负载均衡算法
- 优先分配给有对应技能的坐席

**文件修改**（< 5个）:
- `src/ticket_assignment.py`: 新建分配算法模块
- `backend.py`: 调用分配算法

**算法逻辑**:
```python
def smart_assign_ticket(ticket: Ticket) -> str:
    """
    智能分配算法：
    1. 过滤在线坐席
    2. 匹配技能标签（ticket.category → agent.skills）
    3. 负载均衡（当前工单数最少）
    4. 历史服务记录（同一客户优先分配给熟悉的坐席）
    """
    online_agents = get_online_agents()

    # 技能匹配
    skilled = [a for a in online_agents if ticket.category in a.skills.tags]

    # 历史记录
    history = get_customer_history(ticket.customer_email)
    if history and history.preferred_agent in [a.id for a in skilled]:
        return history.preferred_agent

    # 负载均衡
    workloads = [(a.id, count_tickets(a.id)) for a in skilled]
    return min(workloads, key=lambda x: x[1])[0]
```

**验证要点**:
- [ ] 算法响应时间 < 100ms（50个坐席）
- [ ] 技能匹配准确率 > 90%
- [ ] 负载均衡有效（方差 < 20%）
- [ ] 测试脚本 `tests/test_smart_assignment.sh` 通过

**提交**:
```bash
git commit -m "feat: 智能分配算法核心 v3.5.2"
git tag v3.5.2
```

---

#### 增量1-3: 分配算法前端集成（<2小时）

**功能描述**:
- 创建工单时显示"智能分配"选项
- 显示分配推荐理由

**文件修改**（< 3个组件）:
- `agent-workbench/src/components/CreateTicket.vue`: 添加"智能分配"单选框
- `agent-workbench/src/api/tickets.ts`: 调用后端API

**UI设计**:
```
分配给:
○ 智能分配（推荐：张客服 - 电池专家，当前工单数:3）
○ 指定坐席: [下拉选择]
```

**验证要点**:
- [ ] UI正常渲染
- [ ] 选择"智能分配"后成功调用API
- [ ] 用户测试通过（UI验证）

**提交**:
```bash
git commit -m "feat: 智能分配前端集成 v3.5.3 (待UI验证)"
# 等待用户测试确认...
# 用户确认后集成到回归测试
```

---

#### 增量1-4: 批量分配功能（<2小时）

**功能描述**:
- 支持批量选择工单，一键分配给指定坐席

**文件修改**（< 5个）:
- `backend.py`: 新增 `/api/tickets/batch/assign` POST 接口
- `agent-workbench/src/components/TicketList.vue`: 添加批量选择

**API设计**:
```typescript
POST /api/tickets/batch/assign
{
  ticket_ids: string[],      // 工单ID列表
  target_agent_id: string,   // 目标坐席
  reason: string             // 分配原因
}
```

**验证要点**:
- [ ] 支持批量选择（最多50个工单）
- [ ] 分配成功后批量更新状态
- [ ] 测试脚本 `tests/test_batch_assign.sh` 通过

**提交**:
```bash
git commit -m "feat: 批量分配工单功能 v3.5.4"
git tag v3.5.4
```

---

#### 增量1-5: 批量关闭功能（<2小时）

**功能描述**:
- 支持批量关闭已解决的工单

**文件修改**（< 5个）:
- `backend.py`: 新增 `/api/tickets/batch/close` POST 接口
- `agent-workbench/src/components/TicketList.vue`: 添加批量关闭按钮

**API设计**:
```typescript
POST /api/tickets/batch/close
{
  ticket_ids: string[],
  close_reason: string,
  comment: string
}
```

**验证要点**:
- [ ] 只能批量关闭`resolved`状态的工单
- [ ] 记录关闭历史
- [ ] 测试脚本通过

**提交**:
```bash
git commit -m "feat: 批量关闭工单功能 v3.5.5"
git tag v3.5.5
```

---

#### 增量1-6: 批量优先级调整（<2小时）

**功能描述**:
- 支持批量调整工单优先级

**文件修改**（< 5个）:
- `backend.py`: 新增 `/api/tickets/batch/priority` POST 接口
- `agent-workbench/src/components/TicketList.vue`: 添加批量调整按钮

**验证要点**:
- [ ] 支持批量调整（最多50个）
- [ ] 记录调整原因
- [ ] 测试脚本通过

**提交**:
```bash
git commit -m "feat: 批量调整优先级 v3.5.6"
git tag v3.5.6
```

---

### 周期1 验收标准

- [ ] 智能分配成功率 > 90%（技能匹配准确）
- [ ] 分配算法响应时间 < 100ms（50个坐席）
- [ ] 批量操作支持: 分配、关闭、调整优先级（5+操作）
- [ ] 批量操作数量限制: 最多50个工单
- [ ] 所有测试脚本集成到 `tests/regression_test.sh`
- [ ] 回归测试通过率 100%

---

## 4.4 周期2: 协作功能与工单模板（2周）

### 目标

实现内部协作功能（评论、@提醒、附件）和工单模板，提升复杂工单处理效率70%。

### 增量列表（7个增量）

#### 增量2-1: 评论系统后端API（<2小时）

**功能描述**:
- 实现内部评论和公开回复两种类型
- 支持Markdown格式

**文件修改**（< 5个）:
- `src/ticket_comments.py`: 新建评论模块
- `backend.py`: 新增 `/api/tickets/{id}/comments` GET/POST 接口

**数据模型**:
```typescript
interface TicketComment {
  id: string
  ticket_id: string
  comment_type: "public" | "internal"
  content: string              // Markdown格式
  author_id: string
  author_name: string
  mentions: string[]           // @提到的坐席ID
  created_at: Date
}
```

**验证要点**:
- [ ] 支持创建两种类型评论
- [ ] 评论存储到Redis
- [ ] 测试脚本 `tests/test_ticket_comments.sh` 通过

**提交**:
```bash
git commit -m "feat: 评论系统后端API v3.6.1"
git tag v3.6.1
```

---

#### 增量2-2: @提醒通知机制（<2小时）

**功能描述**:
- 评论中@坐席时，实时推送通知

**文件修改**（< 5个）:
- `backend.py`: 评论API中解析@提到的坐席
- SSE推送通知到被@坐席

**通知逻辑**:
```python
def process_mentions(comment: TicketComment):
    for agent_id in comment.mentions:
        # 推送SSE通知
        await sse_queues[agent_id].put({
            "type": "mention",
            "ticket_id": comment.ticket_id,
            "from_agent": comment.author_name,
            "content_preview": comment.content[:50]
        })
```

**验证要点**:
- [ ] @提醒实时推送（延迟 < 1秒）
- [ ] 通知包含工单链接
- [ ] 测试脚本通过

**提交**:
```bash
git commit -m "feat: @提醒通知机制 v3.6.2"
git tag v3.6.2
```

---

#### 增量2-3: 评论UI组件（<2小时）

**功能描述**:
- 工单详情页显示评论列表
- 支持公开回复和内部备注

**文件修改**（< 3个组件）:
- `agent-workbench/src/components/TicketComments.vue`: 评论列表
- `agent-workbench/src/components/CommentEditor.vue`: 评论编辑器

**UI设计**:
```
评论历史:
┌─────────────────────────────────────┐
│ 🕐 2025-01-27 10:00                │
│ 👨‍💼 李客服（公开回复）               │
│ 您好，我们已为您查询...              │
├─────────────────────────────────────┤
│ 🕐 2025-01-27 10:05                │
│ 🔒 张客服（内部备注）                │
│ @王技术 帮忙看下这个电池问题         │
└─────────────────────────────────────┘
```

**验证要点**:
- [ ] 评论列表正确显示
- [ ] 内部备注有🔒标识
- [ ] @提到的坐席高亮显示
- [ ] 用户测试通过（UI验证）

**提交**:
```bash
git commit -m "feat: 评论UI组件 v3.6.3 (待UI验证)"
```

---

#### 增量2-4: 附件上传功能（<2小时）

**功能描述**:
- 支持上传图片、文档、视频

**文件修改**（< 5个）:
- `backend.py`: 新增 `/api/tickets/{id}/attachments` POST 接口
- 集成文件存储（本地存储或OSS）

**API设计**:
```typescript
POST /api/tickets/{id}/attachments
Content-Type: multipart/form-data

file: File
comment_type: "public" | "internal"
```

**文件大小限制**:
- 图片: 10MB
- 文档: 20MB
- 视频: 50MB

**验证要点**:
- [ ] 支持多种文件类型（jpg, png, pdf, mp4）
- [ ] 文件大小验证
- [ ] 附件下载功能正常
- [ ] 测试脚本通过

**提交**:
```bash
git commit -m "feat: 附件上传功能 v3.6.4"
git tag v3.6.4
```

---

#### 增量2-5: 协作日志自动记录（<2小时）

**功能描述**:
- 自动记录所有工单操作（创建、状态变更、分配等）

**文件修改**（< 5个）:
- `src/audit_log.py`: 新建审计日志模块
- `backend.py`: 在关键操作后调用日志记录

**日志格式**:
```typescript
interface AuditLog {
  id: string
  ticket_id: string
  event_type: "created" | "status_changed" | "assigned" | "commented"
  operator_id: string
  operator_name: string
  details: Record<string, any>
  created_at: Date
}
```

**验证要点**:
- [ ] 关键操作全部记录
- [ ] 日志可查询（按工单ID）
- [ ] 测试脚本通过

**提交**:
```bash
git commit -m "feat: 协作日志自动记录 v3.6.5"
git tag v3.6.5
```

---

#### 增量2-6: 工单模板后端API（<2小时）

**功能描述**:
- 支持创建和管理工单模板

**文件修改**（< 5个）:
- `src/ticket_template.py`: 新建模板模块
- `backend.py`: 新增 `/api/templates` CRUD接口

**数据模型**:
```typescript
interface TicketTemplate {
  id: string
  name: string
  ticket_type: "pre_sale" | "after_sale" | "complaint"
  category: string
  priority: "low" | "medium" | "high"
  title_template: string       // 支持变量: {customer_name}
  description_template: string
  created_by: string
}
```

**验证要点**:
- [ ] 支持创建、编辑、删除模板
- [ ] 模板变量替换正确
- [ ] 测试脚本通过

**提交**:
```bash
git commit -m "feat: 工单模板后端API v3.6.6"
git tag v3.6.6
```

---

#### 增量2-7: 工单模板前端UI（<2小时）

**功能描述**:
- 创建工单时可选择模板
- 模板管理页面

**文件修改**（< 3个组件）:
- `agent-workbench/src/components/CreateTicket.vue`: 添加模板选择
- `agent-workbench/src/views/TemplateManagement.vue`: 模板管理页面

**UI设计**:
```
创建工单:
使用模板: [选择模板 ▼]
  ○ 电池续航问题模板
  ○ 物流配送问题模板
  ○ 退换货申请模板
  ○ 不使用模板

[选择模板后自动填充标题和描述]
```

**验证要点**:
- [ ] 模板选择后自动填充
- [ ] 变量替换正确（如{customer_name}）
- [ ] 管理员可创建/编辑模板
- [ ] 用户测试通过（UI验证）

**提交**:
```bash
git commit -m "feat: 工单模板前端UI v3.6.7 (待UI验证)"
```

---

### 周期2 验收标准

- [ ] 内部评论可用（公开/内部两种类型）
- [ ] @提醒实时推送（延迟 < 1秒）
- [ ] 附件上传/下载功能正常（支持5+文件类型）
- [ ] 协作日志完整记录（10+事件类型）
- [ ] 工单模板功能可用（5+预设模板）
- [ ] 所有测试脚本集成到回归测试
- [ ] 回归测试通过率 100%

---

## 4.5 周期3: SLA可视化与自动化（3周）

### 目标

实现SLA实时监控面板和自动化规则引擎，提升服务质量和自动化率70%。

### 增量列表（10个增量）

#### 增量3-1: SLA计时器核心逻辑（<2小时）

**功能描述**:
- 实现首次响应和解决时效计时

**文件修改**（< 5个）:
- `src/sla_timer.py`: 新建SLA计时模块
- `backend.py`: 工单创建时启动计时

**计时逻辑**:
```python
class SLATimer:
    def __init__(self, ticket: Ticket):
        self.ticket_id = ticket.ticket_id
        self.priority = ticket.priority
        self.created_at = ticket.created_at

        # 根据优先级设置目标时效
        self.frt_target = get_frt_target(ticket.priority)
        self.rt_target = get_rt_target(ticket.priority, ticket.ticket_type)

    def get_frt_remaining(self) -> float:
        """首次响应剩余时间（分钟）"""
        elapsed = (now() - self.created_at) / 60
        return max(0, self.frt_target - elapsed)

    def get_rt_remaining(self) -> float:
        """解决时效剩余时间（小时）"""
        elapsed = (now() - self.created_at) / 3600
        return max(0, self.rt_target - elapsed)

    def get_status(self) -> str:
        """SLA状态: normal/warning/urgent/violated"""
        frt_pct = self.get_frt_remaining() / self.frt_target
        if frt_pct > 0.5:
            return "normal"
        elif frt_pct > 0.2:
            return "warning"
        elif frt_pct > 0:
            return "urgent"
        else:
            return "violated"
```

**验证要点**:
- [ ] 计时准确（误差 < 1秒）
- [ ] 支持暂停/恢复（等待客户时）
- [ ] 测试脚本通过

**提交**:
```bash
git commit -m "feat: SLA计时器核心逻辑 v3.7.1"
git tag v3.7.1
```

---

#### 增量3-2: SLA状态实时更新（<2小时）

**功能描述**:
- 每分钟更新所有活跃工单的SLA状态

**文件修改**（< 5个）:
- `backend.py`: 新增后台任务（定时器）
- 使用APScheduler实现定时任务

**定时任务逻辑**:
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('interval', minutes=1)
async def update_sla_status():
    # 获取所有活跃工单
    active_tickets = await ticket_store.list_active()

    for ticket in active_tickets:
        timer = SLATimer(ticket)
        ticket.sla_status = timer.get_status()
        ticket.frt_remaining = timer.get_frt_remaining()
        ticket.rt_remaining = timer.get_rt_remaining()

        # 保存更新
        await ticket_store.save(ticket)

        # 如果进入urgent/violated，推送通知
        if ticket.sla_status in ["urgent", "violated"]:
            await send_sla_alert(ticket)
```

**验证要点**:
- [ ] 定时任务正常运行（每分钟执行）
- [ ] SLA状态更新准确
- [ ] 性能可接受（1000个工单 < 5秒）
- [ ] 测试脚本通过

**提交**:
```bash
git commit -m "feat: SLA状态实时更新 v3.7.2"
git tag v3.7.2
```

---

#### 增量3-3: SLA监控仪表盘UI（<2小时）

**功能描述**:
- 创建SLA监控仪表盘页面

**文件修改**（< 3个组件）:
- `agent-workbench/src/views/SLADashboard.vue`: 仪表盘页面
- `agent-workbench/src/components/SLAGauge.vue`: SLA仪表组件

**UI设计**:
```
SLA达成率 - 本周
┌─────────────────────────────────────┐
│ 首次响应 SLA                        │
│ ━━━━━━━━━━━━━━━━━━━━━ 92%          │
│ 达成: 184次  违规: 16次             │
├─────────────────────────────────────┤
│ 解决时效 SLA                        │
│ ━━━━━━━━━━━━━━━━━ 88%              │
│ 达成: 132次  违规: 18次             │
└─────────────────────────────────────┘

超时工单TOP5:
1. TKT-001 电池问题 已超时 2小时
2. TKT-002 物流查询 已超时 1.5小时
```

**验证要点**:
- [ ] 仪表盘实时更新（每分钟刷新）
- [ ] 图表准确显示达成率
- [ ] 超时工单列表正确
- [ ] 用户测试通过（UI验证）

**提交**:
```bash
git commit -m "feat: SLA监控仪表盘UI v3.7.3 (待UI验证)"
```

---

#### 增量3-4: SLA预警通知（<2小时）

**功能描述**:
- 达到80%阈值时通知坐席

**文件修改**（< 5个）:
- `backend.py`: 在SLA状态更新时检查阈值
- SSE推送预警通知

**预警逻辑**:
```python
def check_sla_alert(ticket: Ticket):
    timer = SLATimer(ticket)
    frt_pct = timer.get_frt_remaining() / timer.frt_target

    if frt_pct < 0.2 and frt_pct > 0:  # 80%阈值
        # 推送通知给处理坐席
        await notify_agent(ticket.assigned_to, {
            "type": "sla_alert",
            "level": "urgent",
            "ticket_id": ticket.ticket_id,
            "remaining": timer.get_frt_remaining()
        })
```

**验证要点**:
- [ ] 预警及时推送（延迟 < 5秒）
- [ ] 通知包含剩余时间
- [ ] 测试脚本通过

**提交**:
```bash
git commit -m "feat: SLA预警通知 v3.7.4"
git tag v3.7.4
```

---

#### 增量3-5: 自动化规则引擎核心（<2小时）

**功能描述**:
- 实现规则引擎框架（IF-THEN）

**文件修改**（< 5个）:
- `src/automation_engine.py`: 新建自动化引擎模块

**规则引擎设计**:
```python
class AutomationEngine:
    def __init__(self):
        self.rules = []  # 规则列表，按优先级排序

    async def evaluate(self, event: Event, ticket: Ticket):
        """评估事件，执行匹配的规则"""
        for rule in self.rules:
            if not rule.is_active:
                continue

            # 检查触发条件
            if rule.matches(event, ticket):
                # 执行动作
                await rule.execute(ticket)

                # 记录日志
                log_automation(rule.id, ticket.ticket_id)
```

**验证要点**:
- [ ] 规则引擎正常运行
- [ ] 规则按优先级执行
- [ ] 测试脚本通过

**提交**:
```bash
git commit -m "feat: 自动化规则引擎核心 v3.7.5"
git tag v3.7.5
```

---

#### 增量3-6: 自动回复规则（<2小时）

**功能描述**:
- 实现非工作时间自动回复

**文件修改**（< 5个）:
- `src/automation_rules/auto_reply.py`: 自动回复规则

**规则示例**:
```python
class AfterHoursAutoReply(AutomationRule):
    def matches(self, event: Event, ticket: Ticket) -> bool:
        return (
            event.type == "ticket_created" and
            not is_work_hours()
        )

    async def execute(self, ticket: Ticket):
        # 自动发送公开回复
        await add_comment(
            ticket_id=ticket.ticket_id,
            comment_type="public",
            content=f"""
您好！感谢联系Fiido客服。

当前为非工作时间，您的工单已收到。
工单编号: {ticket.ticket_id}
预计响应时间: 明天 9:30 前
            """
        )
```

**验证要点**:
- [ ] 非工作时间自动回复
- [ ] 回复内容正确
- [ ] 测试脚本通过

**提交**:
```bash
git commit -m "feat: 自动回复规则 v3.7.6"
git tag v3.7.6
```

---

#### 增量3-7: 自动分配规则（<2小时）

**功能描述**:
- VIP客户优先分配

**文件修改**（< 5个）:
- `src/automation_rules/vip_priority.py`: VIP优先规则

**规则示例**:
```python
class VIPPriorityRule(AutomationRule):
    def matches(self, event: Event, ticket: Ticket) -> bool:
        return (
            event.type == "ticket_created" and
            ticket.customer.is_vip
        )

    async def execute(self, ticket: Ticket):
        # 设置高优先级
        ticket.priority = "high"

        # 分配给VIP专属坐席
        vip_agents = get_vip_agents()
        ticket.assigned_to = select_least_busy(vip_agents)

        # 通知组长
        await notify_supervisor(ticket)
```

**验证要点**:
- [ ] VIP客户自动设置高优先级
- [ ] 分配给VIP专属坐席
- [ ] 测试脚本通过

**提交**:
```bash
git commit -m "feat: VIP优先自动分配 v3.7.7"
git tag v3.7.7
```

---

#### 增量3-8: 自动流转规则（<2小时）

**功能描述**:
- 客户回复自动恢复处理状态

**文件修改**（< 5个）:
- `src/automation_rules/auto_reopen.py`: 自动恢复规则

**规则示例**:
```python
class CustomerReplyAutoReopen(AutomationRule):
    def matches(self, event: Event, ticket: Ticket) -> bool:
        return (
            event.type == "customer_replied" and
            ticket.status == "waiting_customer"
        )

    async def execute(self, ticket: Ticket):
        # 状态改为处理中
        ticket.status = "in_progress"

        # 恢复SLA计时
        resume_sla_timer(ticket)

        # 通知处理坐席
        await notify_agent(ticket.assigned_to, {
            "type": "customer_replied",
            "ticket_id": ticket.ticket_id
        })
```

**验证要点**:
- [ ] 客户回复后自动恢复状态
- [ ] SLA计时恢复
- [ ] 测试脚本通过

**提交**:
```bash
git commit -m "feat: 客户回复自动恢复 v3.7.8"
git tag v3.7.8
```

---

#### 增量3-9: 自动化规则管理UI（<2小时）

**功能描述**:
- 管理员可配置自动化规则

**文件修改**（< 3个组件）:
- `agent-workbench/src/views/AutomationRules.vue`: 规则管理页面
- `agent-workbench/src/components/RuleEditor.vue`: 规则编辑器

**UI设计**:
```
自动化规则管理
┌─────────────────────────────────────┐
│ [+ 新建规则]                        │
│                                     │
│ 🟢 规则1: VIP客户优先                │
│ 优先级: 最高 (1)                    │
│ 触发: 工单创建 + 客户为VIP          │
│ 动作: 设置优先级高 + 分配VIP组       │
│ 状态: ✅ 已启用                      │
│ 统计: 本月匹配 156次                │
│ [编辑] [禁用] [删除]                │
└─────────────────────────────────────┘
```

**验证要点**:
- [ ] 管理员可创建/编辑/删除规则
- [ ] 规则可启用/禁用
- [ ] 显示执行统计
- [ ] 用户测试通过（UI验证）

**提交**:
```bash
git commit -m "feat: 自动化规则管理UI v3.7.9 (待UI验证)"
```

---

#### 增量3-10: 自动化效果报表（<2小时）

**功能描述**:
- 显示自动化节省的时间和成本

**文件修改**（< 3个组件）:
- `agent-workbench/src/views/AutomationStats.vue`: 统计页面

**报表内容**:
```
自动化效果统计 - 本月
┌─────────────────────────────────────┐
│ 自动分配: 980次 (78.4%)             │
│ 自动回复: 1,856次                   │
│ 自动流转: 320次                     │
│                                     │
│ 节省时间:                           │
│ • 自动分配节省: 16.3小时            │
│ • 自动回复节省: 30.9小时            │
│ • 总节省时间: 47.2小时              │
│                                     │
│ 人力成本节省: ¥4,720 (按50元/小时)  │
└─────────────────────────────────────┘
```

**验证要点**:
- [ ] 统计数据准确
- [ ] 图表可视化
- [ ] 用户测试通过（UI验证）

**提交**:
```bash
git commit -m "feat: 自动化效果报表 v3.7.10 (待UI验证)"
```

---

### 周期3 验收标准

- [ ] SLA面板实时更新（每分钟刷新）
- [ ] SLA预警及时推送（80%阈值）
- [ ] SLA达成率报表准确
- [ ] 自动化规则引擎运行稳定
- [ ] 10+自动化规则正常工作
- [ ] 自动化率 > 70%（自动分配、自动回复）
- [ ] 所有测试脚本集成到回归测试
- [ ] 回归测试通过率 100%

---

## 4.6 周期4: 多格式导出与权限强化（2周）

### 目标

实现Excel/PDF导出和操作审计日志，满足合规要求。

### 增量列表（6个增量）

#### 增量4-1: Excel导出功能（<2小时）

**功能描述**:
- 使用openpyxl库生成Excel文件

**文件修改**（< 5个）:
- `src/export_excel.py`: 新建Excel导出模块
- `backend.py`: 在 `/api/tickets/export` 中支持xlsx格式

**导出逻辑**:
```python
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment

def generate_excel(tickets: List[Ticket]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "工单列表"

    # 标题行（加粗）
    headers = ["工单ID", "标题", "状态", "优先级", "客户", "创建时间", "解决时间"]
    ws.append(headers)
    ws[1].font = Font(bold=True)

    # 数据行
    for ticket in tickets:
        ws.append([
            ticket.ticket_id,
            ticket.title,
            ticket.status,
            ticket.priority,
            ticket.customer_name,
            ticket.created_at.strftime("%Y-%m-%d %H:%M"),
            ticket.resolved_at.strftime("%Y-%m-%d %H:%M") if ticket.resolved_at else ""
        ])

    # 自动调整列宽
    for column in ws.columns:
        max_length = max(len(str(cell.value)) for cell in column)
        ws.column_dimensions[column[0].column_letter].width = max_length + 2

    # 保存到字节流
    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()
```

**验证要点**:
- [ ] Excel文件格式正确
- [ ] 数据完整（10000条工单）
- [ ] 导出速度 < 30秒
- [ ] 测试脚本通过

**提交**:
```bash
git commit -m "feat: Excel导出功能 v3.8.1"
git tag v3.8.1
```

---

#### 增量4-2: PDF报表导出（<2小时）

**功能描述**:
- 使用ReportLab生成PDF报表

**文件修改**（< 5个）:
- `src/export_pdf.py`: 新建PDF导出模块
- `backend.py`: 在 `/api/tickets/export` 中支持pdf格式

**PDF内容**:
- 封面（公司Logo、报表标题、导出时间）
- 统计摘要（总工单数、SLA达成率）
- 工单列表（表格形式）
- 图表（工单分布饼图）

**验证要点**:
- [ ] PDF格式正确
- [ ] 包含统计摘要和图表
- [ ] 导出速度 < 45秒（10000条）
- [ ] 测试脚本通过

**提交**:
```bash
git commit -m "feat: PDF报表导出 v3.8.2"
git tag v3.8.2
```

---

#### 增量4-3: 导出格式选择UI（<2小时）

**功能描述**:
- 工单列表页添加导出按钮

**文件修改**（< 3个组件）:
- `agent-workbench/src/components/TicketList.vue`: 添加导出按钮
- `agent-workbench/src/components/ExportDialog.vue`: 导出对话框

**UI设计**:
```
[导出] 按钮 -> 弹出对话框
┌─────────────────────────────────────┐
│ 导出工单                            │
├─────────────────────────────────────┤
│ 导出范围:                           │
│ ○ 导出当前页 (20条)                 │
│ ○ 导出筛选结果 (156条)              │
│ ○ 导出全部工单 (5000条) [需管理员]  │
│                                     │
│ 导出格式:                           │
│ ○ CSV (.csv)                        │
│ ○ Excel (.xlsx)                     │
│ ○ PDF 报表 (.pdf)                   │
│                                     │
│ [取消]            [开始导出]        │
└─────────────────────────────────────┘
```

**验证要点**:
- [ ] 三种格式都可正常导出
- [ ] 导出进度提示
- [ ] 用户测试通过（UI验证）

**提交**:
```bash
git commit -m "feat: 导出格式选择UI v3.8.3 (待UI验证)"
```

---

#### 增量4-4: 操作审计日志增强（<2小时）

**功能描述**:
- 记录所有敏感操作（删除工单、修改状态、转派等）

**文件修改**（< 5个）:
- `src/audit_log.py`: 增强审计日志模块
- `backend.py`: 在敏感操作后记录日志

**日志格式**:
```typescript
interface AuditLog {
  id: string
  operator_id: string
  operator_name: string
  operation: string           // "delete_ticket", "change_status", "assign"
  target_type: string         // "ticket", "agent", "template"
  target_id: string
  changes: Record<string, {old: any, new: any}>  // 变更内容
  ip_address: string
  user_agent: string
  created_at: Date
}
```

**验证要点**:
- [ ] 敏感操作全部记录
- [ ] 记录IP地址和User-Agent
- [ ] 日志不可删除（仅管理员可查看）
- [ ] 测试脚本通过

**提交**:
```bash
git commit -m "feat: 操作审计日志增强 v3.8.4"
git tag v3.8.4
```

---

#### 增量4-5: 审计日志查询UI（<2小时）

**功能描述**:
- 管理员可查询审计日志

**文件修改**（< 3个组件）:
- `agent-workbench/src/views/AuditLogs.vue`: 审计日志页面
- `backend.py`: 新增 `/api/audit-logs` GET 接口

**UI设计**:
```
审计日志（需管理员权限）
┌─────────────────────────────────────┐
│ 筛选:                               │
│ 操作人: [全部 ▼]                    │
│ 操作类型: [全部 ▼]                  │
│ 时间范围: [今天 ▼]                  │
│ [搜索]                              │
├─────────────────────────────────────┤
│ 时间              操作人   操作      │
│ 2025-01-27 10:00  张客服   删除工单  │
│   工单ID: TKT-001                   │
│   原因: 重复工单                    │
│   IP: 192.168.1.100                 │
├─────────────────────────────────────┤
│ 2025-01-27 09:30  李客服   转派工单  │
│   工单ID: TKT-002                   │
│   从: 张客服 → 王客服               │
│   原因: 技术支持需求                │
└─────────────────────────────────────┘
```

**验证要点**:
- [ ] 仅管理员可访问
- [ ] 支持按操作人、类型、时间筛选
- [ ] 显示详细变更内容
- [ ] 用户测试通过（UI验证）

**提交**:
```bash
git commit -m "feat: 审计日志查询UI v3.8.5 (待UI验证)"
```

---

#### 增量4-6: 权限矩阵细化（<2小时）

**功能描述**:
- 细化坐席权限（查看、编辑、删除、导出等）

**文件修改**（< 5个）:
- `src/agent_auth.py`: 添加权限枚举
- `backend.py`: 在敏感操作前检查权限

**权限矩阵**:
```typescript
enum Permission {
  VIEW_TICKET = "view_ticket",
  EDIT_TICKET = "edit_ticket",
  DELETE_TICKET = "delete_ticket",
  ASSIGN_TICKET = "assign_ticket",
  EXPORT_TICKET = "export_ticket",
  MANAGE_TEMPLATE = "manage_template",
  MANAGE_AUTOMATION = "manage_automation",
  VIEW_AUDIT_LOG = "view_audit_log"
}

// 角色 - 权限映射
const role_permissions = {
  "admin": ["*"],  // 所有权限
  "agent": ["view_ticket", "edit_ticket", "assign_ticket"],
  "supervisor": ["view_ticket", "edit_ticket", "assign_ticket", "export_ticket", "manage_template"]
}
```

**验证要点**:
- [ ] 权限检查正确
- [ ] 无权限操作返回403
- [ ] 测试脚本通过

**提交**:
```bash
git commit -m "feat: 权限矩阵细化 v3.8.6"
git tag v3.8.6
```

---

### 周期4 验收标准

- [ ] Excel导出功能正常（格式正确、速度 < 30秒）
- [ ] PDF报表导出正常（包含统计和图表）
- [ ] 多格式导出UI可用（CSV/Excel/PDF）
- [ ] 操作审计日志完整（记录10+敏感操作）
- [ ] 审计日志查询功能正常（仅管理员）
- [ ] 权限矩阵生效（8+权限点）
- [ ] 所有测试脚本集成到回归测试
- [ ] 回归测试通过率 100%

---

## 5. 技术架构设计

### ⭐ 5.1 闭环架构设计

#### 5.1.1 核心设计理念

**传统分层架构 vs 闭环架构对比**:

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  传统分层架构 ❌                                                  │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ 客户端 → API → 业务逻辑 → 数据库                        │     │
│  │ (单向请求-响应，组件独立，状态割裂)                     │     │
│  └────────────────────────────────────────────────────────┘     │
│                                                                  │
│  闭环架构 ✅                                                     │
│  ┌────────────────────────────────────────────────────────┐     │
│  │         客户端 ←─────── SSE 推送                        │     │
│  │           ↓                  ↑                          │     │
│  │         API ←─────── 事件总线                           │     │
│  │           ↓                  ↑                          │     │
│  │      业务逻辑 ←────── 状态管理                          │     │
│  │           ↓                  ↑                          │     │
│  │        数据库 ──────→ 坐席工作台                        │     │
│  │                                                          │     │
│  │ (双向事件流，实时同步，统一状态)                         │     │
│  └────────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────────┘
```

#### 5.1.2 闭环架构全景图

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          Fiido 闭环客服系统架构                           │
└──────────────────────────────────────────────────────────────────────────┘

        ┌─────────────────────────────────────────────────────┐
        │            客户端 (Vue 用户端)                      │
        │  - 发送消息                                          │
        │  - 接收 AI/人工回复                                  │
        │  - 显示实时状态("人工接入中"/"AI服务中")             │
        └─────────┬───────────────────────────────┬───────────┘
                  │ ① POST /api/chat             │ ④ SSE 推送
                  │ (携带 session_name)          │ (manual_message)
                  ↓                              ↑
        ┌─────────────────────────────────────────────────────┐
        │         FastAPI 后端 (backend.py)                   │
        │                                                      │
        │  ② 核心流程                                          │
        │  ┌──────────────────────────────────────────────┐  │
        │  │ 1. OAuth+JWT 认证                            │  │
        │  │ 2. session_state.py 状态检查                 │  │
        │  │ 3. regulator.py 监管引擎检测                 │  │
        │  │ 4. Coze API 调用 (如 bot_active 状态)       │  │
        │  │ 5. smart_assignment.py 智能分配 (如需升级)  │  │
        │  │ 6. SSE 事件推送到各端                        │  │
        │  └──────────────────────────────────────────────┘  │
        │                                                      │
        │  关键模块:                                           │
        │  - session_state.py   统一状态管理                  │
        │  - regulator.py       升级规则引擎                  │
        │  - smart_assignment.py 智能分配算法                 │
        │  - sla_timer.py       SLA 实时计时                  │
        │  - automation_engine.py 自动化规则                  │
        │  - audit_log.py       操作审计                      │
        └─────────┬───────────────────────────────┬───────────┘
                  │ ③ SSE 推送                    │ ⑤ API 调用
                  │ (new_session,                │ (接入/转派/
                  │  sla_alert 等)                │  评论/结束)
                  ↓                              ↑
        ┌─────────────────────────────────────────────────────┐
        │        坐席工作台 (Vue 坐席端)                      │
        │  - 接收新会话通知                                    │
        │  - 查看会话列表 + 客户画像                           │
        │  - 发送人工消息                                      │
        │  - 管理工单生命周期                                  │
        │  - 实时 SLA 倒计时                                   │
        │  - 内部协作(@提醒/评论/附件)                         │
        └─────────┬───────────────────────────────┬───────────┘
                  │ ⑥ POST /api/manual/messages  │ ⑦ SSE 推送
                  │ (发送人工消息)                │ (customer_replied,
                  ↓                              │  ticket_updated)
        ┌─────────────────────────────────────────────────────┐
        │            数据持久层 (Redis + MySQL)                │
        │                                                      │
        │  Redis (热数据，实时读写):                           │
        │  - session_state:{session_name}  会话状态            │
        │  - ticket:{ticket_id}            活跃工单            │
        │  - agent:{agent_id}:workload     坐席负载            │
        │  - sse_queue:{session_name}      SSE 消息队列        │
        │                                                      │
        │  MySQL/PostgreSQL (冷数据，长期存储):                │
        │  - archived_tickets              归档工单            │
        │  - audit_logs                    操作日志            │
        │  - automation_rules              自动化规则          │
        └─────────┬──────────────────────────────────────────┘
                  │ ⑧ 外部集成
                  ↓
        ┌─────────────────────────────────────────────────────┐
        │              外部服务                                │
        │  - Coze AI (workflow API)                            │
        │  - Shopify (订单查询)                                │
        │  - SMTP (邮件通知)                                   │
        │  - OSS/S3 (附件存储)                                 │
        └──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│  关键闭环路径:                                                            │
│                                                                          │
│  路径1: 客户咨询 → AI 回复                                                │
│  客户端 → backend.py → Coze API → backend.py → SSE → 客户端              │
│                                                                          │
│  路径2: AI 升级人工                                                       │
│  regulator.py 检测 → smart_assignment.py 分配 → SSE → 坐席工作台         │
│                                                                          │
│  路径3: 人工回复客户                                                      │
│  坐席工作台 → POST /api/manual/messages → backend.py → SSE → 客户端      │
│                                                                          │
│  路径4: 客户回复人工                                                      │
│  客户端 → POST /api/chat → backend.py → SSE → 坐席工作台                 │
│                                                                          │
│  路径5: SLA 监控预警                                                      │
│  sla_timer.py 定时任务 → 计算剩余时效 → SSE → 坐席工作台(倒计时)          │
│                                                                          │
│  路径6: 工单状态同步                                                      │
│  坐席工作台 → PATCH /api/tickets/{id} → Redis → SSE → 多个坐席工作台     │
└──────────────────────────────────────────────────────────────────────────┘
```

#### 5.1.3 闭环通信机制详解

**1. SSE 事件总线设计**

```python
# 后端 (backend.py) - SSE 事件总线
sse_queues: Dict[str, asyncio.Queue] = {}

# 事件分类
SSE_EVENTS = {
    # 客户端接收的事件
    "CLIENT": [
        "ai_message",           # AI 回复消息
        "manual_message",       # 人工回复消息
        "status_change",        # 会话状态变更
        "agent_typing",         # 坐席正在输入
        "session_ended",        # 会话已结束
    ],

    # 坐席工作台接收的事件
    "AGENT_WORKBENCH": [
        "new_session",          # 新会话待接入
        "session_assigned",     # 会话已分配给你
        "customer_replied",     # 客户回复了消息
        "sla_alert",            # SLA 超时预警
        "mention_notification", # @提醒通知
        "ticket_updated",       # 工单状态更新
        "message_sent",         # 消息发送成功确认
    ],
}

# 推送事件到客户端
async def notify_customer(session_name: str, event: dict):
    if session_name in sse_queues:
        await sse_queues[session_name].put(event)
        logger.info(f"[SSE] 推送到客户端 {session_name}: {event['type']}")

# 推送事件到坐席工作台
async def notify_agent(agent_id: str, event: dict):
    agent_queue_key = f"agent_{agent_id}"
    if agent_queue_key in sse_queues:
        await sse_queues[agent_queue_key].put(event)
        logger.info(f"[SSE] 推送到坐席 {agent_id}: {event['type']}")
```

**2. 状态同步机制**

```python
# 状态变更流程
class SessionState:
    def set_status(self, new_status: SessionStatus):
        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.now()

        # 1. 保存到 Redis (状态真实来源)
        self.save_to_redis()

        # 2. 推送到客户端
        asyncio.create_task(notify_customer(self.session_name, {
            "type": "status_change",
            "old_status": old_status.value,
            "new_status": new_status.value,
            "agent_name": self.assigned_agent_name
        }))

        # 3. 推送到坐席工作台
        if self.assigned_agent:
            asyncio.create_task(notify_agent(self.assigned_agent, {
                "type": "session_assigned",
                "session_name": self.session_name,
                "customer_email": self.customer_email
            }))

        # 4. 记录审计日志
        audit_log.record({
            "event": "status_change",
            "session_name": self.session_name,
            "old_status": old_status.value,
            "new_status": new_status.value,
            "timestamp": self.updated_at
        })
```

**3. 数据一致性保证**

```
┌──────────────────────────────────────────────────────────────┐
│  一致性原则: Single Source of Truth (单一数据源)              │
└──────────────────────────────────────────────────────────────┘

Redis (后端) = 真实来源
    ↓
    └──→ SSE 推送到客户端 (只读副本，不可直接修改)
    └──→ SSE 推送到坐席工作台 (只读副本，不可直接修改)

前端变更 → 必须通过 API 修改后端 Redis → SSE 同步回前端

示例:
❌ 错误: 前端直接修改本地状态
this.session.status = 'manual_live'  // 可能与后端不一致!

✅ 正确: 调用 API，等待 SSE 同步
await fetch('/api/sessions/{id}/assign', {method: 'PUT'})
// SSE 自动推送最新状态到前端，自动更新 UI
```

#### 5.1.4 闭环架构的技术保障

**1. 幂等性设计**

```python
# 所有状态变更接口都支持幂等操作
@app.put("/api/sessions/{session_name}/assign")
async def assign_session(session_name: str, agent_id: str):
    session_state = get_session_state(session_name)

    # 幂等性检查
    if session_state.assigned_agent == agent_id and session_state.status == SessionStatus.MANUAL_LIVE:
        logger.info(f"会话 {session_name} 已分配给 {agent_id}，跳过重复操作")
        return {"success": True, "message": "Already assigned"}

    # 执行分配逻辑...
```

**2. 失败重试机制**

```python
# SSE 推送失败自动重试
async def notify_with_retry(queue_key: str, event: dict, max_retries=3):
    for attempt in range(max_retries):
        try:
            await sse_queues[queue_key].put(event)
            return True
        except Exception as e:
            logger.warning(f"SSE 推送失败 (尝试 {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(0.5)  # 500ms 后重试

    # 所有重试失败，记录错误但不阻塞主流程
    logger.error(f"SSE 推送最终失败: {queue_key} - {event}")
    return False
```

**3. 降级策略**

```python
# 智能分配失败降级到广播通知
try:
    assigned_agent = await smart_assignment_engine.assign(session_name)
    session_state.assigned_agent = assigned_agent
    await notify_agent(assigned_agent, new_session_event)
except Exception as e:
    logger.error(f"智能分配失败: {e}")

    # 降级: 广播给所有在线坐席，手动抢单
    online_agents = get_online_agents()
    for agent in online_agents:
        await notify_agent(agent.id, {
            "type": "new_session",
            "session_name": session_name,
            "mode": "manual_pickup",  # 手动抢单模式
            "reason": "智能分配失败"
        })
```

#### 5.1.5 闭环性能优化

**1. SSE 连接池管理**

```python
# 限制每个用户的并发 SSE 连接数
MAX_SSE_PER_USER = 3
sse_connections: Dict[str, int] = {}

@app.get("/api/chat/stream")
async def chat_stream(session_name: str):
    # 连接数检查
    current_connections = sse_connections.get(session_name, 0)
    if current_connections >= MAX_SSE_PER_USER:
        raise HTTPException(429, "Too many concurrent SSE connections")

    sse_connections[session_name] = current_connections + 1
    try:
        # SSE 流式响应
        yield ...
    finally:
        sse_connections[session_name] -= 1
```

**2. 事件批量处理**

```python
# 合并同类型事件，减少 SSE 推送次数
class EventBatcher:
    def __init__(self, batch_window_ms=100):
        self.batch_window = batch_window_ms / 1000
        self.pending_events: Dict[str, List[dict]] = {}

    async def add_event(self, queue_key: str, event: dict):
        if queue_key not in self.pending_events:
            self.pending_events[queue_key] = []
            asyncio.create_task(self._flush_after_delay(queue_key))

        self.pending_events[queue_key].append(event)

    async def _flush_after_delay(self, queue_key: str):
        await asyncio.sleep(self.batch_window)
        events = self.pending_events.pop(queue_key, [])

        if events:
            # 合并同类型事件
            merged = self._merge_events(events)
            await sse_queues[queue_key].put(merged)
```

**3. 缓存热点数据**

```python
# 缓存坐席技能、SLA 配置等热点数据
from functools import lru_cache

@lru_cache(maxsize=100)
def get_agent_skills(agent_id: str) -> AgentSkills:
    """缓存坐席技能，避免重复查询 Redis"""
    return redis.hgetall(f"agent:{agent_id}:skills")

@lru_cache(maxsize=50)
def get_sla_config(priority: str, ticket_type: str) -> SLAConfig:
    """缓存 SLA 配置"""
    return redis.hgetall(f"sla_config:{priority}:{ticket_type}")
```

---

### 5.2 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                     客户端层                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ 用户端 Vue   │  │ 坐席工作台   │  │ 管理员后台   │      │
│  │ (客户聊天)   │  │ (工单处理)   │  │ (系统配置)   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            ↓ HTTPS
┌─────────────────────────────────────────────────────────────┐
│                     API网关层                                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ FastAPI 后端 (backend.py)                            │   │
│  │ - OAuth+JWT 鉴权                                     │   │
│  │ - 坐席权限中间件                                     │   │
│  │ - 速率限制 (20请求/分钟)                             │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     业务逻辑层                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ 会话管理    │ │ 工单管理    │ │ SLA管理     │           │
│  │ (session)   │ │ (ticket)    │ │ (sla_timer) │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ 智能分配    │ │ 自动化引擎  │ │ 审计日志    │           │
│  │ (assignment)│ │ (automation)│ │ (audit_log) │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     数据持久层                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Redis        │  │ MySQL/PG     │  │ OSS/S3       │      │
│  │ (热数据)     │  │ (归档数据)   │  │ (附件存储)   │      │
│  │ - 活跃工单   │  │ - 历史工单   │  │ - 图片/文档  │      │
│  │ - 会话状态   │  │ - 审计日志   │  │ - 视频       │      │
│  │ - SLA状态    │  │ - 统计报表   │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     外部集成层                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Coze AI      │  │ Shopify      │  │ 邮件服务     │      │
│  │ (AI对话)     │  │ (订单查询)   │  │ (通知)       │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### 5.3 核心模块设计

#### 5.3.1 智能分配模块

**输入**: 新工单（Ticket）
**输出**: 分配坐席ID（agent_id）

**算法流程**:
```
1. 获取在线坐席列表
2. 技能匹配（ticket.category → agent.skills.tags）
3. 历史服务记录查询（同一客户优先分配给熟悉的坐席）
4. 负载均衡（选择当前工单数最少的坐席）
5. 返回推荐坐席
```

**性能要求**:
- 响应时间: < 100ms（50个坐席）
- 匹配准确率: > 90%

#### 5.3.2 自动化引擎模块

**规则结构**:
```
Rule {
  id: string
  name: string
  priority: number              // 执行优先级（数字越小越优先）
  trigger_event: string         // 触发事件: "ticket_created", "customer_replied"
  conditions: Condition[]       // 触发条件（AND关系）
  actions: Action[]             // 执行动作
  is_active: boolean
}
```

**执行流程**:
```
1. 监听事件（ticket_created, status_changed, customer_replied等）
2. 按优先级遍历规则
3. 检查条件是否满足
4. 执行动作（修改状态、发送通知、分配坐席等）
5. 记录执行日志
```

**性能要求**:
- 规则匹配: < 50ms（20个规则）
- 动作执行: < 100ms

#### 5.3.3 SLA计时模块

**计时逻辑**:
```
首次响应时效（FRT）:
  开始: 工单创建时间
  结束: 坐席首次回复时间
  暂停: 不支持暂停

解决时效（RT）:
  开始: 工单创建时间
  结束: 标记为"已解决"时间
  暂停: 状态为"等待客户"或"等待第三方"时暂停
```

**状态判断**:
```
normal:   剩余时间 > 50%
warning:  50% >= 剩余时间 > 20%
urgent:   20% >= 剩余时间 > 0%
violated: 剩余时间 <= 0%
```

**性能要求**:
- 状态更新频率: 每分钟
- 更新速度: < 5秒（1000个工单）

---

### ⭐ 5.4 数据流与事件流

#### 5.4.1 完整业务循环数据流

**核心理念**：客户-AI客服-后端-坐席工作台形成完整的数据闭环，每个环节的数据变更都会触发相应的事件流，确保系统各部分实时同步。

**完整数据流图**：

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        完整业务循环数据流                                 │
└──────────────────────────────────────────────────────────────────────────┘

┌─────────────┐
│   客户端    │
│  (Vue用户端) │
└──────┬──────┘
       │ ① 用户输入消息
       │ POST /api/chat
       │ {
       │   "message": "我的电池续航只有20公里",
       │   "user_id": "session_abc123"
       │ }
       ↓
┌──────────────────────────────────────────────────────────────┐
│                     FastAPI 后端                             │
│                                                              │
│  ② 数据处理流程                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │ a. OAuth+JWT 验证                                  │    │
│  │    → token_manager.get_access_token(session_name)  │    │
│  │                                                     │    │
│  │ b. 会话状态检查                                     │    │
│  │    → session_state.get(session_name)               │    │
│  │    → if status == manual_live: 返回 409            │    │
│  │                                                     │    │
│  │ c. 监管引擎检测                                     │    │
│  │    → regulator.check(message)                      │    │
│  │    → 检测关键词["电池","续航"]                      │    │
│  │    → 触发升级: set_status(pending_manual)          │    │
│  │                                                     │    │
│  │ d. 调用 Coze API                                   │    │
│  │    → POST https://api.coze.com/v1/workflow/stream │    │
│  │    → SSE 流式响应                                   │    │
│  │                                                     │    │
│  │ e. 智能分配坐席(如需升级)                          │    │
│  │    → smart_assignment.assign(session_name)         │    │
│  │    → 技能匹配 + 负载均衡                           │    │
│  │    → 创建工单: POST /api/sessions/{id}/ticket      │    │
│  │                                                     │    │
│  │ f. Redis 状态更新                                   │    │
│  │    → redis.hset(f"session:{session_name}", ...)    │    │
│  │    → redis.hset(f"ticket:{ticket_id}", ...)        │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ③ SSE 事件推送                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │ → 推送到客户端: ai_message                         │    │
│  │ → 推送到坐席工作台: new_session, session_assigned │    │
│  └────────────────────────────────────────────────────┘    │
└──────┬───────────────────────────────────────┬──────────────┘
       │ ④ SSE 推送                            │ ⑤ API 调用
       │ ai_message                            │ 接入/发送
       ↓                                       ↓
┌─────────────┐                        ┌─────────────┐
│   客户端    │                        │ 坐席工作台  │
│  显示AI回复 │                        │ (Vue坐席端) │
└─────────────┘                        └──────┬──────┘
                                              │ ⑥ 坐席操作
                                              │ POST /api/manual/messages
                                              │ {
                                              │   "session_name": "session_abc123",
                                              │   "content": "请问您充电时是否充满?"
                                              │ }
                                              ↓
                                       ┌──────────────┐
                                       │  后端处理    │
                                       │  → 保存消息  │
                                       │  → SSE推送   │
                                       └──────┬───────┘
                                              │ ⑦ SSE 推送
                                              │ manual_message
                                              ↓
                                       ┌─────────────┐
                                       │   客户端    │
                                       │ 显示人工回复 │
                                       └─────────────┘
```

#### 5.4.2 事件流编排图

**关键事件序列**：展示不同场景下的事件触发和传播路径

**场景1：客户发起咨询 → AI响应**

```
时间轴                事件                      数据变化                    通知对象
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
T0      客户发送消息           message: "电池问题"         -
        ↓                     session_name: "session_abc"

T1      后端接收请求           -                          -
        ↓

T2      会话状态检查           session_state.status       -
        ↓                     = bot_active

T3      调用 Coze API         conversation_id保存        -
        ↓

T4      AI开始响应            -                          SSE → 客户端
        ↓                                                (type: ai_message)

T5      监管引擎检测           检测到关键词"电池"          -
        ↓                     触发升级规则

T6      状态变更              session_state.status       SSE → 客户端
        ↓                     = pending_manual           (type: status_change)

T7      创建工单              ticket创建                 -
        ↓                     ticket_id: TKT-001

T8      智能分配              ticket.assigned_to         SSE → 坐席工作台
        ↓                     = agent_123                (type: new_session)

T9      SLA计时启动           ticket.sla_frt_target      -
        ↓                     = 10分钟

T10     通知完成              -                          SSE → agent_123
                                                         (type: session_assigned)
```

**场景2：坐席接入 → 双向通信**

```
时间轴                事件                      数据变化                    通知对象
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
T0      坐席点击"接入"         -                          -
        ↓

T1      PUT /api/sessions/     session_state.status       SSE → 客户端
        {id}/assign           = manual_live              (type: status_change,
        ↓                     assigned_agent=agent_123    content: "人工客服接入")

T2      加载会话历史           从Redis获取messages        -
        ↓

T3      坐席发送消息           message保存到Redis         SSE → 客户端
        ↓                                                (type: manual_message)

T4      客户回复消息           message保存到Redis         SSE → 坐席工作台
        ↓                                                (type: customer_replied)

T5      SLA状态更新           sla_frt_status=normal      SSE → 坐席工作台
        (定时任务)            frt_remaining=8分钟        (type: sla_update)
        ↓

T6      坐席标记"已解决"       ticket.status=resolved     SSE → 客户端
        ↓                     resolved_at=now()          (type: ticket_resolved)

T7      自动回复触发           automation_rule执行        SSE → 客户端
        ↓                     发送确认消息                (type: auto_reply)

T8      结束会话              session_state.status       SSE → 客户端
        ↓                     = bot_active               (type: session_ended)

T9      SLA计时停止           sla记录保存                -
```

#### 5.4.3 数据同步机制

**单一数据源原则**：

```
┌──────────────────────────────────────────────────────────────┐
│                  数据一致性保证机制                          │
└──────────────────────────────────────────────────────────────┘

                    Redis (后端)
                    ↓
        真实数据源 (Single Source of Truth)
        ├─ session_state:{session_name}
        ├─ ticket:{ticket_id}
        ├─ agent:{agent_id}:workload
        └─ conversation:{conversation_id}
                    ↓
        ┌───────────┴───────────┐
        ↓                       ↓
    客户端 (只读副本)      坐席工作台 (只读副本)
    ↓                       ↓
    通过 SSE 自动同步      通过 SSE 自动同步
    不可直接修改            不可直接修改
    ↓                       ↓
    需修改 → API请求 → 后端Redis → SSE推送回前端
```

**数据流向规则**：

1. **写入路径**（单向）：
   ```
   前端 → API请求 → 后端验证 → Redis更新 → SSE推送 → 前端更新
   ```

2. **读取路径**（双向）：
   ```
   前端 → API请求 → Redis读取 → 返回数据
   前端 ← SSE推送 ← Redis变更 ← 其他操作触发
   ```

3. **冲突解决**：
   ```python
   # 乐观锁机制
   def update_session_state(session_name: str, updates: dict):
       # 1. 获取当前版本
       current = redis.hgetall(f"session:{session_name}")
       version = int(current.get("version", 0))

       # 2. 检查版本冲突
       if updates.get("expected_version") != version:
           raise HTTPException(409, "VERSION_CONFLICT")

       # 3. 更新数据
       updates["version"] = version + 1
       redis.hmset(f"session:{session_name}", updates)

       # 4. 推送 SSE
       await notify_all_subscribers(session_name, updates)
   ```

#### 5.4.4 关键数据流详解

**数据流1：会话状态变更流**

```python
# 触发点：坐席接入会话
@app.put("/api/sessions/{session_name}/assign")
async def assign_session(session_name: str, agent_id: str):
    # 1. 更新 Redis 状态（数据源）
    session_state = get_session_state(session_name)
    session_state.status = SessionStatus.MANUAL_LIVE
    session_state.assigned_agent = agent_id
    session_state.updated_at = datetime.now()
    redis.hmset(f"session:{session_name}", session_state.dict())

    # 2. 推送 SSE 到客户端
    await sse_queues[session_name].put({
        "type": "status_change",
        "status": "manual_live",
        "agent_name": get_agent_name(agent_id),
        "message": f"人工客服 {get_agent_name(agent_id)} 为您服务"
    })

    # 3. 推送 SSE 到坐席工作台
    await sse_queues[f"agent_{agent_id}"].put({
        "type": "session_assigned",
        "session_name": session_name,
        "customer_email": session_state.customer_email,
        "conversation_history": get_messages(session_name)
    })

    # 4. 更新坐席负载
    increment_agent_workload(agent_id)

    # 5. 记录审计日志
    audit_log.record({
        "event": "session_assigned",
        "session_name": session_name,
        "agent_id": agent_id,
        "timestamp": datetime.now()
    })
```

**数据流2：工单SLA更新流**

```python
# 定时任务：每分钟执行
@scheduler.scheduled_job('cron', minute='*')
async def update_all_sla_status():
    # 1. 获取所有活跃工单
    active_tickets = redis.smembers("tickets:active")

    for ticket_id in active_tickets:
        # 2. 计算 SLA 状态
        ticket = json.loads(redis.get(f"ticket:{ticket_id}"))
        sla_timer = SLATimer(ticket)

        new_status = sla_timer.get_status()
        frt_remaining = sla_timer.get_frt_remaining()

        # 3. 检测状态变化
        if ticket["sla_status"] != new_status:
            # 4. 更新 Redis
            ticket["sla_status"] = new_status
            ticket["frt_remaining"] = frt_remaining
            redis.set(f"ticket:{ticket_id}", json.dumps(ticket))

            # 5. 推送 SSE 到坐席工作台
            if ticket["assigned_to"]:
                await sse_queues[f"agent_{ticket['assigned_to']}"].put({
                    "type": "sla_alert" if new_status in ["urgent", "violated"] else "sla_update",
                    "ticket_id": ticket_id,
                    "sla_status": new_status,
                    "frt_remaining": frt_remaining,
                    "level": "urgent" if frt_remaining < 2 else "warning"
                })
```

**数据流3：人工消息推送流**

```python
# 坐席发送消息
@app.post("/api/manual/messages")
async def send_manual_message(request: dict):
    session_name = request["session_name"]
    content = request["content"]
    agent_id = request["agent_id"]

    # 1. 构建消息对象
    message = {
        "id": generate_message_id(),
        "session_name": session_name,
        "type": "manual",
        "sender": "agent",
        "sender_id": agent_id,
        "sender_name": get_agent_name(agent_id),
        "content": content,
        "timestamp": datetime.now().isoformat()
    }

    # 2. 保存到 Redis 消息列表
    redis.lpush(f"messages:{session_name}", json.dumps(message))

    # 3. 更新会话状态
    redis.hset(f"session:{session_name}", "last_message_at", message["timestamp"])

    # 4. 更新工单首次响应时间（如果是首次）
    ticket = get_ticket_by_session(session_name)
    if ticket and not ticket.get("first_response_at"):
        redis.hset(f"ticket:{ticket['ticket_id']}", "first_response_at", message["timestamp"])

    # 5. 推送 SSE 到客户端（实时显示）
    await sse_queues[session_name].put({
        "type": "manual_message",
        "message": message,
        "agent_name": message["sender_name"]
    })

    # 6. 推送确认到坐席工作台
    await sse_queues[f"agent_{agent_id}"].put({
        "type": "message_sent",
        "message_id": message["id"],
        "status": "delivered"
    })

    # 7. 记录日志
    logger.info(f"[Manual Message] {agent_id} → {session_name}: {content[:50]}")
```

#### 5.4.5 事件优先级与处理顺序

**事件优先级定义**：

| 优先级 | 事件类型 | 处理延迟 | 说明 |
|-------|---------|---------|------|
| **P0 - 紧急** | sla_alert (violated) | < 10ms | SLA已违规，立即通知 |
| **P1 - 高** | manual_message, customer_replied | < 50ms | 实时消息，立即推送 |
| **P2 - 中** | status_change, session_assigned | < 100ms | 状态变更，快速推送 |
| **P3 - 低** | sla_update, ticket_updated | < 500ms | 定期更新，可延迟 |

**处理队列机制**：

```python
# 优先级队列实现
import heapq

class PrioritySSEQueue:
    def __init__(self):
        self.queue = []
        self.counter = 0

    async def put(self, event: dict):
        priority = self.get_priority(event["type"])
        # 使用计数器确保相同优先级按时间顺序
        heapq.heappush(self.queue, (priority, self.counter, event))
        self.counter += 1

    async def get(self):
        if self.queue:
            _, _, event = heapq.heappop(self.queue)
            return event
        return None

    def get_priority(self, event_type: str) -> int:
        priority_map = {
            "sla_alert": 0,      # P0
            "manual_message": 1,  # P1
            "customer_replied": 1,
            "status_change": 2,   # P2
            "session_assigned": 2,
            "sla_update": 3,      # P3
            "ticket_updated": 3
        }
        return priority_map.get(event_type, 4)
```

---

## 6. 数据与权限设计

### 6.1 数据模型扩展

#### 6.1.1 工单对象（增强版）

```typescript
interface Ticket {
  // ===== 基础信息 =====
  ticket_id: string                   // 工单ID: TKT-20250127-001
  ticket_type: "pre_sale" | "after_sale" | "complaint"
  category: string                    // 问题分类
  priority: "low" | "medium" | "high" | "urgent"
  status: TicketStatus
  title: string
  description: string

  // ===== 客户信息 =====
  customer_email: string
  customer_name: string
  customer_phone: string | null
  customer_is_vip: boolean            // ⭐ 新增

  // ===== 分配信息 =====
  created_by: string
  assigned_to: string | null
  assigned_skills: string[]           // ⭐ 新增：分配时匹配的技能

  // ===== 时间戳 =====
  created_at: Date
  updated_at: Date
  first_response_at: Date | null      // SLA关键时间
  resolved_at: Date | null            // SLA关键时间
  closed_at: Date | null

  // ===== SLA信息 =====
  sla_frt_target: number              // ⭐ 新增：首次响应目标（分钟）
  sla_frt_remaining: number           // ⭐ 新增：首次响应剩余（分钟）
  sla_frt_status: "normal" | "warning" | "urgent" | "violated"  // ⭐ 新增
  sla_rt_target: number               // ⭐ 新增：解决时效目标（小时）
  sla_rt_remaining: number            // ⭐ 新增：解决时效剩余（小时）
  sla_rt_status: "normal" | "warning" | "urgent" | "violated"   // ⭐ 新增
  sla_paused: boolean                 // ⭐ 新增：SLA是否暂停
  sla_paused_duration: number         // ⭐ 新增：暂停总时长（分钟）

  // ===== 协作信息 =====
  comments_count: number              // ⭐ 新增：评论数量
  attachments_count: number           // ⭐ 新增：附件数量
  mentions: string[]                  // ⭐ 新增：@提到的坐席列表

  // ===== 自动化信息 =====
  auto_assigned: boolean              // ⭐ 新增：是否自动分配
  auto_rules_applied: string[]        // ⭐ 新增：应用的自动化规则ID

  // ===== 关联数据 =====
  related_order_id: string | null
  related_session_id: string | null
  tags: string[]

  // ===== 重开相关 =====
  reopened_count: number
  reopened_at: Date | null
}
```

#### 6.1.2 坐席对象（增强版）

```typescript
interface Agent {
  // ===== 基础信息 =====
  id: string
  username: string
  name: string
  avatar_url: string | null
  role: "admin" | "supervisor" | "agent"

  // ===== 技能信息 =====
  skills: {                           // ⭐ 新增
    category: string                  // "product", "logistics", "tech"
    level: "junior" | "intermediate" | "senior"
    tags: string[]                    // ["battery", "motor", "shipping"]
  }

  // ===== 权限信息 =====
  permissions: Permission[]           // ⭐ 新增：细粒度权限

  // ===== 状态信息 =====
  status: AgentStatus
  max_sessions: number
  current_tickets: number             // ⭐ 新增：当前处理工单数

  // ===== 统计信息 =====
  today_stats: {                      // ⭐ 新增
    processed_count: number
    avg_response_time: number         // 秒
    avg_duration: number              // 秒
    satisfaction_score: number        // 1-5
  }
}
```

#### 6.1.3 自动化规则对象

```typescript
interface AutomationRule {
  id: string
  name: string
  description: string
  priority: number                    // 执行优先级（数字越小越优先）
  is_active: boolean

  // ===== 触发条件 =====
  trigger_event: "ticket_created" | "status_changed" | "customer_replied" | "sla_alert"
  conditions: {
    field: string                     // "customer.is_vip", "ticket.category"
    operator: "eq" | "neq" | "contains" | "gt" | "lt"
    value: any
  }[]

  // ===== 执行动作 =====
  actions: {
    type: "set_priority" | "assign_agent" | "add_tag" | "send_reply" | "change_status"
    params: Record<string, any>
  }[]

  // ===== 统计信息 =====
  execution_count: number
  last_executed_at: Date | null
  created_by: string
  created_at: Date
}
```

### 6.2 权限矩阵设计

#### 6.2.1 权限枚举

```typescript
enum Permission {
  // 工单权限
  VIEW_TICKET = "view_ticket",
  CREATE_TICKET = "create_ticket",
  EDIT_TICKET = "edit_ticket",
  DELETE_TICKET = "delete_ticket",
  ASSIGN_TICKET = "assign_ticket",
  EXPORT_TICKET = "export_ticket",

  // 协作权限
  ADD_COMMENT = "add_comment",
  EDIT_COMMENT = "edit_comment",
  DELETE_COMMENT = "delete_comment",
  UPLOAD_ATTACHMENT = "upload_attachment",

  // 模板权限
  VIEW_TEMPLATE = "view_template",
  MANAGE_TEMPLATE = "manage_template",

  // 自动化权限
  VIEW_AUTOMATION = "view_automation",
  MANAGE_AUTOMATION = "manage_automation",

  // 审计权限
  VIEW_AUDIT_LOG = "view_audit_log",

  // 坐席管理权限
  MANAGE_AGENT = "manage_agent",

  // SLA权限
  VIEW_SLA = "view_sla",
  MANAGE_SLA = "manage_sla"
}
```

#### 6.2.2 角色-权限映射

| 角色 | 权限 | 说明 |
|-----|------|------|
| **admin** | ALL | 所有权限 |
| **supervisor** | VIEW_TICKET, EDIT_TICKET, ASSIGN_TICKET, EXPORT_TICKET, MANAGE_TEMPLATE, VIEW_SLA, VIEW_AUDIT_LOG | 主管权限 |
| **agent** | VIEW_TICKET, CREATE_TICKET, EDIT_TICKET, ASSIGN_TICKET, ADD_COMMENT, UPLOAD_ATTACHMENT, VIEW_TEMPLATE | 普通坐席权限 |

#### 6.2.3 权限检查实现

```python
def require_permission(permission: Permission):
    """权限检查装饰器"""
    def decorator(func):
        async def wrapper(*args, agent: Dict = Depends(require_agent), **kwargs):
            # 管理员拥有所有权限
            if agent.get("role") == "admin":
                return await func(*args, agent=agent, **kwargs)

            # 检查坐席权限
            agent_obj = agent_manager.get_agent_by_username(agent["username"])
            if permission not in agent_obj.permissions:
                raise HTTPException(403, f"PERMISSION_DENIED: 需要权限 {permission}")

            return await func(*args, agent=agent, **kwargs)
        return wrapper
    return decorator

# 使用示例
@app.delete("/api/tickets/{ticket_id}")
@require_permission(Permission.DELETE_TICKET)
async def delete_ticket(ticket_id: str, agent: Dict):
    pass
```

### 6.3 数据存储策略

#### 6.3.1 Redis（热数据）

**用途**: 活跃工单、会话状态、SLA状态

**TTL策略**:
- 活跃工单（pending/in_progress）: 无TTL
- 已解决工单（resolved）: 7天
- 已关闭工单（closed）: 30天
- 会话状态: 24小时

**Key设计**:
```
ticket:{ticket_id}                    // 工单对象
ticket:sla:{ticket_id}                // SLA状态
ticket:comments:{ticket_id}           // 评论列表（List）
session:{session_name}                // 会话状态
agent:{agent_id}:stats:{YYYYMMDD}     // 坐席每日统计
automation:rule:{rule_id}             // 自动化规则
```

#### 6.3.2 MySQL/PostgreSQL（冷数据）

**用途**: 归档工单、审计日志、长期统计

**表结构**:
```sql
-- 归档工单表
CREATE TABLE archived_tickets (
  ticket_id VARCHAR(50) PRIMARY KEY,
  data JSON NOT NULL,              -- 工单完整数据
  archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_customer_email (data->'customer_email'),
  INDEX idx_created_at (data->'created_at')
);

-- 审计日志表
CREATE TABLE audit_logs (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  operator_id VARCHAR(50) NOT NULL,
  operation VARCHAR(50) NOT NULL,
  target_type VARCHAR(20) NOT NULL,
  target_id VARCHAR(50) NOT NULL,
  changes JSON,
  ip_address VARCHAR(45),
  user_agent VARCHAR(200),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_operator (operator_id, created_at),
  INDEX idx_target (target_type, target_id)
);
```

#### 6.3.3 OSS/S3（文件存储）

**用途**: 附件存储（图片、文档、视频）

**目录结构**:
```
/tickets/{ticket_id}/attachments/
  - {timestamp}_{filename}.jpg
  - {timestamp}_{filename}.pdf
```

**访问控制**:
- 公开附件: 客户和坐席都可访问
- 内部附件: 仅坐席可访问（带签名URL）

---

## 7. 后续建议

### 7.1 性能优化

#### 7.1.1 数据库优化

**问题**: Redis扫描 `scan_iter("ticket:*")` 性能低

**解决方案**:
1. **使用索引集合**: 维护工单索引（按状态、优先级）
   ```python
   # 创建索引
   redis.sadd("tickets:pending", ticket_id)
   redis.sadd("tickets:priority:high", ticket_id)

   # 快速查询
   pending_tickets = redis.smembers("tickets:pending")
   ```

2. **分页查询**: 避免一次性加载所有工单
   ```python
   # 使用ZSCORE实现分页
   redis.zadd("tickets:all", {ticket_id: created_at})
   redis.zrevrange("tickets:all", start=0, end=49)  # 前50条
   ```

#### 7.1.2 缓存优化

**问题**: 重复查询坐席技能、SLA配置

**解决方案**:
1. **使用Redis缓存**: 缓存坐席技能、SLA配置（TTL 1小时）
   ```python
   @cache(ttl=3600)
   def get_agent_skills(agent_id: str) -> AgentSkills:
       pass
   ```

2. **本地内存缓存**: 使用LRU缓存热点数据
   ```python
   from functools import lru_cache

   @lru_cache(maxsize=100)
   def get_sla_config(priority: str, ticket_type: str) -> SLAConfig:
       pass
   ```

#### 7.1.3 批量操作优化

**问题**: 批量分配50个工单时串行执行慢

**解决方案**:
1. **并发执行**: 使用asyncio并发处理
   ```python
   async def batch_assign_tickets(ticket_ids: List[str], agent_id: str):
       tasks = [assign_ticket(tid, agent_id) for tid in ticket_ids]
       await asyncio.gather(*tasks)
   ```

2. **Redis Pipeline**: 批量写入
   ```python
   pipe = redis.pipeline()
   for ticket in tickets:
       pipe.set(f"ticket:{ticket.ticket_id}", json.dumps(ticket))
   pipe.execute()
   ```

### 7.2 监控与告警

#### 7.2.1 性能监控

**关键指标**:
- API响应时间（P50, P95, P99）
- 工单处理速度（创建到关闭的平均时长）
- SLA达成率（首次响应、解决时效）
- 自动化成功率

**监控工具**:
- **Prometheus**: 采集指标
- **Grafana**: 可视化仪表盘
- **Alertmanager**: 告警推送

**示例仪表盘**:
```
┌─────────────────────────────────────┐
│ API响应时间                         │
│ P50: 120ms  P95: 450ms  P99: 1.2s  │
├─────────────────────────────────────┤
│ SLA达成率（本周）                   │
│ 首次响应: 92%  解决时效: 88%        │
├─────────────────────────────────────┤
│ 自动化率                            │
│ 自动分配: 78%  自动回复: 65%        │
└─────────────────────────────────────┘
```

#### 7.2.2 业务告警

**告警规则**:
1. **SLA达成率 < 85%**: 发送邮件给主管
2. **等待队列 > 50**: 发送钉钉通知
3. **API错误率 > 1%**: 发送短信给开发
4. **Redis内存使用 > 80%**: 发送邮件给运维

**告警示例**:
```
🚨 SLA告警

当前SLA达成率: 82% (低于85%阈值)
首次响应违规: 18次
解决时效违规: 12次

主要原因:
- 坐席人手不足（当前在线: 3人，需要: 5人）
- 复杂问题积压（技术支持类工单: 15个）

建议措施:
1. 增加在线坐席
2. 技术支持组加班处理
```

### 7.3 测试策略

#### 7.3.1 单元测试

**覆盖模块**:
- 智能分配算法（`src/ticket_assignment.py`）
- SLA计时逻辑（`src/sla_timer.py`）
- 自动化规则引擎（`src/automation_engine.py`）

**示例测试**:
```python
# tests/test_smart_assignment.py
import pytest
from src.ticket_assignment import smart_assign_ticket

def test_skill_matching():
    """测试技能匹配"""
    ticket = Ticket(category="battery")
    agents = [
        Agent(id="a1", skills={"tags": ["battery"]}),
        Agent(id="a2", skills={"tags": ["motor"]})
    ]

    assigned = smart_assign_ticket(ticket, agents)
    assert assigned == "a1"

def test_load_balancing():
    """测试负载均衡"""
    ticket = Ticket(category="battery")
    agents = [
        Agent(id="a1", skills={"tags": ["battery"]}, current_tickets=5),
        Agent(id="a2", skills={"tags": ["battery"]}, current_tickets=3)
    ]

    assigned = smart_assign_ticket(ticket, agents)
    assert assigned == "a2"  # 选择工单数少的
```

**目标覆盖率**: 80%

#### 7.3.2 集成测试

**测试场景**:
1. **端到端工单流程**: 创建 → 分配 → 评论 → 解决 → 关闭
2. **自动化规则触发**: VIP客户创建工单 → 自动设置高优先级 → 分配VIP坐席
3. **SLA超时预警**: 工单创建 → 等待超时 → 推送预警通知

**示例测试**:
```bash
#!/bin/bash
# tests/test_e2e_ticket_workflow.sh

echo "测试1: 完整工单流程"

# 1. 创建工单
TICKET_ID=$(curl -X POST "$BASE_URL/api/tickets/create" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "customer_email": "test@example.com",
    "title": "电池续航问题",
    "category": "battery"
  }' | jq -r '.ticket_id')

echo "工单创建成功: $TICKET_ID"

# 2. 验证自动分配
ASSIGNED=$(curl "$BASE_URL/api/tickets/$TICKET_ID" \
  -H "Authorization: Bearer $TOKEN" \
  | jq -r '.assigned_to')

if [ -z "$ASSIGNED" ]; then
  echo "❌ 自动分配失败"
  exit 1
else
  echo "✅ 自动分配成功: $ASSIGNED"
fi

# 3. 添加评论
curl -X POST "$BASE_URL/api/tickets/$TICKET_ID/comments" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "comment_type": "public",
    "content": "我们正在处理您的问题"
  }'

echo "✅ 评论添加成功"

# 4. 标记解决
curl -X PATCH "$BASE_URL/api/tickets/$TICKET_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"status": "resolved"}'

echo "✅ 工单标记解决"

# 5. 验证SLA记录
RESOLVED_AT=$(curl "$BASE_URL/api/tickets/$TICKET_ID" \
  -H "Authorization: Bearer $TOKEN" \
  | jq -r '.resolved_at')

if [ -z "$RESOLVED_AT" ]; then
  echo "❌ SLA记录缺失"
  exit 1
else
  echo "✅ SLA记录完整: $RESOLVED_AT"
fi
```

#### 7.3.3 压力测试

**测试目标**:
- 100并发用户
- 1000个工单同时处理
- SLA状态更新不延迟

**测试工具**: Apache Bench, Locust

**示例脚本**:
```python
# tests/load_test.py
from locust import HttpUser, task, between

class WorkbenchUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # 登录获取token
        response = self.client.post("/api/agent/login", json={
            "username": "agent001",
            "password": "agent123"
        })
        self.token = response.json()["token"]

    @task(3)
    def view_tickets(self):
        """查看工单列表（高频操作）"""
        self.client.get("/api/tickets", headers={
            "Authorization": f"Bearer {self.token}"
        })

    @task(2)
    def create_ticket(self):
        """创建工单（中频操作）"""
        self.client.post("/api/tickets/create", headers={
            "Authorization": f"Bearer {self.token}"
        }, json={
            "customer_email": "test@example.com",
            "title": "测试工单",
            "category": "test"
        })

    @task(1)
    def export_tickets(self):
        """导出工单（低频操作）"""
        self.client.post("/api/tickets/export", headers={
            "Authorization": f"Bearer {self.token}"
        }, json={
            "format": "csv"
        })
```

**运行**:
```bash
locust -f tests/load_test.py --host=http://localhost:8000 --users=100 --spawn-rate=10
```

**通过标准**:
- API响应时间 P95 < 1秒
- 错误率 < 1%
- 无内存泄漏

### 7.4 部署建议

#### 7.4.1 Docker化部署

**Dockerfile**:
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "backend:app", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379/0
      - MYSQL_URL=mysql://user:pass@mysql:3306/fiido
    depends_on:
      - redis
      - mysql

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  mysql:
    image: mysql:8
    environment:
      MYSQL_ROOT_PASSWORD: rootpass
      MYSQL_DATABASE: fiido
    volumes:
      - mysql_data:/var/lib/mysql

volumes:
  redis_data:
  mysql_data:
```

#### 7.4.2 生产环境配置

**环境变量**（`.env.production`）:
```bash
# 数据库
REDIS_URL=redis://redis.prod.example.com:6379/0
MYSQL_URL=mysql://fiido_user:strong_password@mysql.prod.example.com:3306/fiido

# Coze API
COZE_API_BASE=https://api.coze.com
COZE_WORKFLOW_ID=7501234567890
COZE_APP_ID=7501234567891
COZE_OAUTH_CLIENT_ID=your_client_id

# JWT
JWT_SECRET_KEY=generate_strong_random_key_here

# 邮件服务
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=noreply@fiido.com
SMTP_PASSWORD=smtp_password

# OSS/S3
OSS_BUCKET=fiido-attachments
OSS_ACCESS_KEY=your_access_key
OSS_SECRET_KEY=your_secret_key

# 监控
SENTRY_DSN=https://...@sentry.io/...
```

#### 7.4.3 高可用部署

**架构**:
```
┌─────────────┐
│ Nginx LB    │  (负载均衡)
└─────┬───────┘
      │
      ├─────────┬─────────┬─────────┐
      │         │         │         │
┌─────▼───┐ ┌──▼─────┐ ┌─▼──────┐ ┌▼────────┐
│ Backend1│ │Backend2│ │Backend3│ │Backend4 │
└─────┬───┘ └──┬─────┘ └─┬──────┘ └┬────────┘
      │        │          │         │
      └────────┴──────────┴─────────┘
               │
      ┌────────▼────────┐
      │ Redis Cluster   │  (3主3从)
      └────────┬────────┘
               │
      ┌────────▼────────┐
      │ MySQL Master    │
      │ MySQL Slave1/2  │  (主从复制)
      └─────────────────┘
```

**配置建议**:
- **后端**: 4个实例（支持100+并发用户）
- **Redis**: 3主3从集群（支持10000+ TPS）
- **MySQL**: 1主2从（读写分离）
- **Nginx**: 2台（主备）

### 7.5 商业化要点

#### 7.5.1 定价策略

**分层定价**:

| 版本 | 价格 | 坐席数 | 工单/月 | 功能 |
|-----|------|-------|---------|------|
| **基础版** | ¥299/月 | 3个 | 500 | 基础工单、手动分配、CSV导出 |
| **专业版** | ¥999/月 | 10个 | 2000 | 智能分配、SLA监控、Excel/PDF导出、自动化规则（5个） |
| **企业版** | ¥2999/月 | 50个 | 无限 | 所有功能、自动化规则（无限）、API集成、技术支持 |

**增值服务**:
- 额外坐席: ¥100/人/月
- 额外工单包: ¥200/1000条
- 专属客服: ¥500/月

#### 7.5.2 数据安全

**合规要求**（跨境电商）:
1. **GDPR合规**: 客户数据可导出和删除
2. **数据加密**: 敏感字段（邮箱、电话）加密存储
3. **审计日志**: 保留90天操作日志
4. **数据备份**: 每天自动备份，保留30天

**实现**:
```python
# 敏感字段加密
from cryptography.fernet import Fernet

class EncryptedField:
    def __init__(self, key: bytes):
        self.cipher = Fernet(key)

    def encrypt(self, value: str) -> str:
        return self.cipher.encrypt(value.encode()).decode()

    def decrypt(self, value: str) -> str:
        return self.cipher.decrypt(value.encode()).decode()

# 使用
encryptor = EncryptedField(ENCRYPTION_KEY)
ticket.customer_email = encryptor.encrypt("user@example.com")
```

#### 7.5.3 SaaS化改造

**多租户设计**:
```typescript
interface Tenant {
  tenant_id: string
  company_name: string
  subscription_plan: "basic" | "pro" | "enterprise"
  max_agents: number
  max_tickets_per_month: number
  features: string[]              // ["smart_assign", "sla", "automation"]
  created_at: Date
  expires_at: Date
}

// 工单添加租户ID
interface Ticket {
  tenant_id: string               // ⭐ 多租户关键
  // ... 其他字段
}
```

**数据隔离**:
```python
# 所有查询自动添加租户过滤
def get_tickets(tenant_id: str, filters: dict):
    tickets = redis.scan_iter(f"tenant:{tenant_id}:ticket:*")
    # ...
```

---

## 8. 总结

### 8.1 开发进度概览

| 周期 | 功能模块 | 工期 | 增量数 | 测试脚本数 |
|-----|---------|------|--------|-----------|
| 周期1 | 智能分配与批量操作 | 2周 | 6 | 6 |
| 周期2 | 协作功能与工单模板 | 2周 | 7 | 7 |
| 周期3 | SLA可视化与自动化 | 3周 | 10 | 10 |
| 周期4 | 多格式导出与权限 | 2周 | 6 | 6 |
| **总计** | **4个阶段** | **9周** | **29个增量** | **29个测试** |

### 8.2 核心成果

**功能完整度提升**:
- 从当前 40% → 目标 90%（对标Zendesk/聚水潭）

**效率提升**:
- 工单处理效率提升 **60%**（智能分配+批量操作）
- 复杂工单处理提升 **70%**（协作功能）
- 自动化率提升至 **70%**（自动化引擎）
- SLA达成率提升至 **95%**（实时监控）

**技术债务**:
- 0个（严格遵守增量开发原则）
- 回归测试覆盖率 **100%**
- 单元测试覆盖率 **80%**

### 8.3 风险与应对

| 风险 | 可能性 | 影响 | 应对措施 |
|-----|-------|------|---------|
| Redis内存不足 | 中 | 高 | 提前归档、增加容量 |
| 自动化规则冲突 | 低 | 中 | 优先级排序、冲突检测 |
| SLA计时不准确 | 低 | 高 | 充分测试、监控告警 |
| 导出性能差 | 中 | 低 | 限制导出数量、异步生成 |
| 权限混乱 | 低 | 高 | 细粒度权限、审计日志 |

---

## 附录

### 附录A: 开发规范检查清单

每个增量提交前必须检查：

- [ ] 开发时间 < 2小时
- [ ] 修改文件 < 5个（后端）或 < 3个组件（前端）
- [ ] 代码变更 < 300行
- [ ] 已完成自测
- [ ] 已编写测试脚本（后端必须）
- [ ] 回归测试通过（`./tests/regression_test.sh`）
- [ ] 前端UI功能已通过用户测试（如适用）
- [ ] 测试已集成到回归测试套件
- [ ] commit message清晰
- [ ] 已打版本tag（如v3.5.1）
- [ ] 文档已更新（`prd/04_任务拆解/`）

### 附录B: 关键API清单

| API | 方法 | 说明 | 周期 |
|-----|------|------|------|
| `/api/agents/{id}/skills` | PUT | 管理坐席技能 | 周期1 |
| `/api/tickets/batch/assign` | POST | 批量分配工单 | 周期1 |
| `/api/tickets/batch/close` | POST | 批量关闭工单 | 周期1 |
| `/api/tickets/{id}/comments` | GET/POST | 评论系统 | 周期2 |
| `/api/tickets/{id}/attachments` | POST | 上传附件 | 周期2 |
| `/api/templates` | GET/POST/PUT/DELETE | 工单模板 | 周期2 |
| `/api/sla/dashboard` | GET | SLA仪表盘数据 | 周期3 |
| `/api/automation/rules` | GET/POST/PUT/DELETE | 自动化规则 | 周期3 |
| `/api/tickets/export` | POST | 多格式导出（支持xlsx/pdf） | 周期4 |
| `/api/audit-logs` | GET | 审计日志查询 | 周期4 |

### 附录C: 参考文档

- [CONSTRAINTS_AND_PRINCIPLES.md](../02_约束与原则/CONSTRAINTS_AND_PRINCIPLES.md) - 核心约束
- [CLAUDE.md](../../CLAUDE.md) - 开发规范（铁律0-5）
- [L1-2-Part1_工单核心功能.md](../04_任务拆解/L1-2-Part1_工单核心功能.md) - 现有工单功能
- [L1-2-Part2_工单协作与自动化.md](../04_任务拆解/L1-2-Part2_工单协作与自动化.md) - 协作与自动化需求

---

**文档维护者**: Claude Code
**最后更新**: 2025-12-02
**文档状态**: ✅ 待评审
