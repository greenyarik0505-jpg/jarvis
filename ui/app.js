// J.A.R.V.I.S. Frontend Logic

let voiceEnabled = true;

function appendMessage(type, speaker, text) {
    const feed = document.getElementById("terminal-feed");
    const msgDiv = document.createElement("div");
    msgDiv.className = `feed-msg ${type}`;

    if (type === "system") {
        msgDiv.innerHTML = `<span class="time">[SYS]</span> <span class="msg">${text}</span>`;
    } else if (speaker) {
        msgDiv.innerHTML = `<span class="speaker">${speaker}:</span> <span class="msg">${text}</span>`;
    } else {
        msgDiv.innerHTML = `<span class="msg">${text}</span>`;
    }

    feed.appendChild(msgDiv);
    feed.scrollTop = feed.scrollHeight;
}

function setSystemState(state) {
    const el = document.getElementById("system-state");
    const core = document.getElementById("reactor-core");
    const wave = document.querySelector(".wave-container");

    el.innerText = state;

    if (state === "SPEAKING") {
        core.style.boxShadow = "0 0 60px #00f3ff, inset 0 0 25px #ffffff";
        wave.classList.add("wave-active");
    } else if (state === "LISTENING") {
        core.style.boxShadow = "0 0 45px #00ff88, inset 0 0 20px #ffffff";
        wave.classList.add("wave-active");
    } else if (state === "EXECUTING") {
        core.style.boxShadow = "0 0 45px #ff79c6, inset 0 0 20px #ffffff";
        wave.classList.remove("wave-active");
    } else {
        core.style.boxShadow = "0 0 35px #00f3ff, inset 0 0 20px #ffffff";
        wave.classList.remove("wave-active");
    }
}

function handleInputKey(event) {
    if (event.key === "Enter") {
        submitCommand();
    }
}

function submitCommand() {
    const input = document.getElementById("cmd-input");
    const text = input.value.trim();
    if (!text) return;

    appendMessage("user", "YOU", text);
    input.value = "";
    setSystemState("THINKING");

    if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.send_command(text).then((res) => {
            setSystemState("ONLINE");
        }).catch((err) => {
            appendMessage("system", "", "Ошибка: " + err);
            setSystemState("ONLINE");
        });
    }
}

function joinZoom() {
    const input = document.getElementById("zoom-input");
    const link = input.value.trim();
    if (!link) {
        alert("Вставьте ссылку или номер конференции Zoom");
        return;
    }

    appendMessage("system", "", `Подключение к Zoom: ${link}`);
    setSystemState("EXECUTING");

    if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.join_zoom(link).then((ok) => {
            if (ok) {
                document.getElementById("zoom-status").innerText = "CONNECTED";
                document.getElementById("zoom-status").className = "val status-connected";
                document.getElementById("btn-leave-zoom").style.display = "inline-flex";
                appendMessage("zoom", "ZOOM", "Подключение успешно. Аудио-слушатель участников активен.");
            }
            setSystemState("ONLINE");
        });
    }
}

function leaveZoom() {
    if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.leave_zoom().then(() => {
            document.getElementById("zoom-status").innerText = "DISCONNECTED";
            document.getElementById("zoom-status").className = "val status-idle";
            document.getElementById("btn-leave-zoom").style.display = "none";
            appendMessage("system", "", "Конференция Zoom завершена.");
        });
    }
}

function toggleZoomMute() {
    if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.toggle_zoom_mute();
    }
}

function toggleVoice() {
    voiceEnabled = !voiceEnabled;
    const btn = document.getElementById("btn-voice-toggle");
    if (voiceEnabled) {
        btn.classList.add("active");
        btn.querySelector(".btn-text").innerText = "ГОЛОС: ВКЛ";
        if (window.pywebview && window.pywebview.api) {
            window.pywebview.api.set_voice_enabled(true);
        }
    } else {
        btn.classList.remove("active");
        btn.querySelector(".btn-text").innerText = "ГОЛОС: ВЫКЛ";
        if (window.pywebview && window.pywebview.api) {
            window.pywebview.api.set_voice_enabled(false);
        }
    }
}

function emergencyStop() {
    if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.emergency_stop();
        appendMessage("system", "", "Аварийная остановка агента выполнена!");
    }
}

// Callbacks from Python
window.jarvisAPI = {
    onJarvisReply: function(text) {
        appendMessage("jarvis", "JARVIS", text);
        setSystemState("ONLINE");
    },
    onUserSpeech: function(text) {
        appendMessage("user", "YOU (MIC)", text);
    },
    onAction: function(desc) {
        appendMessage("action", "ACTION", desc);
    },
    onZoomParticipant: function(text) {
        appendMessage("zoom", "ZOOM УЧАСТНИК", text);
    },
    setState: function(state) {
        setSystemState(state);
    }
};

window.addEventListener('pywebviewready', function() {
    console.log("J.A.R.V.I.S. Webview bridge initialized.");
});
