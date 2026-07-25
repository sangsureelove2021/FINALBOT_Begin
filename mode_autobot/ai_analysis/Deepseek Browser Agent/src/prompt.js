// src/prompt.js — System prompt and conversation builder
'use strict';

const config = require('./config');

// ─────────────────────────────────────────────
//  System prompt — sent as the first message
// ─────────────────────────────────────────────

function buildSystemPrompt() {
  return "";
}

// ─────────────────────────────────────────────
//  Conversation / message history manager
// ─────────────────────────────────────────────

class ConversationManager {
  constructor() {
    this.messages      = [];
    this._systemPrompt = null;
  }

  /**
   * Build the very first user message that includes the system prompt,
   * working-directory context, and the user's task.
   */
  buildFirstMessage(task, workingDirListing) {
    this._systemPrompt = "";

    const firstMessage = task;

    this.messages.push({ role: 'user', content: firstMessage });
    return firstMessage;
  }

  /**
   * Add a tool result as a user-turn message (feeding results back to the AI).
   */
  addToolResult(toolName, result, isError) {
    const status  = isError ? 'ERROR' : 'SUCCESS';
    const content = [
      '[TOOL RESULT: ' + toolName + ' | ' + status + ']',
      String(result),
      '[END TOOL RESULT]',
      '',
      'Continue with the next step, or provide your final response if the task is complete.',
    ].join('\n');

    this.messages.push({ role: 'user', content: content });
    return content;
  }

  /**
   * Add an assistant message (the AI's raw response).
   */
  addAssistantMessage(content) {
    this.messages.push({ role: 'assistant', content: content });
  }

  /**
   * Get the most recent user message content.
   */
  getLatestUserMessage() {
    const userMessages = this.messages.filter(function(m) { return m.role === 'user'; });
    return userMessages.length > 0 ? userMessages[userMessages.length - 1].content : '';
  }

  /**
   * How many assistant turns have happened.
   */
  get turnCount() {
    return this.messages.filter(function(m) { return m.role === 'assistant'; }).length;
  }

  /**
   * Export the full conversation as a readable text log.
   */
  exportLog() {
    return this.messages.map(function(m) {
      const header = m.role === 'user' ? 'USER' : 'ASSISTANT';
      return '\n' + '─'.repeat(40) + '\n' + header + '\n' + '─'.repeat(40) + '\n' + m.content;
    }).join('\n');
  }
}

module.exports = { buildSystemPrompt, ConversationManager };
