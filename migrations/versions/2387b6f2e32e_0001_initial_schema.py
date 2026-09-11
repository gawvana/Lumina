"""0001_initial_schema

Revision ID: 2387b6f2e32e
Revises: 
Create Date: 2026-09-11 18:30:08.114308

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '2387b6f2e32e'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. schools
    op.create_table(
        'schools',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('settings', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_schools_code', 'schools', ['code'], unique=True)

    # 2. feature_flags
    op.create_table(
        'feature_flags',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('school_id', sa.String(length=36), sa.ForeignKey('schools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('flag_name', sa.String(length=100), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('config', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('school_id', 'flag_name', name='uq_school_feature_flag'),
    )
    op.create_index('ix_feature_flags_school_id', 'feature_flags', ['school_id'])

    # 3. grading_systems
    op.create_table(
        'grading_systems',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('school_id', sa.String(length=36), sa.ForeignKey('schools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('system_type', sa.String(length=30), nullable=False),
        sa.Column('config', sa.JSON(), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_grading_systems_school_id', 'grading_systems', ['school_id'])

    # 4. grade_types
    op.create_table(
        'grade_types',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('school_id', sa.String(length=36), sa.ForeignKey('schools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('code', sa.String(length=30), nullable=False),
        sa.Column('weight', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_grade_types_school_id', 'grade_types', ['school_id'])

    # 5. classes
    op.create_table(
        'classes',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('school_id', sa.String(length=36), sa.ForeignKey('schools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('grade_level', sa.Integer(), nullable=False),
        sa.Column('academic_year', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_classes_school_id', 'classes', ['school_id'])

    # 6. subjects
    op.create_table(
        'subjects',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('school_id', sa.String(length=36), sa.ForeignKey('schools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('code', sa.String(length=30), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_subjects_school_id', 'subjects', ['school_id'])

    # 7. users
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('school_id', sa.String(length=36), sa.ForeignKey('schools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('username', sa.String(length=100), nullable=True),
        sa.Column('language_code', sa.String(length=10), nullable=False, server_default='ru'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_users_school_id', 'users', ['school_id'])
    op.create_index('ix_users_telegram_id', 'users', ['telegram_id'], unique=True)

    # 8. teachers
    op.create_table(
        'teachers',
        sa.Column('id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('bio', sa.String(length=500), nullable=True),
        sa.Column('title', sa.String(length=100), nullable=True),
    )

    # 9. students
    op.create_table(
        'students',
        sa.Column('id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('class_id', sa.String(length=36), sa.ForeignKey('classes.id', ondelete='SET NULL'), nullable=True),
        sa.Column('student_number', sa.String(length=50), nullable=True),
        sa.Column('xp', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('level', sa.Integer(), nullable=False, server_default='1'),
    )
    op.create_index('ix_students_class_id', 'students', ['class_id'])

    # 10. parents
    op.create_table(
        'parents',
        sa.Column('id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('phone_number', sa.String(length=30), nullable=True),
    )

    # 11. student_parents
    op.create_table(
        'student_parents',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('student_id', sa.String(length=36), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False),
        sa.Column('parent_id', sa.String(length=36), sa.ForeignKey('parents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('relationship_type', sa.String(length=50), nullable=False, server_default='guardian'),
        sa.Column('is_confirmed', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('student_id', 'parent_id', name='uq_student_parent'),
    )
    op.create_index('ix_student_parents_student_id', 'student_parents', ['student_id'])
    op.create_index('ix_student_parents_parent_id', 'student_parents', ['parent_id'])

    # 12. teacher_subject_classes
    op.create_table(
        'teacher_subject_classes',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('teacher_id', sa.String(length=36), sa.ForeignKey('teachers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('subject_id', sa.String(length=36), sa.ForeignKey('subjects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('class_id', sa.String(length=36), sa.ForeignKey('classes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('teacher_id', 'subject_id', 'class_id', name='uq_teacher_subject_class'),
    )
    op.create_index('ix_tsc_teacher_id', 'teacher_subject_classes', ['teacher_id'])
    op.create_index('ix_tsc_subject_id', 'teacher_subject_classes', ['subject_id'])
    op.create_index('ix_tsc_class_id', 'teacher_subject_classes', ['class_id'])

    # 13. lessons
    op.create_table(
        'lessons',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('class_id', sa.String(length=36), sa.ForeignKey('classes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('subject_id', sa.String(length=36), sa.ForeignKey('subjects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('teacher_id', sa.String(length=36), sa.ForeignKey('teachers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('lesson_date', sa.Date(), nullable=False),
        sa.Column('period_number', sa.Integer(), nullable=False),
        sa.Column('topic', sa.String(length=255), nullable=True),
        sa.Column('room', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='SCHEDULED'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_lessons_class_id', 'lessons', ['class_id'])
    op.create_index('ix_lessons_subject_id', 'lessons', ['subject_id'])
    op.create_index('ix_lessons_teacher_id', 'lessons', ['teacher_id'])
    op.create_index('ix_lessons_lesson_date', 'lessons', ['lesson_date'])
    op.create_index('ix_lessons_class_date', 'lessons', ['class_id', 'lesson_date'])

    # 14. grades
    op.create_table(
        'grades',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('school_id', sa.String(length=36), sa.ForeignKey('schools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_id', sa.String(length=36), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False),
        sa.Column('teacher_id', sa.String(length=36), sa.ForeignKey('teachers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('lesson_id', sa.String(length=36), sa.ForeignKey('lessons.id', ondelete='CASCADE'), nullable=False),
        sa.Column('subject_id', sa.String(length=36), sa.ForeignKey('subjects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('grade_type_id', sa.String(length=36), sa.ForeignKey('grade_types.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('raw_display', sa.String(length=20), nullable=False),
        sa.Column('weight', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('comment', sa.String(length=500), nullable=True),
        sa.Column('source', sa.String(length=20), nullable=False, server_default='MANUAL'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('is_retake', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('original_grade_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_grades_school_id', 'grades', ['school_id'])
    op.create_index('ix_grades_student_id', 'grades', ['student_id'])
    op.create_index('ix_grades_teacher_id', 'grades', ['teacher_id'])
    op.create_index('ix_grades_lesson_id', 'grades', ['lesson_id'])
    op.create_index('ix_grades_student_active', 'grades', ['student_id', 'is_active'])

    # 15. homework
    op.create_table(
        'homework',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('class_id', sa.String(length=36), sa.ForeignKey('classes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('subject_id', sa.String(length=36), sa.ForeignKey('subjects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('teacher_id', sa.String(length=36), sa.ForeignKey('teachers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('lesson_id', sa.String(length=36), sa.ForeignKey('lessons.id', ondelete='SET NULL'), nullable=True),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_homework_class_id', 'homework', ['class_id'])
    op.create_index('ix_homework_subject_id', 'homework', ['subject_id'])
    op.create_index('ix_homework_teacher_id', 'homework', ['teacher_id'])
    op.create_index('ix_homework_due_date', 'homework', ['due_date'])
    op.create_index('ix_homework_class_due', 'homework', ['class_id', 'due_date'])

    # 16. homework_submissions
    op.create_table(
        'homework_submissions',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('homework_id', sa.String(length=36), sa.ForeignKey('homework.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_id', sa.String(length=36), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='TODO'),
        sa.Column('submitted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('homework_id', 'student_id', name='uq_homework_student'),
    )
    op.create_index('ix_homework_submissions_homework_id', 'homework_submissions', ['homework_id'])
    op.create_index('ix_homework_submissions_student_id', 'homework_submissions', ['student_id'])

    # 17. parent_absence_notes
    op.create_table(
        'parent_absence_notes',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('student_id', sa.String(length=36), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False),
        sa.Column('parent_id', sa.String(length=36), sa.ForeignKey('parents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('date_from', sa.Date(), nullable=False),
        sa.Column('date_to', sa.Date(), nullable=False),
        sa.Column('reason', sa.String(length=500), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='PENDING'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_parent_absence_notes_student_id', 'parent_absence_notes', ['student_id'])
    op.create_index('ix_parent_absence_notes_parent_id', 'parent_absence_notes', ['parent_id'])

    # 18. attendance
    op.create_table(
        'attendance',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('student_id', sa.String(length=36), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False),
        sa.Column('lesson_id', sa.String(length=36), sa.ForeignKey('lessons.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='PRESENT'),
        sa.Column('note', sa.String(length=255), nullable=True),
        sa.Column('parent_note_id', sa.String(length=36), sa.ForeignKey('parent_absence_notes.id', ondelete='SET NULL'), nullable=True),
        sa.Column('recorded_by_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('recorded_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('student_id', 'lesson_id', name='uq_student_lesson_attendance'),
    )
    op.create_index('ix_attendance_student_id', 'attendance', ['student_id'])
    op.create_index('ix_attendance_lesson_id', 'attendance', ['lesson_id'])

    # 19. invites
    op.create_table(
        'invites',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('school_id', sa.String(length=36), sa.ForeignKey('schools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token', sa.String(length=64), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False, server_default='STUDENT'),
        sa.Column('target_class_id', sa.String(length=36), sa.ForeignKey('classes.id', ondelete='SET NULL'), nullable=True),
        sa.Column('target_student_id', sa.String(length=36), sa.ForeignKey('students.id', ondelete='SET NULL'), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('max_uses', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('current_uses', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_by_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_invites_school_id', 'invites', ['school_id'])
    op.create_index('ix_invites_token', 'invites', ['token'], unique=True)

    # 20. audit_logs
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('school_id', sa.String(length=36), sa.ForeignKey('schools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.String(length=36), nullable=False),
        sa.Column('action', sa.String(length=20), nullable=False),
        sa.Column('old_values', sa.JSON(), nullable=True),
        sa.Column('new_values', sa.JSON(), nullable=True),
        sa.Column('reason', sa.String(length=255), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_audit_logs_school_id', 'audit_logs', ['school_id'])
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('ix_audit_logs_entity_type', 'audit_logs', ['entity_type'])
    op.create_index('ix_audit_logs_entity_id', 'audit_logs', ['entity_id'])
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'])
    op.create_index('ix_audit_school_created', 'audit_logs', ['school_id', 'created_at'])


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('invites')
    op.drop_table('attendance')
    op.drop_table('parent_absence_notes')
    op.drop_table('homework_submissions')
    op.drop_table('homework')
    op.drop_table('grades')
    op.drop_table('lessons')
    op.drop_table('teacher_subject_classes')
    op.drop_table('student_parents')
    op.drop_table('parents')
    op.drop_table('students')
    op.drop_table('teachers')
    op.drop_table('users')
    op.drop_table('subjects')
    op.drop_table('classes')
    op.drop_table('grade_types')
    op.drop_table('grading_systems')
    op.drop_table('feature_flags')
    op.drop_table('schools')
