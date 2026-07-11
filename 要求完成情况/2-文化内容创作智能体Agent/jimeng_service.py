"""
豆包(Doubao) AI图片+视频生成服务
图片: Seedream (OpenAI兼容)
视频: Seedance (异步API)
"""

import os, time, requests
from openai import OpenAI

_client = None
ARK_BASE = "https://ark.cn-beijing.volces.com/api/v3"


def _load_key():
    key = os.getenv("ARK_API_KEY", "")
    if key: return key
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('ARK_API_KEY='):
                    return line.split('=',1)[1].strip()
    return ""


def _get_client():
    global _client
    key = _load_key()
    if not _client and key:
        _client = OpenAI(api_key=key, base_url=ARK_BASE)
    return _client


def image_recognition(image_b64: str, prompt: str = "") -> dict:
    """豆包视觉识别（doubao-1-5-vision-pro-32k-250115）"""
    client = _get_client()
    if not client:
        return {"success": False, "error": "未配置ARK_API_KEY"}
    try:
        if not image_b64.startswith("data:"):
            image_b64 = f"data:image/jpeg;base64,{image_b64}"
        resp = client.chat.completions.create(
            model="doubao-1-5-vision-pro-32k-250115",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": image_b64}},
                    {"type": "text", "text": prompt or "请详细识别这张图片中的文化内容，包括文物/建筑名称、朝代/年代、艺术风格、材质技法、文化价值等。"}
                ]
            }],
            max_tokens=2000
        )
        return {"success": True, "answer": resp.choices[0].message.content}
    except Exception as e:
        return {"success": False, "error": str(e)}


def text_to_image(prompt: str, width: int = 2048, height: int = 2048) -> dict:
    """豆包Seedream文生图"""
    client = _get_client()
    if not client:
        return {"success": False, "error": "未配置ARK_API_KEY"}
    try:
        resp = client.images.generate(model="doubao-seedream-4-5-251128", prompt=prompt, size="2048x2048", n=1)
        url = resp.data[0].url if resp.data else ""
        return {"success": True, "image_urls": [url] if url else [], "prompt": prompt}
    except Exception as e:
        return {"success": False, "error": str(e)}


def text_to_video(prompt: str) -> dict:
    """豆包Seedance文生视频（异步）"""
    key = _load_key()
    if not key: return {"success": False, "error": "未配置ARK_API_KEY"}
    try:
        resp = requests.post(f"{ARK_BASE}/contents/generations/tasks",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": "doubao-seedance-1-0-pro-250528", "content": [{"type": "text", "text": prompt}]},
            timeout=30)
        data = resp.json()
        task_id = data.get("id", "")
        return {"success": True, "task_id": task_id, "status": "submitted" if task_id else "failed"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_video_result(task_id: str) -> dict:
    """查询视频生成结果"""
    key = _load_key()
    if not key: return {"success": False, "error": "未配置ARK_API_KEY"}
    try:
        resp = requests.get(f"{ARK_BASE}/contents/generations/tasks/{task_id}",
            headers={"Authorization": f"Bearer {key}"}, timeout=30)
        data = resp.json()
        status = data.get("status", "unknown")
        video_url = ""
        if status == "succeeded" and data.get("content"):
            video_url = data["content"].get("video_url", "")
        return {"success": True, "status": status, "video_url": video_url}
    except Exception as e:
        return {"success": False, "error": str(e)}
