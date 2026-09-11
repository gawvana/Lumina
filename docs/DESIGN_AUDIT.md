# LUMINA — UI/UX & APPLE-LEVEL DESIGN AUDIT

## 1. Executive Aesthetic Evaluation
Lumina rejects noisy, gamified clutter (over-saturated neon rainbows, endless alert banners, distracting full-screen animations). Instead, it adopts modern Apple Human Interface principles:
- **Quiet Depth & Restraint**: Neutral Zinc palette with subtle translucency (`backdrop-filter: blur(16px)`), micro-borders (`1px solid rgba(255,255,255,0.08)`), and soft elevation shadows.
- **Editorial Hierarchy**: Prominent hero cards with large typographic metrics (e.g. GPA `28px 800-weight`, Level `Lvl 2 (250 XP)`), followed by structured cards grouped by context.
- **Direct Manipulation**: Touch targets $\ge 44$px, segmented pill controls for daily vibe check-in, 3D card flips for flashcards, and bottom sheet drawers (`.lumina-sheet`) with tactile grab handles.
- **Haptic Feedback**: Meaningful tactile sensations on iOS/Android via `triggerHaptic`:
  - `selection` for tab switching, card flips, and desk selection.
  - `impact (light)` for language toggle, vibe choice, and homework status toggle.
  - `notification (success)` for grade save, AI hint reception, and attendance submission.
  - `notification (error)` for validation rejections.

## 2. Screen Inventory & UX Flows
1. **Student**:
   - `Home`: Editorial banner (streak badge, XP/Level, deadlines count) $\rightarrow$ Daily Vibe selector $\rightarrow$ Quick study tools $\rightarrow$ Today's schedule $\rightarrow$ Latest grade card.
   - `Grades`: GPA header card $\rightarrow$ Subject accordion with color-coded grade pills ($5, 4, 3, 2$).
   - `Homework`: Categorized deadline list $\rightarrow$ Single-tap checkbox status toggle (`TODO` $\leftrightarrow$ `DONE`).
   - `Schedule`: Timeline of daily periods with room numbers and status tags.
   - `Profile`: Avatar $\rightarrow$ Unlocked achievements badge grid $\rightarrow$ Digital Backpack file library $\rightarrow$ Language and dark mode toggles.
2. **Teacher**:
   - `Dashboard`: Assigned classes cards with quick entry into Journal.
   - `Journal`: Grid with student roster, grade picker bottom sheet with 5-minute undo toast.
   - `Seating`: Classroom desk grid with student avatar badges $\rightarrow$ 1-tap "🎲 Вызвать к доске" fair student selector.
   - `Homework`: Assignment publishing modal with due date and subject selectors.
3. **Parent**:
   - `Overview`: Child switcher dropdown $\rightarrow$ Smart Weekly AI Summary banner with actionable tips $\rightarrow$ Recent grades list.
   - `Attendance`: Absences history with digital absence note submission form.
4. **Admin**:
   - `Overview`: Key institution metrics (Students, Teachers, Classes) $\rightarrow$ Deep link cryptographic invite generator with expiration parameters.
