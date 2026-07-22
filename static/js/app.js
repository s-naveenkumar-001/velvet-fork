class Chatbox {
    constructor() {
        this.args = {
            openButton: document.querySelector('.chatbox__button'),
            chatBox: document.querySelector('.chatbox__support'),
            sendButton: document.querySelector('.send__button'),
            fullscreenButton: document.querySelector('[data-chatbox-fullscreen-btn]')
        }
        this.state = false;
        this.isFullscreen = false;
        this.messages = [];
    }

    display() {
        const {openButton, chatBox, sendButton, fullscreenButton} = this.args;

        openButton.addEventListener('click', () => this.toggleState(chatBox))
        sendButton.addEventListener('click', () => this.onSendButton(chatBox))
        fullscreenButton.addEventListener('click', () => this.toggleFullscreen(chatBox))

        const node = chatBox.querySelector('input');
        node.addEventListener('keyup', ({key}) => {
            if (key === 'Enter') {
                this.onSendButton(chatBox)
            }
        })
    }

    toggleFullscreen(chatBox) {
        this.isFullscreen = !this.isFullscreen;
        chatBox.classList.toggle('chatbox--fullscreen', this.isFullscreen);
        document.body.classList.toggle('chatbox-fullscreen-lock', this.isFullscreen);

        const useEl = this.args.fullscreenButton.querySelector('use');
        useEl.setAttribute('href', this.isFullscreen ? '#icon-contract-outline' : '#icon-expand-outline');
        this.args.fullscreenButton.setAttribute(
            'aria-label',
            this.isFullscreen ? 'Exit full screen' : 'Toggle full screen'
        );
    }

    toggleState(chatBox) {
        this.state = !this.state;

        if (this.state) {
            chatBox.classList.add('chatbox--active')
        } else {
            chatBox.classList.remove('chatbox--active')
            if (this.isFullscreen) {
                this.toggleFullscreen(chatBox);
            }
        }
    }

    onSendButton(chatbox) {
        const textField = chatbox.querySelector('input');
        const text1 = textField.value.trim();
        if (text1 === '') {
            return;
        }

        const msg1 = {name: 'User', message: text1};
        this.messages.push(msg1);
        textField.value = '';
        this.updateChatText(chatbox);

        fetch('/predict', {
            method: 'POST',
            body: JSON.stringify({message: text1}),
            mode: 'cors',
            headers: {
                'Content-Type': 'application/json'
            },
        })
        .then(r => r.json())
        .then(r => {
            const reply = r.answer || r.message || "Sorry, something went wrong. Please try again.";
            const msg2 = {name: 'Aether', message: reply};
            this.messages.push(msg2);
            this.updateChatText(chatbox);
        }).catch((error) => {
            console.error('Error:', error);
            this.messages.push({name: 'Aether', message: "Sorry, I couldn't reach the server. Please try again."});
            this.updateChatText(chatbox);
        });
    }

    updateChatText(chatbox) {
        const chatmessage = chatbox.querySelector('.chatbox__messages');
        chatmessage.replaceChildren();

        this.messages.slice().reverse().forEach((item) => {
            const bubble = document.createElement('div');
            const isAether = item.name === 'Aether';
            bubble.className = 'messages__item ' + (isAether ? 'messages__item--visitor' : 'messages__item--operator');

            if (isAether) {
                const html = renderMarkdownLite(item.message);
                bubble.innerHTML = html;
                if (bubble.querySelector('table')) {
                    bubble.classList.add('messages__item--wide');
                }
            } else {
                bubble.textContent = item.message;
            }
            chatmessage.appendChild(bubble);
        });
    }
}

function escapeHtml(str) {
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function inlineMd(escapedText) {
    return escapedText
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/(^|[^*])\*(?!\*)([^*]+)\*(?!\*)/g, '$1<em>$2</em>');
}

// Minimal, safe (HTML-escaped) Markdown-lite renderer: supports GFM tables,
// bullet/numbered lists, bold/italic, and paragraphs. Free-tier models don't
// always emit a clean separator row, so the separator check is lenient.
function renderMarkdownLite(text) {
    const lines = text.replace(/\r\n/g, '\n').split('\n');
    let html = '';
    let i = 0;

    const isTableRow = (line) => /^\s*\|.*\|\s*$/.test(line);
    const isSeparatorRow = (line) => isTableRow(line) && /^[\s|:-]+$/.test(line) && line.includes('-');
    const splitRow = (line) => line.trim().replace(/^\||\|$/g, '').split('|').map((c) => c.trim());

    while (i < lines.length) {
        const line = lines[i];

        if (isTableRow(line) && i + 1 < lines.length && isSeparatorRow(lines[i + 1])) {
            const headerCells = splitRow(line);
            html += '<table class="chat-table"><thead><tr>' +
                headerCells.map((c) => `<th>${inlineMd(escapeHtml(c))}</th>`).join('') +
                '</tr></thead><tbody>';
            i += 2;
            while (i < lines.length && isTableRow(lines[i])) {
                const rowCells = splitRow(lines[i]);
                html += '<tr>' + rowCells.map((c) => `<td>${inlineMd(escapeHtml(c))}</td>`).join('') + '</tr>';
                i++;
            }
            html += '</tbody></table>';
            continue;
        }

        if (/^\s*[-*]\s+/.test(line)) {
            html += '<ul>';
            while (i < lines.length && /^\s*[-*]\s+/.test(lines[i])) {
                html += `<li>${inlineMd(escapeHtml(lines[i].replace(/^\s*[-*]\s+/, '')))}</li>`;
                i++;
            }
            html += '</ul>';
            continue;
        }

        if (/^\s*\d+\.\s+/.test(line)) {
            html += '<ol>';
            while (i < lines.length && /^\s*\d+\.\s+/.test(lines[i])) {
                html += `<li>${inlineMd(escapeHtml(lines[i].replace(/^\s*\d+\.\s+/, '')))}</li>`;
                i++;
            }
            html += '</ol>';
            continue;
        }

        if (line.trim() === '') {
            i++;
            continue;
        }

        html += `<p>${inlineMd(escapeHtml(line))}</p>`;
        i++;
    }

    return html || escapeHtml(text);
}

const chatbox = new Chatbox();
chatbox.display();
