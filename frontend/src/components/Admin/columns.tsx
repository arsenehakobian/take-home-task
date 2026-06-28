import type { ColumnDef } from "@tanstack/react-table"

import type { UserPublic } from "@/client"
import { Badge } from "@/components/ui/badge"
import { ROLE_LABELS } from "@/lib/roles"
import { cn } from "@/lib/utils"
import { UserActionsMenu } from "./UserActionsMenu"

export type UserTableData = UserPublic & {
  isCurrentUser: boolean
}

const actionsColumn: ColumnDef<UserTableData> = {
  id: "actions",
  header: () => <span className="sr-only">Actions</span>,
  cell: ({ row }) => (
    <div className="flex justify-end">
      <UserActionsMenu user={row.original} />
    </div>
  ),
}

const baseColumns: ColumnDef<UserTableData>[] = [
  {
    accessorKey: "full_name",
    header: "Full Name",
    cell: ({ row }) => {
      const fullName = row.original.full_name
      return (
        <div className="flex items-center gap-2">
          <span
            className={cn("font-medium", !fullName && "text-muted-foreground")}
          >
            {fullName || "N/A"}
          </span>
          {row.original.isCurrentUser && (
            <Badge variant="outline" className="text-xs">
              You
            </Badge>
          )}
        </div>
      )
    },
  },
  {
    accessorKey: "email",
    header: "Email",
    cell: ({ row }) => (
      <span className="text-muted-foreground">{row.original.email}</span>
    ),
  },
  {
    accessorKey: "role",
    header: "Role",
    cell: ({ row }) => {
      const role = row.original.role ?? "member"
      const variant =
        role === "admin"
          ? "default"
          : role === "manager"
            ? "secondary"
            : "outline"
      return <Badge variant={variant}>{ROLE_LABELS[role]}</Badge>
    },
  },
  {
    accessorKey: "is_active",
    header: "Status",
    cell: ({ row }) => (
      <div className="flex items-center gap-2">
        <span
          className={cn(
            "size-2 rounded-full",
            row.original.is_active ? "bg-green-500" : "bg-gray-400",
          )}
        />
        <span className={row.original.is_active ? "" : "text-muted-foreground"}>
          {row.original.is_active ? "Active" : "Inactive"}
        </span>
      </div>
    ),
  },
]

// Build the table columns. The actions column (edit/delete) is only included
// for users who can manage others (admins).
export function getColumns(canManage: boolean): ColumnDef<UserTableData>[] {
  return canManage ? [...baseColumns, actionsColumn] : baseColumns
}
