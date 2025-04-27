# app/services/ceping/pdf_service.py
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
from io import BytesIO
import json
import os
import time
from flask import current_app

class PdfService:
    """PDF报告生成服务"""
    
    def __init__(self):
        # 注册字体（常规和粗体两种）
        self._register_fonts()
        
        # 设置样式
        self.styles = self._create_styles()
        
        # 设置颜色常量
        self.colors = {
            'title_blue': colors.HexColor('#14a9df'),
            'title_dark': colors.HexColor('#235869'),
            'green': colors.HexColor('#008000'),
            'orange': colors.HexColor('#fdbb5a'),
            'dark_blue': colors.HexColor('#1d94f8'),
            'light_grey': colors.HexColor('#f5f5f5'),
        }
        
        # 创建输出目录
        base_dir = current_app.root_path
        self.output_dir = os.path.join(base_dir, 'static', 'reports')
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 图片资源路径
        self.resources_dir = os.path.join(base_dir, 'static', 'images')
    
    def _register_fonts(self):
        """注册中文字体（常规和粗体）"""
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
        """创建样式集合"""
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
            textColor=colors.white
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
            leading=46,
            spaceAfter=10,
            textColor=colors.white,
            backColor=colors.HexColor('#14a9df'),
            leftIndent=20
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
            textColor=colors.HexColor('#235869')
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
        
        # 目录条目
        styles['TOC_Item'] = ParagraphStyle(
            name='TOC_Item',
            fontName=self.bold_font,
            fontSize=16,
            leading=22,
            spaceAfter=8,
            textColor=colors.HexColor('#14a9df')
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
    
    # 绘制页眉、页脚
    def _draw_header(self, canvas, doc, title, logo_path, display_page_num=True):
        """绘制页眉和页码"""
        canvas.saveState()
        
        # 绘制页眉背景
        canvas.setFillColorRGB(0.95, 0.95, 0.95)
        canvas.rect(10*mm, 275*mm, 190*mm, 13*mm, fill=1)
        
        # 添加Logo
        if os.path.exists(logo_path):
            canvas.drawImage(logo_path, 10*mm, 275*mm, width=51*mm, height=13*mm)
        
        # 添加标题
        canvas.setFont(self.default_font, 11)
        canvas.drawRightString(200*mm, 282*mm, title)
        
        # 添加页码 (在页面底部)
        if display_page_num:
            canvas.setFont(self.default_font, 10)
            canvas.setFillColor(colors.black)
            canvas.drawCentredString(105*mm, 15*mm, str(doc.page))
        
        canvas.restoreState()
    
    # 绘制页脚
    def _draw_footer(self, canvas, doc, page_num):
        """绘制页脚"""
        canvas.saveState()
        
        canvas.setFont(self.default_font, 10)
        canvas.drawCentredString(105*mm, 15*mm, str(page_num))
        
        canvas.restoreState()
    
    # 确保文本安全（处理特殊字符）
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
    
    # 创建画布背景
    def _create_cover_canvas(self, file_path):
        """创建带背景图的封面画布"""
        c = canvas.Canvas(file_path, pagesize=A4)
        
        # 添加背景图
        bg_path = os.path.join(self.resources_dir, 'backbj.png')
        if os.path.exists(bg_path):
            c.drawImage(bg_path, 0, 0, width=210*mm, height=297*mm)
        
        return c
    
    # 绘制分数条
    def _draw_score_bar(self, canvas, x, y, width, score, max_score=20, color=colors.blue):
        """绘制分数条"""
        canvas.saveState()
        
        # 根据分数计算宽度比例
        bar_width = (width * score / max_score)
        
        # 背景
        canvas.setFillColor(colors.lightgrey)
        canvas.rect(x, y, width, 10*mm, fill=1)
        
        # 前景
        canvas.setFillColor(color)
        canvas.rect(x, y, bar_width, 10*mm, fill=1)
        
        # 分数文本
        canvas.setFillColor(colors.white)
        canvas.setFont(self.default_font, 12)
        canvas.drawCentredString(x + bar_width/2, y + 5*mm, str(score))
        
        canvas.restoreState()
    
    # MBTI报告生成主方法
    def generate_mbti_report(self, answer, student):
        """生成MBTI测评报告"""
        from app.models.ceping_mbti_leixing import CepingMbtiLeixing
        
        # 解析结果
        jieguo = json.loads(answer.jieguo)
        
        # 计算人格类型
        personality_type = ""
        if jieguo['I']['count'] >= jieguo['E']['count']:
            personality_type += 'I'
        else:
            personality_type += 'E'
            
        if jieguo['N']['count'] >= jieguo['S']['count']:
            personality_type += 'N'
        else:
            personality_type += 'S'
            
        if jieguo['F']['count'] >= jieguo['T']['count']:
            personality_type += 'F'
        else:
            personality_type += 'T'
            
        if jieguo['P']['count'] >= jieguo['J']['count']:
            personality_type += 'P'
        else:
            personality_type += 'J'
        
        # 获取类型详情
        type_info = CepingMbtiLeixing.query.filter_by(name=personality_type).first()
        
        # 创建PDF文件
        filename = f"MBTI_{self._ensure_text_safe(student.name)}_{int(time.time())}.pdf"
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
        
        # 获取logo路径
        logo_path = os.path.join(self.resources_dir, 'logo.png')
        
        # 构建PDF内容
        story = []
        
        # 添加封面
        self._add_mbti_cover(story, student, answer, logo_path)
        story.append(PageBreak())
        
        # 添加前言
        self._add_mbti_preface(story)
        story.append(PageBreak())
        
        # 添加目录
        self._add_mbti_toc(story)
        story.append(PageBreak())
        
        # 添加测评介绍
        self._add_mbti_introduction(story)
        story.append(PageBreak())
        
        # 添加测评结果
        self._add_mbti_results(story, jieguo, personality_type, type_info)
        story.append(PageBreak())
        
        # 添加温馨提示
        self._add_mbti_tips(story)
        
        # 自定义页面回调函数
        def first_page_callback(canvas, doc):
            self._draw_header(canvas, doc, "性格能力测评", logo_path, display_page_num=False)
        
        def later_pages_callback(canvas, doc):
            # 目录页面也不显示页码
            if doc.page <= 3:  # 封面、前言、目录页不显示页码
                self._draw_header(canvas, doc, "性格能力测评", logo_path, display_page_num=False)
            else:
                # 从第4页开始显示页码(显示的页码从1开始)
                current_page = doc.page - 3
                # 保存原始页码
                original_page = doc.page
                # 设置页码
                doc.page = current_page
                # 绘制页眉和页码
                self._draw_header(canvas, doc, "性格能力测评", logo_path, display_page_num=True)
                # 恢复原始页码，避免影响后续页面
                doc.page = original_page
        
        # 构建PDF
        doc.build(
            story,
            onFirstPage=first_page_callback,
            onLaterPages=later_pages_callback
        )
        
        return filepath
    
    def _add_mbti_cover(self, story, student, answer, logo_path):
        """添加MBTI报告封面"""
        # 标题
        title = '性格能力测评'
        subtitle = 'Personality and ability evaluation report'
        
        # 生成标题
        story.append(Paragraph(title, self.styles['Cover_Title']))
        story.append(Spacer(1, 10*mm))
        
        # 添加分隔图片
        separator_path = os.path.join(self.resources_dir, 'stitle_bg.png')
        if os.path.exists(separator_path):
            story.append(Image(separator_path, width=140*mm, height=10*mm))
        
        # 生成副标题
        story.append(Paragraph(subtitle, self.styles['Cover_Subtitle']))
        story.append(Spacer(1, 80*mm))  # 减少间距，为表格腾出空间
        
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
            ('TOPPADDING', (0, 0), (-1, -1), 12),  # 增加上内边距
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),  # 增加下内边距
        ])
        
        # 添加居中效果
        table_width = 320  # 表格总宽度
        page_width = A4[0] - 20*mm  # 页面宽度减去左右边距
        
        # 创建表格并设置样式
        student_table = Table(student_data, colWidths=[100, 220])
        student_table.setStyle(table_style)
        
        # 使用嵌套表格实现居中对齐
        outer_data = [[student_table]]
        outer_table = Table(outer_data, colWidths=[page_width])
        outer_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
        ]))
        
        story.append(outer_table)
    
    def _add_mbti_preface(self, story):
        """添加MBTI报告前言"""
        # 前言标题
        story.append(Paragraph('前言', self.styles['Title']))
        story.append(Spacer(1, 5*mm))
        
        # 添加下划线图片
        line_path = os.path.join(self.resources_dir, 'xian.png')
        if os.path.exists(line_path):
            story.append(Image(line_path, width=20*mm, height=2*mm))
        
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
        story.append(Spacer(1, 30*mm))
        copyright_text = """
        <font color="red">*</font>版权声明<br/>
        本报告内容属于个人隐私，请注意保密<br/>
        本报告必须在专业咨询师的指导下使用<br/>
        本报告的所有权都受到版权保护，未经授权不得擅自转载、挪用、复制、刊印等，不得用于商业或非商业用途
        """
        story.append(Paragraph(copyright_text, self.styles['Copyright']))
    
    def _add_mbti_toc(self, story):
        """添加MBTI报告目录"""
        story.append(Paragraph('目录 Catalog', self.styles['Title']))
        story.append(Spacer(1, 5*mm))
        
        # 添加下划线图片
        line_path = os.path.join(self.resources_dir, 'xian.png')
        if os.path.exists(line_path):
            story.append(Image(line_path, width=54*mm, height=2*mm))
        
        story.append(Spacer(1, 10*mm))
        
        # 目录内容
        toc_data = [
            ['Part.1 性格能力测评体系介绍', '1'],
            ['Part.2 性格能力测评结果分析', '2'],
            ['Part.3 温馨提示', '4']
        ]
        
        # 目录表格样式
        toc_style = TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.bold_font),
            ('FONTSIZE', (0, 0), (-1, -1), 16),
            ('TEXTCOLOR', (0, 0), (0, 0), colors.HexColor('#14a9df')),
            ('TEXTCOLOR', (0, 1), (0, -1), colors.HexColor('#1ca4b6')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#1ca4b6')),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ])
        
        # 创建目录表格
        toc_table = Table(toc_data, colWidths=[450, 40])
        toc_table.setStyle(toc_style)
        story.append(toc_table)
    
    def _add_mbti_introduction(self, story):
        """添加MBTI测评体系介绍"""
        # 章节标题背景
        story.append(Paragraph('Part.1 性格能力测评体系介绍', self.styles['Blue_Title']))
        story.append(Spacer(1, 10*mm))
        
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
            dim_style = ParagraphStyle(
                'Dimension',
                parent=self.styles['Normal'],
                leftIndent=32,
                firstLineIndent=0
            )
            story.append(Paragraph(dim, dim_style))
            story.append(Spacer(1, 3*mm))
        
        story.append(Spacer(1, 5*mm))
        
        # 结论
        conclusion = """性格能力评估系统可以帮助我们认清自己，但是并不剥夺我们认知的自由，把结论强加于人；MBTI可以有效地评估我们的性格类型；引导我们建立自信，信任并理解他人；进而在职业定位和发展、人际关系等领域为我们提供帮助。"""
        story.append(Paragraph(conclusion, self.styles['Normal']))
    
    def _add_mbti_results(self, story, jieguo, personality_type, type_info):
        """添加MBTI测评结果分析"""
        # 章节标题
        story.append(Paragraph('Part.2 性格能力测评结果分析', self.styles['Blue_Title']))
        story.append(Spacer(1, 10*mm))
        
        # 星号图标
        star_path = os.path.join(self.resources_dir, 'xingxing.png')
        if os.path.exists(star_path):
            story.append(Image(star_path, width=4*mm, height=4*mm))
        
        # 小标题
        subtitle = f"""职业性格分析 根据您测评结果进行分析，您的职业性格结果如下所示："""
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=self.styles['Normal'],
            firstLineIndent=0,
            leftIndent=15
        )
        story.append(Paragraph(subtitle, subtitle_style))
        story.append(Spacer(1, 10*mm))
        
        # 创建维度得分表格
        dimensions = [
            {'key': 'E', 'label': '外向(E)', 'opposing_key': 'I', 'opposing_label': '内向(I)'},
            {'key': 'S', 'label': '感觉(S)', 'opposing_key': 'N', 'opposing_label': '直觉(N)'},
            {'key': 'T', 'label': '思考(T)', 'opposing_key': 'F', 'opposing_label': '情感(F)'},
            {'key': 'J', 'label': '判断(J)', 'opposing_key': 'P', 'opposing_label': '知觉(P)'}
        ]
        
        # 创建表格数据
        dim_data = []
        for dim in dimensions:
            key = dim['key']
            opposing_key = dim['opposing_key']
            
            # 获取两边分数
            score1 = jieguo[key]['count']
            score2 = jieguo[opposing_key]['count']
            total = score1 + score2
            
            # 计算比例，避免除以零
            if total > 0:
                percent1 = int((score1 / total) * 100)
            else:
                percent1 = 50
            percent2 = 100 - percent1
            
            # 判断哪边的分数更高，用粗体标记
            left_style = f"<b>{score1}</b>" if score1 >= score2 else str(score1)
            right_style = f"<b>{score2}</b>" if score2 >= score1 else str(score2)
            
            # 添加行数据
            row = [
                dim['label'], 
                Paragraph(left_style, self.styles['Normal']),
                # 这里应该有进度条，但reportlab不直接支持，我们将用表格实现
                dim['opposing_label'],
                Paragraph(right_style, self.styles['Normal'])
            ]
            dim_data.append(row)
        
        # 创建表格
        col_widths = [80, 40, 280, 80, 40]
        dim_table = Table(dim_data, colWidths=col_widths)
        
        # 设置表格样式
        dim_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.default_font),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
            ('ALIGN', (4, 0), (4, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 13),
        ]))
        
        story.append(dim_table)
        story.append(Spacer(1, 10*mm))
        
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
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#235869')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.black),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
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
    
    def _add_mbti_tips(self, story):
        """添加MBTI测评温馨提示"""
        # 章节标题
        story.append(Paragraph('Part.3 温馨提示', self.styles['Blue_Title']))
        story.append(Spacer(1, 10*mm))
        
        # 星号图标
        star_path = os.path.join(self.resources_dir, 'xingxing.png')
        if os.path.exists(star_path):
            story.append(Image(star_path, width=4*mm, height=4*mm))
        
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
            note_style = ParagraphStyle(
                'Note',
                parent=self.styles['Normal'],
                firstLineIndent=0,
                leftIndent=15
            )
            story.append(Paragraph(note, note_style))
            story.append(Spacer(1, 3*mm))
        
        story.append(Spacer(1, 5*mm))
        story.append(Paragraph('您可以在适当的时候选择重新进行测试。', self.styles['Normal']))
        story.append(Paragraph('希望性格能力测评报告能为您的选择提供有价值的参考。', self.styles['Normal']))
    
    def _diagnose_job_data(self, answer, timu_dict):
        """诊断职业兴趣测评数据，帮助排查问题"""
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
    
    # 职业兴趣测评报告生成方法
    def generate_job_report(self, answer, student):
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
            count = {
                "S": {'count': 0, 'color': 'green'},
                "R": {'count': 0, 'color': 'green'},
                "C": {'count': 0, 'color': 'green'},
                "E": {'count': 0, 'color': 'green'},
                "I": {'count': 0, 'color': 'green'},
                "A": {'count': 0, 'color': 'green'}
            }
            
            # 使用题号(tid)作为匹配键 - 这是根据日志确认有效的匹配方式
            for q in timu:
                tid_key = str(q.tid)
                
                # 检查该题目是否在答案中且选择了A选项
                if tid_key in answer_data and answer_data[tid_key] == "A":
                    if q.wid in count:
                        count[q.wid]['count'] += 1
            
            # 对不在结果类型中的类型进行处理 (参考PHP代码)
            for key in count:
                # 检查当前类型是否在结果字符串中
                if key in answer.jieguo:
                    count[key]['color'] = "orange"
                else:
                    # 如果不在结果中且分数大于0，则减1（与PHP代码一致）
                    if count[key]['count'] > 0:
                        count[key]['count'] -= 1
                    count[key]['color'] = "green"
            
            # 获取类型详情
            type_info = CepingJobLeixing.query.filter_by(title=answer.jieguo).first()
            
            # 获取推荐专业
            recommended_majors = CepingJobZhuanye.query.filter_by(title=answer.jieguo).all()
            
            # 创建PDF文件
            filename = f"职业兴趣_{self._ensure_text_safe(student.name)}_{int(time.time())}.pdf"
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
            
            # 获取logo路径
            logo_path = os.path.join(self.resources_dir, 'logo.png')
            
            # 构建PDF内容
            story = []
            
            # 添加封面
            self._add_job_cover(story, student, answer, logo_path)
            story.append(PageBreak())
            
            # 添加前言
            self._add_job_preface(story)
            story.append(PageBreak())
            
            # 添加目录
            self._add_job_toc(story)
            story.append(PageBreak())
            
            # 添加测评介绍
            self._add_job_introduction(story)
            story.append(PageBreak())
            
            # 添加测评结果
            self._add_job_results(story, count, answer.jieguo, type_info, recommended_majors)
            story.append(PageBreak())
            
            # 添加温馨提示
            self._add_job_tips(story)
            
            # 自定义页面回调函数
            def first_page_callback(canvas, doc):
                self._draw_header(canvas, doc, "职业兴趣测评", logo_path, display_page_num=False)
            
            def later_pages_callback(canvas, doc):
                # 目录页面也不显示页码
                if doc.page <= 3:  # 封面、前言、目录页不显示页码
                    self._draw_header(canvas, doc, "职业兴趣测评", logo_path, display_page_num=False)
                else:
                    # 从第4页开始显示页码(显示的页码从1开始)
                    current_page = doc.page - 3
                    # 保存原始页码
                    original_page = doc.page
                    # 设置页码
                    doc.page = current_page
                    # 绘制页眉和页码
                    self._draw_header(canvas, doc, "职业兴趣测评", logo_path, display_page_num=True)
                    # 恢复原始页码，避免影响后续页面
                    doc.page = original_page
            
            # 构建PDF
            doc.build(
                story,
                onFirstPage=first_page_callback,
                onLaterPages=later_pages_callback
            )
            
            return filepath
            
        except Exception as e:
            current_app.logger.error(f"生成职业兴趣报告出错: {str(e)}")
            import traceback
            current_app.logger.error(traceback.format_exc())
            raise e
    
    def _add_job_cover(self, story, student, answer, logo_path):
        """添加职业兴趣报告封面"""
        # 标题
        title = '职业兴趣测评报告'
        subtitle = 'Professional Interest Assessment Report'
        
        # 生成标题
        story.append(Paragraph(title, self.styles['Cover_Title']))
        story.append(Spacer(1, 10*mm))
        
        # 添加分隔图片
        separator_path = os.path.join(self.resources_dir, 'stitle_bg.png')
        if os.path.exists(separator_path):
            story.append(Image(separator_path, width=140*mm, height=10*mm))
        
        # 生成副标题
        story.append(Paragraph(subtitle, self.styles['Cover_Subtitle']))
        story.append(Spacer(1, 80*mm))  # 减少间距，为表格腾出空间
        
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
            ('TOPPADDING', (0, 0), (-1, -1), 12),  # 增加上内边距
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),  # 增加下内边距
        ])
        
        # 添加居中效果
        table_width = 320  # 表格总宽度
        page_width = A4[0] - 20*mm  # 页面宽度减去左右边距
        
        # 创建表格并设置样式
        student_table = Table(student_data, colWidths=[100, 220])
        student_table.setStyle(table_style)
        
        # 使用嵌套表格实现居中对齐
        outer_data = [[student_table]]
        outer_table = Table(outer_data, colWidths=[page_width])
        outer_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
        ]))
        
        story.append(outer_table)
    
    def _add_job_preface(self, story):
        """添加职业兴趣报告前言"""
        # 前言标题
        story.append(Paragraph('前言', self.styles['Title']))
        story.append(Spacer(1, 5*mm))
        
        # 添加下划线图片
        line_path = os.path.join(self.resources_dir, 'xian.png')
        if os.path.exists(line_path):
            story.append(Image(line_path, width=20*mm, height=2*mm))
        
        story.append(Spacer(1, 5*mm))
        
        # 前言内容
        preface_text = """高考是影响考生人生发展的一次重要事件，历来都是学生本人和家长乃至全社会最为重视的事情。高考作为基础教育的"指挥棒"，自从1977年恢复高考以来，关于高考的变革都影响着教育的基本方向和教学策略。《中国职业技术教育》中曾对大学生入校后的关于对专业了解程度的调查显示：对自己所学专业与社会职业要求不清楚的学生占92.2%，选择专业时家长做主的占71.2%，选择专业时听取同学、亲戚意见的占55.3%，对自己不了解的占51.5%，对社会不了解的占62.1%，对职业不了解的占89.2%。从这些数据看来大学生入学时对所学专业与社会职业的了解是有限的，或者说是盲目的。人的一生里总要面临各种抉择，而高考选择专业可能是整个人生的抉择中最有影响、最具挑战性的一个。每逢高考志愿填报时，考生迷茫、家长困惑、老师谨慎。"""
        story.append(Paragraph(preface_text, self.styles['Normal']))
        story.append(Spacer(1, 5*mm))
        
        second_paragraph = """职业兴趣测评系统是启明星高考为解决考生的迷茫，家长老师的困惑，让考生都能选择适合自己的专业，正确做出职业生涯规划，经过多年研究及开发，针对我省高考现状，结合大学生职业规划调查报告，参考大学生就业情况，为高考学生量身打造的。"""
        story.append(Paragraph(second_paragraph, self.styles['Normal']))
        
        # 添加版权声明
        story.append(Spacer(1, 30*mm))
        copyright_text = """
        <font color="red">*</font>版权声明<br/>
        本报告内容属于个人隐私，请注意保密<br/>
        本报告必须在专业咨询师的指导下使用<br/>
        本报告的所有权都受到版权保护，未经授权不得擅自转载、挪用、复制、刊印等，不得用于商业或非商业用途
        """
        story.append(Paragraph(copyright_text, self.styles['Copyright']))
    
    def _add_job_toc(self, story):
        """添加职业兴趣报告目录"""
        story.append(Paragraph('目录 Catalog', self.styles['Title']))
        story.append(Spacer(1, 5*mm))
        
        # 添加下划线图片
        line_path = os.path.join(self.resources_dir, 'xian.png')
        if os.path.exists(line_path):
            story.append(Image(line_path, width=54*mm, height=2*mm))
        
        story.append(Spacer(1, 10*mm))
        
        # 目录内容
        toc_data = [
            ['Part.1 职业兴趣测评体系介绍', '1'],
            ['Part.2 职业兴趣测评结果分析', '3'],
            ['Part.3 温馨提示', '6']
        ]
        
        # 目录表格样式
        toc_style = TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.bold_font),
            ('FONTSIZE', (0, 0), (-1, -1), 16),
            ('TEXTCOLOR', (0, 0), (0, 0), colors.HexColor('#14a9df')),
            ('TEXTCOLOR', (0, 1), (0, -1), colors.HexColor('#1ca4b6')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#1ca4b6')),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ])
        
        # 创建目录表格
        toc_table = Table(toc_data, colWidths=[450, 40])
        toc_table.setStyle(toc_style)
        story.append(toc_table)
    
    def _add_job_introduction(self, story):
        """添加职业兴趣测评体系介绍"""
        # 章节标题背景
        story.append(Paragraph('Part.1 职业兴趣测评体系介绍', self.styles['Blue_Title']))
        story.append(Spacer(1, 10*mm))
        
        # 介绍文本
        intro_text = """职业兴趣测评是以美国心理学家Holland的职业兴趣理论为基础，同时在题目内容设计、常模选取方面结合了考生的实际情况而开发的专业测评工具。通过该系统，可以帮助测试者相对精确地了解自身的个体特点和职业特点之间的匹配关系，同时为测评者在进行职业规划时，提供客观的参考依据分析你的兴趣爱好，推荐你感兴趣和适合的职业作为参考。"""
        story.append(Paragraph(intro_text, self.styles['Normal']))
        story.append(Spacer(1, 5*mm))
        
        second_paragraph = """职业兴趣与职业环境的匹配是决定成功的最重要的因素之一。人们通常倾向于选择与自我职业兴趣类型匹配的职业环境，如具有艺术倾向的个体通常希望在艺术型的职业环境中工作，以便最大限度地发挥个人的潜能。Holland从兴趣的角度出发来探索职业指导问题，根据人格与环境交互作用的观点，把人分为六大类：现实型(R)、研究型(I)、艺术型(A)、社会型(S)、企业型(E)、传统型(C)。"""
        story.append(Paragraph(second_paragraph, self.styles['Normal']))
        story.append(Spacer(1, 10*mm))
        
        # Holland六种类型介绍
        story.append(Paragraph('现实型(R)', self.styles['Heading3']))
        story.append(Paragraph('喜欢具体、实际的工作，喜欢户外活动，有操作机械设备的能力，适合工程技术、农业、制造等领域。', self.styles['Normal']))
        story.append(Spacer(1, 5*mm))
        
        story.append(Paragraph('研究型(I)', self.styles['Heading3']))
        story.append(Paragraph('喜欢思考问题，进行研究和分析，解决复杂问题，适合科学研究、医疗、技术分析等领域。', self.styles['Normal']))
        story.append(Spacer(1, 5*mm))
        
        story.append(Paragraph('艺术型(A)', self.styles['Heading3']))
        story.append(Paragraph('喜欢从事艺术、音乐、文学等富有创造性和表现力的活动，适合设计、表演、写作等领域。', self.styles['Normal']))
        story.append(Spacer(1, 5*mm))
        
        story.append(Paragraph('社会型(S)', self.styles['Heading3']))
        story.append(Paragraph('喜欢与人交往，帮助他人，具有教导、培训和咨询的能力，适合教育、社会服务、医疗护理等领域。', self.styles['Normal']))
        story.append(Spacer(1, 5*mm))
        
        story.append(Paragraph('企业型(E)', self.styles['Heading3']))
        story.append(Paragraph('善于组织、领导和说服他人，喜欢从事管理和销售，适合管理、销售、法律等领域。', self.styles['Normal']))
        story.append(Spacer(1, 5*mm))
        
        story.append(Paragraph('传统型(C)', self.styles['Heading3']))
        story.append(Paragraph('喜欢按部就班、有序和规则的工作，善于处理数据，适合会计、行政、档案管理等领域。', self.styles['Normal']))
    
    def _add_job_results(self, story, count, job_type, type_info, recommended_majors):
        """添加职业兴趣测评结果分析"""
        # 章节标题
        story.append(Paragraph('Part.2 职业兴趣测评结果分析', self.styles['Blue_Title']))
        story.append(Spacer(1, 10*mm))
        
        # 星号图标
        star_path = os.path.join(self.resources_dir, 'xingxing.png')
        if os.path.exists(star_path):
            story.append(Image(star_path, width=4*mm, height=4*mm))
        
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
        
        # 记录分数汇总，用于调试
        score_summary = {}
        for ht in holland_types:
            key = ht['key']
            score_summary[key] = count[key]['count']
        current_app.logger.info(f"结果页面显示的分数汇总: {score_summary}")
        
        # 创建分数条表格数据
        bar_data = []
        for holland in holland_types:
            key = holland['key']
            score = count[key]['count']
            color_name = count[key]['color']
            
            # 创建表格行
            row = [
                holland['label'],
                str(score)
            ]
            bar_data.append(row)
        
        # 创建表格
        bar_table = Table(bar_data, colWidths=[80, 40])
        
        # 设置表格样式
        bar_style = TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.default_font),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ])
        
        # 为每个维度设置对应的背景色
        for i, holland in enumerate(holland_types):
            key = holland['key']
            color_name = count[key]['color']
            if color_name == 'green':
                bar_style.add('BACKGROUND', (1, i), (1, i), colors.green)
            else:
                bar_style.add('BACKGROUND', (1, i), (1, i), colors.orange)
            bar_style.add('TEXTCOLOR', (1, i), (1, i), colors.white)
        
        bar_table.setStyle(bar_style)
        story.append(bar_table)
        story.append(Spacer(1, 10*mm))
        
        # 职业兴趣代码
        story.append(Paragraph(f'您的职业兴趣（霍兰德）代码是：{job_type}', self.styles['Heading2']))
        story.append(Spacer(1, 10*mm))
        
        # 创建得分表格
        score_data = [
            ['职业类型', '艺术型(A)', '社会型(S)', '企业型(E)', '传统型(C)', '实际型(R)', '研究型(I)'],
            ['分值', str(count['A']['count']), str(count['S']['count']), str(count['E']['count']), 
             str(count['C']['count']), str(count['R']['count']), str(count['I']['count'])]
        ]
        
        # 记录表格中显示的分数，用于调试
        current_app.logger.info(f"表格中显示的分数: A={count['A']['count']}, S={count['S']['count']}, E={count['E']['count']}, C={count['C']['count']}, R={count['R']['count']}, I={count['I']['count']}")
        
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
        
        # 星号图标
        if os.path.exists(star_path):
            story.append(Image(star_path, width=4*mm, height=4*mm))
            
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
    
    def _add_job_tips(self, story):
        """添加职业兴趣测评温馨提示"""
        # 章节标题
        story.append(Paragraph('Part.3 温馨提示', self.styles['Blue_Title']))
        story.append(Spacer(1, 10*mm))
        
        # 星号图标
        star_path = os.path.join(self.resources_dir, 'xingxing.png')
        if os.path.exists(star_path):
            story.append(Image(star_path, width=4*mm, height=4*mm))
        
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
            note_style = ParagraphStyle(
                'Note',
                parent=self.styles['Normal'],
                firstLineIndent=0,
                leftIndent=15
            )
            story.append(Paragraph(note, note_style))
            story.append(Spacer(1, 3*mm))