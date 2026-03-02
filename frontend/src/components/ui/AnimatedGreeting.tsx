"use client";
/**
 * AnimatedGreeting — displays "Olá, [nome]!" with a color-shifting gradient.
 * Gradient cycles through avocado tones using CSS keyframe animation.
 */
export default function AnimatedGreeting({ nome }: { nome: string }) {
    return (
        <>
            <p
                className="text-base sm:text-lg font-medium"
                style={{
                    background: "linear-gradient(90deg, #5CA34F, #7CC96E, #A8E063, #5CA34F)",
                    backgroundSize: "200% auto",
                    WebkitBackgroundClip: "text",
                    WebkitTextFillColor: "transparent",
                    backgroundClip: "text",
                    animation: "gradient-shift 3s linear infinite",
                }}
            >
                Olá, {nome}! Como vamos organizar as finanças hoje? 🥑
            </p>

            <style>{`
        @keyframes gradient-shift {
          0%   { background-position: 0% center; }
          100% { background-position: 200% center; }
        }
      `}</style>
        </>
    );
}
