# LUMINA — ROLE-BASED ACCESS CONTROL (RBAC) MATRIX

| Capability / API Endpoint | ADMIN | TEACHER | STUDENT | PARENT | Server Enforcement Rule |
|---|:---:|:---:|:---:|:---:|---|
| **School Management** | ✅ | ❌ | ❌ | ❌ | School admin role verified via `require_roles(UserRole.ADMIN)` |
| **Manage Curriculum & Classes** | ✅ | ❌ | ❌ | ❌ | Admin only |
| **Generate School Invites** | ✅ | ❌ | ❌ | ❌ | Scoped strictly to admin's `school_id` |
| **Audit Logs Inspection** | ✅ | ❌ | ❌ | ❌ | Access restricted to administrators |
| **Award / Correct Grades** | ✅ | ✅ | ❌ | ❌ | Teacher must be assigned to the class & subject of the lesson |
| **5-Minute Grade Undo** | ❌ | ✅ | ❌ | ❌ | Limited to the awarding teacher within 300 seconds of creation |
| **Record Attendance** | ✅ | ✅ | ❌ | ❌ | Teacher assigned to the lesson or Admin |
| **Interactive Seating Management** | ✅ | ✅ | ❌ | ❌ | Class assigned teachers only |
| **Pick Random Student** | ❌ | ✅ | ❌ | ❌ | Teacher only during active classroom instruction |
| **View Own Academic Grades & GPA**| ❌ | ❌ | ✅ | ❌ | Student can only query own `student_id` |
| **Mark Homework Status (TODO/DONE)**| ❌ | ❌ | ✅ | ❌ | Student in the assigned class |
| **Daily Vibe & XP Progression** | ❌ | ❌ | ✅ | ❌ | Student profile only |
| **AI Study Assistant (Hints & Recaps)**| ❌ | ❌ | ✅ | ❌ | Authenticated student |
| **View Linked Child Data** | ❌ | ❌ | ❌ | ✅ | Parent must have verified `StudentParent` link in database |
| **Submit Child Absence Note** | ❌ | ❌ | ❌ | ✅ | Parent can only submit for verified linked child |
| **Smart Weekly AI Summary** | ❌ | ❌ | ❌ | ✅ | Aggregated only for linked children |
