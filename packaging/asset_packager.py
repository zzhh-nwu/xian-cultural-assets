"""
数字资产包封装模块
- bagit.py 生成校验文件
- manifest.csv 索引生成
- 数字权利证书 HTML 模板
- .zip 打包
"""

import os, json, hashlib, csv, shutil, re
from datetime import datetime
from typing import List, Dict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, 'data', '04_assets')
REGISTRY_DIR = os.path.join(BASE_DIR, 'data', '05_registry')
PROCESSED_DIR = os.path.join(BASE_DIR, 'data', '02_processed')
JSON_PATH = os.path.join(BASE_DIR, 'data', '01_raw', 'text', 'nine_projects.json')

os.makedirs(ASSETS_DIR, exist_ok=True)
os.makedirs(REGISTRY_DIR, exist_ok=True)


class AssetPackager:
    """数字资产包封装器"""

    def __init__(self):
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            self.data = json.load(f)

    # ===== BagIt 打包 =====

    def create_bagit_package(self, source_dir: str, output_name: str = None) -> str:
        """创建BagIt数据包"""
        try:
            import bagit

            if output_name is None:
                output_name = 'xian_cultural_assets'

            output_zip = os.path.join(ASSETS_DIR, f'{output_name}.zip')
            bag_dir = os.path.join(ASSETS_DIR, output_name)

            # 复制source到临时bag目录
            if os.path.exists(bag_dir):
                shutil.rmtree(bag_dir)

            shutil.copytree(source_dir, bag_dir,
                            ignore=shutil.ignore_patterns('__pycache__', '.git', '.DS_Store'))

            # 创建bag
            bag = bagit.make_bag(bag_dir, {
                'Contact-Name': '大学生数据要素素质大赛参赛团队',
                'Source-Organization': '西安文化产权交易中心(适配)',
                'External-Description': '西安文物/非遗/文旅数字资产包',
                'Bagging-Date': datetime.now().strftime('%Y-%m-%d'),
                'External-Identifier': 'XA-CULTURE-2025-001',
                'Bag-Size': f'{self._get_dir_size(bag_dir) / (1024*1024):.1f} MB',
                'BagIt-Profile-Identifier': '数字资产登记标准 v1.0',
            })

            # 打包为zip
            shutil.make_archive(output_zip.replace('.zip', ''), 'zip',
                               os.path.dirname(bag_dir), output_name)

            print(f'BagIt数据包已创建: {output_zip}')
            return output_zip

        except ImportError:
            print('bagit未安装，使用简易打包')
            return self._simple_zip(source_dir, 'xian_cultural_assets.zip')

    def _simple_zip(self, source_dir: str, zip_name: str) -> str:
        output_zip = os.path.join(ASSETS_DIR, zip_name)
        shutil.make_archive(output_zip.replace('.zip', ''), 'zip', source_dir)
        print(f'简易打包完成: {output_zip}')
        return output_zip

    # ===== Manifest 索引 =====

    def generate_manifest(self, source_dir: str = None) -> str:
        """生成 manifest.csv 资产清单"""
        if source_dir is None:
            source_dir = PROCESSED_DIR

        rows = []
        for root, dirs, files in os.walk(source_dir):
            for f in files:
                path = os.path.join(root, f)
                rel_path = os.path.relpath(path, source_dir)
                with open(path, 'rb') as fp:
                    sha256 = hashlib.sha256(fp.read()).hexdigest()
                rows.append({
                    'file_path': rel_path,
                    'format': os.path.splitext(f)[1].lower(),
                    'size_bytes': os.path.getsize(path),
                    'sha256': sha256,
                    'last_modified': datetime.fromtimestamp(os.path.getmtime(path)).isoformat(),
                })

        # 也可以用项目元数据补充
        for project in self.data['projects']:
            rows.append({
                'file_path': f"metadata/{project['asset_id']}.jsonld",
                'format': '.jsonld',
                'size_bytes': 0,
                'sha256': self._sha256_dict(project),
                'last_modified': datetime.now().isoformat(),
            })

        manifest_path = os.path.join(REGISTRY_DIR, 'manifest.csv')
        with open(manifest_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['file_path', 'format', 'size_bytes', 'sha256', 'last_modified'])
            writer.writeheader()
            writer.writerows(rows)

        print(f'资产清单已生成: {manifest_path} ({len(rows)} 条记录)')
        return manifest_path

    # ===== 数字权利证书 =====

    def generate_rights_certificate(self, project: dict = None) -> str:
        """生成数字权利证书 HTML"""
        if project is None:
            project = self.data['projects'][0]

        fingerprint = self._sha256_dict(project)[:32]
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>数字权利证书 - {project['title']}</title>
<style>
  body {{ font-family: 'SimSun', serif; max-width: 800px; margin: 40px auto; padding: 20px; }}
  .cert {{ border: 3px double #8B0000; padding: 40px; background: #FFFEF5; }}
  h1 {{ text-align: center; color: #8B0000; font-size: 24px; margin-bottom: 5px; }}
  .subtitle {{ text-align: center; color: #666; font-size: 14px; margin-bottom: 30px; }}
  table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
  td {{ padding: 10px 8px; border: 1px solid #DDD; }}
  .label {{ background: #F5F5F5; font-weight: bold; width: 25%; }}
  .seal {{ text-align: center; margin-top: 40px; color: #8B0000; font-size: 18px; }}
  .footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 30px; }}
</style>
</head>
<body>
<div class="cert">
  <h1>数字权利证书</h1>
  <p class="subtitle">Digital Rights Certificate</p>
  <hr style="border-color: #8B0000;">
  <table>
    <tr><td class="label">证书编号</td><td>XA-DRC-2025-{project['asset_id'].split('-')[-1]}</td></tr>
    <tr><td class="label">资产名称</td><td>{project['title']} ({project.get('title_en', '')})</td></tr>
    <tr><td class="label">资产类型</td><td>{project['asset_type']}</td></tr>
    <tr><td class="label">权利人</td><td>{project.get('copyright_holder', '')}</td></tr>
    <tr><td class="label">授权条款</td><td>{project.get('license', 'CC BY-NC-ND 4.0')}</td></tr>
    <tr><td class="label">登记标准</td><td>数字资产登记标准 v1.0</td></tr>
    <tr><td class="label">数字指纹</td><td style="font-family: Consolas; font-size: 11px;">SHA256:{fingerprint}</td></tr>
    <tr><td class="label">签发日期</td><td>{now}</td></tr>
    <tr><td class="label">签发机构</td><td>西安文化产权交易中心（虚拟预埋）</td></tr>
  </table>
  <div class="seal">
    <p style="font-size: 28px; margin: 0;">【电子签章预留区域】</p>
    <p style="margin: 5px 0;">西安文化产权交易中心</p>
  </div>
</div>
<p class="footer">此证书为数字资产权利证明，与实物证书具有同等效力 | 证书唯一编号可通过西部九省数字资产登记平台验证</p>
</body>
</html>'''
        cert_path = os.path.join(REGISTRY_DIR, f'{project["asset_id"]}_rights_certificate.html')
        with open(cert_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f'权利证书已生成: {cert_path}')
        return cert_path

    def generate_all_certificates(self) -> List[str]:
        paths = []
        for p in self.data['projects']:
            paths.append(self.generate_rights_certificate(p))
        return paths

    # ===== 工具方法 =====

    def _sha256_dict(self, d: dict) -> str:
        return hashlib.sha256(
            json.dumps(d, sort_keys=True, ensure_ascii=False).encode('utf-8')
        ).hexdigest()

    def _get_dir_size(self, path: str) -> int:
        total = 0
        for root, dirs, files in os.walk(path):
            for f in files:
                total += os.path.getsize(os.path.join(root, f))
        return total


if __name__ == '__main__':
    print('=' * 60)
    print('  数字资产包封装工具')
    print('=' * 60)
    packager = AssetPackager()

    # 生成manifest
    packager.generate_manifest()

    # 生成所有权利证书
    packager.generate_all_certificates()

    # BagIt打包（如果有实际文件目录）
    bag_path = os.path.join(PROCESSED_DIR)
    if os.path.exists(bag_path) and os.listdir(bag_path):
        packager.create_bagit_package(bag_path)
    else:
        print('处理目录为空，跳过了BagIt打包。放置数据文件后会自动打包。')

    print(f'\n完成！输出位置: {REGISTRY_DIR}')
