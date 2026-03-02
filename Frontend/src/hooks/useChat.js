import { useEffect, useRef, useState } from "react";

export function useChat(activeProject) {
    const [input, setInput] = useState("");

    const [chatHistories, setChatHistories] = useState({});
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef(null);
    const messages = chatHistories[activeProject] || [];

    // Auto-scroll til bunnen (also when loading toggles)
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, loading]);


    const addMessageToProject = (newMessage) => {
    setChatHistories((prev) => ({
        ...prev,
        [activeProject]: [...(prev[activeProject] || []), newMessage],
    }));
};

    const sendMessage = async () => {
        const text = input.trim();
        if (!text || loading) return;

        const userMessage = { role: "user", content: text };

        addMessageToProject(userMessage);


        setInput("");
        setLoading(true);

        try {
            const response = await fetch("http://127.0.0.1:8000/ask", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                question: text,
                project: activeProject
                }),
            });

            const data = await response.json();

            const aiMessage = {
                role: "assistant",
                content: data.answer,
                sources: data.sources || [],
            };
            addMessageToProject(aiMessage);


        } catch (error) {
            console.error("Feil:", error);
            addMessageToProject({
                role: "assistant",
                content: "Beklager, det skjedde en feil. Prøv igjen senere.",
            });
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
