import type { UserRole } from "@/client"

// Human-friendly labels for each role, used across the admin UI.
export const ROLE_LABELS: Record<UserRole, string> = {
  admin: "Admin",
  manager: "Manager",
  member: "Member",
}

// Ordered from least to most privileged for selects.
export const ROLE_OPTIONS: { value: UserRole; label: string }[] = [
  { value: "member", label: ROLE_LABELS.member },
  { value: "manager", label: ROLE_LABELS.manager },
  { value: "admin", label: ROLE_LABELS.admin },
]
