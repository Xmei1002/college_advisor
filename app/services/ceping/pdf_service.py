# app/services/ceping/pdf_service.py
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import  ParagraphStyle
import json
import os
import time
import traceback
from flask import current_app
from abc import ABC

class BasePdfService(ABC):
    """PDF报告生成基础服务"""
    
    def __init__(self):
        """初始化PDF服务基础组件"""
        # 注册字体
        self._register_fonts()
        
        # 创建颜色常量
        self.colors = self._create_color_palette()
        
        # 创建样式
        self.styles = self._create_styles()
        
        # 设置路径
        self._setup_paths()
    
    def _setup_paths(self):
        """设置输出和资源路径"""
        base_dir = current_app.root_path
        # 输出目录
        self.output_dir = os.path.join(base_dir, 'static', 'reports')
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 资源目录
        self.resources_dir = os.path.join(base_dir, 'static', 'images')
        
        # 常用资源路径
        self.logo_path = os.path.join(self.resources_dir, 'logo.png')
        self.line_path = os.path.join(self.resources_dir, 'xian.png')
        self.star_path = os.path.join(self.resources_dir, 'xingxing.png')
        self.separator_path = os.path.join(self.resources_dir, 'stitle_bg.png')
    
    def _create_color_palette(self):
        """创建颜色调色板"""
        return {
            'title_blue': colors.HexColor('#14a9df'),  # 标题蓝
            'title_dark': colors.HexColor('#235869'),  # 深标题色
            'green': colors.HexColor('#008000'),       # 绿色
            'orange': colors.HexColor('#fdbb5a'),      # 橙色
            'dark_blue': colors.HexColor('#1d94f8'),   # 深蓝
            'light_blue': colors.HexColor('#1ca4b6'),  # 浅蓝
            'light_grey': colors.HexColor('#f5f5f5'),  # 浅灰
        }
    
    def _register_fonts(self):
        """注册中文字体"""
        try:
            base_dir = current_app.root_path
            font_dir = os.path.join(base_dir, 'static', 'fonts')
            
            # 注册微软雅黑常规字体
            msyh_font_path = os.path.join(font_dir, 'msyh.ttf')
            if os.path.exists(msyh_font_path):
                pdfmetrics.registerFont(TTFont('msyh', msyh_font_path))
            else:
                current_app.logger.warning(f"常规字体文件不存在: {msyh_font_path}, 将使用默认字体")
            
            # 注册微软雅黑粗体字体
            msyhbd_font_path = os.path.join(font_dir, 'msyhbd.ttf')
            if os.path.exists(msyhbd_font_path):
                pdfmetrics.registerFont(TTFont('msyhbd', msyhbd_font_path))
            else:
                current_app.logger.warning(f"粗体字体文件不存在: {msyhbd_font_path}, 将使用默认字体")
                
            self.default_font = 'msyh'
            self.bold_font = 'msyhbd'
        except Exception as e:
            current_app.logger.error(f"字体加载失败: {str(e)}")
            self.default_font = 'Helvetica'
            self.bold_font = 'Helvetica-Bold'
    
    def _create_styles(self):
        """创建报告通用样式集合"""
        styles = {}
        
        # 封面标题
        styles['Cover_Title'] = ParagraphStyle(
            name='Cover_Title',
            fontName=self.bold_font,
            fontSize=40,
            leading=48,
            alignment=1,  # 居中
            spaceAfter=20
        )
        
        # 封面副标题
        styles['Cover_Subtitle'] = ParagraphStyle(
            name='Cover_Subtitle',
            fontName=self.default_font,
            fontSize=19,
            leading=25,
            alignment=1,  # 居中
            spaceAfter=30,
            textColor=colors.black
        )
        
        # 主标题
        styles['Title'] = ParagraphStyle(
            name='Title',
            fontName=self.default_font,
            fontSize=24,
            leading=32,
            alignment=0,  # 左对齐
            spaceAfter=10
        )
        
        # 蓝色背景标题
        styles['Blue_Title'] = ParagraphStyle(
            name='Blue_Title',
            fontName=self.default_font,
            fontSize=20,
            leading=24,  # 减小行高使文本在单元格内更紧凑
            spaceAfter=0,  # 移除段落后的空间，因为表格会提供间距
            textColor=colors.white,
            # 移除背景色设置，改由表格提供
            leftIndent=0,  # 移除左缩进，因为表格会提供padding
            alignment=0,  # 左对齐
        )
        
        # 一级标题
        styles['Heading1'] = ParagraphStyle(
            name='Heading1',
            fontName=self.bold_font,
            fontSize=18,
            leading=25,
            spaceAfter=10
        )
        
        # 二级标题
        styles['Heading2'] = ParagraphStyle(
            name='Heading2',
            fontName=self.bold_font,
            fontSize=16,
            leading=22,
            spaceAfter=8,
            textColor=self.colors['title_dark']
        )
        
        # 三级标题
        styles['Heading3'] = ParagraphStyle(
            name='Heading3',
            fontName=self.default_font,
            fontSize=14,
            leading=20,
            spaceAfter=6,
            textColor=colors.green
        )
        
        # 正文
        styles['Normal'] = ParagraphStyle(
            name='Normal',
            fontName=self.default_font,
            fontSize=12,
            leading=22,
            spaceAfter=6,
            firstLineIndent=32  # 首行缩进
        )
        
        # 列表项样式
        styles['List_Item'] = ParagraphStyle(
            name='List_Item',
            parent=styles['Normal'],
            firstLineIndent=0,
            leftIndent=15
        )
        
        # 目录条目
        styles['TOC_Item'] = ParagraphStyle(
            name='TOC_Item',
            fontName=self.bold_font,
            fontSize=16,
            leading=22,
            spaceAfter=8,
            textColor=self.colors['title_blue']
        )
        
        # 页脚
        styles['Footer'] = ParagraphStyle(
            name='Footer',
            fontName=self.default_font,
            fontSize=10,
            leading=15,
            alignment=1  # 居中
        )
        
        # 版权声明
        styles['Copyright'] = ParagraphStyle(
            name='Copyright',
            fontName=self.default_font,
            fontSize=10,
            leading=15,
            textColor=colors.gray
        )
        
        return styles
    
    def _draw_header(self, canvas, doc, title, display_page_num=True):
        """绘制页眉和页码"""
        canvas.saveState()
        
        # 绘制页眉背景
        # canvas.setFillColorRGB(0.95, 0.95, 0.95)
        # canvas.rect(10*mm, 275*mm, 190*mm, 13*mm, fill=1)
        
        # 添加Logo
        if os.path.exists(self.logo_path):
            canvas.drawImage(self.logo_path, 10*mm, 275*mm, width=51*mm, height=13*mm)
        
        # 添加标题
        canvas.setFont(self.default_font, 11)
        canvas.drawRightString(200*mm, 282*mm, title)
        
        # 添加页码 (在页面底部)
        if display_page_num:
            canvas.setFont(self.default_font, 10)
            canvas.setFillColor(colors.black)
            canvas.drawCentredString(105*mm, 15*mm, str(doc.page))
        
        canvas.restoreState()
    
    def _ensure_text_safe(self, text):
        """确保文本安全可用于PDF"""
        if text is None:
            return ""
        
        # 确保文本是字符串
        if not isinstance(text, str):
            text = str(text)
            
        # 处理可能导致问题的特殊字符
        text = text.replace('\u2028', ' ')  # 行分隔符
        text = text.replace('\u2029', ' ')  # 段落分隔符
        
        # 替换其他可能导致问题的Unicode控制字符
        import re
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        return text
    
    def _add_common_cover(self, story, title, subtitle, student, answer, show_student_info=True):
        """添加通用报告封面"""
        # 生成标题
        story.append(Paragraph(title, self.styles['Cover_Title']))
        story.append(Spacer(1, 10*mm))
        
        # 添加分隔图片
        if os.path.exists(self.separator_path):
            story.append(Image(self.separator_path, width=140*mm, height=10*mm))
        
        # 生成副标题
        story.append(Paragraph(subtitle, self.styles['Cover_Subtitle']))
        story.append(Spacer(1, 80*mm))
        
        if show_student_info:
            # 学生信息表格
            student_data = [
                ['姓       名:', student.name],
                ['学       校:', student.school or ''],
                ['报告时间:', time.strftime('%Y-%m-%d', time.localtime(answer.addtime))]
            ]
            
            # 表格样式
            table_style = TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), self.default_font),
                ('FONTSIZE', (0, 0), (-1, -1), 16),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ])
            
            # 创建表格并设置样式
            student_table = Table(student_data, colWidths=[100, 220])
            student_table.setStyle(table_style)
            
            # 使用嵌套表格实现居中对齐
            page_width = A4[0] - 20*mm  # 页面宽度减去左右边距
            outer_data = [[student_table]]
            outer_table = Table(outer_data, colWidths=[page_width])
            outer_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'CENTER'),
                ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
            ]))
            
            story.append(outer_table)
    
    def _add_common_copyright(self, story):
        """添加版权声明"""
        story.append(Spacer(1, 30*mm))
        copyright_text = """
        <font color="red">*</font>版权声明<br/>
        本报告内容属于个人隐私，请注意保密<br/>
        本报告必须在专业咨询师的指导下使用<br/>
        本报告的所有权都受到版权保护，未经授权不得擅自转载、挪用、复制、刊印等，不得用于商业或非商业用途
        """
        story.append(Paragraph(copyright_text, self.styles['Copyright']))
    
    def _add_common_toc(self, story, toc_items):
        """添加通用目录"""
        story.append(Paragraph('目录 Catalog', self.styles['Title']))
        story.append(Spacer(1, 5*mm))
        
        # 添加下划线图片
        if os.path.exists(self.line_path):
            story.append(Image(self.line_path, width=54*mm, height=2*mm))
        
        story.append(Spacer(1, 10*mm))
        
        # 目录表格样式
        toc_style = TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.bold_font),
            ('FONTSIZE', (0, 0), (-1, -1), 16),
            ('TEXTCOLOR', (0, 0), (0, -1), self.colors['title_blue']),
            ('TEXTCOLOR', (1, 0), (1, -1), self.colors['light_blue']),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ])
        
        # 创建目录表格
        toc_table = Table(toc_items, colWidths=[450, 40])
        toc_table.setStyle(toc_style)
        story.append(toc_table)
    
    def _add_star_icon(self, story):
        """添加星形图标"""
        if os.path.exists(self.star_path):
            story.append(Image(self.star_path, width=4*mm, height=4*mm))
    
    def _add_section_title(self, story, title):
        """添加章节标题"""
        # 创建段落
        title_paragraph = Paragraph(title, self.styles['Blue_Title'])
        
        # 使用表格包装段落以实现垂直居中
        data = [[title_paragraph]]
        table = Table(data, colWidths=[480])
        
        # 设置表格样式，背景色和垂直居中
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), self.colors['title_blue']),
            ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (0, 0), 20),
            ('RIGHTPADDING', (0, 0), (0, 0), 10),
            ('TOPPADDING', (0, 0), (0, 0), 10),
            ('BOTTOMPADDING', (0, 0), (0, 0), 10)
        ]))
        
        # 添加到故事流
        story.append(table)
        story.append(Spacer(1, 10*mm))
    
    def _get_standard_doc(self, filename):
        """获取标准文档对象"""
        filepath = os.path.join(self.output_dir, filename)
        
        # 创建文档
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            leftMargin=10*mm,
            rightMargin=10*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )
        
        return doc, filepath
    
    def _create_page_callbacks(self, title):
        """创建页面回调函数"""
        
        def first_page_callback(canvas, doc):
            self._draw_header(canvas, doc, title, display_page_num=False)
        
        def later_pages_callback(canvas, doc):
            # 目录页面也不显示页码
            if doc.page <= 3:  # 封面、前言、目录页不显示页码
                self._draw_header(canvas, doc, title, display_page_num=False)
            else:
                # 从第4页开始显示页码(显示的页码从1开始)
                current_page = doc.page - 3
                # 保存原始页码
                original_page = doc.page
                # 设置页码
                doc.page = current_page
                # 绘制页眉和页码
                self._draw_header(canvas, doc, title, display_page_num=True)
                # 恢复原始页码，避免影响后续页面
                doc.page = original_page
        
        return first_page_callback, later_pages_callback


class MbtiReportService(BasePdfService):
    """MBTI测评报告生成服务"""
    
    def __init__(self):
        super().__init__()
        # 特定于MBTI报告的初始化
    
    def generate_report(self, answer, student):
        """生成MBTI测评报告"""
        from app.models.ceping_mbti_leixing import CepingMbtiLeixing
        
        try:
            # 解析结果
            jieguo = json.loads(answer.jieguo)
            
            # 计算人格类型
            personality_type = self._calculate_personality_type(jieguo)
            
            # 获取类型详情
            type_info = CepingMbtiLeixing.query.filter_by(name=personality_type).first()
            
            # 创建PDF文件名
            filename = f"MBTI_{self._ensure_text_safe(student.name)}_{int(time.time())}.pdf"
            doc, filepath = self._get_standard_doc(filename)
            
            # 构建PDF内容
            story = []
            
            # 添加封面
            self._add_cover(story, student, answer)
            story.append(PageBreak())
            
            # 添加前言
            self._add_preface(story)
            story.append(PageBreak())
            
            # 添加目录
            self._add_toc(story)
            story.append(PageBreak())
            
            # 添加测评介绍
            self._add_introduction(story)
            story.append(PageBreak())
            
            # 添加测评结果
            self._add_results(story, jieguo, personality_type, type_info)
            story.append(PageBreak())
            
            # 添加温馨提示
            self._add_tips(story)
            
            # 设置页面回调
            first_page, later_pages = self._create_page_callbacks("性格能力测评")
            
            # 构建PDF
            doc.build(story, onFirstPage=first_page, onLaterPages=later_pages)
            
            return filepath
            
        except Exception as e:
            current_app.logger.error(f"生成MBTI报告时出错: {str(e)}")
            current_app.logger.error(traceback.format_exc())
            raise
    
    def _calculate_personality_type(self, jieguo):
        """计算MBTI人格类型"""
        personality_type = ""
        
        # 计算各维度
        dimensions = [
            ('I', 'E'),  # 内向/外向
            ('N', 'S'),  # 直觉/感觉
            ('F', 'T'),  # 情感/思考
            ('P', 'J')   # 感知/判断
        ]
        
        for dim1, dim2 in dimensions:
            if jieguo[dim1]['count'] >= jieguo[dim2]['count']:
                personality_type += dim1
            else:
                personality_type += dim2
                
        return personality_type
    
    def _add_cover(self, story, student, answer):
        """添加MBTI报告封面"""
        self._add_common_cover(
            story, 
            '性格能力测评', 
            'Personality and ability evaluation report',
            student,
            answer
        )
    
    def _add_preface(self, story):
        """添加MBTI报告前言"""
        # 前言标题
        story.append(Paragraph('前言', self.styles['Title']))
        story.append(Spacer(1, 5*mm))
        
        # 添加下划线图片
        if os.path.exists(self.line_path):
            story.append(Image(self.line_path, width=20*mm, height=2*mm))
        
        story.append(Spacer(1, 5*mm))
        
        # 前言内容
        preface_text = [
            """性格能力测评采用当今世界上应用最广泛的性格测试工具之一MBTI作为基础研发。MBTI被翻译成近20种世界主要语言，每年的使用者多达千万。据有关统计，世界500强公司中有92%引入了MBTI测试，应用于员工的MBTI测试，可以帮助员工自我发展及提升组织绩效。""",
            
            """探索自我，性格能力测评可以帮助了解：我是什么性格？我适合什么职业？我的性格优势和劣势是什么？性格能力测评可以更好的帮你了解自我、从而做出最适合你的职业选择，更容易获取事业上的成功。""",
            
            """性格能力测评系统是启明星高考为解决考生的迷茫，家长老师的困惑，让考生都能选择适合自己的科目，正确做出职业生涯规划，经过多年研究及开发，针对我省高考现状，结合大学生职业规划调查报告，参考大学生就业情况，为高考学生量身打造的。"""
        ]
        
        for text in preface_text:
            story.append(Paragraph(text, self.styles['Normal']))
            story.append(Spacer(1, 5*mm))
        
        # 添加版权声明
        self._add_common_copyright(story)
    
    def _add_toc(self, story):
        """添加MBTI报告目录"""
        toc_items = [
            ['Part.1 性格能力测评体系介绍', '1'],
            ['Part.2 性格能力测评结果分析', '2'],
            ['Part.3 温馨提示', '4']
        ]
        
        self._add_common_toc(story, toc_items)
    
    def _add_introduction(self, story):
        """添加MBTI测评体系介绍"""
        # 章节标题背景
        self._add_section_title(story, 'Part.1 性格能力测评体系介绍')
        
        # 介绍文本
        intro_texts = [
            """MBTI从能量的来源方向、信息收集的方式、做决定时候的偏好、以及生活态度四个方面对人格进行考量，其中每个一部分又分两个倾向，分别是：能量来源-内向(I)、外向(E)；信息收集-感觉(S)、直觉(N)；决定偏好-思考(T)、情感(F)；生活态度-感知(P)、判断(J)。MBTI性格评估主要应用于职业规划、团队建设、人际交往、教育等方面。""",
            
            """心理学认为，"性格"是一种个体内部的行为倾向，它具有整体性、结构性、持久稳定性等特点，是每个人特有的，可以对个人外显的行为、态度提供统一的、内在的解释。MBTI的人格类型分为四个维度，每个维度上有两个方向，一共八个方面，对应八种人格特点，具体如下："""
        ]
        
        for text in intro_texts:
            story.append(Paragraph(text, self.styles['Normal']))
            story.append(Spacer(1, 5*mm))
        
        # 维度说明
        dimensions = [
            "我们与世界相互作用方式：外向Extraversion (E)---内向Introversion (I)",
            "我们获得信息的主要方式：感觉Sensing (S)---直觉iNtuition (N)",
            "我们的决策方式：思考Thinking (T)---情感Feeling (F)",
            "我们的做事方式：判断Judging (J)---感知Perceiving (P)"
        ]
        
        for dim in dimensions:
            story.append(Paragraph(dim, self.styles['List_Item']))
            story.append(Spacer(1, 3*mm))
        
        story.append(Spacer(1, 5*mm))
        
        # 结论
        conclusion = """性格能力评估系统可以帮助我们认清自己，但是并不剥夺我们认知的自由，把结论强加于人；MBTI可以有效地评估我们的性格类型；引导我们建立自信，信任并理解他人；进而在职业定位和发展、人际关系等领域为我们提供帮助。"""
        story.append(Paragraph(conclusion, self.styles['Normal']))
    
    def _add_results(self, story, jieguo, personality_type, type_info):
        """添加MBTI测评结果分析"""
        # 章节标题
        self._add_section_title(story, 'Part.2 性格能力测评结果分析')
        
        # 添加星号图标
        self._add_star_icon(story)
        
        # 小标题
        subtitle = f"""职业性格分析 根据您测评结果进行分析，您的职业性格结果如下所示："""
        story.append(Paragraph(subtitle, self.styles['List_Item']))
        story.append(Spacer(1, 5*mm))  # 减小标题后的间距
        
        # 维度对比数据
        dimensions = [
            {'left_key': 'E', 'left_label': '外向(E)', 'right_key': 'I', 'right_label': '内向(I)'},
            {'left_key': 'S', 'left_label': '感觉(S)', 'right_key': 'N', 'right_label': '直觉(N)'},
            {'left_key': 'T', 'left_label': '思考(T)', 'right_key': 'F', 'right_label': '情感(F)'},
            {'left_key': 'J', 'left_label': '判断(J)', 'right_key': 'P', 'right_label': '知觉(P)'}
        ]
        
        # 创建表格数据
        bar_data = []
        
        # 为每个维度创建进度条行
        for dim in dimensions:
            left_key = dim['left_key']
            right_key = dim['right_key']
            
            # 获取分数
            left_score = jieguo[left_key]['count']
            right_score = jieguo[right_key]['count']
            
            # 创建行数据
            row = [
                dim['left_label'],  # 左侧标签
                str(left_score),    # 左侧分数
                '',                 # 左侧进度条
                '',                 # 右侧进度条
                str(right_score),   # 右侧分数
                dim['right_label']  # 右侧标签
            ]
            bar_data.append(row)
        
        # 创建表格
        total_width = 310  # 进度条总宽度
        
        # 动态计算每行的列宽
        final_col_widths = []
        for dim in dimensions:
            left_key = dim['left_key']
            right_key = dim['right_key']
            
            # 获取分数
            left_score = jieguo[left_key]['count']
            right_score = jieguo[right_key]['count']
            total_score = left_score + right_score
            
            # 计算比例
            if total_score > 0:
                left_ratio = left_score / total_score
                right_ratio = right_score / total_score
            else:
                left_ratio = right_ratio = 0.5
            
            # 计算进度条宽度（保留一些最小宽度）
            left_bar_width = max(20, int(left_ratio * total_width))
            right_bar_width = max(20, int(right_ratio * total_width))
            
            # 添加一行的列宽
            row_col_widths = [70, 30, left_bar_width, right_bar_width, 30, 70]
            final_col_widths.append(row_col_widths)
        
        # 创建多个表格，每行一个表格
        for i, (row, widths) in enumerate(zip(bar_data, final_col_widths)):
            row_table = Table([row], colWidths=widths)
            
            # 获取维度信息
            dim = dimensions[i]
            left_key = dim['left_key']
            right_key = dim['right_key']
            left_score = jieguo[left_key]['count']
            right_score = jieguo[right_key]['count']
            
            # 设置表格样式
            row_style = TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), self.default_font),
                ('FONTSIZE', (0, 0), (0, 0), 13),  # 左标签略小
                ('FONTSIZE', (5, 0), (5, 0), 13),  # 右标签略小
                ('FONTSIZE', (1, 0), (1, 0), 14),  # 左分数稍大
                ('FONTSIZE', (4, 0), (4, 0), 14),  # 右分数稍大
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (4, 0), 'CENTER'),
                ('ALIGN', (5, 0), (5, 0), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
                # 减小条形高度
                ('BOTTOMPADDING', (0, 0), (-1, 0), 3),
                ('TOPPADDING', (0, 0), (-1, 0), 3),
                
                # 设置左侧进度条背景色
                ('BACKGROUND', (2, 0), (2, 0), colors.HexColor('#3498db')),  # 蓝色
                
                # 设置右侧进度条背景色
                ('BACKGROUND', (3, 0), (3, 0), colors.HexColor('#f39c12')),  # 橙色
                
                # 设置分数文本颜色为白色
                ('TEXTCOLOR', (1, 0), (1, 0), colors.black),
                ('TEXTCOLOR', (4, 0), (4, 0), colors.black),
                
            ])
            
            # 加粗显示较高分数
            if left_score > right_score:
                row_style.add('FONTNAME', (1, 0), (1, 0), self.bold_font)
                row_style.add('FONTNAME', (0, 0), (0, 0), self.bold_font)  # 加粗左侧标签
            elif right_score > left_score:
                row_style.add('FONTNAME', (4, 0), (4, 0), self.bold_font)
                row_style.add('FONTNAME', (5, 0), (5, 0), self.bold_font)  # 加粗右侧标签
            
            # 应用样式
            row_table.setStyle(row_style)
            
            # 添加到故事
            story.append(row_table)
            story.append(Spacer(1, 8*mm))  # 增加行间距，从1mm改为8mm
        
        story.append(Spacer(1, 5*mm))
        
        # 以下代码保持不变...
        # 创建得分汇总表格
        score_data = [
            ['性格维度', '得分', '倾向'],
            ['我们如何与世界相互作用', 
            max(jieguo['E']['count'], jieguo['I']['count']), 
            '外向' if jieguo['E']['count'] > jieguo['I']['count'] else '内向'],
            ['我们关注哪些事物', 
            max(jieguo['S']['count'], jieguo['N']['count']), 
            '感觉' if jieguo['S']['count'] > jieguo['N']['count'] else '直觉'],
            ['我们如何思考问题', 
            max(jieguo['T']['count'], jieguo['F']['count']), 
            '思考' if jieguo['T']['count'] > jieguo['F']['count'] else '情感'],
            ['我们如何做事', 
            max(jieguo['J']['count'], jieguo['P']['count']), 
            '判断' if jieguo['J']['count'] > jieguo['P']['count'] else '知觉']
        ]
        
        # 创建表格
        score_table = Table(score_data, colWidths=[300, 100, 100])
        
        # 设置表格样式
        score_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.default_font),
            ('FONTNAME', (0, 0), (-1, 0), self.bold_font),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 0), (-1, 0), self.colors['title_dark']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.black),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),  # 减小内边距
            ('TOPPADDING', (0, 0), (-1, -1), 8),     # 减小内边距
        ]))
        
        story.append(score_table)
        story.append(Spacer(1, 10*mm))
        
        # 类型解析
        result_text = f"""您的职业性格是<b>{personality_type}</b>，具体特征如下："""
        story.append(Paragraph(result_text, self.styles['Normal']))
        story.append(Spacer(1, 5*mm))
        
        if type_info:
            # 性格特质
            story.append(Paragraph('性格特质', self.styles['Heading3']))
            trait_text = self._ensure_text_safe(type_info.xingge).replace('\n', '<br/>')
            story.append(Paragraph(trait_text, self.styles['Normal']))
            story.append(Spacer(1, 5*mm))
            
            # 添加分页符，后续内容放到下一页
            story.append(PageBreak())
            
            # 优势分析
            story.append(Paragraph('优势分析', self.styles['Heading3']))
            advantage_text = self._ensure_text_safe(type_info.youshi).replace('\n', '<br/>')
            story.append(Paragraph(advantage_text, self.styles['Normal']))
            story.append(Spacer(1, 5*mm))
            
            # 劣势分析
            story.append(Paragraph('劣势分析', self.styles['Heading3']))
            disadvantage_text = self._ensure_text_safe(type_info.lueshi).replace('\n', '<br/>')
            story.append(Paragraph(disadvantage_text, self.styles['Normal']))
            story.append(Spacer(1, 5*mm))
            
            # 职业领域
            story.append(Paragraph('职业领域', self.styles['Heading3']))
            career_text = self._ensure_text_safe(type_info.zhiye).replace('\n', '<br/>')
            story.append(Paragraph(career_text, self.styles['Normal']))
            story.append(Spacer(1, 5*mm))
            
            # 典型职业
            story.append(Paragraph('典型职业', self.styles['Heading3']))
            typical_job_text = self._ensure_text_safe(type_info.dianxing).replace('\n', '<br/>')
            story.append(Paragraph(typical_job_text, self.styles['Normal']))

    def _add_tips(self, story):
        """添加MBTI测评温馨提示"""
        # 章节标题
        self._add_section_title(story, 'Part.3 温馨提示')
        
        # 添加星号图标
        self._add_star_icon(story)
        
        # 温馨提示标题
        story.append(Paragraph('温馨提示', self.styles['Heading3']))
        story.append(Spacer(1, 5*mm))
        
        story.append(Paragraph('亲爱的同学：', self.styles['Normal']))
        story.append(Spacer(1, 5*mm))
        
        tips_texts = [
            """性格能力测评报告展示的是你的性格倾向，而不是你的知识、技能、经验。只要你是认真、真实地填写了测试问卷，那么通常情况下你都能得到一个确实和你的性格相匹配的类型。希望你能从中或多或少地获得一些有益的信息。""",
            
            """MBTI提供的性格类型描述仅供测试者确定自己的性格类型之用，性格类型没有好坏，只有不同。每一种性格特征都有其价值和优点，也有缺点和需要注意的地方。清楚地了解自己的性格优劣势，有利于更好地发挥自己的特长，而尽可能的在为人处事中避免自己性格中的劣势，更好地和他人相处，更好地作重要的决策。""",
            
            """您在答题时，难免受到当时的答题环境、心情等各种因素的影响。如果您觉得最终的测试结果与您的实际情况不是很符合，可能有如下几种原因："""
        ]
        
        for text in tips_texts:
            story.append(Paragraph(text, self.styles['Normal']))
            story.append(Spacer(1, 5*mm))
        
        # 注意事项列表
        notes = [
            "1. 请回忆您作答时候的情形, 您是根据自己的第一反应做出的回答吗？",
            "2. 您是否受到自己应该选择什么或者别人希望您选择什么的影响？",
            "3. 您答题的时候心情是不是比较放松？",
            "4. 您是否对绝大多数题都进行了认真做答？",
            "5. 您答题的时候有没有受到干扰？"
        ]
        
        for note in notes:
            story.append(Paragraph(note, self.styles['List_Item']))
            story.append(Spacer(1, 3*mm))
        
        story.append(Spacer(1, 5*mm))
        story.append(Paragraph('您可以在适当的时候选择重新进行测试。', self.styles['Normal']))
        story.append(Paragraph('希望性格能力测评报告能为您的选择提供有价值的参考。', self.styles['Normal']))


class JobReportService(BasePdfService):
    """职业兴趣测评报告生成服务"""
    
    def __init__(self):
        super().__init__()
        # 特定于职业兴趣报告的初始化
    
    def generate_report(self, answer, student):
        """生成职业兴趣测评报告"""
        from app.models.ceping_job_leixing import CepingJobLeixing
        from app.models.ceping_job_zhuanye import CepingJobZhuanye
        from app.models.ceping_job_timu import CepingJobTimu
        
        try:
            # 解析答案数据
            answer_data = json.loads(answer.answer)
            
            # 获取题目信息
            timu = CepingJobTimu.query.order_by(CepingJobTimu.tid).all()
            
            # 计算结果 - 初始化所有维度的计数为0
            count = self._calculate_job_scores(answer_data, timu, answer.jieguo)
            
            # 获取类型详情
            type_info = CepingJobLeixing.query.filter_by(title=answer.jieguo).first()
            
            # 获取推荐专业
            recommended_majors = CepingJobZhuanye.query.filter_by(title=answer.jieguo).all()
            
            # 创建PDF文件名
            filename = f"职业兴趣_{self._ensure_text_safe(student.name)}_{int(time.time())}.pdf"
            doc, filepath = self._get_standard_doc(filename)
            
            # 构建PDF内容
            story = []
            
            # 添加封面
            self._add_cover(story, student, answer)
            story.append(PageBreak())
            
            # 添加前言
            self._add_preface(story)
            story.append(PageBreak())
            
            # 添加目录
            self._add_toc(story)
            story.append(PageBreak())
            
            # 添加测评介绍
            self._add_introduction(story)
            story.append(PageBreak())
            
            # 添加测评结果
            self._add_results(story, count, answer.jieguo, type_info, recommended_majors)
            story.append(PageBreak())
            
            # 添加温馨提示
            self._add_tips(story)
            
            # 设置页面回调
            first_page, later_pages = self._create_page_callbacks("职业兴趣测评")
            
            # 构建PDF
            doc.build(story, onFirstPage=first_page, onLaterPages=later_pages)
            
            return filepath
            
        except Exception as e:
            current_app.logger.error(f"生成职业兴趣报告时出错: {str(e)}")
            current_app.logger.error(traceback.format_exc())
            raise
    
    def _calculate_job_scores(self, answer_data, timu, result_type):
        """计算职业兴趣得分"""
        # 初始化所有维度的计数
        count = {
            "S": {'count': 0, 'color': 'green'},
            "R": {'count': 0, 'color': 'green'},
            "C": {'count': 0, 'color': 'green'},
            "E": {'count': 0, 'color': 'green'},
            "I": {'count': 0, 'color': 'green'},
            "A": {'count': 0, 'color': 'green'}
        }
        
        # 创建题目ID到维度的映射
        timu_map = {str(q.tid): q.wid for q in timu}
        
        # 计算每个维度的得分
        for tid, answer_choice in answer_data.items():
            wid = timu_map.get(tid)
            if wid and wid in count and answer_choice == "A":
                count[wid]['count'] += 1
        
        # 对不在结果类型中的类型进行处理 (参考原代码逻辑)
        for key in count:
            # 检查当前类型是否在结果字符串中
            if key in result_type:
                count[key]['color'] = "orange"
            else:
                # 如果不在结果中且分数大于0，则减1
                if count[key]['count'] > 0:
                    count[key]['count'] -= 1
                count[key]['color'] = "green"
        
        return count
    
    def _add_cover(self, story, student, answer):
        """添加职业兴趣报告封面"""
        self._add_common_cover(
            story, 
            '职业兴趣测评报告', 
            'Professional Interest Assessment Report',
            student,
            answer
        )
    
    def _add_preface(self, story):
        """添加职业兴趣报告前言"""
        # 前言标题
        story.append(Paragraph('前言', self.styles['Title']))
        story.append(Spacer(1, 5*mm))
        
        # 添加下划线图片
        if os.path.exists(self.line_path):
            story.append(Image(self.line_path, width=20*mm, height=2*mm))
        
        story.append(Spacer(1, 5*mm))
        
        # 前言内容
        preface_text = """高考是影响考生人生发展的一次重要事件，历来都是学生本人和家长乃至全社会最为重视的事情。高考作为基础教育的"指挥棒"，自从1977年恢复高考以来，关于高考的变革都影响着教育的基本方向和教学策略。《中国职业技术教育》中曾对大学生入校后的关于对专业了解程度的调查显示：对自己所学专业与社会职业要求不清楚的学生占92.2%，选择专业时家长做主的占71.2%，选择专业时听取同学、亲戚意见的占55.3%，对自己不了解的占51.5%，对社会不了解的占62.1%，对职业不了解的占89.2%。从这些数据看来大学生入学时对所学专业与社会职业的了解是有限的，或者说是盲目的。人的一生里总要面临各种抉择，而高考选择专业可能是整个人生的抉择中最有影响、最具挑战性的一个。每逢高考志愿填报时，考生迷茫、家长困惑、老师谨慎。"""
        story.append(Paragraph(preface_text, self.styles['Normal']))
        story.append(Spacer(1, 5*mm))
        
        second_paragraph = """职业兴趣测评系统是启明星高考为解决考生的迷茫，家长老师的困惑，让考生都能选择适合自己的专业，正确做出职业生涯规划，经过多年研究及开发，针对我省高考现状，结合大学生职业规划调查报告，参考大学生就业情况，为高考学生量身打造的。"""
        story.append(Paragraph(second_paragraph, self.styles['Normal']))
        
        # 添加版权声明
        self._add_common_copyright(story)
    
    def _add_toc(self, story):
        """添加职业兴趣报告目录"""
        toc_items = [
            ['Part.1 职业兴趣测评体系介绍', '1'],
            ['Part.2 职业兴趣测评结果分析', '3'],
            ['Part.3 温馨提示', '6']
        ]
        
        self._add_common_toc(story, toc_items)
    
    def _add_introduction(self, story):
        """添加职业兴趣测评体系介绍"""
        # 章节标题背景
        self._add_section_title(story, 'Part.1 职业兴趣测评体系介绍')
        
        # 介绍文本
        intro_text = """职业兴趣测评是以美国心理学家Holland的职业兴趣理论为基础，同时在题目内容设计、常模选取方面结合了考生的实际情况而开发的专业测评工具。通过该系统，可以帮助测试者相对精确地了解自身的个体特点和职业特点之间的匹配关系，同时为测评者在进行职业规划时，提供客观的参考依据分析你的兴趣爱好，推荐你感兴趣和适合的职业作为参考。"""
        story.append(Paragraph(intro_text, self.styles['Normal']))
        story.append(Spacer(1, 5*mm))
        
        second_paragraph = """职业兴趣与职业环境的匹配是决定成功的最重要的因素之一。人们通常倾向于选择与自我职业兴趣类型匹配的职业环境，如具有艺术倾向的个体通常希望在艺术型的职业环境中工作，以便最大限度地发挥个人的潜能。Holland从兴趣的角度出发来探索职业指导问题，根据人格与环境交互作用的观点，把人分为六大类：现实型(R)、研究型(I)、艺术型(A)、社会型(S)、企业型(E)、传统型(C)。"""
        story.append(Paragraph(second_paragraph, self.styles['Normal']))
        story.append(Spacer(1, 10*mm))
        
        # Holland六种类型介绍
        holland_types = [
            ('现实型(R)', '喜欢具体、实际的工作，喜欢户外活动，有操作机械设备的能力，适合工程技术、农业、制造等领域。'),
            ('研究型(I)', '喜欢思考问题，进行研究和分析，解决复杂问题，适合科学研究、医疗、技术分析等领域。'),
            ('艺术型(A)', '喜欢从事艺术、音乐、文学等富有创造性和表现力的活动，适合设计、表演、写作等领域。'),
            ('社会型(S)', '喜欢与人交往，帮助他人，具有教导、培训和咨询的能力，适合教育、社会服务、医疗护理等领域。'),
            ('企业型(E)', '善于组织、领导和说服他人，喜欢从事管理和销售，适合管理、销售、法律等领域。'),
            ('传统型(C)', '喜欢按部就班、有序和规则的工作，善于处理数据，适合会计、行政、档案管理等领域。')
        ]
        
        # 添加每种类型的介绍
        for type_name, type_desc in holland_types:
            story.append(Paragraph(type_name, self.styles['Heading3']))
            story.append(Paragraph(type_desc, self.styles['Normal']))
            story.append(Spacer(1, 5*mm))
    
    def _add_results(self, story, count, job_type, type_info, recommended_majors):
        """添加职业兴趣测评结果分析"""
        # 章节标题
        self._add_section_title(story, 'Part.2 职业兴趣测评结果分析')
        
        # 添加星号图标
        self._add_star_icon(story)
        
        # 小标题
        story.append(Paragraph('根据您测评结果进行分析，您的职业兴趣结果如下所示：', self.styles['Normal']))
        story.append(Spacer(1, 10*mm))
        
        # 创建各维度得分条
        holland_types = [
            {'key': 'A', 'label': 'A艺术型'},
            {'key': 'S', 'label': 'S社会型'},
            {'key': 'E', 'label': 'E企业型'},
            {'key': 'C', 'label': 'C传统型'},
            {'key': 'R', 'label': 'R实际型'},
            {'key': 'I', 'label': 'I研究型'}
        ]
        
        # 最大得分用于计算进度条长度
        max_score = 20  # 职业兴趣满分
        bar_width = 300  # 进度条最大宽度
        
        # 为每个维度创建单独的表格
        for holland in holland_types:
            key = holland['key']
            score = count[key]['count']
            color_name = count[key]['color']
            
            # 计算进度条宽度
            score_width = int((score / max_score) * bar_width)
            if score_width == 0 and score > 0:
                score_width = 10  # 确保即使分数很低也有一点显示
            
            # 定义表格结构
            label_width = 80  # 标签宽度
            score_label_width = 30  # 分数文本宽度
            
            # 创建包含进度条的表格
            progress_bar_data = [['', '']]  # 两个单元格：一个显示分数进度，一个显示剩余空间
            progress_colWidths = [score_width, bar_width - score_width]
            
            progress_table = Table(progress_bar_data, colWidths=progress_colWidths)
            
            # 样式：为进度条部分着色，为整个条加边框
            progress_style = TableStyle([
                # 进度条颜色
                ('BACKGROUND', (0, 0), (0, 0), self.colors['orange'] if color_name == 'orange' else colors.green),
                # 背景条颜色（浅灰色）
                ('BACKGROUND', (1, 0), (1, 0), colors.lightgrey),
                # 为整个进度条添加边框
                ('BOX', (0, 0), (1, 0), 0.5, colors.black),
                # 调整高度和内边距
                ('TOPPADDING', (0, 0), (1, 0), 6),
                ('BOTTOMPADDING', (0, 0), (1, 0), 6),
                # 移除内部单元格边框
                ('LINEAFTER', (0, 0), (0, 0), 0, colors.white)
            ])
            
            progress_table.setStyle(progress_style)
            
            # 创建完整行的表格（包括标签、分数和进度条）
            row = [
                holland['label'],         # 类型标签
                str(score),               # 分数
                progress_table            # 进度条（嵌套表格）
            ]
            
            # 计算最终表格列宽
            colWidths = [label_width, score_label_width, bar_width + 2]  # +2是为了边框
            
            # 创建最终表格
            bar_table = Table([row], colWidths=colWidths)
            
            # 设置最终表格样式
            bar_style = TableStyle([
                ('FONTNAME', (0, 0), (0, 0), self.bold_font),
                ('FONTNAME', (1, 0), (1, 0), self.default_font),
                ('FONTSIZE', (0, 0), (0, 0), 14),  # 标签字体
                ('FONTSIZE', (1, 0), (1, 0), 14),  # 分数字体
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),  # 标签左对齐
                ('ALIGN', (1, 0), (1, 0), 'CENTER'), # 分数居中
                ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'), # 所有内容垂直居中
                ('RIGHTPADDING', (1, 0), (1, 0), 5),   # 调整分数右边距
                ('LEFTPADDING', (2, 0), (2, 0), 5),    # 调整进度条左边距
            ])
            
            # 应用样式
            bar_table.setStyle(bar_style)
            
            # 添加到故事
            story.append(bar_table)
            story.append(Spacer(1, 5*mm))  # 表格间距
        
        story.append(Spacer(1, 10*mm))
        
        # 职业兴趣代码
        story.append(Paragraph(f'您的职业兴趣（霍兰德）代码是：{job_type}', self.styles['Heading2']))
        story.append(Spacer(1, 10*mm))
        
        # 以下代码保持不变...
        # 创建得分表格
        score_data = [
            ['职业类型', '艺术型(A)', '社会型(S)', '企业型(E)', '传统型(C)', '实际型(R)', '研究型(I)'],
            ['分值', str(count['A']['count']), str(count['S']['count']), str(count['E']['count']), 
             str(count['C']['count']), str(count['R']['count']), str(count['I']['count'])]
        ]
        
        # 创建表格
        score_table = Table(score_data)
        
        # 设置表格样式
        score_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.default_font),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(score_table)
        story.append(Spacer(1, 5*mm))
        
        # 满分说明
        story.append(Paragraph('职业兴趣满分为20分', self.styles['Normal']))
        story.append(PageBreak())
        
        # 类型详情
        if type_info:
            story.append(Paragraph('职业兴趣测评详细分析', self.styles['Heading2']))
            story.append(Spacer(1, 5*mm))
            
            # 职业兴趣倾向
            story.append(Paragraph('职业兴趣倾向', self.styles['Heading3']))
            interest_text = self._ensure_text_safe(type_info.zyxqqx).replace('\n', '<br/>')
            story.append(Paragraph(interest_text, self.styles['Normal']))
            story.append(Spacer(1, 5*mm))
            
            # 性格倾向
            story.append(Paragraph('性格倾向', self.styles['Heading3']))
            personality_text = self._ensure_text_safe(type_info.xgqx).replace('\n', '<br/>')
            story.append(Paragraph(personality_text, self.styles['Normal']))
            story.append(Spacer(1, 5*mm))
            
            # 职业领域
            story.append(Paragraph('职业领域', self.styles['Heading3']))
            career_text = self._ensure_text_safe(type_info.zyly).replace('\n', '<br/>')
            story.append(Paragraph(career_text, self.styles['Normal']))
            story.append(Spacer(1, 5*mm))
            
            # 典型职业
            story.append(Paragraph('典型职业', self.styles['Heading3']))
            typical_job_text = self._ensure_text_safe(type_info.dxzy).replace('\n', '<br/>')
            story.append(Paragraph(typical_job_text, self.styles['Normal']))
            story.append(Spacer(1, 5*mm))
        else:
            story.append(Paragraph('未找到对应的职业兴趣类型详情', self.styles['Normal']))
        
        # 添加分页
        story.append(PageBreak())
        
        # 适合专业分析
        story.append(Paragraph('适合专业分析', self.styles['Heading2']))
        story.append(Spacer(1, 5*mm))
        
        # 添加星号图标
        self._add_star_icon(story)
            
        # 专业分析说明
        analysis_text = """根据您在职业兴趣倾向、职业性格测评的得分，通过数据统计和分析，将其与常模的数据进行比较，结合国家教育部最新公布的普通高等院校专业目录，我们为您提供匹配度最高的专业大类，专业大类招生是高校招生未来的趋势，根据教育部专业目录要求，专业大类是学科门类下设的一级学科，未来学生选择的专业是专业大类下设的二级学科。不同高校的专业建设情况及人才培养需求不同，因而同一专业大类下设的专业数量和专业方向也不尽相同。在此提醒家长和学生在专业选择上，务必明确目标院校中是否开设意愿就读的专业及您的孩子是否可以报考该专业！"""
        story.append(Paragraph(analysis_text, self.styles['Normal']))
        story.append(Spacer(1, 10*mm))
        
        # 推荐专业大类
        story.append(Paragraph('推荐专业大类', self.styles['Heading3']))
        
        # 将推荐专业拼接成一行文本
        if recommended_majors:
            majors_text = '、'.join([self._ensure_text_safe(major.zymc) for major in recommended_majors])
            story.append(Paragraph(majors_text, self.styles['Normal']))
        else:
            story.append(Paragraph('暂无推荐专业', self.styles['Normal']))

    def _add_tips(self, story):
        """添加职业兴趣测评温馨提示"""
        # 章节标题
        self._add_section_title(story, 'Part.3 温馨提示')
        
        # 添加星号图标
        self._add_star_icon(story)
        
        # 温馨提示标题
        story.append(Paragraph('温馨提示', self.styles['Heading3']))
        story.append(Spacer(1, 5*mm))
        
        # 温馨提示内容
        tips_text = """希望我们的测评报告会对您的专业选择提供有效的帮助。本测试仅作为考生在高考专业选择时的一种参考，并不代表我们推荐的适合测试者的专业可作为唯一的专业报考依据，本测评系统的研发单位不为个人的最终选择承担责任，除本报告外，建议您在报考时参考多方面的因素："""
        story.append(Paragraph(tips_text, self.styles['Normal']))
        story.append(Spacer(1, 5*mm))
        
        # 注意事项列表
        notes = [
            "1. 适当考虑自身性格、气质、价值观等因素，选择专业。",
            "2. 审视自己的家庭经济状况（个别院校、专业学费较高）。",
            "3. 考虑自己的身体状况（部分专业对考生的身体素质有特殊要求，如公安类院校需要体能测试）。",
            "4. 考虑自己对地域环境的适应性（不同的地域，其社会风俗人情、生活饮食习惯、消费水平和气候等都有很大差异）。",
            "5. 选专业先了解专业真正含义（就业前景、就业率、就业方向、供职部门、行业发展等因素）。",
            "6. 权衡学校和专业，二者兼顾。（全方位了解学校和专业，权衡自己对专业和学校的要求）。",
            "7. 考虑社会的发展对所选专业的对应行业领域的影响。",
            "8. 考虑报考政策和录取政策。"
        ]
        
        for note in notes:
            story.append(Paragraph(note, self.styles['List_Item']))
            story.append(Spacer(1, 3*mm))

class PdfService:
    """PDF报告生成服务 - 主类"""
    
    def __init__(self):
        """初始化PDF服务"""
        # 创建专用报告服务实例
        self.mbti_service = MbtiReportService()
        self.job_service = JobReportService()
        
        # 初始化基础目录
        base_dir = current_app.root_path
        self.output_dir = os.path.join(base_dir, 'static', 'reports')
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_mbti_report(self, answer, student):
        """
        生成MBTI测评报告
        
        Args:
            answer: MBTI测评答案对象
            student: 学生对象
            
        Returns:
            str: 生成的PDF文件路径
        """
        try:
            return self.mbti_service.generate_report(answer, student)
        except Exception as e:
            current_app.logger.error(f"生成MBTI报告失败: {str(e)}")
            current_app.logger.error(traceback.format_exc())
            raise ValueError(f"生成报告时发生错误: {str(e)}")
    
    def generate_job_report(self, answer, student):
        """
        生成职业兴趣测评报告
        
        Args:
            answer: 职业兴趣测评答案对象
            student: 学生对象
            
        Returns:
            str: 生成的PDF文件路径
        """
        try:
            return self.job_service.generate_report(answer, student)
        except Exception as e:
            current_app.logger.error(f"生成职业兴趣报告失败: {str(e)}")
            current_app.logger.error(traceback.format_exc())
            raise ValueError(f"生成报告时发生错误: {str(e)}")
    
    def _diagnose_job_data(self, answer, timu_dict):
        """
        诊断职业兴趣测评数据，帮助排查问题
        
        Args:
            answer: 职业兴趣测评答案对象
            timu_dict: 题目字典
        """
        try:
            # 记录答案对象基本信息
            current_app.logger.info(f"答案ID: {answer.id}, 结果类型: {answer.jieguo}")
            
            # 解析答案数据
            answer_data = json.loads(answer.answer)
            current_app.logger.info(f"答案数据长度: {len(answer_data)}")
            
            # 分析前5个答案（如果有的话）
            sample_answers = dict(list(answer_data.items())[:5])
            current_app.logger.info(f"答案数据样本: {sample_answers}")
            
            # 检查题目字典
            current_app.logger.info(f"题目字典长度: {len(timu_dict)}")
            
            # 分析前5个题目信息（如果有的话）
            sample_timu = dict(list(timu_dict.items())[:5])
            current_app.logger.info(f"题目数据样本: {sample_timu}")
            
            # 统计答案类型分布
            answer_types = {}
            for value in answer_data.values():
                if value not in answer_types:
                    answer_types[value] = 0
                answer_types[value] += 1
            current_app.logger.info(f"答案类型分布: {answer_types}")
            
            # 检查答案中的题目ID是否在题目字典中存在
            missing_timu = []
            for question_id in answer_data.keys():
                if question_id not in timu_dict:
                    missing_timu.append(question_id)
            
            if missing_timu:
                current_app.logger.warning(f"有{len(missing_timu)}个题目ID在题目字典中不存在: {missing_timu[:5]}")
            else:
                current_app.logger.info("所有题目ID在题目字典中都存在")
            
            # 检查wid值
            wid_counts = {}
            for timu_info in timu_dict.values():
                wid = timu_info.get("wid", "")
                if wid not in wid_counts:
                    wid_counts[wid] = 0
                wid_counts[wid] += 1
            
            current_app.logger.info(f"题目中的wid分布: {wid_counts}")
            
        except Exception as e:
            current_app.logger.error(f"诊断数据时出错: {str(e)}")
    
    def get_report_path(self, report_id):
        """
        获取报告文件路径
        
        Args:
            report_id: 报告ID或文件名
            
        Returns:
            str: 完整的报告文件路径
        """
        if not report_id:
            return None
            
        # 如果已经是完整路径，直接返回
        if os.path.isabs(report_id) and os.path.exists(report_id):
            return report_id
            
        # 如果是相对路径，拼接输出目录
        filepath = os.path.join(self.output_dir, report_id)
        if os.path.exists(filepath):
            return filepath
            
        # 如果文件不存在，检查是否是没有扩展名的ID
        if not report_id.endswith('.pdf'):
            # 检查对应的PDF文件是否存在
            pdf_path = os.path.join(self.output_dir, f"{report_id}.pdf")
            if os.path.exists(pdf_path):
                return pdf_path
        
        return None
    