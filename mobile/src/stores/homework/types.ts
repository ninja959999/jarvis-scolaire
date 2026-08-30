import type { Homework } from "@/services/shared/Homework";

export interface HomeworkStore {
  homeworks: Record<number, Homework[]>
  updateHomeworks: (epochWeekNumber: number, homeworks: Homework[]) => void
}
