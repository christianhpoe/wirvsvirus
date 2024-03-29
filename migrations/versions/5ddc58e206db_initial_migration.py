"""Initial migration.

Revision ID: 5ddc58e206db
Revises: 
Create Date: 2020-03-22 16:44:05.065703

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5ddc58e206db'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=120), nullable=True),
    sa.Column('email', sa.String(length=120), nullable=True),
    sa.Column('password_hash', sa.String(length=128), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_email'), 'user', ['email'], unique=True)
    op.create_index(op.f('ix_user_username'), 'user', ['username'], unique=False)
    op.create_table('page',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('creator_id', sa.Integer(), nullable=True),
    sa.Column('artist_name', sa.String(), nullable=True),
    sa.Column('artist_category', sa.String(), nullable=True),
    sa.Column('artist_job', sa.String(), nullable=True),
    sa.Column('artist_location_lat', sa.Float(), nullable=True),
    sa.Column('artist_location_long', sa.Float(), nullable=True),
    sa.Column('description_title', sa.String(), nullable=True),
    sa.Column('description_general', sa.String(), nullable=True),
    sa.Column('description_crisis', sa.String(), nullable=True),
    sa.Column('description_rewards', sa.String(), nullable=True),
    sa.Column('titlepicture_path', sa.String(), nullable=True),
    sa.Column('media_path', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['creator_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('reward',
    sa.Column('Page_Id', sa.Integer(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(), nullable=True),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('category_form', sa.String(), nullable=True),
    sa.Column('category_time', sa.String(), nullable=True),
    sa.Column('price', sa.Float(), nullable=True),
    sa.Column('primary', sa.Boolean(), nullable=True),
    sa.Column('active', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['Page_Id'], ['page.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('reward')
    op.drop_table('page')
    op.drop_index(op.f('ix_user_username'), table_name='user')
    op.drop_index(op.f('ix_user_email'), table_name='user')
    op.drop_table('user')
    # ### end Alembic commands ###
