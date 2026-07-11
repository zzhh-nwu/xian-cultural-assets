"""
多媒体数据处理模块
处理图片、音频、视频的格式转换、质量优化和标准化
由于用户无GPU，所有操作均使用CPU实现
"""

import os, json
from typing import List, Tuple, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_DIR = os.path.join(BASE_DIR, 'data', '01_raw')
PROCESSED_DIR = os.path.join(BASE_DIR, 'data', '02_processed')


class MediaProcessor:
    """多媒体数据处理器"""

    def __init__(self):
        os.makedirs(os.path.join(PROCESSED_DIR, 'images'), exist_ok=True)
        os.makedirs(os.path.join(PROCESSED_DIR, 'audio'), exist_ok=True)
        os.makedirs(os.path.join(PROCESSED_DIR, 'video'), exist_ok=True)

    # ===== 图片处理 =====

    def process_image(self, input_path: str, output_path: str = None,
                      target_size: Tuple[int, int] = (1920, 1080),
                      quality: int = 85, remove_watermark_region: Optional[Tuple] = None) -> str:
        """处理图片：统一分辨率、压缩、可选去水印"""
        try:
            from PIL import Image, ImageFilter

            img = Image.open(input_path)

            # 统一分辨率（保持宽高比，填充黑边）
            img.thumbnail(target_size, Image.Resampling.LANCZOS)
            if img.size != target_size:
                new_img = Image.new('RGB', target_size, (0, 0, 0))
                x = (target_size[0] - img.size[0]) // 2
                y = (target_size[1] - img.size[1]) // 2
                new_img.paste(img, (x, y))
                img = new_img

            # 可选：去水印（需手动指定水印区域）
            if remove_watermark_region:
                import cv2
                import numpy as np
                cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                mask = np.zeros(cv_img.shape[:2], np.uint8)
                x, y, w, h = remove_watermark_region
                mask[y:y+h, x:x+w] = 255
                cv_img = cv2.inpaint(cv_img, mask, 3, cv2.INPAINT_TELEA)
                img = Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))

            if output_path is None:
                base = os.path.splitext(os.path.basename(input_path))[0]
                output_path = os.path.join(PROCESSED_DIR, 'images', f'{base}.png')

            img.save(output_path, 'PNG', optimize=True)
            return output_path
        except ImportError as e:
            print(f'图片处理模块未完全安装: {e}')
            return input_path

    def batch_process_images(self, image_dir: str) -> List[str]:
        """批量处理目录中的图片"""
        results = []
        for f in os.listdir(image_dir):
            if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.webp')):
                path = os.path.join(image_dir, f)
                result = self.process_image(path)
                results.append(result)
        print(f'批量处理完成: {len(results)} 张图片')
        return results

    # ===== 音频处理 =====

    def process_audio(self, input_path: str, output_path: str = None,
                      target_sr: int = 44100, channels: int = 2,
                      clip_seconds: int = 30) -> str:
        """处理音频：转WAV、统一采样率、截取片段"""
        try:
            from pydub import AudioSegment

            audio = AudioSegment.from_file(input_path)
            audio = audio.set_frame_rate(target_sr).set_channels(channels)

            # 截取前N秒作为展示片段
            if len(audio) > clip_seconds * 1000:
                audio = audio[:clip_seconds * 1000]

            if output_path is None:
                base = os.path.splitext(os.path.basename(input_path))[0]
                output_path = os.path.join(PROCESSED_DIR, 'audio', f'{base}.wav')

            audio.export(output_path, format='wav')
            return output_path
        except ImportError as e:
            print(f'音频处理模块未安装: {e} (需要 pydub + ffmpeg)')
            return input_path

    # ===== 视频处理 =====

    def process_video(self, input_path: str, output_path: str = None,
                      clip_seconds: int = 30, target_fps: int = 30) -> str:
        """处理视频：转MP4 H.264、截取精华片段"""
        try:
            from moviepy.editor import VideoFileClip

            clip = VideoFileClip(input_path)

            # 截取前N秒
            if clip.duration > clip_seconds:
                clip = clip.subclip(0, clip_seconds)

            if output_path is None:
                base = os.path.splitext(os.path.basename(input_path))[0]
                output_path = os.path.join(PROCESSED_DIR, 'video', f'{base}.mp4')

            clip.write_videofile(output_path, codec='libx264', fps=target_fps,
                                audio_codec='aac', verbose=False, logger=None)
            clip.close()
            return output_path
        except ImportError as e:
            print(f'视频处理模块未安装: {e} (需要 moviepy + ffmpeg)')
            return input_path

    # ===== 语音合成（免费、无需API key） =====

    async def generate_speech(self, text: str, output_path: str,
                              voice: str = "zh-CN-XiaoxiaoNeural") -> str:
        """使用Edge TTS生成语音（免费，无需API key）"""
        try:
            import edge_tts
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(output_path)
            print(f'语音已合成: {output_path}')
            return output_path
        except ImportError:
            print('edge-tts未安装，跳过语音合成')
            return ''
        except Exception as e:
            print(f'语音合成失败: {e}')
            return ''

    def generate_speech_sync(self, text: str, output_path: str = None,
                             voice: str = "zh-CN-XiaoxiaoNeural") -> str:
        """同步版本的语音合成"""
        import asyncio
        if output_path is None:
            output_path = os.path.join(PROCESSED_DIR, 'audio', 'tts_output.mp3')
        return asyncio.run(self.generate_speech(text, output_path, voice))

    # ===== 统计信息 =====

    def get_processing_report(self) -> dict:
        return {
            'processor': 'MediaProcessor v1.0',
            'capabilities': {
                'image': 'PIL + OpenCV (CPU)',
                'audio': 'pydub (requires ffmpeg)',
                'video': 'moviepy (requires ffmpeg)',
                'tts': 'edge-tts (free, no API key)',
            },
            'limitations': 'No GPU; SD/Whisper/YOLOv8 not available locally',
            'output_dirs': {
                'images': os.path.join(PROCESSED_DIR, 'images'),
                'audio': os.path.join(PROCESSED_DIR, 'audio'),
                'video': os.path.join(PROCESSED_DIR, 'video'),
            }
        }


if __name__ == '__main__':
    print('=' * 60)
    print('  多媒体数据处理器')
    print('=' * 60)
    processor = MediaProcessor()
    report = processor.get_processing_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print('\n处理器就绪。实际媒体文件需手工下载后放入对应目录处理。')
