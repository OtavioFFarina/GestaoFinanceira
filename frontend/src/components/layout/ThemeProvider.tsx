"use client";
/**
 * ThemeProvider — applies dark/light CSS class to <html> based on auth user's preference.
 * Must be rendered inside AuthProvider.
 */
import { useEffect } from "react";
import { useAuth } from "@/lib/auth";

export default function ThemeProvider({ children }: { children: React.ReactNode }) {
    const { user } = useAuth();

    useEffect(() => {
        const tema = user?.tema ?? "dark";
        const root = document.documentElement;

        if (tema === "light") {
            root.classList.add("light");
            root.classList.remove("dark");
        } else {
            root.classList.add("dark");
            root.classList.remove("light");
        }
    }, [user?.tema]);

    return <>{children}</>;
}
