"use client";

import { useEffect } from "react";
import { CheckCircle2, Trash2 } from "lucide-react";

export type ToastType = "success" | "delete";

interface ToastProps {
    message: string;
    type: ToastType;
    visible: boolean;
    onClose: () => void;
}

const C = {
    surface: "var(--surface)",
    elevated: "var(--elevated)",
    border: "var(--border)",
    avocado: "var(--avocado)",
    danger: "var(--danger)",
    text: "var(--text)",
};

export default function Toast({ message, type, visible, onClose }: ToastProps) {
    useEffect(() => {
        if (visible) {
            const timer = setTimeout(() => onClose(), 1500); // Rápido: 1.5s
            return () => clearTimeout(timer);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [visible]);

    if (!visible) return null;

    const isSuccess = type === "success";

    return (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-[100] px-4 py-3 rounded-2xl flex items-center gap-3 shadow-2xl"
            style={{
                backgroundColor: C.surface,
                border: `1px solid ${isSuccess ? C.avocado : C.danger}`,
                animation: "toast-in 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards",
            }}>

            <div className="w-8 h-8 rounded-full flex items-center justify-center"
                style={{ backgroundColor: isSuccess ? `${C.avocado}20` : `${C.danger}20` }}>
                {isSuccess ? (
                    <CheckCircle2 size={18} style={{ color: C.avocado }} />
                ) : (
                    <Trash2 size={18} style={{ color: C.danger }} />
                )}
            </div>

            <span className="text-sm font-semibold" style={{ color: C.text }}>
                {message}
            </span>

            <style>{`
                @keyframes toast-in {
                    0% { transform: translate(-50%, 100%) scale(0.9); opacity: 0; }
                    100% { transform: translate(-50%, 0) scale(1); opacity: 1; }
                }
            `}</style>
        </div>
    );
}
