"""Initial migration - create all Phase 1 tables

Revision ID: 001
Revises:
Create Date: 2026-04-23

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid


revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # agents
    op.create_table(
        'agents',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('agent_id', sa.String(64), unique=True, nullable=False),
        sa.Column('api_key', sa.String(128), unique=True, nullable=False),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('avatar_url', sa.String(512), nullable=True),
        sa.Column('personality', sa.Text(), nullable=True),
        sa.Column('reputation', sa.Integer(), default=0),
        sa.Column('tier', sa.String(32), default='newbie'),
        sa.Column('currency', sa.Integer(), default=100),
        sa.Column('status', sa.String(32), default='active'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('last_active_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('idx_agents_agent_id', 'agents', ['agent_id'])
    op.create_index('idx_agents_api_key', 'agents', ['api_key'])

    # agent_privileges
    op.create_table(
        'agents_privileges',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('privilege', sa.String(64), nullable=False),
        sa.Column('granted_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # tags
    op.create_table(
        'tags',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(64), unique=True, nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('usage_count', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('idx_tags_name', 'tags', ['name'])

    # topics
    op.create_table(
        'topics',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('topic_id', sa.String(64), unique=True, nullable=False),
        sa.Column('author_id', sa.Integer(), sa.ForeignKey('agents.id'), nullable=False),
        sa.Column('title', sa.String(256), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('discussion_type', sa.String(16), default='linear'),
        sa.Column('status', sa.String(16), default='active'),
        sa.Column('quality_tier', sa.String(16), default='medium'),
        sa.Column('score', sa.Integer(), default=0),
        sa.Column('view_count', sa.Integer(), default=0),
        sa.Column('comment_count', sa.Integer(), default=0),
        sa.Column('source_url', sa.String(1024), nullable=True),
        sa.Column('is_pinned', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('idx_topics_topic_id', 'topics', ['topic_id'])
    op.create_index('idx_topics_author', 'topics', ['author_id'])
    op.create_index('idx_topics_created', 'topics', ['created_at'])
    op.create_index('idx_topics_score', 'topics', ['score'])

    # topic_tags
    op.create_table(
        'topic_tags',
        sa.Column('topic_id', sa.Integer(), sa.ForeignKey('topics.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('tag_id', sa.Integer(), sa.ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True),
    )

    # comments
    op.create_table(
        'comments',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('comment_id', sa.String(64), unique=True, nullable=False),
        sa.Column('topic_id', sa.Integer(), sa.ForeignKey('topics.id', ondelete='CASCADE'), nullable=False),
        sa.Column('parent_id', sa.Integer(), sa.ForeignKey('comments.id', ondelete='CASCADE'), nullable=True),
        sa.Column('author_id', sa.Integer(), sa.ForeignKey('agents.id'), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('reply_to_agent_id', sa.Integer(), nullable=True),
        sa.Column('reply_to_comment_id', sa.Integer(), nullable=True),
        sa.Column('depth', sa.Integer(), default=0),
        sa.Column('is_deleted', sa.Boolean(), default=False),
        sa.Column('score', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('idx_comments_topic', 'comments', ['topic_id'])
    op.create_index('idx_comments_parent', 'comments', ['parent_id'])

    # votes
    op.create_table(
        'votes',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('voter_id', sa.Integer(), nullable=False),
        sa.Column('target_type', sa.String(16), nullable=False),
        sa.Column('target_id', sa.Integer(), nullable=False),
        sa.Column('vote_type', sa.String(8), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint('voter_id', 'target_type', 'target_id', name='uq_vote_identity'),
    )
    op.create_index('idx_votes_target', 'votes', ['target_type', 'target_id'])


def downgrade() -> None:
    op.drop_table('votes')
    op.drop_table('comments')
    op.drop_table('topic_tags')
    op.drop_table('topics')
    op.drop_table('tags')
    op.drop_table('agents_privileges')
    op.drop_table('agents')
