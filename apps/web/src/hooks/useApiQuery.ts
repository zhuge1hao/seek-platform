"use client";

import useSWR, { type Key, type SWRConfiguration } from "swr";

type ApiQueryOptions<T> = SWRConfiguration<T> & {
  enabled?: boolean;
};

export function useApiQuery<T>(key: Key, fetcher: () => Promise<T>, options: ApiQueryOptions<T> = {}) {
  const { enabled = true, keepPreviousData = true, revalidateOnFocus = false, refreshInterval = 0, ...rest } = options;
  return useSWR<T>(enabled ? key : null, fetcher, {
    keepPreviousData,
    revalidateOnFocus,
    refreshInterval,
    shouldRetryOnError: false,
    ...rest
  });
}
