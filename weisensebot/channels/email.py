"""
Email channel implementation using IMAP polling + SMTP replies.

邮件通道实现说明

本模块实现了 WeiSenseBot 的邮件通道功能，支持通过 IMAP 接收邮件和通过 SMTP 发送回复。

功能概述：
--------
1. 接收邮件 (Inbound)
   - 使用 IMAP 协议轮询邮箱中的未读邮件
   - 解析邮件内容（包括纯文本和 HTML）
   - 保存邮件附件到本地目录
   - 将邮件转换为内部事件消息传递给消息总线

2. 发送邮件 (Outbound)
   - 使用 SMTP 协议发送回复邮件
   - 支持自动回复模式（可配置）
   - 维护邮件对话线程（Subject 和 Message-ID）

3. 附件处理功能 (新增)
   - 自动检测邮件中的附件
   - 保存附件到 workspace/email_attachments 目录
   - 文件名格式：{timestamp}_{uuid}_{original_filename}
   - 在邮件内容末尾添加附件链接（file:// 协议）
   - 支持多种附件类型（PDF、图片、文档、压缩包等）

附件处理详细说明：
-----------------
1. 附件保存目录
   - 默认路径：~/.weisensebot/workspace/email_attachments
   - 可通过配置中的 workspace 参数自定义
   - 示例：/Users/gaoshine/.weisensebot/workspace/email_attachments

2. 文件名处理
   - 清理特殊字符（< > : " | ? * 等）
   - 添加时间戳前缀防止冲突
   - 添加 UUID 后缀确保唯一性
   - 示例：20260310_095845_a1b2c3d4_report.pdf

3. 支持的文件类型
   - PDF (.pdf)
   - 图片 (.jpg, .png, .gif)
   - 文本 (.txt)
   - 压缩包 (.zip)
   - 其他类型使用 .bin 扩展名

4. 附件链接格式
   - 在邮件内容末尾添加 "Attachments:" 部分
   - 每个附件占一行，格式为：
     - file:///完整/文件路径

5. 错误处理
   - 单个附件保存失败不影响其他附件
   - 错误信息记录到日志
   - 附件内容为空时给出警告

核心方法说明：
-------------
- _get_attachments_dir(): 获取附件保存目录路径
- _sanitize_filename(): 清理文件名中的特殊字符
- _save_attachment(): 保存单个附件到磁盘
- _save_attachments(): 批量保存所有附件
- _extract_text_body(): 提取邮件正文和附件信息
- _fetch_messages(): 获取邮件并处理附件

配置参数：
----------
Email channel 配置项：
  - imapHost: IMAP 服务器地址
  - imapPort: IMAP 端口（通常为 993）
  - imapUsername: IMAP 用户名
  - imapPassword: IMAP 密码（或授权码）
  - imapUseSsl: 是否使用 SSL 连接
  - smtpHost: SMTP 服务器地址
  - smtpPort: SMTP 端口（通常为 465）
  - smtpUsername: SMTP 用户名
  - smtpPassword: SMTP 密码（或授权码）
  - smtpUseSsl: 是否使用 SSL 连接
  - fromAddress: 发件人地址
  - autoReplyEnabled: 是否启用自动回复
  - pollIntervalSeconds: 轮询间隔（秒）
  - markSeen: 是否标记邮件为已读
  - maxBodyChars: 邮件正文最大字符数
  - workspace: 工作目录路径（附件保存位置）

使用示例：
---------
1. 配置文件示例 (.weisensebot/config.json):
   {
     "channels": {
       "email": {
         "enabled": true,
         "imapHost": "imap.qq.com",
         "imapPort": 993,
         "imapUsername": "your_email@qq.com",
         "imapPassword": "your_auth_code",
         "smtpHost": "smtp.qq.com",
         "smtpPort": 465,
         "smtpUsername": "your_email@qq.com",
         "smtpPassword": "your_auth_code",
         "workspace": "~/.weisensebot/workspace"
       }
     }
   }

2. 邮件处理流程：
   a. 启动 EmailChannel
   b. 每隔 pollIntervalSeconds 秒轮询一次 IMAP 邮箱
   c. 对于每封新邮件：
      - 解析邮件头（From, Subject, Date, Message-ID）
      - 提取邮件正文
      - 保存所有附件到 workspace/email_attachments
      - 构建包含正文和附件链接的内容字符串
      - 通过消息总线发送给 Agent 处理
   d. Agent 处理后通过 send() 方法回复邮件

注意事项：
---------
- QQ邮箱需要使用授权码而非密码
- 附件保存在本地磁盘，请注意磁盘空间
- 文件名中的特殊字符会被替换为下划线
- 同名文件会通过时间戳和 UUID 区分
- 内嵌图片（inline）不会被保存为附件

"""

import asyncio
import html
import imaplib
import os
import re
import smtplib
import ssl
import uuid
from datetime import date, datetime
from email import policy
from email.header import decode_header, make_header
from email.message import EmailMessage
from email.parser import BytesParser
from email.utils import parseaddr
from pathlib import Path
from typing import Any, Tuple

from loguru import logger

from weisensebot.bus.events import OutboundMessage
from weisensebot.bus.queue import MessageBus
from weisensebot.channels.base import BaseChannel
from weisensebot.config.schema import EmailConfig


class EmailChannel(BaseChannel):
    """
    Email channel.

    Inbound:
    - Poll IMAP mailbox for unread messages.
    - Convert each message into an inbound event.

    Outbound:
    - Send responses via SMTP back to the sender address.
    """

    name = "email"
    _IMAP_MONTHS = (
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    )

    def __init__(self, config: EmailConfig, bus: MessageBus):
        super().__init__(config, bus)
        self.config: EmailConfig = config
        self._last_subject_by_chat: dict[str, str] = {}
        self._last_message_id_by_chat: dict[str, str] = {}
        self._processed_uids: set[str] = set()  # Capped to prevent unbounded growth
        self._MAX_PROCESSED_UIDS = 100000

    async def start(self) -> None:
        """Start polling IMAP for inbound emails."""
        if not self.config.consent_granted:
            logger.warning(
                "Email channel disabled: consent_granted is false. "
                "Set channels.email.consentGranted=true after explicit user permission."
            )
            return

        if not self._validate_config():
            return

        self._running = True
        logger.info("Starting Email channel (IMAP polling mode)...")

        poll_seconds = max(5, int(self.config.poll_interval_seconds))
        while self._running:
            try:
                inbound_items = await asyncio.to_thread(self._fetch_new_messages)
                for item in inbound_items:
                    sender = item["sender"]
                    subject = item.get("subject", "")
                    message_id = item.get("message_id", "")

                    if subject:
                        self._last_subject_by_chat[sender] = subject
                    if message_id:
                        self._last_message_id_by_chat[sender] = message_id

                    await self._handle_message(
                        sender_id=sender,
                        chat_id=sender,
                        content=item["content"],
                        metadata=item.get("metadata", {}),
                    )
            except Exception as e:
                logger.error("Email polling error: {}", e)

            await asyncio.sleep(poll_seconds)

    async def stop(self) -> None:
        """Stop polling loop."""
        self._running = False

    async def send(self, msg: OutboundMessage) -> None:
        """Send email via SMTP."""
        if not self.config.consent_granted:
            logger.warning("Skip email send: consent_granted is false")
            return

        if not self.config.smtp_host:
            logger.warning("Email channel SMTP host not configured")
            return

        to_addr = msg.chat_id.strip()
        if not to_addr:
            logger.warning("Email channel missing recipient address")
            return

        # Determine if this is a reply (recipient has sent us an email before)
        is_reply = to_addr in self._last_subject_by_chat
        force_send = bool((msg.metadata or {}).get("force_send"))

        # autoReplyEnabled only controls automatic replies, not proactive sends
        if is_reply and not self.config.auto_reply_enabled and not force_send:
            logger.info("Skip automatic email reply to {}: auto_reply_enabled is false", to_addr)
            return

        base_subject = self._last_subject_by_chat.get(to_addr, "nanobot reply")
        subject = self._reply_subject(base_subject)
        if msg.metadata and isinstance(msg.metadata.get("subject"), str):
            override = msg.metadata["subject"].strip()
            if override:
                subject = override

        email_msg = EmailMessage()
        email_msg["From"] = self.config.from_address or self.config.smtp_username or self.config.imap_username
        email_msg["To"] = to_addr
        email_msg["Subject"] = subject
        email_msg.set_content(msg.content or "")

        in_reply_to = self._last_message_id_by_chat.get(to_addr)
        if in_reply_to:
            email_msg["In-Reply-To"] = in_reply_to
            email_msg["References"] = in_reply_to

        try:
            await asyncio.to_thread(self._smtp_send, email_msg)
        except Exception as e:
            logger.error("Error sending email to {}: {}", to_addr, e)
            raise

    def _validate_config(self) -> bool:
        missing = []
        if not self.config.imap_host:
            missing.append("imap_host")
        if not self.config.imap_username:
            missing.append("imap_username")
        if not self.config.imap_password:
            missing.append("imap_password")
        if not self.config.smtp_host:
            missing.append("smtp_host")
        if not self.config.smtp_username:
            missing.append("smtp_username")
        if not self.config.smtp_password:
            missing.append("smtp_password")

        if missing:
            logger.error("Email channel not configured, missing: {}", ', '.join(missing))
            return False
        return True

    def _smtp_send(self, msg: EmailMessage) -> None:
        timeout = 30
        if self.config.smtp_use_ssl:
            with smtplib.SMTP_SSL(
                self.config.smtp_host,
                self.config.smtp_port,
                timeout=timeout,
            ) as smtp:
                smtp.login(self.config.smtp_username, self.config.smtp_password)
                smtp.send_message(msg)
            return

        with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port, timeout=timeout) as smtp:
            if self.config.smtp_use_tls:
                smtp.starttls(context=ssl.create_default_context())
            smtp.login(self.config.smtp_username, self.config.smtp_password)
            smtp.send_message(msg)

    def _fetch_new_messages(self) -> list[dict[str, Any]]:
        """Poll IMAP and return parsed unread messages."""
        return self._fetch_messages(
            search_criteria=("UNSEEN",),
            mark_seen=self.config.mark_seen,
            dedupe=True,
            limit=0,
        )

    def fetch_messages_between_dates(
        self,
        start_date: date,
        end_date: date,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """
        Fetch messages in [start_date, end_date) by IMAP date search.

        This is used for historical summarization tasks (e.g. "yesterday").
        """
        if end_date <= start_date:
            return []

        return self._fetch_messages(
            search_criteria=(
                "SINCE",
                self._format_imap_date(start_date),
                "BEFORE",
                self._format_imap_date(end_date),
            ),
            mark_seen=False,
            dedupe=False,
            limit=max(1, int(limit)),
        )

    def _fetch_messages(
        self,
        search_criteria: tuple[str, ...],
        mark_seen: bool,
        dedupe: bool,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Fetch messages by arbitrary IMAP search criteria."""
        messages: list[dict[str, Any]] = []
        mailbox = self.config.imap_mailbox or "INBOX"

        if self.config.imap_use_ssl:
            client = imaplib.IMAP4_SSL(self.config.imap_host, self.config.imap_port)
        else:
            client = imaplib.IMAP4(self.config.imap_host, self.config.imap_port)

        try:
            client.login(self.config.imap_username, self.config.imap_password)
            status, _ = client.select(mailbox)
            if status != "OK":
                return messages

            status, data = client.search(None, *search_criteria)
            if status != "OK" or not data:
                return messages

            ids = data[0].split()
            if limit > 0 and len(ids) > limit:
                ids = ids[-limit:]
            for imap_id in ids:
                status, fetched = client.fetch(imap_id, "(BODY.PEEK[] UID)")
                if status != "OK" or not fetched:
                    continue

                raw_bytes = self._extract_message_bytes(fetched)
                if raw_bytes is None:
                    continue

                uid = self._extract_uid(fetched)
                if dedupe and uid and uid in self._processed_uids:
                    continue

                parsed = BytesParser(policy=policy.default).parsebytes(raw_bytes)
                sender = parseaddr(parsed.get("From", ""))[1].strip().lower()
                if not sender:
                    continue

                # 解码邮件主题、日期和消息ID
                subject = self._decode_header_value(parsed.get("Subject", ""))
                date_value = parsed.get("Date", "")
                message_id = parsed.get("Message-ID", "").strip()
                
                # 提取邮件正文和附件信息（仅用于收集附件元数据，实际保存在下面）
                body, _ = self._extract_text_body(parsed)
                
                # 保存所有附件到磁盘并获取文件路径列表
                attachment_paths = self._save_attachments(parsed)

                # 如果正文为空，设置默认提示
                if not body:
                    body = "(empty email body)"

                # 限制正文长度（根据配置的 max_body_chars）
                body = body[: self.config.max_body_chars]
                
                # 构建邮件内容字符串
                content = (
                    f"Email received.\n"
                    f"From: {sender}\n"
                    f"Subject: {subject}\n"
                    f"Date: {date_value}\n\n"
                    f"{body}"
                )
                
                # 如果有附件，在邮件内容末尾添加附件链接
                if attachment_paths:
                    content += "\n\nAttachments:\n"
                    for path in attachment_paths:
                        # 使用 file:// 协议格式化文件路径，便于在终端中点击打开
                        content += f"- file://{path}\n"

                metadata = {
                    "message_id": message_id,
                    "subject": subject,
                    "date": date_value,
                    "sender_email": sender,
                    "uid": uid,
                }
                messages.append(
                    {
                        "sender": sender,
                        "subject": subject,
                        "message_id": message_id,
                        "content": content,
                        "metadata": metadata,
                    }
                )

                if dedupe and uid:
                    self._processed_uids.add(uid)
                    # mark_seen is the primary dedup; this set is a safety net
                    if len(self._processed_uids) > self._MAX_PROCESSED_UIDS:
                        # Evict a random half to cap memory; mark_seen is the primary dedup
                        self._processed_uids = set(list(self._processed_uids)[len(self._processed_uids) // 2:])

                if mark_seen:
                    client.store(imap_id, "+FLAGS", "\\Seen")
        finally:
            try:
                client.logout()
            except Exception:
                pass

        return messages

    @classmethod
    def _format_imap_date(cls, value: date) -> str:
        """Format date for IMAP search (always English month abbreviations)."""
        month = cls._IMAP_MONTHS[value.month - 1]
        return f"{value.day:02d}-{month}-{value.year}"

    @staticmethod
    def _extract_message_bytes(fetched: list[Any]) -> bytes | None:
        for item in fetched:
            if isinstance(item, tuple) and len(item) >= 2 and isinstance(item[1], (bytes, bytearray)):
                return bytes(item[1])
        return None

    @staticmethod
    def _extract_uid(fetched: list[Any]) -> str:
        for item in fetched:
            if isinstance(item, tuple) and item and isinstance(item[0], (bytes, bytearray)):
                head = bytes(item[0]).decode("utf-8", errors="ignore")
                m = re.search(r"UID\s+(\d+)", head)
                if m:
                    return m.group(1)
        return ""

    @staticmethod
    def _decode_header_value(value: str) -> str:
        if not value:
            return ""
        try:
            return str(make_header(decode_header(value)))
        except Exception:
            return value

    def _get_attachments_dir(self) -> Path:
        """
        获取附件保存目录
        
        Returns:
            Path: 附件保存目录的路径对象
        
        说明:
            - 从配置中读取 workspace 设置，如果不存在则使用默认值 ~/.weisensebot/workspace
            - 在 workspace 下创建 email_attachments 子目录用于存储附件
            - 示例路径: /Users/gaoshine/.weisensebot/workspace/email_attachments
        """
        # 从配置中获取 workspace，如果配置中没有则使用默认值
        workspace = getattr(self.config, 'workspace', '~/.weisensebot/workspace')
        # 展开波浪号路径（~ -> /Users/gaoshine）并拼接附件子目录
        attachments_dir = Path(os.path.expanduser(workspace)) / 'email_attachments'
        return attachments_dir

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """
        清理文件名中的特殊字符
        
        Args:
            filename (str): 原始文件名
        
        Returns:
            str: 清理后的安全文件名
        
        说明:
            - 移除或替换文件名中的特殊字符（如 < > : " | ? * 等）
            - 替换多个连续的下划线为单个下划线
            - 去除首尾的下划线和空格
            - 如果文件名为空，则生成随机文件名
        
        示例:
            输入: "报告<>文档.pdf"
            输出: "报告_文档.pdf"
        """
        # 如果文件名为空，生成一个随机的文件名
        if not filename:
            return f"attachment_{uuid.uuid4().hex[:8]}"
        
        # 移除或替换文件系统不允许的特殊字符
        # < > : " | ? * 以及控制字符（0x00-0x1f）都替换为下划线
        filename = re.sub(r'[<>:"|?*\x00-\x1f]', '_', filename)
        
        # 将多个连续的下划线替换为单个下划线，避免文件名过长
        filename = re.sub(r'_+', '_', filename)
        
        # 去除首尾的下划线和空格
        filename = filename.strip('._ ')
        
        # 如果清理后文件名为空（例如原文件名全是特殊字符），生成随机文件名
        if not filename:
            return f"attachment_{uuid.uuid4().hex[:8]}"
        
        return filename

    def _save_attachment(self, part: Any) -> str | None:
        """
        保存单个附件到磁盘
        
        Args:
            part (Any): 邮件附件部分对象
        
        Returns:
            str | None: 保存后的文件绝对路径，如果保存失败则返回 None
        
        说明:
            - 从邮件部分获取附件文件名，如果文件名缺失则根据 Content-Type 推断扩展名
            - 清理文件名以确保文件系统安全
            - 在文件名中添加时间戳和 UUID 以防止文件名冲突
            - 格式: {timestamp}_{uuid}_{original_filename}
            - 示例: 20260310_095845_a1b2c3d4_report.pdf
            - 自动创建附件目录（如果不存在）
            - 将附件内容写入磁盘并记录日志
        
        支持的文件类型:
            - PDF: .pdf
            - 图片: .jpg, .png, .gif
            - 文本: .txt
            - 压缩包: .zip
            - 其他类型使用 .bin 扩展名
        """
        try:
            # 获取附件的原始文件名
            filename = part.get_filename()
            
            # 如果文件名为空（部分邮件附件可能没有设置文件名）
            if not filename:
                # 根据附件的 Content-Type 推测文件扩展名
                content_type = part.get_content_type()
                ext = {
                    'application/pdf': '.pdf',
                    'image/jpeg': '.jpg',
                    'image/png': '.png',
                    'image/gif': '.gif',
                    'text/plain': '.txt',
                    'application/zip': '.zip',
                    'application/x-zip-compressed': '.zip',
                }.get(content_type, '.bin')
                filename = f"unnamed{ext}"
            
            # 清理文件名，移除特殊字符
            filename = self._sanitize_filename(filename)
            
            # 添加时间戳和 UUID 前缀，防止不同邮件中的同名文件冲突
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')  # 格式: 20260310_095845
            unique_id = uuid.uuid4().hex[:8]  # 取 UUID 的前 8 位作为唯一标识
            
            # 分离文件名和扩展名
            base, ext = os.path.splitext(filename)
            # 如果没有扩展名，使用 .bin 作为默认值
            if not ext:
                ext = '.bin'
            
            # 组合最终的唯一文件名: 时间戳_UUID_原文件名
            unique_filename = f"{timestamp}_{unique_id}_{base}{ext}"
            
            # 获取附件保存目录，如果目录不存在则自动创建
            attachments_dir = self._get_attachments_dir()
            attachments_dir.mkdir(parents=True, exist_ok=True)
            
            # 构建完整的文件路径
            file_path = attachments_dir / unique_filename
            
            # 解码并保存附件内容
            payload = part.get_payload(decode=True)
            if payload:
                # 将字节数据写入文件
                file_path.write_bytes(payload)
                logger.info("保存附件成功: {}", file_path)
                return str(file_path)
            else:
                # 附件内容为空的情况
                logger.warning("附件 {} 没有内容", filename)
                return None
                
        except Exception as e:
            # 保存过程中发生错误，记录日志但不影响其他附件的处理
            logger.error("保存附件失败 {}: {}", filename, e)
            return None

    def _save_attachments(self, msg: Any) -> list[str]:
        """
        保存邮件中的所有附件
        
        Args:
            msg (Any): 邮件消息对象
        
        Returns:
            list[str]: 已保存附件的文件路径列表
        
        说明:
            - 遍历邮件的所有部分（使用 msg.walk()）
            - 检查每个部分的 Content-Disposition 是否为 'attachment'
            - 只保存标记为附件的部分（不包括内嵌图片等 inline 内容）
            - 对每个附件调用 _save_attachment() 方法进行保存
            - 返回成功保存的附件路径列表
        
        注意:
            - 如果邮件不是多部分邮件（is_multipart() = False），直接返回空列表
            - 单个附件保存失败不会影响其他附件的保存
            - 返回的路径是绝对路径，可以用于 file:// 协议链接
        """
        attachment_paths = []
        
        # 如果不是多部分邮件，直接返回空列表
        if not msg.is_multipart():
            return attachment_paths
        
        # 遍历邮件的所有部分
        for part in msg.walk():
            # 检查该部分是否为附件
            content_disposition = part.get_content_disposition()
            if content_disposition == 'attachment':
                # 保存附件并获取文件路径
                file_path = self._save_attachment(part)
                if file_path:
                    attachment_paths.append(file_path)
        
        return attachment_paths

    @classmethod
    def _extract_text_body(cls, msg: Any) -> Tuple[str, list[str]]:
        """Best-effort extraction of readable body text and list of attachment info."""
        if msg.is_multipart():
            plain_parts: list[str] = []
            html_parts: list[str] = []
            attachment_info: list[str] = []
            for part in msg.walk():
                content_disposition = part.get_content_disposition()
                if content_disposition == "attachment":
                    # Collect attachment information
                    filename = part.get_filename() or "unnamed"
                    content_type = part.get_content_type()
                    attachment_info.append(f"{filename} ({content_type})")
                    continue
                content_type = part.get_content_type()
                try:
                    payload = part.get_content()
                except Exception:
                    payload_bytes = part.get_payload(decode=True) or b""
                    charset = part.get_content_charset() or "utf-8"
                    payload = payload_bytes.decode(charset, errors="replace")
                if not isinstance(payload, str):
                    continue
                if content_type == "text/plain":
                    plain_parts.append(payload)
                elif content_type == "text/html":
                    html_parts.append(payload)
            if plain_parts:
                return "\n\n".join(plain_parts).strip(), attachment_info
            if html_parts:
                return cls._html_to_text("\n\n".join(html_parts)).strip(), attachment_info
            return "", attachment_info

        try:
            payload = msg.get_content()
        except Exception:
            payload_bytes = msg.get_payload(decode=True) or b""
            charset = msg.get_content_charset() or "utf-8"
            payload = payload_bytes.decode(charset, errors="replace")
        if not isinstance(payload, str):
            return "", []
        if msg.get_content_type() == "text/html":
            return cls._html_to_text(payload).strip(), []
        return payload.strip(), []

    @staticmethod
    def _html_to_text(raw_html: str) -> str:
        text = re.sub(r"<\s*br\s*/?>", "\n", raw_html, flags=re.IGNORECASE)
        text = re.sub(r"<\s*/\s*p\s*>", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"<[^>]+>", "", text)
        return html.unescape(text)

    def _reply_subject(self, base_subject: str) -> str:
        subject = (base_subject or "").strip() or "nanobot reply"
        prefix = self.config.subject_prefix or "Re: "
        if subject.lower().startswith("re:"):
            return subject
        return f"{prefix}{subject}"
