#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
claw-ex 配置模板管理模块
负责配置模板的创建、查看、应用、导出、删除等操作
支持模板变量替换功能
"""

import os
import json
import re
from datetime import datetime
from pathlib import Path

# 模板存储路径
TEMPLATE_DIR = Path.home() / '.openclaw' / 'templates'
TEMPLATE_INDEX_FILE = TEMPLATE_DIR / 'templates_index.json'

# 颜色支持
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GRAY = '\033[90m'

def c_cyan(s): return f"{Colors.CYAN}{s}{Colors.RESET}"
def c_yellow(s): return f"{Colors.YELLOW}{s}{Colors.RESET}"
def c_green(s): return f"{Colors.GREEN}{s}{Colors.RESET}"
def c_red(s): return f"{Colors.RED}{s}{Colors.RESET}"
def c_gray(s): return f"{Colors.GRAY}{s}{Colors.RESET}"
def c_bold(s): return f"{Colors.BOLD}{s}{Colors.RESET}"

def ensure_template_dir():
    """确保模板目录存在"""
    TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)

def load_template_index():
    """加载模板索引文件"""
    if not TEMPLATE_INDEX_FILE.exists():
        return {'templates': []}
    try:
        with open(TEMPLATE_INDEX_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {'templates': []}

def save_template_index(index):
    """保存模板索引文件"""
    ensure_template_dir()
    with open(TEMPLATE_INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

def template_exists(template_id):
    """检查模板是否存在"""
    index = load_template_index()
    return any(t['id'] == template_id for t in index['templates'])

def validate_template_id(template_id):
    """验证模板 ID 合法性"""
    if not template_id or not template_id.strip():
        return False, '模板 ID 不能为空'
    template_id = template_id.strip()
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', template_id):
        return False, '模板 ID 只能以字母开头，包含字母、数字、下划线和连字符'
    if len(template_id) > 50:
        return False, '模板 ID 长度不能超过 50 个字符'
    return True, ''

def extract_variables(content):
    """从内容中提取变量名列表（{var_name} 格式）"""
    if isinstance(content, str):
        return list(set(re.findall(r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}', content)))
    elif isinstance(content, dict):
        variables = []
        for value in content.values():
            variables.extend(extract_variables(value))
        return list(set(variables))
    elif isinstance(content, list):
        variables = []
        for item in content:
            variables.extend(extract_variables(item))
        return list(set(variables))
    return []

def substitute_variables(content, variables):
    """替换内容中的变量"""
    if isinstance(content, str):
        result = content
        for var_name, var_value in variables.items():
            result = result.replace(f'{{{var_name}}}', str(var_value))
        return result
    elif isinstance(content, dict):
        return {k: substitute_variables(v, variables) for k, v in content.items()}
    elif isinstance(content, list):
        return [substitute_variables(item, variables) for item in content]
    return content

def list_templates():
    """获取所有模板列表"""
    index = load_template_index()
    templates = []
    for t in index['templates']:
        template_file = TEMPLATE_DIR / f"{t['id']}.json"
        templates.append({
            'id': t['id'],
            'name': t.get('name', t['id']),
            'description': t.get('description', ''),
            'category': t.get('category', 'general'),
            'created_at': t.get('created_at', ''),
            'updated_at': t.get('updated_at', ''),
            'has_content': template_file.exists(),
            'variables': t.get('variables', [])
        })
    return templates

def get_template(template_id):
    """获取模板详细信息"""
    index = load_template_index()
    for t in index['templates']:
        if t['id'] == template_id:
            template_file = TEMPLATE_DIR / f"{template_id}.json"
            template_data = {
                'id': t['id'],
                'name': t.get('name', t['id']),
                'description': t.get('description', ''),
                'category': t.get('category', 'general'),
                'created_at': t.get('created_at', ''),
                'updated_at': t.get('updated_at', ''),
                'variables': t.get('variables', [])
            }
            if template_file.exists():
                try:
                    with open(template_file, 'r', encoding='utf-8') as f:
                        template_data['content'] = json.load(f)
                except (json.JSONDecodeError, IOError) as e:
                    template_data['content_error'] = str(e)
            return template_data
    return None

def create_template(template_id, name='', description='', category='general', content=None, variables=None):
    """创建配置模板"""
    valid, msg = validate_template_id(template_id)
    if not valid:
        return False, msg
    if template_exists(template_id):
        return False, f'模板 "{template_id}" 已存在'
    ensure_template_dir()
    if variables is None and content is not None:
        variables = extract_variables(content)
    template_meta = {
        'id': template_id,
        'name': name or template_id,
        'description': description or f'{template_id} 配置模板',
        'category': category,
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
        'variables': variables or []
    }
    index = load_template_index()
    index['templates'].append(template_meta)
    save_template_index(index)
    if content is not None:
        template_file = TEMPLATE_DIR / f"{template_id}.json"
        with open(template_file, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2, ensure_ascii=False)
    return True, f'模板 "{template_id}" 创建成功'

def update_template(template_id, **kwargs):
    """更新模板"""
    if not template_exists(template_id):
        return False, f'模板 "{template_id}" 不存在'
    index = load_template_index()
    for t in index['templates']:
        if t['id'] == template_id:
            for key, value in kwargs.items():
                if key in ['name', 'description', 'category', 'variables']:
                    t[key] = value
            t['updated_at'] = datetime.now().isoformat()
            break
    save_template_index(index)
    return True, f'模板 "{template_id}" 更新成功'

def apply_template(template_id, target_path, variables=None, dry_run=False):
    """应用模板到目标"""
    template = get_template(template_id)
    if not template:
        return False, f'模板 "{template_id}" 不存在'
    if 'content' not in template:
        return False, f'模板 "{template_id}" 内容为空'
    if 'content_error' in template:
        return False, f'模板内容加载失败：{template["content_error"]}'
    content = template['content']
    if variables:
        content = substitute_variables(content, variables)
    remaining_vars = extract_variables(content)
    if remaining_vars:
        return False, f'模板中有未替换的变量：{", ".join(remaining_vars)}'
    target_file = Path(target_path)
    if dry_run:
        preview = json.dumps(content, indent=2, ensure_ascii=False)
        return True, f'预览模式 - 将写入 {len(preview)} 字节到 {target_file}\n\n{preview}'
    target_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(target_file, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2, ensure_ascii=False)
        return True, f'模板已应用到 {target_file}'
    except IOError as e:
        return False, f'写入失败：{e}'

def export_template(template_id, output_path=None):
    """导出模板"""
    template = get_template(template_id)
    if not template:
        return False, f'模板 "{template_id}" 不存在', None
    export_data = {
        'version': '1.0',
        'exported_at': datetime.now().isoformat(),
        'template': template
    }
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            return True, f'模板已导出到 {output_file}', export_data
        except IOError as e:
            return False, f'导出失败：{e}', None
    return True, '模板导出成功', export_data

def delete_template(template_id):
    """删除模板"""
    if not template_exists(template_id):
        return False, f'模板 "{template_id}" 不存在'
    index = load_template_index()
    index['templates'] = [t for t in index['templates'] if t['id'] != template_id]
    save_template_index(index)
    template_file = TEMPLATE_DIR / f"{template_id}.json"
    if template_file.exists():
        template_file.unlink()
    return True, f'模板 "{template_id}" 已删除'

def import_template(import_file):
    """导入模板"""
    import_path = Path(import_file)
    if not import_path.exists():
        return False, f'导入文件不存在：{import_file}'
    try:
        with open(import_path, 'r', encoding='utf-8') as f:
            import_data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        return False, f'读取导入文件失败：{e}'
    if 'template' not in import_data:
        return False, '无效的导入文件格式：缺少 template 字段'
    template = import_data['template']
    template_id = template.get('id')
    if not template_id:
        return False, '无效的导入文件格式：缺少 template.id'
    if template_exists(template_id):
        return False, f'模板 "{template_id}" 已存在'
    content = template.pop('content', None)
    success, message = create_template(
        template_id=template_id,
        name=template.get('name', template_id),
        description=template.get('description', ''),
        category=template.get('category', 'general'),
        content=content,
        variables=template.get('variables')
    )
    return success, message

# 命令行输出函数
def print_template_table(templates, output_format='json'):
    """打印模板列表表格"""
    if output_format == 'json':
        print(json.dumps(templates, indent=2, ensure_ascii=False))
        return
    if not templates:
        print(c_yellow('  暂无模板，使用 claw-ex template create <template_id> 创建第一个模板\n'))
        return
    headers = ['模板 ID', '名称', '分类', '变量', '创建时间']
    rows = []
    for t in templates:
        vars_str = ', '.join(t.get('variables', [])[:3])
        if len(t.get('variables', [])) > 3:
            vars_str += '...'
        created = t.get('created_at', '')[:19].replace('T', ' ') if t.get('created_at') else ''
        rows.append([
            c_yellow(t['id']),
            t.get('name', t['id'])[:20],
            t.get('category', 'general')[:15],
            vars_str or '-',
            created
        ])
    # 表格输出
    col_widths = []
    for i, h in enumerate(headers):
        max_width = max(len(h), max(len(str(row[i])) if i < len(row) else 0 for row in rows))
        col_widths.append(max_width + 2)
    line = '┌' + '┬'.join('─' * w for w in col_widths) + '┐'
    sep = '├' + '┼'.join('─' * w for w in col_widths) + '┤'
    end = '└' + '┴'.join('─' * w for w in col_widths) + '┘'
    header_row = '│' + '│'.join(h.ljust(w) for h, w in zip(headers, col_widths)) + '│'
    print(line)
    print(header_row)
    print(sep)
    for row in rows:
        padded_row = list(row) + [''] * (len(headers) - len(row))
        row_str = '│' + '│'.join(str(cell).ljust(w) for cell, w in zip(padded_row, col_widths)) + '│'
        print(row_str)
    print(end)
    print(c_gray(f'\n共 {len(templates)} 个模板\n'))

def print_template_detail(template, output_format='json'):
    """打印模板详情"""
    if output_format == 'json':
        print(json.dumps(template, indent=2, ensure_ascii=False))
        return
    if not template:
        print(c_red('❌ 模板不存在\n'))
        return
    print(c_cyan(f'\n📄 模板详情：{c_yellow(template["id"])}\n'))
    headers = ['属性', '值']
    rows = [
        ['模板 ID', c_bold(template['id'])],
        ['名称', template.get('name', template['id'])],
        ['描述', template.get('description', '-') or '-'],
        ['分类', template.get('category', 'general')],
        ['变量', ', '.join(template.get('variables', [])) or '无'],
        ['创建时间', template.get('created_at', '')[:19].replace('T', ' ') if template.get('created_at') else '-'],
        ['更新时间', template.get('updated_at', '')[:19].replace('T', ' ') if template.get('updated_at') else '-']
    ]
    max_key = max(len(h) for h, _ in rows)
    for key, value in rows:
        print(f"  {key:<{max_key}}  {value}")
    if 'content' in template:
        print(c_cyan('\n📦 模板内容:\n'))
        print(json.dumps(template['content'], indent=2, ensure_ascii=False))
    print()
