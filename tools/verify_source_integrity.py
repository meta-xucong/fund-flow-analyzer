# -*- coding: utf-8 -*-
"""
源代码完整性检查工具

检查源代码文件的编码和完整性
"""
import argparse
import sys
from pathlib import Path


def check_file_encoding(file_path: Path) -> bool:
    """
    检查文件编码是否为UTF-8
    
    Args:
        file_path: 文件路径
        
    Returns:
        是否为有效UTF-8
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read()
        return True
    except UnicodeDecodeError:
        return False


def check_file_integrity(file_path: Path) -> dict:
    """
    检查文件完整性
    
    Args:
        file_path: 文件路径
        
    Returns:
        检查结果字典
    """
    result = {
        'path': str(file_path),
        'valid': True,
        'issues': []
    }
    
    # 检查编码
    if not check_file_encoding(file_path):
        result['valid'] = False
        result['issues'].append('非UTF-8编码')
    
    # 检查Python文件语法
    if file_path.suffix == '.py':
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                compile(f.read(), file_path.name, 'exec')
        except SyntaxError as e:
            result['valid'] = False
            result['issues'].append(f'语法错误: {e}')
    
    return result


def verify_directory(root_dir: Path, extensions: list = None) -> dict:
    """
    验证目录下所有文件
    
    Args:
        root_dir: 根目录
        extensions: 要检查的文件扩展名列表，默认['.py']
        
    Returns:
        验证结果汇总
    """
    if extensions is None:
        extensions = ['.py']
    
    results = {
        'total': 0,
        'valid': 0,
        'invalid': 0,
        'files': []
    }
    
    for ext in extensions:
        for file_path in root_dir.rglob(f'*{ext}'):
            # 跳过虚拟环境目录
            if 'venv' in str(file_path) or '__pycache__' in str(file_path):
                continue
            
            results['total'] += 1
            check_result = check_file_integrity(file_path)
            results['files'].append(check_result)
            
            if check_result['valid']:
                results['valid'] += 1
            else:
                results['invalid'] += 1
    
    return results


def print_results(results: dict):
    """打印检查结果"""
    print(f"\n{'='*60}")
    print(f"源代码完整性检查报告")
    print(f"{'='*60}")
    print(f"总文件数: {results['total']}")
    print(f"有效文件: {results['valid']}")
    print(f"问题文件: {results['invalid']}")
    print(f"{'='*60}\n")
    
    if results['invalid'] > 0:
        print("问题文件列表:")
        for file_result in results['files']:
            if not file_result['valid']:
                print(f"\n✗ {file_result['path']}")
                for issue in file_result['issues']:
                    print(f"  - {issue}")
        print()
        return False
    else:
        print("✓ 所有文件检查通过!")
        return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='源代码完整性检查')
    parser.add_argument('--root', type=str, default='.',
                       help='项目根目录，默认当前目录')
    parser.add_argument('--ext', nargs='+', default=['.py'],
                       help='要检查的文件扩展名，默认.py')
    
    args = parser.parse_args()
    
    root_dir = Path(args.root).resolve()
    
    if not root_dir.exists():
        print(f"错误: 目录不存在 {root_dir}")
        sys.exit(1)
    
    print(f"检查目录: {root_dir}")
    print(f"文件类型: {', '.join(args.ext)}")
    
    results = verify_directory(root_dir, args.ext)
    success = print_results(results)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
