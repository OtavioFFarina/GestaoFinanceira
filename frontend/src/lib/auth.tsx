"use client";
/**
 * AuthContext — provides user session across the app.
 * Token is stored in localStorage and sent on every API request.
 */
import { createContext, useCallback, useContext, useEffect, useState } from "react";

const API_BASE =
    typeof window !== "undefined"
        ? `http://${window.location.hostname}:8000/api`
        : "http://localhost:8000/api";

export interface AuthUser {
    usuario_id: string;
    nome_exibicao: string;
    tema: "dark" | "light";
    email: string;
    foto_url?: string | null;
    token: string;
}

interface AuthCtx {
    user: AuthUser | null;
    loading: boolean;
    login: (email: string, senha: string) => Promise<void>;
    logout: () => Promise<void>;
    updateUser: (partial: Partial<AuthUser>) => void;
}

const AuthContext = createContext<AuthCtx | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [user, setUser] = useState<AuthUser | null>(null);
    const [loading, setLoading] = useState(true);

    // Rehydrate from localStorage on mount
    useEffect(() => {
        try {
            const stored = localStorage.getItem("gf_user");
            if (stored) setUser(JSON.parse(stored));
        } catch { /* ignore */ }
        setLoading(false);
    }, []);

    const login = useCallback(async (email: string, senha: string) => {
        const res = await fetch(`${API_BASE}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, senha }),
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail ?? "Credenciais inválidas.");
        }
        const data = await res.json();
        const userData = {
            usuario_id: data.usuario_id,
            nome_exibicao: data.nome_exibicao,
            tema: data.tema as "dark" | "light",
            token: data.token,
            email: data.email,
        };
        setUser(userData as AuthUser);
        localStorage.setItem("gf_user", JSON.stringify(userData));
    }, []);

    const logout = useCallback(async () => {
        if (user?.token) {
            await fetch(`${API_BASE}/auth/logout`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ token: user.token }),
            }).catch(() => { });
        }
        setUser(null);
        localStorage.removeItem("gf_user");
    }, [user]);

    const updateUser = useCallback((partial: Partial<AuthUser>) => {
        setUser((prev) => {
            if (!prev) return prev;
            const updated = { ...prev, ...partial };
            localStorage.setItem("gf_user", JSON.stringify(updated));
            return updated;
        });
    }, []);

    return (
        <AuthContext.Provider value={{ user, loading, login, logout, updateUser }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth(): AuthCtx {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
    return ctx;
}
