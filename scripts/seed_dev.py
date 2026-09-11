"""Deterministic development database seeder for Lumina Telegram School OS."""

import asyncio
import os
import sys
from pathlib import Path

# Ensure workspace root is in sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date, datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import (
    Base,
    Class,
    FeatureFlag,
    Grade,
    GradeType,
    GradingSystem,
    Homework,
    HomeworkSubmission,
    Attendance,
    Lesson,
    Parent,
    School,
    Student,
    StudentParent,
    Subject,
    Teacher,
    TeacherSubjectClass,
    User,
)
from db.session import AsyncSessionLocal, engine
from shared.config import settings
from shared.enums import (
    AttendanceStatus,
    GradeSource,
    GradingSystemType,
    HomeworkStatus,
    LessonStatus,
    UserRole,
)


async def seed_database():
    """Populates the database with realistic, deterministic development and testing data."""
    print("Seeding development database...")
    async with AsyncSessionLocal() as db:
        # Check if already seeded
        existing_school = await db.execute(select(School).limit(1))
        if existing_school.scalars().first():
            print("Database already seeded. Skipping.")
            return

        # 1. Create School
        school = School(
            name="Lumina Demonstration School #1",
            code="LUMINA-01",
            settings={"country": "UZ", "timezone": settings.DEFAULT_TIMEZONE},
            is_active=True,
        )
        db.add(school)
        await db.flush()

        # 2. Feature Flags (Default all OFF)
        flags = FeatureFlag.get_default_flags(school.id)
        for f in flags:
            db.add(f)

        # 3. Grading System (5-point)
        gs = GradingSystem(
            school_id=school.id,
            name="5-балльная система",
            system_type=GradingSystemType.POINTS_5.value,
            config={"min": 1, "max": 5, "passing": 3},
            is_default=True,
        )
        db.add(gs)
        await db.flush()

        # 4. Grade Types
        gt_oral = GradeType(school_id=school.id, name="Ответ на уроке", code="ORAL", weight=1.0)
        gt_quiz = GradeType(school_id=school.id, name="Самостоятельная работа", code="QUIZ", weight=1.5)
        gt_test = GradeType(school_id=school.id, name="Контрольная работа", code="TEST", weight=2.0)
        gt_hw = GradeType(school_id=school.id, name="Домашняя работа", code="HOMEWORK", weight=1.0)
        db.add_all([gt_oral, gt_quiz, gt_test, gt_hw])
        await db.flush()

        # 5. Classes
        class_7a = Class(school_id=school.id, name="7-А", grade_level=7, academic_year="2026-2027")
        class_8b = Class(school_id=school.id, name="8-Б", grade_level=8, academic_year="2026-2027")
        db.add_all([class_7a, class_8b])
        await db.flush()

        # 6. Subjects
        sub_alg = Subject(school_id=school.id, name="Алгебра", code="ALG")
        sub_eng = Subject(school_id=school.id, name="Английский язык", code="ENG")
        sub_hist = Subject(school_id=school.id, name="История", code="HIST")
        sub_phys = Subject(school_id=school.id, name="Физика", code="PHYS")
        db.add_all([sub_alg, sub_eng, sub_hist, sub_phys])
        await db.flush()

        # 7. Admin User
        u_admin = User(
            school_id=school.id,
            telegram_id=1001,
            role=UserRole.ADMIN.value,
            first_name="Азиз",
            last_name="Рахимов",
            username="admin_aziz",
            language_code="ru",
            is_active=True,
        )
        db.add(u_admin)

        # 8. Teachers
        u_teach1 = User(
            school_id=school.id,
            telegram_id=1002,
            role=UserRole.TEACHER.value,
            first_name="Елена",
            last_name="Петрова",
            username="teacher_elena",
            language_code="ru",
            is_active=True,
        )
        u_teach2 = User(
            school_id=school.id,
            telegram_id=1003,
            role=UserRole.TEACHER.value,
            first_name="Дилшод",
            last_name="Каримов",
            username="teacher_dilshod",
            language_code="ru",
            is_active=True,
        )
        db.add_all([u_teach1, u_teach2])
        await db.flush()

        t_prof1 = Teacher(id=u_teach1.id, bio="Преподаватель высшей категории", title="Учитель математики")
        t_prof2 = Teacher(id=u_teach2.id, bio="Cambridge CELTA certified", title="Учитель английского языка")
        db.add_all([t_prof1, t_prof2])
        await db.flush()

        # 9. Students
        u_st1 = User(
            school_id=school.id,
            telegram_id=2001,
            role=UserRole.STUDENT.value,
            first_name="Тимур",
            last_name="Алимов",
            username="student_timur",
            language_code="ru",
            is_active=True,
        )
        u_st2 = User(
            school_id=school.id,
            telegram_id=2002,
            role=UserRole.STUDENT.value,
            first_name="Мадина",
            last_name="Алимова",
            username="student_madina",
            language_code="ru",
            is_active=True,
        )
        u_st3 = User(
            school_id=school.id,
            telegram_id=2003,
            role=UserRole.STUDENT.value,
            first_name="Жасур",
            last_name="Рустамов",
            username="student_jasur",
            language_code="ru",
            is_active=True,
        )
        db.add_all([u_st1, u_st2, u_st3])
        await db.flush()

        s_prof1 = Student(id=u_st1.id, class_id=class_7a.id, student_number="01", xp=180, level=2)
        s_prof2 = Student(id=u_st2.id, class_id=class_7a.id, student_number="02", xp=95, level=1)
        s_prof3 = Student(id=u_st3.id, class_id=class_8b.id, student_number="01", xp=60, level=1)
        db.add_all([s_prof1, s_prof2, s_prof3])
        await db.flush()

        # 10. Parent User (Sherzod Alimov, father of Timur and Madina)
        u_par1 = User(
            school_id=school.id,
            telegram_id=3001,
            role=UserRole.PARENT.value,
            first_name="Шерзод",
            last_name="Алимов",
            username="parent_sherzod",
            language_code="ru",
            is_active=True,
        )
        db.add(u_par1)
        await db.flush()

        p_prof1 = Parent(id=u_par1.id, phone_number="+998901234567")
        db.add(p_prof1)
        await db.flush()

        # Link parent to Student 1 & Student 2
        sp1 = StudentParent(student_id=u_st1.id, parent_id=u_par1.id, relationship_type="father", is_confirmed=True)
        sp2 = StudentParent(student_id=u_st2.id, parent_id=u_par1.id, relationship_type="father", is_confirmed=True)
        db.add_all([sp1, sp2])

        # 11. Curriculum Mapping
        tsc1 = TeacherSubjectClass(teacher_id=u_teach1.id, subject_id=sub_alg.id, class_id=class_7a.id)
        tsc2 = TeacherSubjectClass(teacher_id=u_teach1.id, subject_id=sub_phys.id, class_id=class_7a.id)
        tsc3 = TeacherSubjectClass(teacher_id=u_teach2.id, subject_id=sub_eng.id, class_id=class_7a.id)
        tsc4 = TeacherSubjectClass(teacher_id=u_teach1.id, subject_id=sub_alg.id, class_id=class_8b.id)
        db.add_all([tsc1, tsc2, tsc3, tsc4])
        await db.flush()

        # 12. Lessons for Today & Yesterday
        today = date.today()
        yesterday = today - timedelta(days=1)

        l1 = Lesson(
            class_id=class_7a.id,
            subject_id=sub_alg.id,
            teacher_id=u_teach1.id,
            lesson_date=today,
            period_number=1,
            topic="Квадратные уравнения",
            room="Каб. 204",
            status=LessonStatus.SCHEDULED.value,
        )
        l2 = Lesson(
            class_id=class_7a.id,
            subject_id=sub_eng.id,
            teacher_id=u_teach2.id,
            lesson_date=today,
            period_number=2,
            topic="Past Continuous & Past Simple",
            room="Каб. 108",
            status=LessonStatus.SCHEDULED.value,
        )
        l_past = Lesson(
            class_id=class_7a.id,
            subject_id=sub_alg.id,
            teacher_id=u_teach1.id,
            lesson_date=yesterday,
            period_number=1,
            topic="Линейные функции",
            room="Каб. 204",
            status=LessonStatus.COMPLETED.value,
        )
        db.add_all([l1, l2, l_past])
        await db.flush()

        # 13. Grades
        g1 = Grade(
            school_id=school.id,
            student_id=u_st1.id,
            teacher_id=u_teach1.id,
            lesson_id=l_past.id,
            subject_id=sub_alg.id,
            grade_type_id=gt_quiz.id,
            value=5.0,
            raw_display="5",
            weight=1.5,
            comment="Отличная самостоятельная работа",
            source=GradeSource.MANUAL.value,
            is_active=True,
            is_retake=False,
        )
        g2 = Grade(
            school_id=school.id,
            student_id=u_st2.id,
            teacher_id=u_teach1.id,
            lesson_id=l_past.id,
            subject_id=sub_alg.id,
            grade_type_id=gt_quiz.id,
            value=4.0,
            raw_display="4",
            weight=1.5,
            comment="Хорошая работа",
            source=GradeSource.MANUAL.value,
            is_active=True,
            is_retake=False,
        )
        db.add_all([g1, g2])

        # 14. Attendance
        att1 = Attendance(
            student_id=u_st1.id,
            lesson_id=l_past.id,
            status=AttendanceStatus.PRESENT.value,
            recorded_by_id=u_teach1.id,
        )
        att2 = Attendance(
            student_id=u_st2.id,
            lesson_id=l_past.id,
            status=AttendanceStatus.LATE.value,
            note="Опоздание на 10 мин",
            recorded_by_id=u_teach1.id,
        )
        db.add_all([att1, att2])

        # 15. Homework
        hw1 = Homework(
            class_id=class_7a.id,
            subject_id=sub_alg.id,
            teacher_id=u_teach1.id,
            lesson_id=l1.id,
            title="Параграф 14, № 14.3 - 14.8",
            description="Решить задачи на формулу корней квадратного уравнения в тетради.",
            due_date=today + timedelta(days=2),
        )
        hw2 = Homework(
            class_id=class_7a.id,
            subject_id=sub_eng.id,
            teacher_id=u_teach2.id,
            lesson_id=l2.id,
            title="Workbook page 42, ex. 1-4",
            description="Complete the grammar exercises on Past Continuous.",
            due_date=today + timedelta(days=1),
        )
        db.add_all([hw1, hw2])
        await db.flush()

        # Submissions
        sub1 = HomeworkSubmission(
            homework_id=hw1.id,
            student_id=u_st1.id,
            status=HomeworkStatus.DONE.value,
            submitted_at=datetime.now(timezone.utc),
        )
        db.add(sub1)

        await db.commit()
        print("Database successfully seeded with realistic entities!")


if __name__ == "__main__":
    asyncio.run(seed_database())
