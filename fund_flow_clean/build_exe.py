#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
打包脚本 - 将资金流向分析系统打包为独立EXE
"""
import PyInstaller.__main__
import os
import sys
import shutil

def clean_build():
    """清理之前的构建文件"""
    dirs_to_remove = ['build', 'dist']
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            print(f"[*] 清理 {dir_name} 目录...")
            shutil.rmtree(dir_name)
    
    # 清理spec文件
    for f in os.listdir('.'):
        if f.endswith('.spec'):
            os.remove(f)
            print(f"[*] 删除 {f}")

def build_exe():
    """构建EXE"""
    print("[*] 开始打包资金流向分析系统...")
    
    # PyInstaller参数
    args = [
        'launch.py',  # 主入口文件
        '--name=FundFlowAnalyzer',  # EXE名称
        '--onefile',  # 打包为单个文件
        '--windowed',  # 无控制台窗口（GUI应用）
        '--icon=NONE',  # 无图标
        
        # 添加数据文件
        '--add-data=frontend;frontend',
        '--add-data=database;database',
        
        # 隐藏导入（确保所有依赖都被包含）
        '--hidden-import=flask',
        '--hidden-import=flask_cors',
        '--hidden-import=pandas',
        '--hidden-import=pandas._libs.tslibs.np_datetime',
        '--hidden-import=pandas._libs.tslibs.nattype',
        '--hidden-import=pandas._libs.tslibs.timezones',
        '--hidden-import=pandas._libs.tslibs.timestamps',
        '--hidden-import=numpy',
        '--hidden-import=akshare',
        '--hidden-import=requests',
        '--hidden-import=sqlite3',
        '--hidden-import=concurrent.futures',
        '--hidden-import=threading',
        '--hidden-import=logging',
        '--hidden-import=datetime',
        '--hidden-import=json',
        '--hidden-import=csv',
        '--hidden-import=zipfile',
        '--hidden-import=shutil',
        '--hidden-import=pathlib',
        '--hidden-import=functools',
        '--hidden-import=warnings',
        '--hidden-import=signal',
        '--hidden-import=time',
        '--hidden-import=os',
        '--hidden-import=sys',
        '--hidden-import=atexit',
        '--hidden-import=subprocess',
        '--hidden-import=socket',
        '--hidden-import=webbrowser',
        
        # 排除不必要的模块（减小体积）
        '--exclude-module=matplotlib',
        '--exclude-module=tkinter',
        '--exclude-module=PyQt5',
        '--exclude-module=PyQt6',
        '--exclude-module=PySide2',
        '--exclude-module=PySide6',
        '--exclude-module=unittest',
        '--exclude-module=pytest',
        '--exclude-module=IPython',
        '--exclude-module=jupyter',
        '--exclude-module=notebook',
        '--exclude-module=scipy',
        '--exclude-module=PIL',
        '--exclude-module=Pillow',
        '--exclude-module=cryptography',
        '--exclude-module=bcrypt',
        '--exclude-module=paramiko',
        '--exclude-module=pycryptodome',
        '--exclude-module=Crypto',
        
        # 运行时钩子
        '--runtime-hook=runtime_hook.py',
        
        # 优化
        '--strip',  # 去除符号表
        '--noupx',  # 不使用UPX压缩（避免被杀毒软件误报）
    ]
    
    PyInstaller.__main__.run(args)
    
    print("[*] 打包完成！")
    print("[*] EXE文件位于: dist/FundFlowAnalyzer.exe")

def copy_additional_files():
    """复制额外文件到dist目录"""
    dist_dir = 'dist'
    if not os.path.exists(dist_dir):
        os.makedirs(dist_dir)
    
    # 复制前端静态文件
    if os.path.exists('frontend'):
        frontend_dist = os.path.join(dist_dir, 'frontend')
        if os.path.exists(frontend_dist):
            shutil.rmtree(frontend_dist)
        shutil.copytree('frontend', frontend_dist)
        print(f"[*] 复制 frontend 到 {frontend_dist}")
    
    # 复制数据库目录
    if os.path.exists('database'):
        db_dist = os.path.join(dist_dir, 'database')
        if not os.path.exists(db_dist):
            os.makedirs(db_dist)
        print(f"[*] 创建 {db_dist}")

if __name__ == '__main__':
    clean_build()
    build_exe()
    copy_additional_files()
    print("\n[OK] 所有步骤完成！")
