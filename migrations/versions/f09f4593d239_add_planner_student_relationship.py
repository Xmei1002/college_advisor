"""Add planner-student relationship

Revision ID: f09f4593d239
Revises: b4f11439bce3
Create Date: 2025-03-27 15:28:44.045679

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f09f4593d239'
down_revision = 'b4f11439bce3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('career_preferences',
    sa.Column('student_id', sa.Integer(), nullable=False),
    sa.Column('career_direction', sa.String(length=50), nullable=True, comment='就业发展方向，如金融,教师,医生等'),
    sa.Column('academic_preference', sa.String(length=100), nullable=True, comment='学术学位偏好，如985,211等'),
    sa.Column('civil_service_preference', sa.String(length=100), nullable=True, comment='公务员意向'),
    sa.Column('employment_location', sa.String(length=100), nullable=True, comment='就业地区'),
    sa.Column('income_expectation', sa.String(length=100), nullable=True, comment='职业稳定性与收入平衡'),
    sa.Column('work_stability', sa.String(length=100), nullable=True, comment='工作稳定性'),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['student_id'], ['students.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('student_id')
    )
    op.create_table('college_preferences',
    sa.Column('student_id', sa.Integer(), nullable=False),
    sa.Column('preferred_locations', sa.String(length=500), nullable=True, comment='意向地域，多个地区以逗号分隔'),
    sa.Column('tuition_range', sa.String(length=50), nullable=True, comment='学费范围，如"1万以内"、"1-2万"等'),
    sa.Column('preferred_majors', sa.String(length=1000), nullable=True, comment='意向专业，多个专业以逗号分隔'),
    sa.Column('school_types', sa.String(length=100), nullable=True, comment='学校类型，如985,211,双一流等'),
    sa.Column('preferred_schools', sa.String(length=1000), nullable=True, comment='意向学校，多个学校以逗号分隔'),
    sa.Column('strategy', sa.String(length=20), nullable=True, comment='填报策略：院校优先 or 专业优先'),
    sa.Column('application_preference', sa.Text(), nullable=True, comment='报考倾向：家庭背景资源、意向院校以及专业等情况的详细描述'),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['student_id'], ['students.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('student_id')
    )
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('planner_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'users', ['planner_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('planner_id')

    op.drop_table('college_preferences')
    op.drop_table('career_preferences')
    # ### end Alembic commands ###
