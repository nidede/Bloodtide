"""
游戏打包脚本 - 将游戏打包成 Windows 可执行文件
使用方法: python build.py
"""
import os
import sys
import subprocess
import shutil

def clean():
    """清理所有构建文件"""
    dirs_to_clean = ['build', 'dist']
    for d in dirs_to_clean:
        if os.path.exists(d):
            print(f"清理 {d}/ ...")
            shutil.rmtree(d)
    # 清理 .spec 文件生成的缓存
    for f in os.listdir('.'):
        if f.endswith('.spec'):
            print(f"清理 {f} ...")
            os.remove(f)
    print("清理完成!")

def clean_build():
    """只清理 build 和 dist 目录"""
    dirs_to_clean = ['build', 'dist']
    for d in dirs_to_clean:
        if os.path.exists(d):
            print(f"清理 {d}/ ...")
            shutil.rmtree(d)
    print("构建目录清理完成!")

def generate_spec():
    """生成 spec 配置文件"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/core/main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'pygame',
        'network',
        'network.room',
        'network.discovery',
        'network.sync',
        'network.game_sync',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SurvivorGame',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SurvivorGame',
)
'''
    with open('survivor.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    print("spec 文件已生成!")

def build():
    """执行打包"""
    print("=" * 50)
    print("开始打包 SurvivorGame...")
    print("=" * 50)

    # 检查 PyInstaller 是否安装
    try:
        import PyInstaller
        print(f"PyInstaller 版本: {PyInstaller.__version__}")
    except ImportError:
        print("正在安装 PyInstaller...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])

    # 执行打包
    cmd = ['pyinstaller', 'survivor.spec', '--clean']
    result = subprocess.run(cmd, shell=True)

    if result.returncode == 0:
        print("=" * 50)
        print("打包成功!")
        print(f"输出目录: dist/SurvivorGame/")
        print("=" * 50)

        # 创建 ZIP 压缩包
        create_zip()
    else:
        print("打包失败!")
        sys.exit(1)

def create_zip():
    """创建 ZIP 压缩包"""
    import zipfile
    import datetime

    dist_dir = 'dist/SurvivorGame'
    zip_name = f'dist/SurvivorGame_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.zip'

    print(f"创建压缩包: {zip_name}")

    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(dist_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, 'dist')
                zipf.write(file_path, arcname)
                print(f"  添加: {arcname}")

    print(f"压缩包创建完成: {zip_name}")

def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == 'clean':
            clean()
        elif sys.argv[1] == 'zip':
            create_zip()
        else:
            print("用法: python build.py [clean|zip]")
    else:
        # 只清理 build 和 dist，不清理 spec 文件
        clean_build()
        # 重新生成 spec 文件
        generate_spec()
        # 执行打包
        build()

if __name__ == '__main__':
    main()
