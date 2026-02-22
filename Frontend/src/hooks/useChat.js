import { useEffect, useRef, useState } from "react";

export function useChat() {
    const [input, setInput] = useState("");
    const [messages, setMessages] = useState([]);
    const [loading, setLoading] = useState(false);

    const messagesEndRef = useRef(null);

    // Auto-scroll til bunnen
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, loading]);

    const sendMessage = async () => {
        const text = input.trim();
        if (!text || loading) return;

        const userMessage = { role: "user", content: text };

        setMessages((prev) => [...prev, userMessage]);
        setInput("");
        setLoading(true);

        try {
            const response = await fetch("http://127.0.0.1:8000/ask", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ question: text }),
            });

            const data = await response.json();

            const aiMessage = {
                role: "assistant",
                content: data.answer,
                sources: data.sources || [],
            };

            setMessages((prev) => [...prev, aiMessage]);
        } catch (error) {
            console.error("Feil:", error);
            // keep functionality
            setMessages((prev) => [
                ...prev,
                { role: "assistant", content: "Noe gikk galt. Prøv igjen." },
            ]);
        } finally {
            setLoading(false);
        }
    };

    return {
        input,
        setInput,
        messages,
        loading,
        sendMessage,
        messagesEndRef,
    };
}
