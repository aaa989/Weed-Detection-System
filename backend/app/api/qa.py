import httpx
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/qa", tags=["qa"])


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]


class ChatResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None


SYSTEM_PROMPT = """你是一个专业的杂草识别检测AI助手。你的职责是：

1. 帮助用户了解杂草识别检测系统的功能和使用方法
2. 解答关于YOLO目标检测、深度学习模型相关的问题
3. 分析检测结果，提供专业建议
4. 解答杂草种类、分布、危害等相关知识

系统功能包括：
- 单图检测：上传单张遥感影像，检测其中的杂草和作物
- 批量检测：同时上传最多50张图片进行检测
- 视频检测：上传视频进行实时或完整检测
- 摄像头实时检测：使用摄像头进行实时目标检测

请用中文回答，保持专业、友好、有帮助的语气。"""


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not settings.deepseek_api_key:
        raise HTTPException(status_code=500, detail="AI服务未配置API密钥")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in request.messages:
        messages.append({"role": msg.role, "content": msg.content})

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                settings.deepseek_api_url,
                headers={
                    "Authorization": f"Bearer {settings.deepseek_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "deepseek-chat",
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 2000,
                },
            )

        if response.status_code != 200:
            logger.error(f"DeepSeek API error: {response.status_code} {response.text}")
            raise HTTPException(status_code=502, detail="AI服务请求失败")

        result = response.json()
        content = result["choices"][0]["message"]["content"]

        return ChatResponse(
            success=True,
            message="回答成功",
            data={"content": content, "role": "assistant"},
        )

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="AI服务超时")
    except Exception as e:
        logger.error(f"QA API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI服务异常: {str(e)}")
