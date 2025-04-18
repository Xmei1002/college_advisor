"""修改志愿序号为字符

Revision ID: 76765d186b8d
Revises: bd39e4b0253e
Create Date: 2025-04-11 09:32:48.673699

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '76765d186b8d'
down_revision = 'bd39e4b0253e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('volunteer_colleges', schema=None) as batch_op:
        batch_op.alter_column('volunteer_index',
               existing_type=mysql.INTEGER(),
               type_=sa.String(length=20),
               existing_comment='志愿在方案中的序号(1-48)',
               existing_nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('volunteer_colleges', schema=None) as batch_op:
        batch_op.alter_column('volunteer_index',
               existing_type=sa.String(length=20),
               type_=mysql.INTEGER(),
               existing_comment='志愿在方案中的序号(1-48)',
               existing_nullable=False)

    # ### end Alembic commands ###
