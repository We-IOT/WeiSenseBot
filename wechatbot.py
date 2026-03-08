"""
微信机器人 - WeiSenseBot智能体与微信群的对接示例

功能说明：
- 使用WeiSenseBot的process_direct方法直接处理消息
- 通过wxautox库监听微信群消息
- 支持同时监听多个群或个人
- 支持动态加载自定义agent策略文件
- 接收用户消息后，交由WeiSenseBot智能体处理
- 将智能体的回复发送回微信群
- 支持聊天记录保存功能

使用方法：
1. 确保已安装wxautox库: pip install wxautox
2. 确保微信客户端已登录
3. 运行此脚本，通过命令行参数指定监听群和配置

基本用法：
    # 监听单个群（使用默认agent配置）
    python wechatbot.py -g "工作群"
    
    # 监听多个群
    python wechatbot.py -g "工作群" -g "客服群" -g "技术群"
    
    # 使用自定义agent配置
    python wechatbot.py -g "客服群" -a /path/to/customer_agent.md
    
    # 完整参数
    python wechatbot.py -g "工作群" -a work_agent.md -p 2
    
    # 启用聊天记录保存
    python wechatbot.py -g "工作群" --save-chat
    
    # 查看帮助
    python wechatbot.py --help

不同群使用不同agent配置：
    为不同群分别运行实例即可，例如：
    
    # 终端1: 工作群使用工作助手配置
    python wechatbot.py -g "工作群" -a work_agent.md
    
    # 终端2: 客服群使用客服配置
    python wechatbot.py -g "客服群" -a customer_agent.md
"""

import asyncio
import argparse
import shutil
import tempfile
from pathlib import Path
from datetime import datetime
import re
import os
from weisensebot.bus.queue import MessageBus  # 消息总线，用于组件间通信
from weisensebot.agent.loop import AgentLoop  # 智能体循环，核心处理逻辑
from weisensebot.providers.litellm_provider import LiteLLMProvider  # LLM提供商
from weisensebot.config.loader import load_config  # 配置加载器
from wxautox import WeChat  # 微信自动化库
import time


def extract_send_files_xml(text):
    """
    从agent响应中提取<send_files>或<send_file>标签的内容，支持多个文件
    
    参数:
        text: agent的响应文本
    
    返回:
        list: 包含文件信息的字典列表，每个字典包含file_path, caption等字段
              如果未找到标签，返回None
    
    新格式示例（支持多个文件）:
        <send_files>
          <file>
            <file_path>/path/to/file1.jpg</file_path>
            <caption>文件1说明</caption>
          </file>
          <file>
            <file_path>/path/to/file2.pdf</file_path>
            <caption>文件2说明</caption>
          </file>
        </send_files>
    
    旧格式示例（向后兼容）:
        <send_file>
          <file_path>/path/to/file.jpg</file_path>
          <caption>文件说明</caption>
        </send_file>
    """
    # 优先尝试匹配新的多文件格式 <send_files>
    pattern = r'<send_files>(.*?)</send_files>'
    match = re.search(pattern, text, re.DOTALL)
    
    if match:
        xml_content = match.group(1)
        # 提取所有<file>标签
        file_pattern = r'<file>(.*?)</file>'
        file_matches = re.findall(file_pattern, xml_content, re.DOTALL)
        
        files = []
        for file_content in file_matches:
            file_info = {}
            # 提取file_path
            file_path_match = re.search(r'<file_path>(.*?)</file_path>', file_content, re.DOTALL)
            if file_path_match:
                file_info['file_path'] = file_path_match.group(1).strip()
            
            # 提取caption（可选）
            caption_match = re.search(r'<caption>(.*?)</caption>', file_content, re.DOTALL)
            if caption_match:
                file_info['caption'] = caption_match.group(1).strip()
            
            if file_info:
                files.append(file_info)
        
        return files if files else None
    
    # 如果没有找到新格式，尝试匹配旧的单文件格式 <send_file>
    pattern = r'<send_file>(.*?)</send_file>'
    match = re.search(pattern, text, re.DOTALL)
    
    if not match:
        return None
    
    xml_content = match.group(1)
    
    # 提取各个字段
    result = {}
    
    # 提取file_path
    file_path_match = re.search(r'<file_path>(.*?)</file_path>', xml_content, re.DOTALL)
    if file_path_match:
        result['file_path'] = file_path_match.group(1).strip()
    
    # 提取to（可选）
    to_match = re.search(r'<to>(.*?)</to>', xml_content, re.DOTALL)
    if to_match:
        result['to'] = to_match.group(1).strip()
    
    # 提取channel（可选）
    channel_match = re.search(r'<channel>(.*?)</channel>', xml_content, re.DOTALL)
    if channel_match:
        result['channel'] = channel_match.group(1).strip()
    
    # 提取caption（可选）
    caption_match = re.search(r'<caption>(.*?)</caption>', xml_content, re.DOTALL)
    if caption_match:
        result['caption'] = caption_match.group(1).strip()
    
    return [result] if result else None


def remove_xml_tags(text):
    """
    从文本中移除<send_file>或<send_files>标签及其内容，保留其他文本
    
    参数:
        text: 原始文本
    
    返回:
        str: 移除XML标签后的纯文本
    """
    # 移除<send_files>...</send_files>标签及其内容（新格式）
    pattern = r'<send_files>.*?</send_files>'
    cleaned_text = re.sub(pattern, '', text, flags=re.DOTALL)
    
    # 移除<send_file>...</send_file>标签及其内容（旧格式）
    pattern = r'<send_file>.*?</send_file>'
    cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.DOTALL)
    
    # 清理多余的空行
    cleaned_text = re.sub(r'\n\s*\n', '\n\n', cleaned_text)
    
    return cleaned_text.strip()


def validate_file_path(file_path):
    """
    验证文件路径是否存在且可访问
    
    参数:
        file_path: 文件路径
    
    返回:
        tuple: (是否有效, 错误消息)
    """
    if not file_path:
        return False, "文件路径为空"
    
    if not os.path.exists(file_path):
        return False, f"文件不存在: {file_path}"
    
    if not os.path.isfile(file_path):
        return False, f"路径不是文件: {file_path}"
    
    if not os.access(file_path, os.R_OK):
        return False, f"文件不可读: {file_path}"
    
    return True, ""


def send_wechat_file(chat, file_path, caption=None, chat_logger=None, chat_name=None):
    """
    通过微信发送文件
    
    参数:
        chat: 微信聊天对象
        file_path: 文件绝对路径
        caption: 文件说明（可选）
        chat_logger: 聊天记录器（可选）
        chat_name: 聊天对象名称（用于记录日志）
    
    返回:
        tuple: (是否成功, 消息)
    """
    try:
        # 验证文件路径
        is_valid, error_msg = validate_file_path(file_path)
        if not is_valid:
            print(f"[文件发送失败] {error_msg}")
            return False, error_msg
        
        # 获取文件信息
        file_size = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)
        
        # 转换文件大小为可读格式
        if file_size < 1024:
            size_str = f"{file_size} B"
        elif file_size < 1024 * 1024:
            size_str = f"{file_size / 1024:.1f} KB"
        else:
            size_str = f"{file_size / (1024 * 1024):.1f} MB"
        
        print(f"\n{'='*60}")
        print(f"📎 正在发送文件...")
        print(f"{'='*60}")
        print(f"文件名: {file_name}")
        print(f"大小: {size_str}")
        print(f"路径: {file_path}")
        if caption:
            print(f"说明: {caption}")
        print(f"{'='*60}")
        
        # 发送文件
        chat.SendFiles(file_path)
        
        # 如果有caption，发送说明文字
        if caption:
            time.sleep(0.5)  # 稍微延迟，确保文件先发送
            chat.SendMsg(caption)
        
        success_msg = f"✅ 文件发送成功: {file_name} ({size_str})"
        print(success_msg)
        
        # 记录到聊天日志
        if chat_logger and chat_name:
            log_msg = f"[发送文件] {file_name} ({size_str})"
            if caption:
                log_msg += f"\n{caption}"
            chat_logger.log_message(chat_name, "nanobot", log_msg)
        
        return True, success_msg
        
    except Exception as e:
        error_msg = f"文件发送失败: {str(e)}"
        print(f"[错误] {error_msg}")
        import traceback
        traceback.print_exc()
        return False, error_msg


class ChatLogger:
    """
    聊天记录管理类
    
    功能：
    - 记录微信聊天消息到本地文件
    - 按聊天对象分类存储
    - 自动添加时间戳和发言者信息
    
    存储格式：
    workspace/chats/
    ├── 工作群.md
    ├── 客服群.md
    └── 张三.md
    
    每个文件的格式：
    # 聊天对象名称
    
    ## YYYY-MM-DD
    
    ### HH:MM:SS | 发言者
    消息内容
    """
    
    def __init__(self, workspace: Path, chat_dir: str = "chats"):
        """
        初始化聊天记录器
        
        参数:
            workspace: 工作空间路径
            chat_dir: 聊天记录存储目录名称（默认为 "chats"）
        """
        self.workspace = workspace
        self.chat_dir_path = workspace / chat_dir
        self.chat_dir_path.mkdir(exist_ok=True)
        print(f"聊天记录目录: {self.chat_dir_path}")
    
    def _get_chat_file(self, chat_name: str) -> Path:
        """
        获取聊天对象的记录文件路径
        
        参数:
            chat_name: 聊天对象名称（群名/人名）
        
        返回:
            Path: 聊天记录文件路径
        """
        return self.chat_dir_path / f"{chat_name}.md"
    
    def _get_today_date(self) -> str:
        """获取今天的日期字符串（YYYY-MM-DD）"""
        return datetime.now().strftime("%Y-%m-%d")
    
    def _get_current_time(self) -> str:
        """获取当前时间字符串（HH:MM:SS）"""
        return datetime.now().strftime("%H:%M:%S")
    
    def log_message(self, chat_name: str, sender: str, message: str, max_retries: int = 3):
        """
        记录单条聊天消息
        
        参数:
            chat_name: 聊天对象名称（群名/人名）
            sender: 发言者名称
            message: 消息内容
            max_retries: 最大重试次数（默认为3，用于Win10文件锁定问题）
        
        记录格式：
        ### HH:MM:SS | 发言者
        消息内容
        
        注意:
            - 使用重试机制处理Win10中的文件锁定问题
            - 使用临时文件写入方式减少文件锁定风险
        """
        chat_file = self._get_chat_file(chat_name)
        today_date = self._get_today_date()
        current_time = self._get_current_time()
        
        # 构建新消息条目
        new_entry = f"\n\n### {current_time} | {sender}\n{message}"
        
        # 使用重试机制写入文件
        for attempt in range(max_retries):
            try:
                # 读取现有内容
                if chat_file.exists():
                    content = chat_file.read_text(encoding="utf-8")
                else:
                    # 新文件，创建标题
                    content = f"# {chat_name} 聊天记录\n\n## {today_date}"
                
                # 检查是否需要添加新的日期标题
                date_header = f"## {today_date}"
                if date_header not in content:
                    content += f"\n\n{date_header}"
                
                # 追加新消息
                content += new_entry
                
                # 在Windows中，使用临时文件写入方式来减少文件锁定问题
                import tempfile
                import uuid
                
                # 创建临时文件
                temp_file = chat_file.parent / f"{chat_file.name}.tmp.{uuid.uuid4().hex[:8]}"
                
                try:
                    # 写入临时文件
                    temp_file.write_text(content, encoding="utf-8")
                    
                    # 重命名临时文件到目标文件（原子操作）
                    temp_file.replace(chat_file)
                    
                finally:
                    # 清理临时文件
                    if temp_file.exists():
                        try:
                            temp_file.unlink()
                        except:
                            pass
                
                # 写入成功，打印日志
                print(f"[聊天记录] {chat_name} | {current_time} | {sender}")
                return
                
            except PermissionError as e:
                # 文件被占用，等待后重试
                if attempt < max_retries - 1:
                    import time
                    wait_time = 0.5 * (attempt + 1)  # 递增等待时间
                    print(f"[聊天记录] 文件被占用，等待 {wait_time}秒 后重试... (尝试 {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    # 最后一次尝试也失败了，记录错误但不中断程序
                    print(f"[聊天记录] 记录失败: {chat_name} | {current_time} | {sender}")
                    print(f"[聊天记录] 错误: 文件写入失败（权限错误）: {e}")
                    
            except OSError as e:
                # 其他文件操作错误
                if attempt < max_retries - 1:
                    import time
                    wait_time = 0.5 * (attempt + 1)
                    print(f"[聊天记录] 文件操作错误，等待 {wait_time}秒 后重试... (尝试 {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    print(f"[聊天记录] 记录失败: {chat_name} | {current_time} | {sender}")
                    print(f"[聊天记录] 错误: {e}")
                    
            except Exception as e:
                # 未知错误，不重试
                print(f"[聊天记录] 记录失败: {chat_name} | {current_time} | {sender}")
                print(f"[聊天记录] 错误: {e}")
                break


def parse_args():
    """
    解析命令行参数
    
    返回:
        argparse.Namespace: 解析后的参数对象
    
    支持的参数:
        -g, --group: 监听的群名/人名（可多次指定，必填）
        -a, --agent-profile: Agent策略文件路径（可选）
        -p, --poll-interval: 轮询间隔（秒，默认为1）
        --save-chat: 启用聊天记录保存（默认为 False）
        --no-save-chat: 禁用聊天记录保存（默认行为）
        -d, --chat-dir: 聊天记录存储目录（默认为 "chats"）
    """
    parser = argparse.ArgumentParser(
        description='微信机器人 - WeiSenseBot智能体与微信群的对接示例',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 监听单个群
  python weisensebot.py -g "工作群"
  
  # 监听多个群
  python weisensebot.py -g "工作群" -g "客服群" -g "技术群"
  
  # 使用自定义agent配置
  python weisensebot.py -g "客服群" -a /path/to/customer_agent.md
  
  # 完整参数
  python weisensebot.py -g "工作群" -a work_agent.md -p 2
  
  # 启用聊天记录保存
  python weisensebot.py -g "工作群" --save-chat
        """
    )
    
    parser.add_argument(
        '-g', '--group',
        required=True,
        action='append',
        help='监听的群名/人名（可多次指定）'
    )
    
    parser.add_argument(
        '-a', '--agent-profile',
        type=str,
        help='Agent策略文件路径（agent.md），如果不指定则使用默认配置'
    )
    
    parser.add_argument(
        '-p', '--poll-interval',
        type=int,
        default=1,
        help='轮询间隔（秒），默认为1'
    )
    
    parser.add_argument(
        '--save-chat',
        action='store_true',
        default=False,
        dest='save_chat',
        help='是否保存聊天记录（默认为 False），使用 --save-chat 启用'
    )
    
    parser.add_argument(
        '--no-save-chat',
        action='store_false',
        dest='save_chat',
        help='禁用聊天记录保存（默认禁用）'
    )
    
    parser.add_argument(
        '-d', '--chat-dir',
        type=str,
        default='chats',
        help='聊天记录存储目录（默认为 "chats"）'
    )
    
    return parser.parse_args()


def load_agent_profile(profile_path: str, original_workspace: Path) -> Path:
    """
    加载agent策略文件，创建临时workspace
    
    原理：
    - WeiSenseBot的agent行为由workspace中的引导文件控制（AGENTS.md、SOUL.md、USER.md等）
    - 本函数创建临时workspace，将指定的agent策略文件作为AGENTS.md
    - 将原workspace的其他引导文件复制到临时workspace
    - 返回临时workspace路径，用于初始化AgentLoop
    
    参数:
        profile_path: agent策略文件路径
        original_workspace: 原始workspace路径（用于复制其他引导文件）
    
    返回:
        Path: 临时workspace路径
    
    注意:
        - 临时workspace在程序退出后不会被自动删除，以便保留会话历史
        - 根据agent配置文件名生成固定的workspace名称，保留记忆和会话历史
    """
    # 读取agent策略文件
    profile_file = Path(profile_path)
    if not profile_file.exists():
        raise FileNotFoundError(f"Agent策略文件不存在: {profile_path}")
    
    agent_content = profile_file.read_text(encoding="utf-8")
    
    # 根据agent配置文件名生成固定的临时workspace名称
    # 例如：work_agent.md -> nanobot_wechat_work_agent
    profile_name = profile_file.stem
    temp_dir = Path(tempfile.gettempdir())
    temp_workspace = temp_dir / f"nanobot_wechat_{profile_name}"
    
    # 创建临时workspace目录（如果不存在则创建）
    temp_workspace.mkdir(exist_ok=True)
    
    # 将agent策略文件写入临时workspace的AGENTS.md
    (temp_workspace / "AGENTS.md").write_text(agent_content, encoding="utf-8")
    
    # 复制原workspace的其他引导文件
    bootstrap_files = ["SOUL.md", "USER.md", "TOOLS.md", "IDENTITY.md"]
    for filename in bootstrap_files:
        src_file = original_workspace / filename
        if src_file.exists():
            shutil.copy(src_file, temp_workspace / filename)
    
    # 创建memory目录
    memory_dir = temp_workspace / "memory"
    memory_dir.mkdir(exist_ok=True)
    
    # 复制原workspace的MEMORY.md（如果存在）
    original_memory = original_workspace / "memory" / "MEMORY.md"
    if original_memory.exists():
        shutil.copy(original_memory, memory_dir / "MEMORY.md")
    
    print(f"已创建临时workspace: {temp_workspace}")
    print(f"已加载agent策略文件: {profile_path}")
    
    return temp_workspace


def _make_provider(config):
    """
    从配置创建 LiteLLMProvider 实例
    
    参数:
        config: 加载后的配置对象，包含API密钥、模型名称等信息
    
    返回:
        LiteLLMProvider实例，如果缺少API密钥则返回None
    
    说明:
        - 从配置中获取提供商信息
        - 验证API密钥是否存在（bedrock模型除外）
        - 创建并返回LiteLLMProvider实例，用于与LLM交互
    """
    # 从配置获取提供商信息
    p = config.get_provider()
    model = config.agents.defaults.model
    
    # 检查API密钥配置（bedrock模型使用AWS密钥，不需要此处配置）
    if not (p and p.api_key) and not model.startswith("bedrock/"):
        print("错误: 未配置 API key")
        print("请在 ~/.weisensebot/config.json 的 providers 部分设置 API key")
        return None
    
    # 创建LiteLLMProvider实例
    return LiteLLMProvider(
        api_key=p.api_key if p else None,  # API密钥
        api_base=config.get_api_base(),     # API基础URL
        default_model=model,                # 默认模型名称
        extra_headers=p.extra_headers if p else None,  # 额外的HTTP头
        provider_name=config.get_provider_name(),       # 提供商名称
    )


async def simple_direct_call(args):
    """
    主函数：监听微信群消息，使用AgentLoop处理并回复
    
    工作流程：
    1. 加载nanobot配置文件
    2. 如果指定了agent_profile，创建临时workspace并加载策略文件
    3. 创建消息总线
    4. 初始化LLM提供商
    5. 创建AgentLoop智能体实例
    6. 如果启用聊天记录，初始化ChatLogger
    7. 初始化微信监听，添加所有指定的群/人
    8. 持续监听并处理每个群/人的消息
    9. 将回复发送回对应的群/人
    10. 记录聊天消息（如果启用）
    
    参数:
        args: 命令行参数对象
    
    说明:
        - process_direct方法直接处理消息，不需要通过消息队列
        - 每个群/人有独立的session_key，会话历史互不干扰
        - channel固定为"wechat"
    """
    
    # ============================================
    # 步骤1: 加载配置
    # ============================================
    print("正在加载配置...")
    config = load_config()  # 从~/.weisensebot/config.json加载配置
    original_workspace = config.workspace_path
    
    # ============================================
    # 步骤2: 处理agent策略文件
    # ============================================
    workspace = original_workspace
    if args.agent_profile:
        print(f"正在加载agent策略文件: {args.agent_profile}")
        try:
            workspace = load_agent_profile(args.agent_profile, original_workspace)
        except FileNotFoundError as e:
            print(f"错误: {e}")
            return
        except Exception as e:
            print(f"加载agent策略文件时出错: {e}")
            return
    
    print(f"配置加载完成: {config}")
    print(f"使用workspace: {workspace}")
    
    # ============================================
    # 步骤3: 创建消息总线
    # ============================================
    # AgentLoop需要MessageBus参数，但process_direct方法不会实际使用它
    bus = MessageBus()
    
    # ============================================
    # 步骤4: 创建LLM提供商
    # ============================================
    print("正在初始化 LLM 提供商...")
    provider = _make_provider(config)
    if provider is None:
        print("LLM提供商初始化失败，程序退出")
        return
    print(f"LLM提供商初始化成功: {config.agents.defaults.model}")
    
    # ============================================
    # 步骤5: 创建AgentLoop智能体
    # ============================================
    print("正在初始化 AgentLoop...")
    agent_loop = AgentLoop(
        bus=bus,                                          # 消息总线
        provider=provider,                                 # LLM提供商
        workspace=workspace,                              # 工作空间路径
        model=config.agents.defaults.model,               # 使用的模型
        max_iterations=20,                                # 最大迭代次数
        brave_api_key=config.tools.web.search.api_key or None,  # 搜索API密钥
        exec_config=config.tools.exec,                    # 执行配置
        restrict_to_workspace=config.tools.restrict_to_workspace,  # 是否限制在工作空间内
    )
    print("AgentLoop初始化完成")
    
    # ============================================
    # 步骤6: 初始化聊天记录器（如果启用）
    # ============================================
    chat_logger = None
    if args.save_chat:
        print("\n" + "="*60)
        print("正在初始化聊天记录器...")
        print("="*60)
        chat_logger = ChatLogger(workspace, args.chat_dir)
        print("聊天记录器初始化完成")

    # ============================================
    # 步骤7: 初始化微信监听
    # ============================================
    print("\n" + "="*60)
    print("正在启动微信监听...")
    print("="*60)
    
    # 创建WeChat实例
    wx = WeChat()
    
    # 添加所有要监听的群/人
    target_groups = args.group
    for group in target_groups:
        wx.AddListenChat(group)
        print(f"已添加监听目标: {group}")
    
    print(f"\n共监听 {len(target_groups)} 个目标")
    
    # ============================================
    # 步骤8: 持续监听并处理消息
    # ============================================
    print("\n开始监听消息... (按Ctrl+C退出)")
    print("="*60)
    
    while True:
        try:
            # 获取监听到的消息
            msgs = wx.GetListenMessage()
            
            # 遍历每个聊天的消息
            for chat in msgs:
                msg_list = msgs.get(chat)  # 获取该聊天的消息列表
                
                # 遍历每条消息
                for i in msg_list:
                    # 只处理来自已监听目标的消息
                    # chat对象的名称或ID需要与监听目标匹配
                    # 这里使用简单的字符串匹配
                    is_monitored = False
                    for target in target_groups:
                        if target in str(chat):
                            is_monitored = True
                            break
                    
                    if not is_monitored:
                        continue
                    
                    print(f"\n[{chat}] 收到消息: {i}")
                    
                    # 只处理好友发送的消息（type == 'friend'）
                    if i.type == 'friend':
                        # 提取用户消息内容
                        user_message = i.content
                        print(f"用户消息: {user_message}")
                        
                        # 记录用户消息（如果启用聊天记录）
                        if chat_logger:
                            sender_name = i[0]  # 获取发送者姓名
                            chat_logger.log_message(str(chat), sender_name, user_message)
                        
                        # 生成session_key（每个群/人独立）
                        session_key = f"wechat:{chat}"
                        
                        # ========================================
                        # 调用nanobot智能体处理消息
                        # ========================================
                        print("正在维思机器人智能体处理...")
                        response = await agent_loop.process_direct(
                            content=user_message,          # 用户输入的消息内容
                            session_key=session_key,       # 会话标识，用于维护上下文
                            channel="wechat",              # 渠道类型固定为wechat
                            chat_id=str(chat)              # 聊天ID
                        )

                        # 打印智能体响应
                        print("\n" + "="*60)
                        print("智能体响应:")
                        print("="*60)
                        print(response)
                        print("="*60)
                        
                        # ========================================
                        # 检查是否需要发送文件
                        # ========================================
                        files_info = extract_send_files_xml(response)
                        
                        if files_info:
                            # 响应中包含文件发送请求
                            print(f"\n检测到文件发送请求，共 {len(files_info)} 个文件")
                            
                            # 逐个发送文件
                            for idx, file_info in enumerate(files_info, 1):
                                print(f"\n[{idx}/{len(files_info)}] 处理文件...")
                                print(f"文件信息: {file_info}")
                                
                                # 发送文件
                                file_path = file_info.get('file_path')
                                caption = file_info.get('caption')
                                
                                if file_path:
                                    success, msg = send_wechat_file(
                                        chat=chat,
                                        file_path=file_path,
                                        caption=caption,
                                        chat_logger=chat_logger,
                                        chat_name=str(chat)
                                    )
                                    
                                    if not success:
                                        # 文件发送失败，通知用户
                                        error_msg = f"抱歉，文件发送失败: {msg}"
                                        chat.SendMsg(error_msg)
                                        print(f"已发送错误消息到: {chat}")
                            
                            # 提取并发送纯文本部分（去除XML标签）
                            text_response = remove_xml_tags(response)
                        else:
                            # 没有文件发送请求，使用原始响应
                            text_response = response
                        
                        # 记录机器人回复（如果启用聊天记录）
                        if chat_logger and not files_info:
                            # 如果有文件发送，已经在send_wechat_file中记录了
                            chat_logger.log_message(str(chat), "WeiSensebot", text_response)
                        
                        # ========================================
                        # 发送文本回复到微信群
                        # ========================================
                        if text_response.strip():  # 只在有文本内容时发送
                            # 格式: [发送者姓名:]回复内容
                            sender_name = i[0]  # 获取发送者姓名
                            reply_message = f'[{sender_name}:]{text_response}'
                            chat.SendMsg(reply_message)
                            print(f"已发送回复到: {chat}")
            
            # 休眠指定时间，避免频繁轮询占用CPU
            time.sleep(args.poll_interval)
            
        except Exception as e:
            print(f"处理消息时出错: {e}")
            import traceback
            traceback.print_exc()
            # 继续循环，不因单个错误退出


# ============================================
# 程序入口
# ============================================
if __name__ == "__main__":
    try:
        # 解析命令行参数
        args = parse_args()
        
        # 运行异步主函数
        asyncio.run(simple_direct_call(args))
    except KeyboardInterrupt:
        print("\n程序已停止")
    except Exception as e:
        print(f"程序运行出错: {e}")
        import traceback
        traceback.print_exc()