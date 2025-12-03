const chatBox = document.getElementById("chat-box");
const input = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");
const langDisplay = document.getElementById("lang-display");

function bubble(sender, text, isUser) {
    const div = document.createElement("div");
    div.className = `p-5 rounded-2xl max-w-[80%] bubble-pop shadow ${
        isUser 
        ? "ml-auto bg-white text-gray-900"
        : "bg-white/10 text-white backdrop-blur-lg border border-white/10"
    }`;

    div.innerHTML = `<strong>${sender}:</strong><br>${text}`;
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function typing() {
    const t = document.createElement("div");
    t.id = "typing";
    t.className = "p-4 rounded-xl text-gray-300 italic";
    t.textContent = "Assistant is typing...";
    chatBox.appendChild(t);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function stopTyping() {
    const t = document.getElementById("typing");
    if (t) t.remove();
}

async function sendMessage() {
    const text = input.value.trim();
    if (!text) return;

    bubble("You", text, true);
    input.value = "";

    typing();
    sendBtn.disabled = true;

    const resp = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text })
    });

    stopTyping();
    sendBtn.disabled = false;

    const data = await resp.json();
    if (data.success) {
        langDisplay.classList.remove("hidden");
        langDisplay.innerText = `Detected Language: ${data.original_language}`;
        bubble("Assistant", data.answer, false);
    }
}

sendBtn.onclick = sendMessage;
input.addEventListener("keydown", e => {
    if (e.key === "Enter") sendMessage();
});
