"use client";

import { getAdminUsers, type AdminUser } from "@/lib/api";
import { useApiQuery } from "@/hooks/useApiQuery";
import { queryKeys } from "@/lib/queryKeys";

type Params = { role?: string; enabled?: string; keyword?: string; limit?: number };

export function useAdminUsers(params: Params = {}, enabled = true) {
  return useApiQuery<{ users: AdminUser[] }>(queryKeys.adminUsers(params), () => getAdminUsers(params), { enabled });
}
