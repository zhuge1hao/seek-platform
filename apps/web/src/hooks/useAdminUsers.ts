"use client";

import useSWR from "swr";
import { getAdminUsers, type AdminUser } from "@/lib/api";
import { queryKeys } from "@/lib/queryKeys";

type Params = { role?: string; enabled?: string; keyword?: string; limit?: number };

export function useAdminUsers(params: Params = {}, enabled = true) {
  return useSWR<{ users: AdminUser[] }>(
    enabled ? queryKeys.adminUsers(params) : null,
    () => getAdminUsers(params),
    { keepPreviousData: true, revalidateOnFocus: false, refreshInterval: 0 }
  );
}
