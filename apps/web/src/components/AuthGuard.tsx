"use client";

import { ReactNode, useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { clearAuthSession, verifyAuth } from "@/lib/auth";
import { LoadingState } from "@/components/ui/LoadingState";

type AuthGuardProps = {
  children: ReactNode;
};

const protectedPaths = ["/agent", "/agents", "/chat", "/ai-creation", "/board", "/competition-diagnosis"];

export function AuthGuard({ children }: AuthGuardProps) {
  const pathname = usePathname();
  const router = useRouter();
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    const needsAuth = protectedPaths.some((path) => pathname === path || pathname.startsWith(`${path}/`));
    if (!needsAuth) {
      setChecked(true);
      return;
    }
    let active = true;
    verifyAuth()
      .then(() => active && setChecked(true))
      .catch(() => {
        clearAuthSession();
        router.replace("/login");
      });
    return () => {
      active = false;
    };
  }, [pathname, router]);

  if (!checked) {
    return <LoadingState fullScreen label="正在验证登录状态..." />;
  }

  return <>{children}</>;
}
