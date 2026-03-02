"use client";

import { useState, useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { Menu, X } from "lucide-react";
import ProfileDropdown from "@/components/layout/ProfileDropdown";

const C = {
    bg: "var(--bg)", surface: "var(--surface)", elevated: "var(--elevated)",
    border: "var(--border)", muted: "var(--muted)", avocado: "var(--avocado)",
};

const NAV_ITEMS = [
    { label: "Dashboard", href: "/" },
    { label: "Histórico", href: "/historico" },
    { label: "Metas", href: "/metas" },
    { label: "Reserva", href: "/reserva" },
    { label: "Dívidas", href: "/dividas" },
    { label: "Receber", href: "/receber" },
    { label: "Configurações", href: "/configuracoes" },
];

interface Props {
    /** The label that should be highlighted as active */
    activeItem?: string;
}

export default function AppNav({ activeItem }: Props) {
    const router = useRouter();
    const pathname = usePathname();
    const [open, setOpen] = useState(false);

    // Close drawer on route change
    useEffect(() => { setOpen(false); }, [pathname]);

    // Prevent body scroll when drawer is open
    useEffect(() => {
        document.body.style.overflow = open ? "hidden" : "";
        return () => { document.body.style.overflow = ""; };
    }, [open]);

    const isActive = (href: string, label: string) => {
        if (activeItem) return activeItem === label;
        return pathname === href;
    };

    return (
        <>
            {/* ── Top bar ────────────────────────────────────────────────── */}
            <nav
                className="sticky top-0 z-40 px-4 md:px-6 py-3 flex items-center justify-between backdrop-blur-md"
                style={{ backgroundColor: `${C.bg}CC`, borderBottom: `1px solid ${C.border}` }}
            >
                {/* Logo */}
                <div className="flex items-center gap-2">
                    <span
                        className="w-7 h-7 rounded-lg text-sm font-bold flex items-center justify-center flex-shrink-0"
                        style={{ backgroundColor: C.avocado }}
                    >🥑</span>
                    <span className="font-bold tracking-tight text-sm md:text-base">GestãoFinanceira</span>
                </div>

                {/* Desktop nav links — hidden on mobile */}
                <div className="hidden md:flex items-center gap-0.5">
                    {NAV_ITEMS.map(({ label, href }) => (
                        <button
                            key={label}
                            onClick={() => router.push(href)}
                            className="px-3 py-1.5 rounded-lg text-sm transition-colors hover:opacity-80"
                            style={{ color: isActive(href, label) ? C.avocado : C.muted }}
                        >
                            {label}
                        </button>
                    ))}
                </div>

                {/* Right side: profile + hamburger */}
                <div className="flex items-center gap-2">
                    <ProfileDropdown />
                    {/* Hamburger — visible on mobile only */}
                    <button
                        className="md:hidden w-11 h-11 flex items-center justify-center rounded-xl transition-opacity hover:opacity-70"
                        style={{ backgroundColor: C.elevated, border: `1px solid ${C.border}` }}
                        onClick={() => setOpen(true)}
                        aria-label="Abrir menu"
                    >
                        <Menu size={20} style={{ color: C.muted }} />
                    </button>
                </div>
            </nav>

            {/* ── Mobile drawer overlay ──────────────────────────────────── */}
            {open && (
                <div
                    className="fixed inset-0 z-50 md:hidden"
                    onClick={() => setOpen(false)}
                >
                    {/* Backdrop */}
                    <div
                        className="absolute inset-0"
                        style={{ backgroundColor: "rgba(0,0,0,0.6)", backdropFilter: "blur(2px)" }}
                    />

                    {/* Drawer panel — slides from right */}
                    <div
                        className="absolute top-0 right-0 h-full w-72 flex flex-col shadow-2xl"
                        style={{
                            backgroundColor: C.surface,
                            borderLeft: `1px solid ${C.border}`,
                            animation: "drawer-in 0.22s cubic-bezier(0.32,0,0.67,0)",
                        }}
                        onClick={e => e.stopPropagation()}
                    >
                        {/* Drawer header */}
                        <div
                            className="flex items-center justify-between px-5 py-4"
                            style={{ borderBottom: `1px solid ${C.border}` }}
                        >
                            <div className="flex items-center gap-2">
                                <span className="w-7 h-7 rounded-lg text-sm font-bold flex items-center justify-center" style={{ backgroundColor: C.avocado }}>🥑</span>
                                <span className="font-bold tracking-tight text-sm">GestãoFinanceira</span>
                            </div>
                            <button
                                className="w-9 h-9 flex items-center justify-center rounded-xl hover:opacity-70 transition-opacity"
                                style={{ backgroundColor: C.elevated }}
                                onClick={() => setOpen(false)}
                                aria-label="Fechar menu"
                            >
                                <X size={18} style={{ color: C.muted }} />
                            </button>
                        </div>

                        {/* Nav links */}
                        <nav className="flex-1 overflow-y-auto py-3 px-3">
                            {NAV_ITEMS.map(({ label, href }) => (
                                <button
                                    key={label}
                                    onClick={() => router.push(href)}
                                    className="w-full text-left px-4 py-3.5 rounded-xl text-sm font-medium transition-all mb-1 flex items-center gap-3"
                                    style={{
                                        backgroundColor: isActive(href, label) ? `${C.avocado}18` : "transparent",
                                        color: isActive(href, label) ? C.avocado : C.muted,
                                        border: isActive(href, label) ? `1px solid ${C.avocado}30` : "1px solid transparent",
                                    }}
                                >
                                    {label}
                                </button>
                            ))}
                        </nav>

                        {/* Drawer footer */}
                        <div
                            className="px-5 py-4 text-xs"
                            style={{ color: C.muted, borderTop: `1px solid ${C.border}` }}
                        >
                            GestãoFinanceira © 2026
                        </div>
                    </div>
                </div>
            )}

            <style>{`
                @keyframes drawer-in {
                    from { transform: translateX(100%); opacity: 0.7; }
                    to   { transform: translateX(0);    opacity: 1; }
                }
            `}</style>
        </>
    );
}
