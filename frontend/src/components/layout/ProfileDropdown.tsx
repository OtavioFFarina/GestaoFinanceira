"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import type { AuthUser } from "@/lib/auth";

const C = {
    surface: "var(--surface)", elevated: "var(--elevated)", border: "var(--border)",
    muted: "var(--muted)", avocado: "var(--avocado)", text: "var(--text)", danger: "var(--danger)",
};

const API_BASE =
    typeof window !== "undefined"
        ? `http://${window.location.hostname}:8000/api`
        : "http://localhost:8000/api";

export default function ProfileDropdown() {
    const { user, logout, updateUser } = useAuth();
    const router = useRouter();
    const [open, setOpen] = useState(false);
    const [editingName, setEditingName] = useState(false);
    const [newName, setNewName] = useState(user?.nome_exibicao ?? "");
    const [saving, setSaving] = useState(false);
    const ref = useRef<HTMLDivElement>(null);

    // Close on outside click
    useEffect(() => {
        const handler = (e: MouseEvent) => {
            if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
        };
        document.addEventListener("mousedown", handler);
        return () => document.removeEventListener("mousedown", handler);
    }, []);

    const handleLogout = async () => {
        setOpen(false);
        await logout();
        router.replace("/login");
    };

    const saveName = async () => {
        if (!user || !newName.trim()) return;
        setSaving(true);
        try {
            const res = await fetch(`${API_BASE}/perfil/${user.usuario_id}`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ nome_exibicao: newName.trim() }),
            });
            if (res.ok) {
                updateUser({ nome_exibicao: newName.trim() });
                setEditingName(false);
            }
        } finally {
            setSaving(false);
        }
    };

    const initials = (user?.nome_exibicao ?? "U")
        .split(" ")
        .slice(0, 2)
        .map((w) => w[0].toUpperCase())
        .join("");

    return (
        <div ref={ref} className="relative">
            {/* Avatar button */}
            <button
                onClick={() => setOpen((o) => !o)}
                className="w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold text-white transition-all hover:scale-105 hover:ring-2 select-none"
                style={{ backgroundColor: C.avocado, "--tw-ring-color": C.avocado } as React.CSSProperties}
                title={user?.nome_exibicao}
            >
                {user?.foto_url ? (
                    <img src={user.foto_url} alt="avatar" className="w-full h-full rounded-full object-cover" />
                ) : (
                    initials
                )}
            </button>

            {/* Dropdown */}
            {open && (
                <div
                    className="absolute right-0 top-11 w-60 rounded-2xl shadow-2xl z-50 overflow-hidden"
                    style={{
                        backgroundColor: C.surface,
                        border: `1px solid ${C.border}`,
                        animation: "dropdown-in 0.18s ease-out",
                    }}
                >
                    {/* Header */}
                    <div className="px-4 py-3" style={{ borderBottom: `1px solid ${C.border}` }}>
                        <div className="flex items-center gap-3">
                            <div
                                className="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold text-white flex-shrink-0"
                                style={{ backgroundColor: C.avocado }}
                            >
                                {initials}
                            </div>
                            <div className="min-w-0">
                                <p className="text-sm font-semibold truncate">{user?.nome_exibicao}</p>
                                <p className="text-xs truncate" style={{ color: C.muted }}>Conta pessoal</p>
                            </div>
                        </div>
                    </div>

                    {/* Edit Name */}
                    <div className="p-2">
                        {editingName ? (
                            <div className="px-2 py-1.5 space-y-2">
                                <input
                                    value={newName}
                                    onChange={(e) => setNewName(e.target.value)}
                                    onKeyDown={(e) => { if (e.key === "Enter") saveName(); if (e.key === "Escape") setEditingName(false); }}
                                    placeholder="Seu nome..."
                                    className="w-full rounded-lg px-3 py-2 text-sm outline-none"
                                    style={{ backgroundColor: C.elevated, border: `1px solid ${C.border}` }}
                                    autoFocus
                                />
                                <div className="flex gap-2">
                                    <button
                                        onClick={saveName}
                                        disabled={saving}
                                        className="flex-1 py-1.5 rounded-lg text-xs font-semibold text-white hover:opacity-90 disabled:opacity-50"
                                        style={{ backgroundColor: C.avocado }}
                                    >
                                        {saving ? "..." : "Salvar"}
                                    </button>
                                    <button
                                        onClick={() => setEditingName(false)}
                                        className="flex-1 py-1.5 rounded-lg text-xs hover:opacity-80"
                                        style={{ backgroundColor: C.elevated, color: C.muted, border: `1px solid ${C.border}` }}
                                    >
                                        Cancelar
                                    </button>
                                </div>
                            </div>
                        ) : (
                            <>
                                <DropdownItem onClick={() => { setNewName(user?.nome_exibicao ?? ""); setEditingName(true); }}>
                                    ✏️ Alterar nome
                                </DropdownItem>
                                <DropdownItem onClick={() => { router.push("/configuracoes"); setOpen(false); }}>
                                    ⚙️ Configurações
                                </DropdownItem>
                            </>
                        )}

                        <div className="my-1.5" style={{ borderTop: `1px solid ${C.border}` }} />
                        <DropdownItem onClick={handleLogout} danger>
                            🚪 Sair da conta
                        </DropdownItem>
                    </div>
                </div>
            )}

            <style>{`
        @keyframes dropdown-in {
          from { opacity: 0; transform: scale(0.95) translateY(-6px); }
          to   { opacity: 1; transform: scale(1) translateY(0); }
        }
      `}</style>
        </div>
    );
}

function DropdownItem({ children, onClick, danger = false }: {
    children: React.ReactNode; onClick: () => void; danger?: boolean;
}) {
    const [hovered, setHovered] = useState(false);
    return (
        <button
            onClick={onClick}
            onMouseEnter={() => setHovered(true)}
            onMouseLeave={() => setHovered(false)}
            className="w-full text-left px-3 py-2 rounded-xl text-sm transition-all flex items-center gap-2"
            style={{
                backgroundColor: hovered ? (danger ? `${C.danger}18` : C.elevated) : "transparent",
                color: danger ? C.danger : (hovered ? "white" : C.muted),
            }}
        >
            {children}
        </button>
    );
}
