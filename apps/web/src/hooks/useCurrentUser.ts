"use client";

import useSWR from "swr";
import { getCurrentUser } from "@/lib/api";
import type { AuthUser } from "@/lib/auth";
import { queryKeys } from "@/lib/queryKeys";

export function useCurrentUser(enabled = true) {
  return useSWR<AuthUser>(
    enabled ? queryKeys.currentUser : null,
    getCurrentUser,
    { keepPreviousData: true, revalidateOnFocus: true, refreshInterval: 0 }
  );
}
