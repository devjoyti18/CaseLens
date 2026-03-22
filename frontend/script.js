// Tab switching logic
const chatbotTab = document.getElementById('chatbot-tab');
const uploadTab = document.getElementById('upload-tab');
const chatbotContent = document.getElementById('chatbot-content');
const uploadContent = document.getElementById('upload-content');

chatbotTab.addEventListener('click', () => {
    chatbotTab.classList.add('active');
    uploadTab.classList.remove('active');
    chatbotContent.classList.remove('hidden');
    uploadContent.classList.add('hidden');
});

uploadTab.addEventListener('click', () => {
    uploadTab.classList.add('active');
    chatbotTab.classList.remove('active');
    uploadContent.classList.remove('hidden');
    chatbotContent.classList.add('hidden');
});

// Chatbot logic
const chatWindow = document.getElementById('chat-window');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');
const downloadBtn = document.getElementById('download-chat');
const clearBtn = document.getElementById('clear-chat');

let chatHistory = [];

function appendMessage(sender, text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = text;
    messageDiv.appendChild(contentDiv);
    chatWindow.appendChild(messageDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

function addToHistory(sender, text) {
    chatHistory.push({ sender, text });
}

// handleSend is now replaced by sendQuery for backend integration

function getSampleBotResponse(userText) {
    // Simple sample responses
    const samples = [
        "Hello! How can I help you with your contract?",
        "I'm here to answer your contract-related questions.",
        "Please upload a document if you'd like me to analyze it.",
        "Could you clarify your question?"
    ];
    if (userText.toLowerCase().includes('hello')) return samples[0];
    if (userText.toLowerCase().includes('contract')) return samples[1];
    if (userText.toLowerCase().includes('upload')) return samples[2];
    return samples[3];
}

sendBtn.addEventListener('click', handleSend);
chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') handleSend();
});
sendBtn.addEventListener('click', sendQuery);
chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') sendQuery();
});

clearBtn.addEventListener('click', () => {
    chatWindow.innerHTML = '';
    chatHistory = [];
});

downloadBtn.addEventListener('click', () => {
    if (chatHistory.length === 0) return;
    // Dynamically load jsPDF if not already loaded
    if (typeof window.jspdf === 'undefined') {
        const script = document.createElement('script');
        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js';
        script.onload = () => generatePDF();
        document.body.appendChild(script);
    } else {
        generatePDF();
    }

    function generatePDF() {
        const { jsPDF } = window.jspdf || window.jspdf_umd;
        const doc = new jsPDF();
        let y = 15;
        doc.setFontSize(12);
        chatHistory.forEach(msg => {
            let lines = doc.splitTextToSize(`${msg.sender}: ${msg.text}`, 180);
            lines.forEach(line => {
                if (y > 280) {
                    doc.addPage();
                    y = 15;
                }
                doc.text(line, 15, y);
                y += 8;
            });
        });
        doc.save('chat_history.pdf');
    }
});


// // ===== Document upload logic (Browser-only, no server) =====

// const uploadForm = document.getElementById('upload-form');
// const uploadStatus = document.getElementById('upload-status');

// let rawDataDirHandle = null;

// uploadForm.addEventListener('submit', async (e) => {
//     e.preventDefault();

//     const fileInput = document.getElementById('file-upload');
//     if (!fileInput.files.length) {
//         uploadStatus.textContent = 'Please select a file.';
//         uploadStatus.style.color = '#d70022';
//         return;
//     }

//     try {
//         // Ask user to select rawData folder ONCE
//         if (!rawDataDirHandle) {
//             rawDataDirHandle = await window.showDirectoryPicker({
//                 mode: 'readwrite'
//             });
//         }

//         const file = fileInput.files[0];

//         // Create file inside rawData
//         const fileHandle = await rawDataDirHandle.getFileHandle(file.name, {
//             create: true
//         });

//         const writable = await fileHandle.createWritable();
//         await writable.write(file);
//         await writable.close();

//         uploadStatus.textContent =
//             `Saved to rag/dataStore/rawData → ${file.name} ✅`;
//         uploadStatus.style.color = '#0078d7';

//         uploadForm.reset();
//     } catch (err) {
//         uploadStatus.textContent = 'Upload cancelled or failed ❌';
//         uploadStatus.style.color = '#d70022';
//         console.error(err);
//     }
// });








// // ===== Query → Python RAG =====

// async function sendQuery() {
//     const queryInput = document.getElementById("chat-input");
//     const responseBox = document.getElementById("send-btn");

//     const query = queryInput.value.trim();
//     if (!query) return;

//     // Show user message in chat
//     appendMessage('user', query);
//     addToHistory('User', query);
//     queryInput.value = '';

//     // Show bot thinking message
//     const thinkingDiv = document.createElement('div');
//     thinkingDiv.className = 'message bot';
//     const thinkingContent = document.createElement('div');
//     thinkingContent.className = 'message-content';
//     thinkingContent.textContent = 'Thinking...';
//     thinkingDiv.appendChild(thinkingContent);
//     chatWindow.appendChild(thinkingDiv);
//     chatWindow.scrollTop = chatWindow.scrollHeight;

//     try {
//         const res = await fetch("http://127.0.0.1:5000/query", {
//             method: "POST",
//             headers: {
//                 "Content-Type": "application/json"
//             },
//             body: JSON.stringify({ query })
//         });
//         const data = await res.json();
//         // Remove 'Thinking...' message
//         chatWindow.removeChild(thinkingDiv);
//         if (data.answer) {
//             appendMessage('bot', data.answer);
//             addToHistory('Bot', data.answer);
//         } else {
//             appendMessage('bot', '❌ No answer received.');
//             addToHistory('Bot', '❌ No answer received.');
//         }
//     } catch (err) {
//         chatWindow.removeChild(thinkingDiv);
//         appendMessage('bot', '❌ Error connecting to RAG backend');
//         addToHistory('Bot', '❌ Error connecting to RAG backend');
//         console.error(err);
//     }
// }
