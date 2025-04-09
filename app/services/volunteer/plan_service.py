# app/services/volunteer/plan_service.py
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError
from app.extensions import db
from app.models.student_volunteer_plan import StudentVolunteerPlan, VolunteerCollege, VolunteerSpecialty, VolunteerCategoryAnalysis
from app.services.college.recommendation_service import RecommendationService
from app.services.ai.moonshot import MoonshotAI
import json
from app.services.student.student_data_service import StudentDataService

class VolunteerPlanService:
    """志愿方案服务类，处理学生志愿方案相关业务逻辑"""
    
    @staticmethod
    def create_volunteer_plan(student_id, planner_id, volunteer_data):
        """
        创建学生志愿方案
        
        :param student_id: 学生ID
        :param planner_id: 规划师ID
        :param volunteer_data: 志愿数据，格式为：
            {
                'remarks': '方案备注',
                'colleges': [
                    {
                        'category_id': 1,  # 类别ID(1:冲, 2:稳, 3:保)
                        'group_id': 1,     # 志愿段ID(1-12)
                        'volunteer_index': 1,  # 志愿序号(1-48)
                        'college_id': 123,     # 院校ID
                        'college_name': '北京大学',  # 院校名称
                        'college_group_id': 456,    # 院校专业组ID
                        'score_diff': -10,          # 分差
                        'prediction_score': 650,    # 预测分数
                        'recommend_type': 'ai',     # 推荐类型
                        'ai_analysis': '分析内容...',  # AI分析
                        'specialties': [
                            {
                                'specialty_id': 789,     # 专业ID
                                'specialty_code': 'CS01',  # 专业代码
                                'specialty_name': '计算机科学',  # 专业名称
                                'specialty_index': 1,    # 专业序号(1-6)
                                'prediction_score': 650,  # 专业预测分数
                                'plan_number': 50,       # 计划招生人数
                                'tuition': 5000,         # 学费
                                'remarks': '专业备注',     # 备注
                                'ai_analysis': '专业分析...',  # AI分析
                                'fenshuxian_id': 12345    # 关联分数线ID
                            }
                        ]
                    }
                ]
            }
        :return: 创建的志愿方案
        """
        try:
            # 开始数据库事务
            with db.session.begin_nested():
                # 1. 获取学生当前的最新版本号
                latest_plan = StudentVolunteerPlan.query.filter_by(
                    student_id=student_id
                ).order_by(StudentVolunteerPlan.version.desc()).first()
                
                new_version = 1
                if latest_plan:
                    new_version = latest_plan.version + 1
                    
                    # 将所有之前的方案设置为非当前版本(批量更新，只执行一次数据库操作)
                    db.session.query(StudentVolunteerPlan).filter(
                        StudentVolunteerPlan.student_id == student_id,
                        StudentVolunteerPlan.is_current == True
                    ).update({"is_current": False}, synchronize_session=False)
                
                # 2. 创建新的志愿方案
                plan = StudentVolunteerPlan(
                    student_id=student_id,
                    planner_id=planner_id,
                    version=new_version,
                    is_current=True,
                    remarks=volunteer_data.get('remarks', '')
                )
                db.session.add(plan)
                db.session.flush()  # 刷新会话以获取plan.id，但不提交事务
                
                # 3. 预先准备所有需要批量插入的志愿院校和专业
                volunteer_colleges = []
                volunteer_specialties = []
                
                # 4. 处理院校志愿
                for college_data in volunteer_data.get('colleges', []):
                    college = VolunteerCollege(
                        plan_id=plan.id,
                        category_id=college_data.get('category_id'),
                        group_id=college_data.get('group_id'),
                        volunteer_index=college_data.get('volunteer_index'),
                        college_id=college_data.get('college_id'),
                        college_name=college_data.get('college_name'),
                        college_group_id=college_data.get('college_group_id'),
                        score_diff=college_data.get('score_diff'),
                        prediction_score=college_data.get('prediction_score'),
                        recommend_type=college_data.get('recommend_type', VolunteerCollege.RECOMMEND_PLANNER),
                        ai_analysis=college_data.get('ai_analysis', ''),
                        area_name=college_data.get('area_name'),
                        group_name=college_data.get('group_name'),
                        min_tuition=college_data.get('min_tuition'),
                        max_tuition=college_data.get('max_tuition'),
                        min_score=college_data.get('min_score'),
                        plan_number=college_data.get('plan_number'),
                        school_type_text=college_data.get('school_type_text'),
                        subject_requirements=college_data.get('subject_requirements'),
                        tese_text=college_data.get('tese_text'),
                        teshu_text=college_data.get('teshu_text'),
                        uncode=college_data.get('uncode'),
                        nature=college_data.get('nature')
                    )
                    volunteer_colleges.append(college)
                
                # 5. 批量添加院校志愿
                if volunteer_colleges:
                    db.session.bulk_save_objects(volunteer_colleges)
                    db.session.flush()  # 刷新会话以获取志愿院校的ID
                
                    # 构建院校ID映射，用于关联专业
                    college_id_map = {}
                    for idx, college in enumerate(volunteer_colleges):
                        college_data = volunteer_data['colleges'][idx]
                        college_id_map[f"{college_data['volunteer_index']}"] = college.id
                    
                    # 6. 处理专业志愿
                    for idx, college_data in enumerate(volunteer_data.get('colleges', [])):
                        college_id = college_id_map.get(f"{college_data['volunteer_index']}")
                        if not college_id:
                            continue
                            
                        for specialty_data in college_data.get('specialties', []):
                            specialty = VolunteerSpecialty(
                                volunteer_college_id=college_id,
                                specialty_id=specialty_data.get('specialty_id'),
                                specialty_code=specialty_data.get('specialty_code'),
                                specialty_name=specialty_data.get('specialty_name'),
                                specialty_index=specialty_data.get('specialty_index'),
                                prediction_score=specialty_data.get('prediction_score'),
                                plan_number=specialty_data.get('plan_number'),
                                tuition=specialty_data.get('tuition'),
                                remarks=specialty_data.get('remarks', ''),
                                ai_analysis=specialty_data.get('ai_analysis', ''),
                                fenshuxian_id=specialty_data.get('fenshuxian_id')
                            )
                            volunteer_specialties.append(specialty)
                
                # 7. 批量添加专业志愿
                if volunteer_specialties:
                    db.session.bulk_save_objects(volunteer_specialties)
            
            # 提交事务
            db.session.commit()
            
            # 8. 返回创建的方案详情
            return {
                'plan': plan.to_dict(),
                'college_count': len(volunteer_colleges),
                'specialty_count': len(volunteer_specialties)
            }
            
        except SQLAlchemyError as e:
            # 回滚事务
            db.session.rollback()
            current_app.logger.error(f"创建志愿方案失败: {str(e)}")
            raise
    
    @staticmethod
    def get_volunteer_plan(plan_id, include_details=True, category_id=None, group_id=None, volunteer_index=None):
        """
        获取志愿方案详情
        
        :param plan_id: 志愿方案ID
        :param include_details: 是否包含详细志愿信息
        :param category_id: 按类别ID过滤(1:冲, 2:稳, 3:保)
        :param group_id: 按志愿段ID过滤(1-12)
        :param volunteer_index: 按志愿序号过滤(1-48)
        :return: 志愿方案详情
        """
        plan = StudentVolunteerPlan.query.get_or_404(plan_id)
        result = plan.to_dict()
        
        # # 获取志愿类别分析信息
        # analyses_query = VolunteerCategoryAnalysis.query.filter_by(plan_id=plan_id)
        
        # # 如果指定了类别ID，也按类别ID过滤分析
        # if category_id is not None:
        #     analyses_query = analyses_query.filter_by(category_id=category_id)
            
        # # 获取分析结果并添加到返回数据中
        # category_analyses = analyses_query.all()
        # result['category_analyses'] = [analysis.to_dict() for analysis in category_analyses]
        
        if include_details:
            # 构建基础查询
            colleges_query = VolunteerCollege.query.filter_by(plan_id=plan_id)
            
            # 应用过滤条件
            if category_id is not None:
                colleges_query = colleges_query.filter_by(category_id=category_id)
            if group_id is not None:
                colleges_query = colleges_query.filter_by(group_id=group_id)
            if volunteer_index is not None:
                colleges_query = colleges_query.filter_by(volunteer_index=volunteer_index)
                
            # 执行查询获取结果
            colleges = colleges_query.all()
            college_ids = [college.id for college in colleges]
            
            # 批量获取所有专业，避免N+1查询问题
            all_specialties = {}
            if college_ids:
                specialties = VolunteerSpecialty.query.filter(
                    VolunteerSpecialty.volunteer_college_id.in_(college_ids)
                ).all()
                
                # 按院校ID分组专业
                for specialty in specialties:
                    if specialty.volunteer_college_id not in all_specialties:
                        all_specialties[specialty.volunteer_college_id] = []
                    all_specialties[specialty.volunteer_college_id].append(specialty.to_dict())
            
            # 构建完整的志愿方案详情
            volunteer_colleges = []
            for college in colleges:
                college_dict = college.to_dict()
                college_dict['specialties'] = all_specialties.get(college.id, [])
                volunteer_colleges.append(college_dict)
            
            result['colleges'] = volunteer_colleges
        
        return result
    
    @staticmethod
    def update_volunteer_plan(plan_id, update_data, create_new_version= False):
        """
        修改学生志愿方案
        
        :param plan_id: 志愿方案ID
        :param update_data: 更新数据，格式与create_volunteer_plan相同
        :param create_new_version: 是否创建新版本，True则创建新版本，False则更新当前版本
        :return: 更新后的志愿方案
        """
        try:
            plan = StudentVolunteerPlan.query.get_or_404(plan_id)
            new_plan = None

            # 1. 获取原方案
            if create_new_version:
                # 创建新版本的方案
                new_plan = StudentVolunteerPlan(
                    student_id=plan.student_id,
                    planner_id=plan.planner_id,
                    version=plan.version + 1,
                    is_current=True,
                    remarks=update_data.get('remarks')
                )
                
                # 将所有当前版本设为非当前版本
                db.session.query(StudentVolunteerPlan).filter(
                    StudentVolunteerPlan.student_id == plan.student_id,
                    StudentVolunteerPlan.is_current == True
                ).update({"is_current": False}, synchronize_session=False)
                
                db.session.add(new_plan)
                db.session.flush()
                
                plan_id = new_plan.id
            else:
                # 更新当前版本
                if 'remarks' in update_data:
                    plan.remarks = update_data.get('remarks')
                plan_id = plan.id
            
            # 2. 处理院校志愿更新
            if 'colleges' in update_data:
                # 获取所有现有的院校志愿ID
                existing_colleges = {c.volunteer_index: c.id for c in 
                                    VolunteerCollege.query.filter_by(plan_id=plan_id).all()}
                
                colleges_to_add = []
                colleges_to_update = []
                college_indexes_to_keep = []
                
                # 处理更新和新增的院校志愿
                for college_data in update_data.get('colleges', []):
                    volunteer_index = college_data.get('volunteer_index')
                    college_indexes_to_keep.append(volunteer_index)
                    
                    if volunteer_index in existing_colleges:
                        # 更新现有院校志愿
                        college_id = existing_colleges[volunteer_index]
                        college = VolunteerCollege.query.get(college_id)
                        for key, value in college_data.items():
                            if key != 'specialties' and hasattr(college, key):
                                setattr(college, key, value)
                        # 强制设置recommend_type为规划师调整
                        college.recommend_type = VolunteerCollege.RECOMMEND_PLANNER
                        colleges_to_update.append(college)
                    else:
                        # 添加新院校志愿
                        college = VolunteerCollege(
                            plan_id=plan_id,
                            category_id=college_data.get('category_id'),
                            group_id=college_data.get('group_id'),
                            volunteer_index=volunteer_index,
                            college_id=college_data.get('college_id'),
                            college_name=college_data.get('college_name'),
                            college_group_id=college_data.get('college_group_id'),
                            score_diff=college_data.get('score_diff'),
                            prediction_score=college_data.get('prediction_score'),
                            recommend_type=VolunteerCollege.RECOMMEND_PLANNER,
                            ai_analysis=college_data.get('ai_analysis', ''),
                            area_name=college_data.get('area_name'),
                            group_name=college_data.get('group_name'),
                            min_tuition=college_data.get('min_tuition'),
                            max_tuition=college_data.get('max_tuition'),
                            min_score=college_data.get('min_score'),
                            plan_number=college_data.get('plan_number'),
                            school_type_text=college_data.get('school_type_text'),
                            subject_requirements=college_data.get('subject_requirements'),
                            tese_text=college_data.get('tese_text'),
                            teshu_text=college_data.get('teshu_text'),
                            uncode=college_data.get('uncode'),
                            nature=college_data.get('nature'),
                        )
                        colleges_to_add.append(college)
                
                # 批量添加新院校志愿
                if colleges_to_add:
                    db.session.bulk_save_objects(colleges_to_add)
                
                # 批量更新现有院校志愿
                if colleges_to_update:
                    db.session.bulk_save_objects(colleges_to_update, update_changed_only=True)
                
                # 删除不再需要的院校志愿
                if college_indexes_to_keep:
                    db.session.query(VolunteerCollege).filter(
                        VolunteerCollege.plan_id == plan_id,
                        ~VolunteerCollege.volunteer_index.in_(college_indexes_to_keep)
                    ).delete(synchronize_session=False)
                
                db.session.flush()
                
                # 3. 处理专业志愿更新
                # 获取所有院校志愿ID的映射
                updated_colleges = {c.volunteer_index: c.id for c in 
                                    VolunteerCollege.query.filter_by(plan_id=plan_id).all()}
                
                # 收集所有需要处理的专业志愿
                specialties_to_process = []
                for college_data in update_data.get('colleges', []):
                    volunteer_index = college_data.get('volunteer_index')
                    if volunteer_index in updated_colleges and 'specialties' in college_data:
                        college_id = updated_colleges[volunteer_index]
                        specialties_to_process.append((college_id, college_data['specialties']))
                
                # 批量处理每个院校的专业志愿
                for college_id, specialties in specialties_to_process:
                    # 获取现有的专业志愿
                    existing_specialties = {s.specialty_index: s.id for s in 
                                            VolunteerSpecialty.query.filter_by(volunteer_college_id=college_id).all()}
                    
                    specialties_to_add = []
                    specialties_to_update = []
                    specialty_indexes_to_keep = []
                    
                    # 处理更新和新增的专业志愿
                    for specialty_data in specialties:
                        specialty_index = specialty_data.get('specialty_index')
                        specialty_indexes_to_keep.append(specialty_index)
                        
                        if specialty_index in existing_specialties:
                            # 更新现有专业志愿
                            specialty_id = existing_specialties[specialty_index]
                            specialty = VolunteerSpecialty.query.get(specialty_id)
                            for key, value in specialty_data.items():
                                if hasattr(specialty, key):
                                    setattr(specialty, key, value)
                            specialties_to_update.append(specialty)
                        else:
                            # 添加新专业志愿
                            specialty = VolunteerSpecialty(
                                volunteer_college_id=college_id,
                                specialty_id=specialty_data.get('specialty_id'),
                                specialty_code=specialty_data.get('specialty_code'),
                                specialty_name=specialty_data.get('specialty_name'),
                                specialty_index=specialty_index,
                                prediction_score=specialty_data.get('prediction_score'),
                                plan_number=specialty_data.get('plan_number'),
                                tuition=specialty_data.get('tuition'),
                                remarks=specialty_data.get('remarks', ''),
                                ai_analysis=specialty_data.get('ai_analysis', ''),
                                fenshuxian_id=specialty_data.get('fenshuxian_id')
                            )
                            specialties_to_add.append(specialty)
                    
                    # 批量添加新专业志愿
                    if specialties_to_add:
                        db.session.bulk_save_objects(specialties_to_add)
                    
                    # 批量更新现有专业志愿
                    if specialties_to_update:
                        db.session.bulk_save_objects(specialties_to_update, update_changed_only=True)
                    
                    # 删除不再需要的专业志愿
                    if specialty_indexes_to_keep:
                        db.session.query(VolunteerSpecialty).filter(
                            VolunteerSpecialty.volunteer_college_id == college_id,
                            ~VolunteerSpecialty.specialty_index.in_(specialty_indexes_to_keep)
                        ).delete(synchronize_session=False)
            
            db.session.commit()
                
            # 返回更新后的方案
            result_plan_id = new_plan.id if create_new_version else plan_id
            return VolunteerPlanService.get_volunteer_plan(result_plan_id)
                
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"更新志愿方案失败: {str(e)}")
            raise
        
    @staticmethod
    def create_empty_plan(student_id, planner_id, remarks, user_data_hash=None, 
                        generation_status='pending', generation_progress=0, 
                        generation_message=None,student_data_snapshot=None):
        """
        创建空的志愿方案
        
        :param student_id: 学生ID
        :param planner_id: 规划师ID
        :param remarks: 备注说明
        :param user_data_hash: 用户数据哈希
        :param generation_status: 生成状态
        :param generation_progress: 生成进度
        :param generation_message: 生成消息
        :return: 创建的志愿方案
        """
        try:
            # 获取最新版本号
            latest_plan = StudentVolunteerPlan.query.filter_by(
                student_id=student_id
            ).order_by(StudentVolunteerPlan.version.desc()).first()
            
            new_version = 1
            if latest_plan:
                new_version = latest_plan.version + 1
                
                # 将所有之前的方案设置为非当前版本
                db.session.query(StudentVolunteerPlan).filter(
                    StudentVolunteerPlan.student_id == student_id,
                    StudentVolunteerPlan.is_current == True
                ).update({"is_current": False}, synchronize_session=False)
            
            # 创建新的志愿方案
            plan = StudentVolunteerPlan(
                student_id=student_id,
                planner_id=planner_id,
                version=new_version,
                is_current=True,
                remarks=remarks,
                user_data_hash=user_data_hash,
                generation_status=generation_status,
                generation_progress=generation_progress,
                generation_message=generation_message or "开始生成志愿方案",
                student_data_snapshot=student_data_snapshot
            )
            
            db.session.add(plan)
            db.session.commit()
            
            return plan.to_dict()
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"创建空志愿方案失败: {str(e)}")
            raise

    @staticmethod
    def add_volunteer_college(plan_id, college_data):
        """
        向志愿方案添加院校志愿
        
        :param plan_id: 志愿方案ID
        :param college_data: 院校志愿数据
        :return: 添加的院校志愿
        """
        try:
            # 检查方案是否存在
            # plan = StudentVolunteerPlan.query.get_or_404(plan_id)
            
            # 检查是否已存在相同序号的志愿
            existing = VolunteerCollege.query.filter_by(
                plan_id=plan_id, 
                volunteer_index=college_data.get('volunteer_index')
            ).first()
            
            if existing:
                # 可选择更新或抛出错误
                for key, value in college_data.items():
                    if key != 'specialties' and hasattr(existing, key):
                        setattr(existing, key, value)
                db.session.commit()
                return existing.to_dict()
            
            # 创建新的院校志愿
            college = VolunteerCollege(
                plan_id=plan_id,
                category_id=college_data.get('category_id'),
                group_id=college_data.get('group_id'),
                volunteer_index=college_data.get('volunteer_index'),
                college_id=college_data.get('college_id'),
                college_name=college_data.get('college_name'),
                college_group_id=college_data.get('college_group_id'),
                score_diff=college_data.get('score_diff'),
                prediction_score=college_data.get('prediction_score'),
                recommend_type=college_data.get('recommend_type', VolunteerCollege.RECOMMEND_AI),
                ai_analysis=college_data.get('ai_analysis', ''),
                area_name=college_data.get('area_name'),
                group_name=college_data.get('group_name'),
                min_tuition=college_data.get('min_tuition'),
                max_tuition=college_data.get('max_tuition'),
                min_score=college_data.get('min_score'),
                plan_number=college_data.get('plan_number'),
                school_type_text=college_data.get('school_type_text'),
                subject_requirements=college_data.get('subject_requirements'),
                tese_text=college_data.get('tese_text'),
                teshu_text=college_data.get('teshu_text'),
                uncode=college_data.get('uncode'),
                nature=college_data.get('nature'),
            )
            
            db.session.add(college)
            db.session.commit()
            
            return college.to_dict()
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"添加院校志愿失败: {str(e)}")
            raise

    @staticmethod
    def add_volunteer_specialty(volunteer_college_id, specialty_data):
        """
        向院校志愿添加专业志愿
        
        :param volunteer_college_id: 院校志愿ID
        :param specialty_data: 专业志愿数据
        :return: 添加的专业志愿
        """
        try:
            # 检查院校志愿是否存在
            # college = VolunteerCollege.query.get_or_404(volunteer_college_id)
            
            # 检查是否已存在相同序号的专业
            existing = VolunteerSpecialty.query.filter_by(
                volunteer_college_id=volunteer_college_id, 
                specialty_index=specialty_data.get('specialty_index')
            ).first()
            
            if existing:
                # 可选择更新或抛出错误
                for key, value in specialty_data.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                db.session.commit()
                return existing.to_dict()
            
            # 创建新的专业志愿
            specialty = VolunteerSpecialty(
                volunteer_college_id=volunteer_college_id,
                specialty_id=specialty_data.get('specialty_id'),
                specialty_code=specialty_data.get('specialty_code'),
                specialty_name=specialty_data.get('specialty_name'),
                specialty_index=specialty_data.get('specialty_index'),
                prediction_score=specialty_data.get('prediction_score'),
                plan_number=specialty_data.get('plan_number'),
                tuition=specialty_data.get('tuition'),
                remarks=specialty_data.get('remarks', ''),
                ai_analysis=specialty_data.get('ai_analysis', ''),
                fenshuxian_id=specialty_data.get('fenshuxian_id')
            )
            
            db.session.add(specialty)
            db.session.commit()
            
            return specialty.to_dict()
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"添加专业志愿失败: {str(e)}")
            raise

    @staticmethod
    def batch_add_volunteer_colleges(plan_id, colleges_data):
        """
        批量添加院校志愿
        
        :param plan_id: 志愿方案ID
        :param colleges_data: 院校志愿数据列表
        :return: 批量添加结果
        """
        try:
            current_app.logger.info(f"批量添加院校志愿, {len(colleges_data)} 个院校")
            
            # 获取现有院校志愿的序号
            existing_indexes = {c.volunteer_index for c in 
                            VolunteerCollege.query.filter_by(plan_id=plan_id).all()}
            
            colleges_to_add = []
            colleges_to_update = []
            
            # 分类需要添加和更新的院校志愿
            for college_data in colleges_data:
                # 确保所有数值字段都为有效的整数
                volunteer_index = int(college_data.get('volunteer_index', 0) or 0)
                category_id = int(college_data.get('category_id', 0) or 0)
                group_id = int(college_data.get('group_id', 0) or 0)
                college_id = int(college_data.get('college_id', 0) or 0)
                college_group_id = int(college_data.get('college_group_id', 0) or 0)
                score_diff = int(college_data.get('score_diff', 0) or 0)
                prediction_score = int(college_data.get('prediction_score', 0) or 0)
                
                if volunteer_index in existing_indexes:
                    # 获取现有院校志愿进行更新
                    college = VolunteerCollege.query.filter_by(
                        plan_id=plan_id, 
                        volunteer_index=volunteer_index
                    ).first()
                    
                    # 更新字段
                    college.category_id = category_id
                    college.group_id = group_id
                    college.college_id = college_id
                    college.college_name = college_data.get('college_name', '')
                    college.college_group_id = college_group_id
                    college.score_diff = score_diff
                    college.prediction_score = prediction_score
                    college.recommend_type = college_data.get('recommend_type', VolunteerCollege.RECOMMEND_AI)
                    college.ai_analysis = college_data.get('ai_analysis', ''),
                    college.area_name=college_data.get('area_name'),
                    college.group_name=college_data.get('group_name'),
                    college.min_tuition=college_data.get('min_tuition'),
                    college.max_tuition=college_data.get('max_tuition'),
                    college.min_score=college_data.get('min_score'),
                    college.plan_number=college_data.get('plan_number'),
                    college.school_type_text=college_data.get('school_type_text'),
                    college.subject_requirements=college_data.get('subject_requirements'),
                    college.tese_text=college_data.get('tese_text'),
                    college.teshu_text=college_data.get('teshu_text'),
                    college.uncode=college_data.get('uncode'),
                    college.nature=college_data.get('nature'),
                    
                    colleges_to_update.append(college)
                else:
                    # 创建新的院校志愿
                    college = VolunteerCollege(
                        plan_id=plan_id,
                        category_id=category_id,
                        group_id=group_id,
                        volunteer_index=volunteer_index,
                        college_id=college_id,
                        college_name=college_data.get('college_name', ''),
                        college_group_id=college_group_id,
                        score_diff=score_diff,
                        prediction_score=prediction_score,
                        recommend_type=college_data.get('recommend_type', VolunteerCollege.RECOMMEND_AI),
                        ai_analysis=college_data.get('ai_analysis'),
                        area_name=college_data.get('area_name'),
                        group_name=college_data.get('group_name'),
                        min_tuition=college_data.get('min_tuition'),
                        max_tuition=college_data.get('max_tuition'),
                        min_score=college_data.get('min_score'),
                        plan_number=college_data.get('plan_number'),
                        school_type_text=college_data.get('school_type_text'),
                        subject_requirements=college_data.get('subject_requirements'),
                        tese_text=college_data.get('tese_text'),
                        teshu_text=college_data.get('teshu_text'),
                        uncode=college_data.get('uncode'),
                        nature=college_data.get('nature'),
                    )
                    colleges_to_add.append(college)
            
            # 批量添加新院校志愿
            if colleges_to_add:
                db.session.bulk_save_objects(colleges_to_add)
            
            # 批量更新现有院校志愿
            if colleges_to_update:
                for college in colleges_to_update:
                    db.session.add(college)
            
            db.session.commit()
            
            return {
                'plan_id': plan_id,
                'added_count': len(colleges_to_add),
                'updated_count': len(colleges_to_update),
                'total_count': len(colleges_to_add) + len(colleges_to_update)
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"批量添加院校志愿失败: {str(e)}")
            raise

    @staticmethod
    def batch_add_volunteer_specialties(volunteer_college_id, specialties_data):
        """
        批量添加专业志愿
        
        :param volunteer_college_id: 院校志愿ID
        :param specialties_data: 专业志愿数据列表
        :return: 批量添加结果
        """
        try:
            # 检查院校志愿是否存在
            # college = VolunteerCollege.query.get_or_404(volunteer_college_id)
            
            # 获取现有专业志愿的序号
            existing_indexes = {s.specialty_index for s in 
                              VolunteerSpecialty.query.filter_by(volunteer_college_id=volunteer_college_id).all()}
            
            specialties_to_add = []
            specialties_to_update = []
            
            # 分类需要添加和更新的专业志愿
            for specialty_data in specialties_data:
                index = specialty_data.get('specialty_index')
                if index in existing_indexes:
                    # 获取现有专业志愿进行更新
                    specialty = VolunteerSpecialty.query.filter_by(
                        volunteer_college_id=volunteer_college_id, 
                        specialty_index=index
                    ).first()
                    
                    for key, value in specialty_data.items():
                        if hasattr(specialty, key):
                            setattr(specialty, key, value)
                    
                    specialties_to_update.append(specialty)
                else:
                    # 创建新的专业志愿
                    specialty = VolunteerSpecialty(
                        volunteer_college_id=volunteer_college_id,
                        specialty_id=specialty_data.get('specialty_id'),
                        specialty_code=specialty_data.get('specialty_code'),
                        specialty_name=specialty_data.get('specialty_name'),
                        specialty_index=index,
                        prediction_score=specialty_data.get('prediction_score'),
                        plan_number=specialty_data.get('plan_number'),
                        tuition=specialty_data.get('tuition'),
                        remarks=specialty_data.get('remarks', ''),
                        ai_analysis=specialty_data.get('ai_analysis', ''),
                        fenshuxian_id=specialty_data.get('fenshuxian_id')
                    )
                    specialties_to_add.append(specialty)
            
            # 批量添加新专业志愿
            if specialties_to_add:
                db.session.bulk_save_objects(specialties_to_add)
            
            # 批量更新现有专业志愿
            if specialties_to_update:
                for specialty in specialties_to_update:
                    db.session.add(specialty)
            
            db.session.commit()
            
            return {
                'volunteer_college_id': volunteer_college_id,
                'added_count': len(specialties_to_add),
                'updated_count': len(specialties_to_update),
                'total_count': len(specialties_to_add) + len(specialties_to_update)
            }
            
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"批量添加专业志愿失败: {str(e)}")
            raise
        

def ai_select_college_ids(filtered_colleges, user_info, recommendation_data, is_first=False):
    """
    AI选择院校ID，基于学生成绩类型选择不同的推荐策略
    
    :param filtered_colleges: 筛选出的院校列表(包含简化数据)
    :param user_info: 用户信息文本
    :param recommendation_data: 学生推荐数据，包含各类成绩信息
    :return: 选择的院校ID列表
    """
    try:
        # 检查学生是否有高考成绩
        has_gaokao_score = recommendation_data.get('student_score', 0) > 0
        
        # 检查学生是否有模考成绩
        latest_mock_score = recommendation_data.get('mock_exam_score', 0) > 0
        if is_first:
            return fallback_recommendation(filtered_colleges)

        # 基于成绩类型选择推荐策略
        if has_gaokao_score:
            # 有高考成绩且不是第一次生成方案，使用AI推荐
            current_app.logger.info("学生有高考成绩，使用AI推荐")
            return ai_recommend_with_score(filtered_colleges, user_info)
        elif latest_mock_score:
            # 有模考成绩，使用模考成绩推荐
            current_app.logger.info(f"学生使用最新模考成绩 {latest_mock_score} 进行推荐")
            return fallback_recommendation(filtered_colleges)
        else:
            # 没有任何成绩，使用备选方案
            current_app.logger.info("学生没有可用成绩，使用备选推荐方案")
            return fallback_recommendation(filtered_colleges)
        
    except Exception as e:
        # 任何错误时使用备选方案
        current_app.logger.error(f"AI选择院校ID过程中发生错误: {str(e)}")
        return fallback_recommendation(filtered_colleges)

def ai_recommend_with_score(filtered_colleges, user_info):
    """使用AI基于高考成绩推荐院校"""
    # 这里是原来的AI推荐逻辑
    simplified_colleges = []
    for college in filtered_colleges:
        simplified_colleges.append({
            'cgid': college['cgid'],  # 院校专业组ID
            'name': college['cname'],  # 院校名称
            'city': college['area_name'],  # 城市
            'tese': college['tese_text'],  # 院校特色
            'specialties': [
                {
                    "spname": specialty["spname"],
                    "tuition": specialty["tuition"],
                    "spid": specialty["spid"]
                }
                for specialty in college['specialties']
            ]
        })
    
    simplified_colleges_json = json.dumps(simplified_colleges, ensure_ascii=False)
    # 调用AI服务并解析结果
    ai_res_json = MoonshotAI.filter_colleges(user_info, simplified_colleges_json)
    ai_res_dict = json.loads(ai_res_json)
    
    # 验证AI返回结果是否符合要求（最多4个学校）
    if len(ai_res_dict) > 4:
        # 只保留前4个学校
        ai_res_dict = {k: ai_res_dict[k] for k in list(ai_res_dict.keys())[:4]}
    
    # 验证每个学校的专业是否符合要求（最多6个专业）
    for cgid, spids in ai_res_dict.items():
        if len(spids) > 6:
            ai_res_dict[cgid] = spids[:6]
    
    return ai_res_dict

def fallback_recommendation(filtered_colleges):
    """备选推荐方案"""
    # 准备备选方案（前4个学校，每个学校前6个专业）
    fallback_result = {}
    for college in filtered_colleges[:4]:
        cgid = str(college['cgid'])
        specialties = college['specialties'][:6]
        if specialties:
            fallback_result[cgid] = [str(s['spid']) for s in specialties]
    
    return fallback_result
    
def process_batch(student_id, planner_id, category_id, group_id, plan_id=None, is_first=False):
    """
    处理一个批次的志愿
    
    :param student_id: 学生ID
    :param planner_id: 规划师ID
    :param category_id: 类别ID(1:冲, 2:稳, 3:保)
    :param group_id: 组内ID(1-4)
    :param plan_id: 志愿方案ID，如果已有
    :return: 更新后的志愿方案ID和批次处理状态
    """
    
    try:
        # 计算实际的group_id（1-12）
        actual_group_id = (category_id - 1) * 4 + group_id

        current_app.logger.info(f"=====类别ID={category_id}, 分组ID={actual_group_id}, 方案ID={plan_id}=====")
        # 使用StudentDataService获取学生数据
        recommendation_data = StudentDataService.extract_college_recommendation_data(student_id)
        # 获取学生的文本信息
        user_info = StudentDataService.generate_student_profile_text(student_id)

        student_score = int(recommendation_data['student_score'] or 0)
        subject_type = int(recommendation_data['subject_type'] or 1)
        education_level = int(recommendation_data['education_level'] or 11)
        student_subjects = recommendation_data['student_subjects']
        area_ids = recommendation_data.get('area_ids', [])
        specialty_types = recommendation_data.get('specialty_types', [])
        tuition_ranges = recommendation_data.get('tuition_ranges', [])
        mock_exam_score = int(recommendation_data['mock_exam_score'] or 0)

        # 确保area_ids和specialty_types是可迭代的且包含有效整数
        area_ids = [int(aid) for aid in area_ids if aid and str(aid).isdigit()]
        specialty_types = [int(st) for st in specialty_types if st and str(st).isdigit()]
        
        # 1. 获取筛选结果
        filtered_colleges, _ = RecommendationService.get_colleges_by_category_and_group(
            student_score=student_score > 0 and student_score or mock_exam_score,
            subject_type=subject_type,
            education_level=education_level,
            category_id=category_id,
            group_id=actual_group_id,
            student_subjects=student_subjects,
            area_ids=area_ids,
            specialty_types=specialty_types,
            tuition_ranges=tuition_ranges,
            page=1,
            per_page=100  # 获取足够多的结果供AI选择
        )
        
        current_app.logger.info(f"筛选到的院校数量: {len(filtered_colleges)}")
        
        # 如果没有筛选到院校，直接返回
        if not filtered_colleges:
            return plan_id, False
        
        # 2. 让AI选择院校及专业，并返回对应ID
        ai_selection = ai_select_college_ids(filtered_colleges, user_info, recommendation_data, is_first=is_first)

        # 如果AI没有选择结果，直接返回
        if not ai_selection:
            return plan_id, False

        # 3. 根据AI选择结果构建完整的院校志愿数据
        colleges_data = []
        for idx, (cgid, selected_spids) in enumerate(ai_selection.items()):
            # 将字符串类型的cgid转换为整数
            cgid = int(cgid) if isinstance(cgid, str) and cgid.isdigit() else (cgid if isinstance(cgid, int) else 0)
            if cgid == 0:
                continue
                
            # 查找对应的完整院校数据
            college_data = next((c for c in filtered_colleges if c['cgid'] == cgid), None)
            if not college_data:
                continue
                
            # 计算在整个方案中的序号（1-48）
            volunteer_index = (actual_group_id - 1) * 4 + idx + 1
            
            # 构建院校志愿数据
            college_volunteer = {
                'category_id': category_id,
                'group_id': actual_group_id,
                'volunteer_index': volunteer_index,
                'college_id': college_data['cid'],
                'college_name': college_data['cname'],
                'college_group_id': college_data['cgid'],
                'score_diff': college_data['score_diff'],
                'prediction_score': college_data['min_score'],
                'recommend_type': 'ai',
                'specialties': [],
                'area_name': college_data['area_name'],
                'group_name': college_data['group_name'],
                'min_tuition': college_data['min_tuition'],
                'max_tuition': college_data['max_tuition'],
                'min_score': college_data['min_score'],
                'plan_number': college_data['plan_number'],
                'school_type_text': college_data['school_type_text'],
                'subject_requirements': college_data['subject_requirements'],
                'tese_text': college_data['tese_text'],
                'teshu_text': college_data['teshu_text'],
                'uncode': college_data['uncode'],
                'nature': college_data['school_nature'],  
            }
            
            # 处理专业ID列表
            valid_spids = []
            for spid in selected_spids:
                # 确保spid是有效的整数
                if isinstance(spid, str) and spid.isdigit():
                    valid_spids.append(int(spid))
                elif isinstance(spid, int):
                    valid_spids.append(spid)
            
            # 只添加AI选中的专业数据
            selected_spids_set = set(valid_spids)
            sp_idx = 0
            for specialty in college_data['specialties']:
                if sp_idx >= 6:  # 最多添加6个专业
                    break
                    
                specialty_id = specialty.get('spid', 0)
                if specialty_id in selected_spids_set:
                    # 添加专业数据
                    specialty_data = {
                        'specialty_id': specialty_id,
                        'specialty_code': specialty.get('spcode', ''),
                        'specialty_name': specialty.get('spname', ''),
                        'specialty_index': sp_idx + 1,  # 专业序号从1开始
                        'prediction_score': int(specialty.get('prediction_score', 0) or 0),
                        'plan_number': int(specialty.get('plan_number', 0) or 0),
                        'tuition': int(specialty.get('tuition', 0) or 0),
                        'fenshuxian_id': int(specialty.get('id', 0) or 0)
                    }
                    college_volunteer['specialties'].append(specialty_data)
                    sp_idx += 1
                
            colleges_data.append(college_volunteer)

        # 4. 更新志愿方案
        if not plan_id:
            # 如果没有方案ID，创建新方案
            plan = VolunteerPlanService.create_empty_plan(
                student_id=student_id,
                planner_id=planner_id,
                remarks="AI生成的志愿方案"
            )
            plan_id = plan['id']

        # 批量添加院校志愿和专业
        if colleges_data:
            # 添加院校志愿
            college_result = VolunteerPlanService.batch_add_volunteer_colleges(plan_id, colleges_data)
            
            # 查询刚添加的院校志愿，获取它们的ID
            added_colleges = VolunteerCollege.query.filter_by(plan_id=plan_id).all()
            college_id_map = {college.volunteer_index: college.id for college in added_colleges}
            
            # 为每个院校添加专业志愿
            for college_data in colleges_data:
                volunteer_index = college_data['volunteer_index']
                if volunteer_index in college_id_map:
                    college_id = college_id_map[volunteer_index]
                    specialties_data = college_data.get('specialties', [])
                    if specialties_data:
                        VolunteerPlanService.batch_add_volunteer_specialties(college_id, specialties_data)
            
        return plan_id, bool(colleges_data)  # 返回方案ID和成功状态
        
    except Exception as e:
        current_app.logger.error(f"处理批次志愿失败: {str(e)}")
        # 重新抛出异常或返回失败状态
        return plan_id, False
    
def generate_complete_volunteer_plan(student_id, planner_id, user_data_hash, is_first=False):
    """
    生成完整的志愿方案(包含进度跟踪)
    
    :param student_id: 学生ID
    :param planner_id: 规划师ID
    :return: 生成的志愿方案
    """
    # 获取学生数据快照
    student_snapshot = StudentDataService.generate_student_data_snapshot(student_id)
    current_snapshot = json.dumps(student_snapshot, ensure_ascii=False)

    # 查找之前的方案
    previous_plan = StudentVolunteerPlan.query.filter_by(
        student_id=student_id,
        is_current=True,
        generation_status=StudentVolunteerPlan.GENERATION_STATUS_SUCCESS
    ).order_by(StudentVolunteerPlan.version.desc()).first()
    previous_snapshot = json.dumps(previous_plan.student_data_snapshot, ensure_ascii=False) if previous_plan else None

    # 创建空方案并设置所有初始状态
    plan = VolunteerPlanService.create_empty_plan(
        student_id=student_id,
        planner_id=planner_id,
        remarks="AI生成的志愿方案",
        user_data_hash=user_data_hash,
        generation_status=StudentVolunteerPlan.GENERATION_STATUS_PROCESSING,
        generation_progress=0,
        generation_message="开始生成志愿方案",
        student_data_snapshot=current_snapshot
    )
    plan_id = plan['id']

    from app.tasks.volunteer_tasks import analyze_student_snapshots_ai
    analyze_student_snapshots_ai.delay(plan_id, current_snapshot, previous_snapshot)

    try:
        # 处理所有批次
        batch_count = 12
        processed_count = 0
        
        # 遍历所有类别和组
        for category_id in [1,2,3]:  # 冲、稳、保
            for group_id in range(1, 5):  # 每类4个小组(1-4)
                # 处理一个批次
                plan_id, success = process_batch(
                    student_id=student_id,
                    planner_id=planner_id,
                    category_id=category_id,
                    group_id=group_id,
                    plan_id=plan_id,
                    is_first=is_first
                )
                
                # 更新进度
                processed_count += 1
                progress = int((processed_count / batch_count) * 100)
                
                # 更新方案状态
                StudentVolunteerPlan.query.filter_by(id=plan_id).update({
                    'generation_progress': progress,
                    'generation_message': f"已处理{processed_count}/{batch_count}个批次"
                })
                db.session.commit()
        
        # 全部处理完成，更新状态
        StudentVolunteerPlan.query.filter_by(id=plan_id).update({
            'generation_status': StudentVolunteerPlan.GENERATION_STATUS_SUCCESS,
            'generation_progress': 100,
            'generation_message': "志愿方案生成完成"
        })
        db.session.commit()
        
        # 返回完整方案
        return VolunteerPlanService.get_volunteer_plan(plan_id)
        
    except Exception as e:
        # 发生错误，更新状态
        StudentVolunteerPlan.query.filter_by(id=plan_id).update({
            'generation_status': StudentVolunteerPlan.GENERATION_STATUS_FAILED,
            'generation_message': f"生成失败: {str(e)}"
        })
        db.session.commit()
        raise