"use client";

import { useEffect, useState } from "react";

export default function GlobalLoader() {
    const [dots, setDots] = useState("");

    useEffect(() => {
        const interval = setInterval(() => {
            setDots(prev => (prev.length >= 3 ? "" : prev + "."));
        }, 400);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="fixed inset-0 z-[100] flex flex-col items-center justify-center bg-black/60 backdrop-blur-md">
            <div className="text-7xl animate-bounce mb-4">🥑</div>
            <p className="text-sm font-medium text-white tracking-widest">
                CARREGANDO{dots}
            </p>
        </div>
    );
}
