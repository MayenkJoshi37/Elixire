const chatBox = document.getElementById("chat-box");
const input = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");
const langDisplay = document.getElementById("lang-display");

function bubble(sender, text, isUser) {
    const div = document.createElement("div");
    div.className = `p-4 rounded-xl max-w-[80%] shadow fade-in ${
        isUser ? "ml-auto bg-white text-gray-900" : "bg-gray-800 text-gray-200"
    }`;
    div.innerHTML = `<strong>${sender}:</strong><br>${text}`;
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function typing() {
    const t = document.createElement("div");
    t.id = "typing";
    t.className = "p-4 rounded-xl bg-gray-700/50 text-gray-300 fade-in";
    t.innerText = "Assistant is typing...";
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

    const data = await resp.json();
    stopTyping();
    sendBtn.disabled = false;

    if (data.success) {
        langDisplay.classList.remove("hidden");
        langDisplay.innerText = "Detected Language: " + data.detected_language;
        bubble("Assistant", data.answer, false);
    }
}
sendBtn.onclick = sendMessage;
input.addEventListener("keydown", e => {
    if (e.key === "Enter") sendMessage();
});
