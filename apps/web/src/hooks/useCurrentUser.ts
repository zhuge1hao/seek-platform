"use client";

import { getCurrentUser } from "@/lib/api";
import type { AuthUser } from "@/lib/auth";
import { useApiQuery } from "@/hooks/useApiQuery";
import { queryKeys } from "@/lib/queryKeys";

export function useCurrentUser(enabled = true) {
  return useApiQuery<AuthUser>(queryKeys.currentUser, getCurrentUser, { enabled, revalidateOnFocus: true });
}
