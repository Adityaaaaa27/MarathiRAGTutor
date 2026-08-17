/**
 * Marathi RAG Tutor — Multi-Standard Frontend Client Logic
 * Supports Standards 6 and 7 (with expansion for 8, 9, 10).
 */

document.addEventListener("DOMContentLoaded", () => {
    const chatMessages = document.getElementById("chat-messages");
    const chatForm = document.getElementById("chat-form");
    const questionInput = document.getElementById("question-input");
    const sendBtn = document.getElementById("send-btn");
    const clearBtn = document.getElementById("clear-btn");
    const statusText = document.getElementById("status-text");
    const standardSelect = document.getElementById("standard-select");
    const pillButtons = document.querySelectorAll(".pill-btn");
    const sampleContainer = document.getElementById("sample-questions-container");
    const infoStandardName = document.getElementById("info-standard-name");
    const infoChunkCount = document.getElementById("info-chunk-count");
    const activeStdLabel = document.getElementById("active-std-label");
    const welcomeTitle = document.getElementById("welcome-title");
    const welcomeDesc = document.getElementById("welcome-desc");

    let currentStandard = "6";
    let isWaitingForResponse = false;
    let standardsData = [];

    // Standard-specific sample questions
    const sampleQuestionsByStandard = {
        "6": [
            { icon: "📖", q: "पाठ्यपुस्तकातील १ ते २० पर्यंतचे सर्व पाठ आणि कवितांची यादी द्या." },
            { icon: "🔤", q: "Matheran baddal kay mahiti dili ahe?" },
            { icon: "🔤", q: "chimanich gharte ya pathat Isha baddal kay sangitle ahe?" },
            { icon: "🌸", q: "'या भारतात बंधुभाव' या प्रार्थनेचा मुख्य संदेश काय आहे?" },
            { icon: "🍱", q: "'आजोबांचा तीन पुड्यांचा डबा' या पाठातून काय शिकायला मिळते?" },
            { icon: "🚀", q: "डॉ. ए. पी. जे. अब्दुल कलाम यांचे बालपण कसे होते?" },
        ],
        "7": [
            { icon: "📖", q: "सातवीच्या पाठ्यपुस्तकातील सर्व पाठ आणि कवितांची यादी द्या." },
            { icon: "🔤", q: "shyamche bandhuprem ya pathacha saransh kay ahe?" },
            { icon: "💌", q: "'श्यामचे बंधुप्रेम' या पाठाचा सारांश काय आहे?" },
            { icon: "🌾", q: "'माझ्या अंगणात' या कवितेचा भावार्थ सांगा." },
            { icon: "📚", q: "'वाचनाचे वेड' या पाठातून आपल्याला काय शिकायला मिळते?" },
            { icon: "🌟", q: "पंडिता रामाबाई यांचे कार्य कोणते होते?" },
        ],
        "8": [
            { icon: "📖", q: "आठवीच्या पाठ्यपुस्तकातील सर्व पाठ आणि कवितांची यादी द्या." },
            { icon: "🔤", q: "Bharat amucha desh ya geetatun kay sandesh milto?" },
            { icon: "🇮🇳", q: "'भारत अमुचा देश' या गीताचा मुख्य संदेश काय आहे?" },
            { icon: "🐦", q: "'चिव चिव चिमण्या' या पाठातून काय शिकायला मिळते?" },
            { icon: "🌌", q: "स्टीफन हॉकिंग यांच्या जीवनातून कोणती प्रेरणा मिळते?" },
            { icon: "🏔️", q: "'ध्येयपूर्तीचा ध्यास' या पाठातून काय संदेश मिळतो?" },
        ],
    };

    // Standard Titles and Details
    const standardTitles = {
        "6": { name: "इयत्ता ६ वी", title: "बालभारती (इयत्ता सहावी)", color: "#3b82f6" },
        "7": { name: "इयत्ता ७ वी", title: "बालभारती (इयत्ता सातवी)", color: "#10b981" },
        "8": { name: "इयत्ता ८ वी", title: "बालभारती (इयत्ता आठवी)", color: "#f59e0b" },
    };

    // Update Sample Questions in Sidebar
    function renderSampleQuestions(std) {
        const questions = sampleQuestionsByStandard[std] || sampleQuestionsByStandard["6"] || [];
        sampleContainer.innerHTML = "";

        questions.forEach((item) => {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.className = "sample-btn";
            btn.setAttribute("data-q", item.q);
            btn.innerHTML = `<span>${item.icon}</span> ${escapeHtml(item.q)}`;
            btn.addEventListener("click", () => {
                if (!isWaitingForResponse) {
                    submitQuestion(item.q);
                }
            });
            sampleContainer.appendChild(btn);
        });
    }

    // Switch Standard
    function setStandard(std) {
        currentStandard = String(std);

        // Update pills — apply standard color to active pill
        const meta = standardTitles[currentStandard] || standardTitles["6"];
        pillButtons.forEach((btn) => {
            if (btn.getAttribute("data-std") === currentStandard) {
                btn.classList.add("active");
                btn.style.borderColor = meta.color || "#3b82f6";
                btn.style.backgroundColor = (meta.color || "#3b82f6") + "22";
                btn.style.color = meta.color || "#3b82f6";
            } else {
                btn.classList.remove("active");
                btn.style.borderColor = "";
                btn.style.backgroundColor = "";
                btn.style.color = "";
            }
        });

        // Update dropdown
        if (standardSelect) {
            standardSelect.value = currentStandard;
        }

        // Update info card and active label
        if (infoStandardName) infoStandardName.textContent = `${meta.name} (${meta.title})`;
        if (activeStdLabel) activeStdLabel.textContent = `${meta.name} बालभारती`;

        // Update chunk count label from fetched standards data
        if (standardsData.length) {
            const stdInfo = standardsData.find((s) => String(s.standard) === currentStandard);
            if (stdInfo && infoChunkCount) {
                infoChunkCount.textContent = stdInfo.is_indexed
                    ? `${stdInfo.chunk_count} Chunks (${meta.name})`
                    : "Not indexed yet";
            }
        }

        // Update welcome message if present
        const welcomeCard = document.getElementById("welcome-card");
        if (welcomeCard && welcomeTitle && welcomeDesc) {
            welcomeTitle.textContent = `नमस्कार! मी तुमचा ${meta.name} चा मराठी शिक्षक आहे.`;
            welcomeDesc.innerHTML = `मी तुमच्या <strong>${meta.title}</strong> मधील अधिकृत माहितीच्या आधारे थेट आणि सोप्या भाषेत उत्तरे देतो.`;
        }

        // Render standard-specific sample questions
        renderSampleQuestions(currentStandard);
    }

    // Event Listeners for Pill Buttons
    pillButtons.forEach((btn) => {
        btn.addEventListener("click", () => {
            const std = btn.getAttribute("data-std");
            if (std) setStandard(std);
        });
    });

    // Event Listener for Sidebar Dropdown
    if (standardSelect) {
        standardSelect.addEventListener("change", (e) => {
            setStandard(e.target.value);
        });
    }

    // Check backend health & fetch standards info
    async function checkHealthAndStandards() {
        try {
            const healthRes = await fetch("/api/health");
            const healthData = await healthRes.json();
            if (healthData.status === "healthy") {
                statusText.textContent = "सिस्टम सज्ज (Connected)";
                statusText.style.color = "#10b981";
            } else {
                statusText.textContent = "सिस्टम सुरू होत आहे...";
                statusText.style.color = "#f59e0b";
            }

            const stdRes = await fetch("/api/standards");
            standardsData = await stdRes.json();
            if (Array.isArray(standardsData)) {
                let totalChunks = 0;
                standardsData.forEach((s) => {
                    totalChunks += s.chunk_count || 0;
                });
                if (infoChunkCount) {
                    const activeInfo = standardsData.find((s) => String(s.standard) === currentStandard);
                    if (activeInfo) {
                        infoChunkCount.textContent = `${activeInfo.chunk_count} Chunks (${activeInfo.name})`;
                    } else {
                        infoChunkCount.textContent = `${totalChunks} Chunks (Total)`;
                    }
                }
            }
        } catch (err) {
            statusText.textContent = "सर्व्हरशी संपर्क नाही";
            statusText.style.color = "#ef4444";
        }
    }

    checkHealthAndStandards();
    setInterval(checkHealthAndStandards, 15000);

    // Initial setup with Standard 6
    setStandard("6");

    // Auto-resize textarea
    questionInput.addEventListener("input", () => {
        questionInput.style.height = "auto";
        questionInput.style.height = Math.min(questionInput.scrollHeight, 120) + "px";
    });

    // Handle Enter to submit, Shift+Enter for newline
    questionInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            submitCurrentQuestion();
        }
    });

    // Clear chat
    clearBtn.addEventListener("click", () => {
        const meta = standardTitles[currentStandard] || standardTitles["6"];
        chatMessages.innerHTML = `
            <div class="welcome-card" id="welcome-card">
                <div class="welcome-icon">🎓</div>
                <h2>नवीन संवाद सुरू झाला आहे!</h2>
                <p><strong>${meta.name}</strong> मधील कोणत्याही पाठाविषयी किंवा कवितेविषयी प्रश्न विचारा.</p>
            </div>
        `;
    });

    // Form submission
    chatForm.addEventListener("submit", (e) => {
        e.preventDefault();
        submitCurrentQuestion();
    });

    function submitCurrentQuestion() {
        const question = questionInput.value.trim();
        if (!question || isWaitingForResponse) return;
        submitQuestion(question);
    }

    async function submitQuestion(questionText) {
        const question = questionText.trim();
        if (!question || isWaitingForResponse) return;

        // Remove welcome card if present
        const welcomeCard = document.getElementById("welcome-card");
        if (welcomeCard) welcomeCard.remove();

        // Append User Message with Standard Tag
        appendUserMessage(question, currentStandard);
        questionInput.value = "";
        questionInput.style.height = "auto";

        // Append Temporary Tutor Loading Card
        const loadingMessageId = "loading-" + Date.now();
        appendLoadingMessage(loadingMessageId);
        scrollToBottom();

        // Set Loading State
        setLoadingState(true);

        try {
            const response = await fetch("/api/ask", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    question: question,
                    standard: currentStandard,
                }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || "सर्व्हरकडून त्रुटी आली.");
            }

            const data = await response.json();
            replaceLoadingWithAnswer(loadingMessageId, data);
        } catch (error) {
            replaceLoadingWithError(loadingMessageId, error.message);
        } finally {
            setLoadingState(false);
            scrollToBottom();
        }
    }

    function setLoadingState(loading) {
        isWaitingForResponse = loading;
        sendBtn.disabled = loading;
        if (loading) {
            sendBtn.classList.add("loading");
        } else {
            sendBtn.classList.remove("loading");
            questionInput.focus();
        }
    }

    function appendUserMessage(text, std) {
        const meta = standardTitles[std] || standardTitles["6"];
        const msgDiv = document.createElement("div");
        msgDiv.className = "message user";
        msgDiv.innerHTML = `
            <div class="avatar">👤</div>
            <div class="message-content">
                <div class="std-chip">${escapeHtml(meta.name)}</div>
                <div class="message-text">${escapeHtml(text)}</div>
            </div>
        `;
        chatMessages.appendChild(msgDiv);
    }

    function appendLoadingMessage(id) {
        const msgDiv = document.createElement("div");
        msgDiv.className = "message tutor";
        msgDiv.id = id;
        msgDiv.innerHTML = `
            <div class="avatar">🎓</div>
            <div class="message-content">
                <div class="message-text">
                    <em>📖 पाठ्यपुस्तकात माहिती शोधत आहे व उत्तर तयार करत आहे...</em>
                </div>
            </div>
        `;
        chatMessages.appendChild(msgDiv);
    }

    function replaceLoadingWithAnswer(id, data) {
        const msgDiv = document.getElementById(id);
        if (!msgDiv) return;

        let parsedAnswer = data.answer;
        if (window.marked && window.marked.parse) {
            parsedAnswer = window.marked.parse(data.answer);
        }

        const transliterationHtml = (data.marathi_question && data.marathi_question !== data.question)
            ? `<div class="transliteration-badge">
                   <span class="badge-icon">🔤</span>
                   <span class="badge-label">मराठी रूपांतरण:</span>
                   <span class="badge-text">${escapeHtml(data.marathi_question)}</span>
               </div>`
            : "";

        msgDiv.innerHTML = `
            <div class="avatar">🎓</div>
            <div class="message-content">
                ${transliterationHtml}
                <div class="message-text">${parsedAnswer}</div>
            </div>
        `;
    }

    function replaceLoadingWithError(id, errorMessage) {
        const msgDiv = document.getElementById(id);
        if (!msgDiv) return;
        msgDiv.innerHTML = `
            <div class="avatar">⚠️</div>
            <div class="message-content" style="border-color: #ef4444;">
                <div class="message-text" style="color: #f87171;">
                    <strong>त्रुटी आली:</strong> ${escapeHtml(errorMessage)}
                </div>
            </div>
        `;
    }

    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function escapeHtml(str) {
        if (!str) return "";
        return str
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});
