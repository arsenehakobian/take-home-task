import type { UserRole } from "@/client"

// Whether a user has admin privileges. The role is authoritative; the legacy
// is_superuser flag is kept as a fallback so existing superusers still pass.
export function isAdmin(
  user?: { is_superuser?: boolean | null; role?: UserRole | null } | null,
): boolean {
  return Boolean(user?.is_superuser || user?.role === "admin")
}

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
