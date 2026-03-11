<div align="center">
  <img src="weisensebot_logo.png" alt="weisensebot" width="500">
  <h1>weisensebot: 超轻量级个人AI助手</h1>
  <p>
    <a href="https://pypi.org/project/weisensebot-ai/"><img src="https://img.shields.io/pypi/v/weisensebot-ai" alt="PyPI"></a>
    <a href="https://pepy.tech/project/weisensebot-ai"><img src="https://static.pepy.tech/badge/weisensebot-ai" alt="下载量"></a>
    <img src="https://img.shields.io/badge/python-≥3.11-blue" alt="Python">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="许可证">
    <a href="./COMMUNICATION.md"><img src="https://img.shields.io/badge/Feishu-Group-E9DBFC?style=flat&logo=feishu&logoColor=white" alt="飞书"></a>
    <a href="./COMMUNICATION.md"><img src="https://img.shields.io/badge/WeChat-Group-C5EAB4?style=flat&logo=wechat&logoColor=white" alt="微信"></a>
    <a href="https://discord.gg/MnCvHqpUGB"><img src="https://img.shields.io/badge/Discord-Community-5865F2?style=flat&logo=discord&logoColor=white" alt="Discord"></a>
  </p>
</div>

🐈 **weisensebot** 是一款**超轻量级**的个人AI助手，类似[OpenClaw](https://github.com/openclaw/openclaw),基于港大团队(HKUDS)开源的[nanobot](https://github.com/HKUDS/nanobot)开发。

⚡️ 用比OpenClaw少**99%**的代码实现核心智能体功能。

📏 实时代码行数：运行 `bash core_agent_lines.sh` 随时验证。


## weisensebot核心特性：

🪶 **超轻量级**：核心智能体代码仅约4,000行 — 比Clawdbot小99%。

🔬 **研究就绪**：代码清晰、易读，易于理解、修改和扩展研究。

⚡️ **闪电般快速**：最小占用意味着更快的启动、更低的资源使用和更快的迭代。

💎 **易于使用**：一键部署，立即可用。

## 🏗️ 架构

<p align="center">
  <img src="weisensebot_arch.png" alt="weisensebot架构" width="800">
</p>

## ✨ 功能

<table align="center">
  <tr align="center">
    <th><p align="center">📈 7×24小时实时市场分析</p></th>
    <th><p align="center">🚀 全栈软件工程师</p></th>
    <th><p align="center">📅 智能日常管理助手</p></th>
    <th><p align="center">📚 个人知识助手</p></th>
  </tr>
  <tr>
    <td align="center"><p align="center"><img src="case/search.gif" width="180" height="400"></p></td>
    <td align="center"><p align="center"><img src="case/code.gif" width="180" height="400"></p></td>
    <td align="center"><p align="center"><img src="case/scedule.gif" width="180" height="400"></p></td>
    <td align="center"><p align="center"><img src="case/memory.gif" width="180" height="400"></p></td>
  </tr>
  <tr>
    <td align="center">发现 • 洞察 • 趋势</td>
    <td align="center">开发 • 部署 • 扩展</td>
    <td align="center">调度 • 自动化 • 组织</td>
    <td align="center">学习 • 记忆 • 推理</td>
  </tr>
</table>

## 📦 安装

**从源码安装**（最新功能，推荐用于开发）

```bash
git clone https://github.com/We-IOT/weisensebot.git
cd weisensebot
pip install -e .
```



## 🚀 快速开始

> [!TIP]
> 在 `~/.weisensebot/config.json` 中设置您的API密钥。
> 获取API密钥：[OpenRouter](https://openrouter.ai/keys)（全球）· [Brave Search](https://brave.com/search/api/)（可选，用于网络搜索）

**1. 初始化**

```bash
weisensebot onboard
```

**2. 配置**（`~/.weisensebot/config.json`）

将这**两部分**添加或合并到您的配置中（其他选项有默认值）。

*设置您的API密钥*（例如OpenRouter，推荐全球用户使用）：
```json
{
  "providers": {
    "openrouter": {
      "apiKey": "sk-or-v1-xxx"
    }
  }
}
```

*设置您的模型*（可选：固定提供商 — 默认自动检测）：
```json
{
  "agents": {
    "defaults": {
      "model": "anthropic/claude-opus-4-5",
      "provider": "openrouter"
    }
  }
}
```

**3. 聊天**

```bash
weisensebot agent
```

就这么简单！您在2分钟内就有了一个可用的AI助手。

## 💬 聊天应用

将weisensebot连接到您喜欢的聊天平台。

| 频道 | 所需信息 |
|---------|---------------|
| **Telegram** | 来自@BotFather的Bot令牌 |
| **Discord** | Bot令牌 + 消息内容意图 |
| **Feishu（飞书）** | App ID + App Secret |
| **DingTalk（钉钉）** | App Key + App Secret |
| **Slack** | Bot令牌 + 应用级令牌 |
| **Email（电子邮件）** | IMAP/SMTP凭据 |
| **QQ** | App ID + App Secret |
| **Wecom** | App ID + App Secret |

<details>
<summary><b>Telegram</b>（推荐）</summary>

**1. 创建bot**
- 打开Telegram，搜索`@BotFather`
- 发送`/newbot`，按照提示操作
- 复制令牌

**2. 配置**

```json
{
  "channels": {
    "telegram": {
      "enabled": true,
      "token": "YOUR_BOT_TOKEN",
      "allowFrom": ["YOUR_USER_ID"]
    }
  }
}
```

> 您可以在Telegram设置中找到您的**用户ID**。它显示为`@yourUserId`。
> 复制此值**不带`@`符号**并将其粘贴到配置文件中。


**3. 运行**

```bash
weisensebot gateway
```

</details>

<details>
<summary><b>Mochat (Claw IM)</b></summary>

默认使用**Socket.IO WebSocket**，支持HTTP轮询回退。

**1. 让weisensebot为您设置Mochat**

只需向weisensebot发送此消息（将`xxx@xxx`替换为您的真实邮箱）：

```
Read https://raw.githubusercontent.com/HKUDS/MoChat/refs/heads/main/skills/weisensebot/skill.md and register on MoChat. My Email account is xxx@xxx Bind me as your owner and DM me on MoChat.
```

weisensebot将自动注册、配置`~/.weisensebot/config.json`并连接到Mochat。

**2. 重启网关**

```bash
weisensebot gateway
```

就这样 — weisensebot会处理其余的工作！

<br>

<details>
<summary>手动配置（高级）</summary>

如果您更喜欢手动配置，请将以下内容添加到`~/.weisensebot/config.json`：

> 保持`claw_token`私密。它应该仅在`X-Claw-Token`头中发送到您的Mochat API端点。

```json
{
  "channels": {
    "mochat": {
      "enabled": true,
      "base_url": "https://mochat.io",
      "socket_url": "https://mochat.io",
      "socket_path": "/socket.io",
      "claw_token": "claw_xxx",
      "agent_user_id": "6982abcdef",
      "sessions": ["*"],
      "panels": ["*"],
      "reply_delay_mode": "non-mention",
      "reply_delay_ms": 120000
    }
  }
}
```



</details>

</details>

<details>
<summary><b>Discord</b></summary>

**1. 创建bot**
- 访问 https://discord.com/developers/applications
- 创建应用 → Bot → 添加Bot
- 复制bot令牌

**2. 启用意图**
- 在Bot设置中，启用**消息内容意图（MESSAGE CONTENT INTENT）**
- （可选）如果计划基于成员数据使用允许列表，启用**服务器成员意图（SERVER MEMBERS INTENT）**

**3. 获取您的用户ID**
- Discord设置 → 高级 → 启用**开发者模式**
- 右键点击您的头像 → **复制用户ID**

**4. 配置**

```json
{
  "channels": {
    "discord": {
      "enabled": true,
      "token": "YOUR_BOT_TOKEN",
      "allowFrom": ["YOUR_USER_ID"],
      "groupPolicy": "mention"
    }
  }
}
```

> `groupPolicy`控制bot在群组频道中的响应方式：
> - `"mention"`（默认） — 仅在@提及时响应
> - `"open"` — 响应所有消息
> 当发送者在`allowFrom`中时，DM（私信）始终响应。

**5. 邀请bot**
- OAuth2 → URL生成器
- 范围：`bot`
- Bot权限：`发送消息`、`读取消息历史`
- 打开生成的邀请URL并将bot添加到您的服务器

**6. 运行**

```bash
weisensebot gateway
```

</details>



<details>
<summary><b>Feishu（飞书）</b></summary>

使用**WebSocket**长连接 — 不需要公网IP。

**1. 创建飞书bot**
- 访问[飞书开放平台](https://open.feishu.cn/app)
- 创建新应用 → 启用**Bot**能力
- **权限**：添加`im:message`（发送消息）和`im:message.p2p_msg:readonly`（接收消息）
- **事件**：添加`im.message.receive_v1`（接收消息）
  - 选择**长连接**模式（需要先运行weisensebot以建立连接）
- 从"凭证与基础信息"获取**App ID**和**App Secret**
- 发布应用

**2. 配置**

```json
{
  "channels": {
    "feishu": {
      "enabled": true,
      "appId": "cli_xxx",
      "appSecret": "xxx",
      "encryptKey": "",
      "verificationToken": "",
      "allowFrom": ["ou_YOUR_OPEN_ID"]
    }
  }
}
```

> `encryptKey`和`verificationToken`在长连接模式下是可选的。
> `allowFrom`：添加您的open_id（向bot发送消息时可在weisensebot日志中找到）。使用`["*"]`允许所有用户。

**3. 运行**

```bash
weisensebot gateway
```

> [!TIP]
> 飞书使用WebSocket接收消息 — 不需要webhook或公网IP！

</details>

<details>
<summary><b>QQ（QQ单聊）</b></summary>

使用带有WebSocket的**botpy SDK** — 不需要公网IP。目前仅支持**私聊**。

**1. 注册并创建bot**
- 访问[QQ开放平台](https://q.qq.com) → 注册为开发者（个人或企业）
- 创建新的bot应用
- 转到**开发设置** → 复制**AppID**和**AppSecret**

**2. 设置沙箱进行测试**
- 在bot管理控制台中，找到**沙箱配置**
- 在**在消息列表配置**下，点击**添加成员**并添加您自己的QQ号码
- 添加后，使用手机QQ扫描bot的二维码 → 打开bot个人资料 → 点击"发消息"开始聊天

**3. 配置**

> - `allowFrom`：添加您的openid（向bot发送消息时可在weisensebot日志中找到）。使用`["*"]`进行公开访问。
> - 对于生产环境：在bot控制台中提交审核并发布。完整的发布流程请参阅[QQ Bot文档](https://bot.q.qq.com/wiki/)。

```json
{
  "channels": {
    "qq": {
      "enabled": true,
      "appId": "YOUR_APP_ID",
      "secret": "YOUR_APP_SECRET",
      "allowFrom": ["YOUR_OPENID"]
    }
  }
}
```

**4. 运行**

```bash
weisensebot gateway
```

现在从QQ向bot发送消息 — 它应该会响应！

</details>

<details>
<summary><b>DingTalk（钉钉）</b></summary>

使用**流模式（Stream Mode）** — 不需要公网IP。

**1. 创建钉钉bot**
- 访问[钉钉开放平台](https://open-dev.dingtalk.com/)
- 创建新应用 → 添加**机器人**能力
- **配置**：
  - 打开**流模式（Stream Mode）**
- **权限**：添加发送消息所需的权限
- 从"凭证"获取**AppKey**（客户端ID）和**AppSecret**（客户端密钥）
- 发布应用

**2. 配置**

```json
{
  "channels": {
    "dingtalk": {
      "enabled": true,
      "clientId": "YOUR_APP_KEY",
      "clientSecret": "YOUR_APP_SECRET",
      "allowFrom": ["YOUR_STAFF_ID"]
    }
  }
}
```

> `allowFrom`：添加您的员工ID。使用`["*"]`允许所有用户。

**3. 运行**

```bash
weisensebot gateway
```

</details>

<details>
<summary><b>Slack</b></summary>

使用**Socket模式（Socket Mode）** — 不需要公网URL。

**1. 创建Slack应用**
- 访问[Slack API](https://api.slack.com/apps) → **创建新应用** → "从零开始"
- 选择名称并选择您的工作区

**2. 配置应用**
- **Socket模式**：打开 → 生成具有`connections:write`范围的**应用级令牌** → 复制它（`xapp-...`）
- **OAuth与权限**：添加bot作用域：`chat:write`、`reactions:write`、`app_mentions:read`
- **事件订阅**：打开 → 订阅bot事件：`message.im`、`message.channels`、`app_mention` → 保存更改
- **应用首页**：滚动到**显示标签页** → 启用**消息标签页** → 勾选**"允许用户从消息标签页发送斜杠命令和消息"**
- **安装应用**：点击**安装到工作区** → 授权 → 复制**Bot令牌**（`xoxb-...`）

**3. 配置weisensebot**

```json
{
  "channels": {
    "slack": {
      "enabled": true,
      "botToken": "xoxb-...",
      "appToken": "xapp-...",
      "allowFrom": ["YOUR_SLACK_USER_ID"],
      "groupPolicy": "mention"
    }
  }
}
```

**4. 运行**

```bash
weisensebot gateway
```

直接向bot发送DM或在频道中@提及它 — 它应该会响应！

> [!TIP]
> - `groupPolicy`：`"mention"`（默认 — 仅在@提及时响应）、`"open"`（响应所有频道消息）或`"allowlist"`（限制到特定频道）。
> - DM策略默认为打开。设置`"dm": {"enabled": false}`以禁用DM。

</details>

<details>
<summary><b>Email（电子邮件）</b></summary>

为weisensebot创建自己的电子邮件账户。它通过**IMAP**轮询接收邮件并通过**SMTP**回复 — 就像个人电子邮件助手。

**1. 获取凭据（Gmail示例）**
- 为您的bot创建一个专用的Gmail账户（例如`my-weisensebot@gmail.com`）
- 启用两步验证 → 创建[应用密码](https://myaccount.google.com/apppasswords)
- 将此应用密码同时用于IMAP和SMTP

**2. 配置**

> - `consentGranted`必须为`true`以允许邮箱访问。这是一个安全闸门 — 设置为`false`以完全禁用。
> - `allowFrom`：添加您的电子邮件地址。使用`["*"]`接受来自任何人的电子邮件。
> - `smtpUseTls`和`smtpUseSsl`默认为`true`/`false`，这对于Gmail（端口587 + STARTTLS）是正确的。无需显式设置它们。
> - 如果您只想读取/分析电子邮件而不发送自动回复，请设置`"autoReplyEnabled": false`。

```json
{
  "channels": {
    "email": {
      "enabled": true,
      "consentGranted": true,
      "imapHost": "imap.gmail.com",
      "imapPort": 993,
      "imapUsername": "my-weisensebot@gmail.com",
      "imapPassword": "your-app-password",
      "smtpHost": "smtp.gmail.com",
      "smtpPort": 587,
      "smtpUsername": "my-weisensebot@gmail.com",
      "smtpPassword": "your-app-password",
      "fromAddress": "my-weisensebot@gmail.com",
      "allowFrom": ["your-real-email@gmail.com"]
    }
  }
}
```
## config.json的例子

```
{
  "agents": {
    "defaults": {
      "workspace": "~/.weisensebot/workspace",
      "model": "anthropic/claude-opus-4-5",
      "maxTokens": 8192,
      "temperature": 0.7,
      "maxToolIterations": 20
    }
  },
  "channels": {
    "whatsapp": {
      "enabled": false,
      "bridgeUrl": "ws://localhost:3001",
      "allowFrom": []
    },
    "telegram": {
      "enabled": false,
      "token": "",
      "allowFrom": [],
      "proxy": null
    },
    "discord": {
      "enabled": false,
      "token": "",
      "allowFrom": [],
      "gatewayUrl": "wss://gateway.discord.gg/?v=10&encoding=json",
      "intents": 37377
    },
    "feishu": {
      "enabled": false,
      "appId": "",
      "appSecret": "",
      "encryptKey": "",
      "verificationToken": "",
      "allowFrom": []
    },
    "mochat": {
      "enabled": false,
      "baseUrl": "https://mochat.io",
      "socketUrl": "",
      "socketPath": "/socket.io",
      "socketDisableMsgpack": false,
      "socketReconnectDelayMs": 1000,
      "socketMaxReconnectDelayMs": 10000,
      "socketConnectTimeoutMs": 10000,
      "refreshIntervalMs": 30000,
      "watchTimeoutMs": 25000,
      "watchLimit": 100,
      "retryDelayMs": 500,
      "maxRetryAttempts": 0,
      "clawToken": "",
      "agentUserId": "",
      "sessions": [],
      "panels": [],
      "allowFrom": [],
      "mention": {
        "requireInGroups": false
      },
      "groups": {},
      "replyDelayMode": "non-mention",
      "replyDelayMs": 120000
    },
    "dingtalk": {
      "enabled": true,
      "clientId": "dingoz5hiecx5ttstxdi",
      "clientSecret": "aTGdQnUSW7V-oSW-CewdRXWbw62q-9XwA2JEQLk_4-UQxGp3eUzBB7JfwxFyepyv",
      "allowFrom": ["*"]
    },
    "email": {
      "enabled": true,
      "consentGranted": true,
      "imapHost": "imap.qq.com",
      "imapPort": 993,
      "imapUsername": "gaoshine2008@qq.com",
      "imapPassword": "jovuwrdmozmdbfij",
      "imapMailbox": "INBOX",
      "imapUseSsl": true,
      "smtpHost": "smtp.qq.com",
      "smtpPort": 465,
      "smtpUsername": "gaoshine2008@qq.com",
      "smtpPassword": "jovuwrdmozmdbfij",
      "smtpUseTls": false,
      "smtpUseSsl": true,
      "fromAddress": "gaoshine2008@qq.com",
      "autoReplyEnabled": true,
      "pollIntervalSeconds": 30,
      "markSeen": true,
      "maxBodyChars": 12000,
      "subjectPrefix": "Re: ",
      "allowFrom": ["*"]
    },
    "slack": {
      "enabled": false,
      "mode": "socket",
      "webhookPath": "/slack/events",
      "botToken": "",
      "appToken": "",
      "userTokenReadOnly": true,
      "groupPolicy": "mention",
      "groupAllowFrom": [],
      "dm": {
        "enabled": true,
        "policy": "open",
        "allowFrom": []
      }
    },
    "qq": {
      "enabled": false,
      "appId": "",
      "secret": "",
      "allowFrom": []
    },
    "wechat": {
      "enabled": false,
      "listenChats": [],
      "allowFrom": []
    },

    "wecom": {
      "enabled": true,
      "bot_id": "aibNE6Uga0k6vJZjJ_XbxpqY_LtJK2JIBc4",
      "secret": "N4y69aYPlM2astwQAWqEpQveG2BRKL1xSXDDwVEZnkR",
      "welcome_message": "Welcome to the WeCom bot!",
      "allowFrom": ["*"]

    }
  },
 
  "providers": {
    "anthropic": {
      "apiKey": "",
      "apiBase": null,
      "extraHeaders": null
    },
    "openai": {
      "apiKey": "",
      "apiBase": null,
      "extraHeaders": null
    },
    "openrouter": {
      "apiKey": "",
      "apiBase": null,
      "extraHeaders": null
    },
    "deepseek": {
      "apiKey": "",
      "apiBase": null,
      "extraHeaders": null
    },
    "groq": {
      "apiKey": "",
      "apiBase": null,
      "extraHeaders": null
    },
    "zhipu": {
      "apiKey": "0219a16e2f0949f09811107e3b5f59e3.3iWQCDuZj2ht4utn",
      "apiBase": "https://open.bigmodel.cn/api/coding/paas/v4",
      "extraHeaders": null
    },
    "dashscope": {
      "apiKey": "",
      "apiBase": null,
      "extraHeaders": null
    },
    "vllm": {
      "apiKey": "",
      "apiBase": "",
      "extraHeaders": null
    },
    "gemini": {
      "apiKey": "",
      "apiBase": null,
      "extraHeaders": null
    },
    "moonshot": {
      "apiKey": "",
      "apiBase": null,
      "extraHeaders": null
    },
    "minimax": {
      "apiKey": "",
      "apiBase": null,
      "extraHeaders": null
    },
    "aihubmix": {
      "apiKey": "",
      "apiBase": null,
      "extraHeaders": null
    }
  },
    "agents": {
    "defaults": {
      "model": "glm-4.7"
    }
  },

  "gateway": {
    "host": "0.0.0.0",
    "port": 18790
  },
  "tools": {
    "web": {
      "search": {
        "apiKey": "",
        "maxResults": 5
      }
    },
    "exec": {
      "timeout": 60
    },
    "restrictToWorkspace": false
  }
}

```




**3. 运行**

```bash
weisensebot gateway
```

</details>

## 🌐 智能体社交网络

🐈 weisensebot能够连接到智能体社交网络（智能体社区）。**只需发送一条消息，您的weisensebot就会自动加入！**

| 平台 | 如何加入（向您的bot发送此消息） |
|----------|-------------|
| [**Moltbook**](https://www.moltbook.com/) | `Read https://moltbook.com/skill.md and follow the instructions to join Moltbook` |
| [**ClawdChat**](https://clawdchat.ai/) | `Read https://clawdchat.ai/skill.md and follow the instructions to join ClawdChat` |

只需将上述命令发送给您的weisensebot（通过CLI或任何聊天频道），它将处理其余的工作。

## ⚙️ 配置

配置文件：`~/.weisensebot/config.json`

### 提供商

> [!TIP]
> - **Groq**通过Whisper提供免费的语音转录。如果配置，Telegram语音消息将自动转录。
> - **智谱编码计划**：如果您使用的是智谱的编码计划，请在zhipu提供商配置中设置`"apiBase": "https://open.bigmodel.cn/api/coding/paas/v4"`。
> - **MiniMax（中国大陆）**：如果您的API密钥来自MiniMax的中国大陆平台（minimaxi.com），请在minimax提供商配置中设置`"apiBase": "https://api.minimaxi.com/v1"`。
> - **火山引擎编码计划**：如果您使用的是火山引擎的编码计划，请在volcengine提供商配置中设置`"apiBase": "https://ark.cn-beijing.volces.com/api/coding/v3"`。
> - **阿里云编码计划**：如果您使用的是阿里云编码计划（百炼），请在dashscope提供商配置中设置`"apiBase": "https://coding.dashscope.aliyuncs.com/v1"`。

| 提供商 | 用途 | 获取API密钥 |
|----------|---------|-------------|
| `custom` | 任何OpenAI兼容的端点（直接，无需LiteLLM） | — |
| `openrouter` | LLM（推荐，访问所有模型） | [openrouter.ai](https://openrouter.ai) |
| `anthropic` | LLM（Claude直接） | [console.anthropic.com](https://console.anthropic.com) |
| `azure_openai` | LLM（Azure OpenAI） | [portal.azure.com](https://portal.azure.com) |
| `openai` | LLM（GPT直接） | [platform.openai.com](https://platform.openai.com) |
| `deepseek` | LLM（DeepSeek直接） | [platform.deepseek.com](https://platform.deepseek.com) |
| `groq` | LLM + **语音转录**（Whisper） | [console.groq.com](https://console.groq.com) |
| `gemini` | LLM（Gemini直接） | [aistudio.google.com](https://aistudio.google.com) |
| `minimax` | LLM（MiniMax直接） | [platform.minimaxi.com](https://platform.minimaxi.com) |
| `aihubmix` | LLM（API网关，访问所有模型） | [aihubmix.com](https://aihubmix.com) |
| `siliconflow` | LLM（SiliconFlow/硅基流动） | [siliconflow.cn](https://siliconflow.cn) |
| `volcengine` | LLM（VolcEngine/火山引擎） | [volcengine.com](https://www.volcengine.com) |
| `dashscope` | LLM（Qwen） | [dashscope.console.aliyun.com](https://dashscope.console.aliyun.com) |
| `moonshot` | LLM（Moonshot/Kimi） | [platform.moonshot.cn](https://platform.moonshot.cn) |
| `zhipu` | LLM（Zhipu GLM） | [open.bigmodel.cn](https://open.bigmodel.cn) |
| `vllm` | LLM（本地，任何OpenAI兼容服务器） | — |
| `openai_codex` | LLM（Codex，OAuth） | `weisensebot provider login openai-codex` |
| `github_copilot` | LLM（GitHub Copilot，OAuth） | `weisensebot provider login github-copilot` |

<details>
<summary><b>OpenAI Codex (OAuth)</b></summary>

Codex使用OAuth而不是API密钥。需要ChatGPT Plus或Pro账户。

**1. 登录：**
```bash
weisensebot provider login openai-codex
```

**2. 设置模型**（合并到`~/.weisensebot/config.json`）：
```json
{
  "agents": {
    "defaults": {
      "model": "openai-codex/gpt-5.1-codex"
    }
  }
}
```

**3. 聊天：**
```bash
weisensebot agent -m "Hello!"
```

> Docker用户：使用`docker run -it`进行交互式OAuth登录。

</details>

<details>
<summary><b>自定义提供商（任何OpenAI兼容的API）</b></summary>

直接连接到任何OpenAI兼容的端点 — LM Studio、llama.cpp、Together AI、Fireworks、Azure OpenAI或任何自托管服务器。绕过LiteLLM；模型名称按原样传递。

```json
{
  "providers": {
    "custom": {
      "apiKey": "your-api-key",
      "apiBase": "https://api.your-provider.com/v1"
    }
  },
  "agents": {
    "defaults": {
      "model": "your-model-name"
    }
  }
}
```

> 对于不需要密钥的本地服务器，将`apiKey`设置为任何非空字符串（例如`"no-key"`）。

</details>

<details>
<summary><b>vLLM（本地 / OpenAI兼容）</b></summary>

使用vLLM或任何OpenAI兼容服务器运行您自己的模型，然后添加到配置中：

**1. 启动服务器**（示例）：
```bash
vllm serve meta-llama/Llama-3.1-8B-Instruct --port 8000
```

**2. 添加到配置中**（部分 — 合并到`~/.weisensebot/config.json`）：

*提供商（密钥可以是本地任何非空字符串）：*
```json
{
  "providers": {
    "vllm": {
      "apiKey": "dummy",
      "apiBase": "http://localhost:8000/v1"
    }
  }
}
```

*模型：*
```json
{
  "agents": {
    "defaults": {
      "model": "meta-llama/Llama-3.1-8B-Instruct"
    }
  }
}
```

</details>

<details>
<summary><b>添加新提供商（开发者指南）</b></summary>

weisensebot使用**提供商注册表**（`weisensebot/providers/registry.py`）作为单一事实来源。
添加新提供商只需**2步** — 无需触及if-elif链。

**步骤1.** 将`ProviderSpec`条目添加到`weisensebot/providers/registry.py`中的`PROVIDERS`：

```python
ProviderSpec(
    name="myprovider",                   # 配置字段名
    keywords=("myprovider", "mymodel"),  # 模型名称关键字用于自动匹配
    env_key="MYPROVIDER_API_KEY",        # LiteLLM的环境变量
    display_name="My Provider",          # 在`weisensebot status`中显示
    litellm_prefix="myprovider",         # 自动前缀：model → myprovider/model
    skip_prefixes=("myprovider/",),      # 不要双重前缀
)
```

**步骤2.** 将字段添加到`weisensebot/config/schema.py`中的`ProvidersConfig`：

```python
class ProvidersConfig(BaseModel):
    ...
    myprovider: ProviderConfig = ProviderConfig()
```

就这样！环境变量、模型前缀、配置匹配和`weisensebot status`显示都将自动工作。

**常用`ProviderSpec`选项：**

| 字段 | 描述 | 示例 |
|-------|-------------|---------|
| `litellm_prefix` | 为LiteLLM自动添加模型名称前缀 | `"dashscope"` → `dashscope/qwen-max` |
| `skip_prefixes` | 如果模型已经以这些开头，则不要添加前缀 | `("dashscope/", "openrouter/")` |
| `env_extras` | 要设置的其他环境变量 | `(("ZHIPUAI_API_KEY", "{api_key}"),)` |
| `model_overrides` | 每模型参数覆盖 | `(("kimi-k2.5", {"temperature": 1.0}),)` |
| `is_gateway` | 可以路由任何模型（如OpenRouter） | `True` |
| `detect_by_key_prefix` | 通过API密钥前缀检测网关 | `"sk-or-"` |
| `detect_by_base_keyword` | 通过API基础URL检测网关 | `"openrouter"` |
| `strip_model_prefix` | 在重新添加前缀之前剥离现有前缀 | `True`（用于AiHubMix） |

</details>


### MCP（模型上下文协议）

> [!TIP]
> 配置格式与Claude Desktop / Cursor兼容。您可以直接从任何MCP服务器的README复制MCP服务器配置。

weisensebot支持[MCP](https://modelcontextprotocol.io/) — 连接外部工具服务器并将它们用作原生智能体工具。

将MCP服务器添加到您的`config.json`：

```json
{
  "tools": {
    "mcpServers": {
      "filesystem": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/dir"]
      },
      "my-remote-mcp": {
        "url": "https://example.com/mcp/",
        "headers": {
          "Authorization": "Bearer xxxxx"
        }
      }
    }
  }
}
```

支持两种传输模式：

| 模式 | 配置 | 示例 |
|------|--------|---------|
| **Stdio** | `command` + `args` | 通过`npx`/`uvx`的本地进程 |
| **HTTP** | `url` + `headers`（可选） | 远程端点（`https://mcp.example.com/sse`） |

使用`toolTimeout`覆盖慢速服务器的默认每次调用30秒超时：

```json
{
  "tools": {
    "mcpServers": {
      "my-slow-server": {
        "url": "https://example.com/mcp/",
        "toolTimeout": 120
      }
    }
  }
}
```

MCP工具在启动时自动发现和注册。LLM可以将它们与内置工具一起使用 — 无需额外配置。




### 安全

> [!TIP]
> 对于生产部署，在配置中设置`"restrictToWorkspace": true`以沙箱化智能体。
> **源码中/`v0.1.4.post3`之后的变更**：在`v0.1.4.post3`及更早版本中，空的`allowFrom`表示"允许所有发送者"。在较新版本（包括从源码构建）中，**空`allowFrom`默认拒绝所有访问**。要允许所有发送者，请设置`"allowFrom": ["*"]`。

| 选项 | 默认值 | 描述 |
|--------|---------|-------------|
| `tools.restrictToWorkspace` | `false` | 当为`true`时，将**所有**智能体工具（shell、文件读/写/编辑、列表）限制到工作区目录。防止路径遍历和范围外访问。 |
| `tools.exec.pathAppend` | `""` | 运行shell命令时要附加到`PATH`的额外目录（例如`/usr/sbin`用于`ufw`）。 |
| `channels.*.allowFrom` | `[]`（允许所有） | 用户ID白名单。空 = 允许所有人；非空 = 只有列出的用户可以交互。 |


## 多实例

同时运行多个weisensebot实例，每个都有自己的工作区和配置。

```bash
# 实例A - Telegram bot
weisensebot gateway -w ~/.weisensebot/botA -p 18791

# 实例B - Discord bot
weisensebot gateway -w ~/.weisensebot/botB -p 18792

# 实例C - 使用自定义配置文件
weisensebot gateway -w ~/.weisensebot/botC -c ~/.weisensebot/botC/config.json -p 18793
```

| 选项 | 短选项 | 描述 |
|--------|-------|-------------|
| `--workspace` | `-w` | 工作区目录（默认：`~/.weisensebot/workspace`） |
| `--config` | `-c` | 配置文件路径（默认：`~/.weisensebot/config.json`） |
| `--port` | `-p` | 网关端口（默认：`18790`） |

每个实例都有自己的：
- 工作区目录（MEMORY.md、HEARTBEAT.md、会话文件）
- Cron作业存储（`workspace/cron/jobs.json`）
- 配置（如果使用`--config`）


## CLI参考

| 命令 | 描述 |
|---------|-------------|
| `weisensebot onboard` | 初始化配置和工作区 |
| `weisensebot agent -m "..."` | 与智能体聊天 |
| `weisensebot agent` | 交互式聊天模式 |
| `weisensebot agent --no-markdown` | 显示纯文本回复 |
| `weisensebot agent --logs` | 聊天期间显示运行时日志 |
| `weisensebot gateway` | 启动网关 |
| `weisensebot status` | 显示状态 |
| `weisensebot provider login openai-codex` | 提供商OAuth登录 |
| `weisensebot channels login` | 链接WhatsApp（扫描二维码） |
| `weisensebot channels status` | 显示频道状态 |

交互式模式退出：`exit`、`quit`、`/exit`、`/quit`、`:q`或`Ctrl+D`。

<details>
<summary><b>心跳（周期性任务）</b></summary>

网关每30分钟唤醒一次，并检查您的工作区中的`HEARTBEAT.md`（`~/.weisensebot/workspace/HEARTBEAT.md`）。如果文件有任务，智能体将执行它们并将结果传递给您最近活动的聊天频道。

**设置：**编辑`~/.weisensebot/workspace/HEARTBEAT.md`（由`weisensebot onboard`自动创建）：

```markdown
## 周期性任务

- [ ] 检查天气预报并发送摘要
- [ ] 扫描收件箱查找紧急邮件
```

智能体也可以自己管理此文件 — 要求它"添加周期性任务"，它将为您更新`HEARTBEAT.md`。

> **注意：**网关必须运行（`weisensebot gateway`），并且您必须至少与机器人聊天一次，以便它知道要传递到哪个频道。

</details>

## 🐳 Docker

> [!TIP]
> `-v ~/.weisensebot:/root/.weisensebot`标志将您的本地配置目录挂载到容器中，因此您的配置和工作区在容器重启之间持久存在。

### Docker Compose

```bash
docker compose run --rm weisensebot-cli onboard   # 首次设置
vim ~/.weisensebot/config.json                     # 添加API密钥
docker compose up -d weisensebot-gateway           # 启动网关
```

```bash
docker compose run --rm weisensebot-cli agent -m "Hello!"   # 运行CLI
docker compose logs -f weisensebot-gateway                   # 查看日志
docker compose down                                      # 停止
```

### Docker

```bash
# 构建镜像
docker build -t weisensebot .

# 初始化配置（仅首次）
docker run -v ~/.weisensebot:/root/.weisensebot --rm weisensebot onboard

# 在主机上编辑配置以添加API密钥
vim ~/.weisensebot/config.json

# 运行网关（连接到启用的频道，例如Telegram/Discord/Mochat）
docker run -v ~/.weisensebot:/root/.weisensebot -p 18790:18790 weisensebot gateway

# 或运行单个命令
docker run -v ~/.weisensebot:/root/.weisensebot --rm weisensebot agent -m "Hello!"
docker run -v ~/.weisensebot:/root/.weisensebot --rm weisensebot status
```

## 🐧 Linux服务

将网关作为systemd用户服务运行，以便它自动启动并在失败时重启。

**1. 查找weisensebot二进制路径：**

```bash
which weisensebot   # 例如 /home/user/.local/bin/weisensebot
```

**2. 创建服务文件**在`~/.config/systemd/user/weisensebot-gateway.service`（如需要，替换`ExecStart`路径）：

```ini
[Unit]
Description=Nanobot Gateway
After=network.target

[Service]
Type=simple
ExecStart=%h/.local/bin/weisensebot gateway
Restart=always
RestartSec=10
NoNewPrivileges=yes
ProtectSystem=strict
ReadWritePaths=%h

[Install]
WantedBy=default.target
```

**3. 启用并启动：**

```bash
systemctl --user daemon-reload
systemctl --user enable --now weisensebot-gateway
```

**常用操作：**

```bash
systemctl --user status weisensebot-gateway        # 检查状态
systemctl --user restart weisensebot-gateway       # 配置更改后重启
journalctl --user -u weisensebot-gateway -f        # 跟踪日志
```

如果您编辑`.service`文件本身，请在重启之前运行`systemctl --user daemon-reload`。

> **注意：**用户服务仅在您登录时运行。要在退出后保持网关运行，启用lingering：
>
> ```bash
> loginctl enable-linger $USER
> ```

## 📁 项目结构

```
weisensebot/
├── agent/          # 🧠 核心智能体逻辑
│   ├── loop.py     #    智能体循环（LLM ↔ 工具执行）
│   ├── context.py  #    提示构建器
│   ├── memory.py   #    持久化内存
│   ├── skills.py   #    技能加载器
│   ├── subagent.py #    后台任务执行
│   └── tools/      #    内置工具（包括spawn）
├── skills/         # 🎯 捆绑技能（github、weather、tmux...）
├── channels/       # 📱 聊天频道集成
├── bus/            # 🚌 消息路由
├── cron/           # ⏰ 定时任务
├── heartbeat/      # 💓 主动唤醒
├── providers/      # 🤖 LLM提供商（OpenRouter等）
├── session/        # 💬 对话会话
├── config/         # ⚙️ 配置
└── cli/            # 🖥️ 命令
```

## 🤝 贡献与路线图

欢迎PR！代码库故意设计得小巧易读。🤗

**路线图** — 选择一个项目并[打开PR](https://github.com/HKUDS/weisensebot/pulls)！

- [ ] **多模态** — 看见和听到（图像、语音、视频）
- [ ] **长期记忆** — 永不忘记重要上下文
- [ ] **更好的推理** — 多步规划和反思
- [ ] **更多集成** — 日历等
- [ ] **自我改进** — 从反馈和错误中学习

### 贡献者

<a href="https://github.com/HKUDS/weisensebot/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=HKUDS/weisensebot&max=100&columns=12&updated=20260210" alt="贡献者" />
</a>


## ⭐ Star历史

<div align="center">
  <a href="https://star-history.com/#HKUDS/weisensebot&Date">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=HKUDS/weisensebot&type=Date&theme=dark" />
      <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=HKUDS/weisensebot&type=Date" />
      <img alt="Star历史图表" src="https://api.star-history.com/svg?repos=HKUDS/weisensebot&type=Date" style="border-radius: 15px; box-shadow: 0 0 30px rgba(0, 217, 255, 0.3);" />
    </picture>
  </a>
</div>

<p align="center">
  <em> 感谢访问 ✨ weisensebot!</em><br><br>
  <img src="https://visitor-badge.laobi.icu/badge?page_id=HKUDS.weisensebot&style=for-the-badge&color=00d4ff" alt="浏览量">
</p>


<p align="center">
  <sub>weisensebot仅用于教育、研究和技术交流目的</sub>
</p>
