from app.services.volunteer.volunteer_analysis_service import AIVolunteerAnalysisService
import json
import copy
from weasyprint import HTML, CSS
from datetime import datetime
from flask import current_app    
from jinja2 import Environment, FileSystemLoader
import os
import base64
from weasyprint.text.fonts import FontConfiguration

_font_config = None

def get_font_config():
    """获取或创建字体配置"""
    global _font_config
    if _font_config is None:
        # 创建新的字体配置
        _font_config = FontConfiguration()
        
        # 获取字体文件的绝对路径
        app_root = current_app.root_path
        regular_font_path = os.path.join(app_root, "static", "fonts", "msyh.ttf")
        bold_font_path = os.path.join(app_root, "static", "fonts", "msyhbd.ttf")
        
        # 验证字体文件存在
        if os.path.exists(regular_font_path) and os.path.exists(bold_font_path):
            current_app.logger.info("微软雅黑字体文件找到并已加载")
        else:
            current_app.logger.warning("微软雅黑字体文件未找到，将使用系统字体")
    
    return _font_config

def export_volunteer_plan_to_pdf(plan_id, template_name="standard"):
    """
    生成志愿方案PDF
    
    :param plan_id: 志愿方案ID
    :param template_name: 模板名称，默认为standard
    :return: 生成的PDF文件路径信息
    """
    # 1. 获取数据
    data = AIVolunteerAnalysisService.get_report_data(plan_id)
    
    # 2. 选择模板
    template = get_template(template_name, data)
    
    # 3. 渲染HTML
    html = render_html_with_template(template, data)
    
    # 4. 生成PDF
    pdf_path = generate_pdf_from_html(html, plan_id)
    
    return {
        'success': True,
        'filename': os.path.basename(pdf_path),
        'filepath': pdf_path,
        'url': f"/uploads/exports/{os.path.basename(pdf_path)}"
    }

def get_template(template_name, data):
    """获取模板并根据学生信息动态选择"""
    app_root = current_app.root_path
    
    # 直接在app目录下查找templates
    config_path = os.path.join(app_root, "templates", "pdf", "template_config.json")
    
    # 读取模板配置文件
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    # 查找指定模板
    template_info = next((t for t in config["templates"] if t["id"] == template_name), None)
    
    # 如果未找到指定模板或无权限访问，使用标准模板
    if not template_info:
        template_name = "standard"
    
    # 构建模板路径 - 与配置文件路径保持一致的目录结构
    template_dir = os.path.join(app_root, "templates", "pdf", "themes", template_name)
    
    return {
        "html_path": os.path.join(template_dir, "template.html"),
        "assets_path": template_dir,
        "template_name": template_name
    }

def render_html_with_template(template, data):
    """使用Jinja2渲染HTML模板"""

    # 获取模板所在目录
    template_dir = os.path.dirname(template["html_path"])
    template_name = os.path.basename(template["html_path"])
    
    # 预处理数据
    processed_data = preprocess_data_for_template(data)
    
    # 读取并编码封面图片
    cover_img_path = os.path.join(template["assets_path"], "cover.png")
    cover_img_base64 = ""
    try:
        with open(cover_img_path, "rb") as f:
            cover_img_base64 = base64.b64encode(f.read()).decode('utf-8')
    except Exception as e:
        print(f"读取图片时出错: {str(e)}")
    
    # 创建Jinja2环境
    env = Environment(
        loader=FileSystemLoader(template_dir, encoding='utf-8'),
        extensions=['jinja2.ext.debug']
    )
    print(f"Cover image base64 length: {len(cover_img_base64)}")

    # 渲染HTML
    try:
        template_obj = env.get_template(template_name)
        html = template_obj.render(
            student=processed_data["student"][0] if processed_data.get("student") else {},
            volunteer_plan=processed_data.get("volunteer_plan", {}),
            template_name=template["template_name"],
            assets_path=template["assets_path"],
            cover_img_base64=cover_img_base64,
            render_date=datetime.now().strftime('%Y-%m-%d'),
        )
        return html
    except Exception as e:
        print(f"渲染模板时出错: {str(e)}")
        raise

def preprocess_data_for_template(data):
    """预处理数据，便于模板使用"""
    
    processed_data = copy.deepcopy(data)
    
    # 处理类别分析内容
    for analysis in processed_data["volunteer_plan"]["category_analyses"]:
        if analysis["analysis_content"]:
            try:
                # 将JSON格式的分析内容转换为Python对象
                analysis["content_object"] = json.loads(analysis["analysis_content"])
            except:
                analysis["content_object"] = {"错误": "解析内容格式不正确"}
    
    # 处理志愿院校，按category_id和volunteer_index排序
    colleges = processed_data["volunteer_plan"]["colleges"]
    colleges.sort(key=lambda x: (x["category_id"], x["volunteer_index"]))
    
    # 按类别分组
    colleges_by_category = {
        1: [], # 冲
        2: [], # 稳
        3: []  # 保
    }
    
    for college in colleges:
        if college["category_id"] in colleges_by_category:
            colleges_by_category[college["category_id"]].append(college)
    
    processed_data["volunteer_plan"]["colleges_by_category"] = colleges_by_category
    
    return processed_data

def generate_pdf_from_html(html, plan_id):
    """生成PDF文件"""
    # 获取应用根目录
    app_root = current_app.root_path
    
    # 确保导出目录存在
    export_dir = os.path.join(app_root, "static", "reports")
    os.makedirs(export_dir, exist_ok=True)
    
    # 生成PDF文件名
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    pdf_filename = f"volunteer_plan_{plan_id}_{timestamp}.pdf"
    pdf_path = os.path.join(export_dir, pdf_filename)
    
    # 获取字体配置
    font_config = get_font_config()
    
    # 定义CSS
    css_string = """
    @font-face {
        font-family: 'Microsoft YaHei';
        src: url('%s') format('truetype');
        font-weight: normal;
    }
    @font-face {
        font-family: 'Microsoft YaHei';
        src: url('%s') format('truetype');
        font-weight: bold;
    }
    body {
        font-family: 'Microsoft YaHei', sans-serif;
    }
    @page { size: A4; margin: 2cm; }
    """ % (
        os.path.join(app_root, "static", "fonts", "msyh.ttf"),
        os.path.join(app_root, "static", "fonts", "msyhbd.ttf")
    )
    
    try:
        # 直接使用HTML字符串生成PDF，不再需要临时文件
        HTML(string=html, base_url=app_root).write_pdf(
            pdf_path,
            stylesheets=[CSS(string=css_string)],
            font_config=font_config,
            presentational_hints=True,
            optimize_size=('fonts', 'images')  # 添加优化选项
        )
        current_app.logger.info(f"PDF生成成功: {pdf_path}")
    except Exception as e:
        current_app.logger.error(f"PDF生成失败: {str(e)}")
        raise
    
    return pdf_path