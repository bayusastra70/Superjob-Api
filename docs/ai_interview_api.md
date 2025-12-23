# AI Interview Feature Documentation

## Overview

The AI Interview feature provides an interactive mock interview experience powered by AI. Candidates can conduct practice interviews with an AI interviewer that adapts questions based on the selected position and experience level. The system supports both text and audio inputs, provides real-time feedback, and delivers comprehensive post-interview evaluations.

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Application                        │
└─────────────────────────────┬───────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │ REST API            │ WebSocket           │
        ▼                     ▼                     │
┌───────────────┐    ┌────────────────────┐        │
│ Interview     │    │ Interview WS       │        │
│ Router        │    │ Handler            │        │
└───────┬───────┘    └─────────┬──────────┘        │
        │                      │                    │
        │            ┌─────────▼──────────┐        │
        │            │ InterviewRuntime   │        │
        │            │ Service            │        │
        │            └─────────┬──────────┘        │
        │                      │                    │
        │    ┌─────────────────┼─────────────────┐ │
        │    │                 │                 │ │
        ▼    ▼                 ▼                 ▼ │
┌───────────────┐    ┌────────────────┐    ┌──────┴────┐
│ Interview     │    │ OpenRouter     │    │ STT       │
│ Repository    │    │ Service        │    │ Service   │
└───────┬───────┘    └───────┬────────┘    └───────────┘
        │                    │
        ▼                    ▼
┌───────────────┐    ┌────────────────┐
│ PostgreSQL    │    │ OpenRouter API │
│ Database      │    │ (LLM Provider) │
└───────────────┘    └────────────────┘
```

### Key Services

| Service               | Location                               | Description                                 |
| --------------------- | -------------------------------------- | ------------------------------------------- |
| `InterviewRepository` | `app/services/interview_repository.py` | Database operations for sessions & messages |
| `InterviewRuntime`    | `app/services/interview_service.py`    | Core interview logic and WebSocket handling |
| `OpenRouterService`   | `app/services/openrouter_service.py`   | AI/LLM integration via OpenRouter           |
| `STTService`          | `app/services/stt_service.py`          | Speech-to-text transcription (Deepgram)     |
| `TTSService`          | `app/services/tts_service.py`          | Text-to-speech synthesis (Deepgram)         |

---

## Deepgram Integration (Speech-to-Text & Text-to-Speech)

### Overview

Deepgram provides both Speech-to-Text (STT) and Text-to-Speech (TTS) capabilities for the AI Interview feature:

- **STT**: Allows candidates to speak their answers instead of typing
- **TTS**: AI Interviewer speaks questions, feedback, and messages aloud

Deepgram offers a free tier with $200 credit on signup.

### Configuration

Set the following environment variable:

```bash
# Required for speech features
DEEPGRAM_API_KEY=your-deepgram-api-key
```

### STTService API

```python
from app.services.stt_service import STTService

stt = STTService()

# Transcribe audio bytes
transcript = await stt.transcribe(
    audio_bytes=audio_data,
    mimetype="audio/webm",  # Supported: webm, wav, mp3
    language="en"
)
```

### TTSService API

```python
from app.services.tts_service import TTSService

tts = TTSService()

# Synthesize speech (returns bytes)
audio_bytes = await tts.synthesize(
    text="Hello, welcome to your interview!",
    voice="aura-asteria-en",  # Optional, defaults to asteria
    encoding="mp3"  # Supported: mp3, wav, flac, aac
)

# Synthesize speech as base64 (for WebSocket)
audio_base64 = await tts.synthesize_base64(
    text="Can you explain SOLID principles?",
)
```

### Available TTS Voices

| Voice ID          | Description                |
| ----------------- | -------------------------- |
| `aura-asteria-en` | Female, American (default) |
| `aura-luna-en`    | Female, American           |
| `aura-stella-en`  | Female, American           |
| `aura-athena-en`  | Female, British            |
| `aura-hera-en`    | Female, American           |
| `aura-orion-en`   | Male, American             |
| `aura-arcas-en`   | Male, American             |
| `aura-perseus-en` | Male, American             |
| `aura-angus-en`   | Male, Irish                |
| `aura-orpheus-en` | Male, American             |
| `aura-helios-en`  | Male, British              |
| `aura-zeus-en`    | Male, American             |

---

## OpenRouter Integration

### Overview

OpenRouter is used as the LLM provider for AI-powered interview interactions. It provides a unified API to access various AI models (OpenAI GPT, Anthropic Claude, etc.) through a single endpoint.

### Configuration

Set the following environment variables:

```bash
# Required: Your OpenRouter API key
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Optional: Model selection (defaults to openai/gpt-4.1-mini)
OPENROUTER_MODEL=openai/gpt-4.1-mini
```

### Supported Models

You can use any model available on OpenRouter. Some recommended options:

| Model                                 | Use Case                                   |
| ------------------------------------- | ------------------------------------------ |
| `openai/gpt-4.1-mini`                 | Default - good balance of quality and cost |
| `openai/gpt-4-turbo`                  | Higher quality, more expensive             |
| `anthropic/claude-3-haiku`            | Fast, cost-effective                       |
| `nvidia/nemotron-3-nano-30b-a3b:free` | Free tier option                           |

### OpenRouterService API

```python
from app.services.openrouter_service import OpenRouterService

# Initialize with defaults from settings
ai = OpenRouterService()

# Or with custom configuration
ai = OpenRouterService(
    api_key="your-api-key",
    model="openai/gpt-4-turbo"
)

# Chat completion
response = await ai.chat(
    messages=[
        {"role": "system", "content": "You are an interviewer..."},
        {"role": "user", "content": "My answer is..."}
    ],
    response_format={"type": "json_object"},  # Optional: for structured output
    timeout=30  # Timeout in seconds
)
```

### Request Format

The service sends requests to OpenRouter in this format:

```json
{
  "model": "openai/gpt-4.1-mini",
  "messages": [
    { "role": "system", "content": "..." },
    { "role": "user", "content": "..." }
  ],
  "response_format": { "type": "json_object" }
}
```

---

## REST API Endpoints

### Base URL

```
/api/v1/interview
```

### Create Interview Session

Creates a new interview session with the specified configuration.

**Endpoint:** `POST /sessions`

**Authentication:** Required (Bearer Token)

**Request Body:**

```json
{
  "position": "Software Engineer",
  "level": "Senior",
  "totalQuestions": 5,
  "type": "technical"
}
```

| Field            | Type    | Description                                  |
| ---------------- | ------- | -------------------------------------------- |
| `position`       | string  | Job position/role for the interview          |
| `level`          | string  | Experience level (Junior, Mid, Senior, etc.) |
| `totalQuestions` | integer | Number of questions in the interview         |
| `type`           | string  | Interview type (technical, behavioral, etc.) |

**Response:** `200 OK`

```json
{
  "sessionId": 123,
  "status": "active"
}
```

---

### List User Sessions

Retrieves all interview sessions for the authenticated user.

**Endpoint:** `GET /sessions`

**Authentication:** Required (Bearer Token)

**Response:** `200 OK`

```json
[
  {
    "id": 123,
    "status": "ended",
    "startedAt": "2024-01-15T10:30:00Z",
    "endedAt": "2024-01-15T11:00:00Z",
    "config": {
      "position": "Software Engineer",
      "level": "Senior",
      "totalQuestions": 5,
      "type": "technical"
    },
    "evaluation": {
      "score": 85,
      "feedback": "Excellent performance...",
      "status": "completed"
    }
  }
]
```

---

### Get Session Detail

Retrieves detailed information about a specific session including messages.

**Endpoint:** `GET /sessions/{session_id}`

**Authentication:** Required (Bearer Token)

**Response:** `200 OK`

```json
{
  "id": 123,
  "status": "active",
  "startedAt": "2024-01-15T10:30:00Z",
  "endedAt": null,
  "config": {
    "position": "Software Engineer",
    "level": "Senior",
    "totalQuestions": 5,
    "type": "technical"
  },
  "evaluation": null,
  "messages": [
    {
      "id": 1,
      "sender": "ai",
      "content": "Welcome to your interview...",
      "message_type": "intro",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

> **Note:** For active sessions, `intro` and `question` message types are filtered out to avoid duplicates with the live WebSocket stream.

---

### Get Interview History

Retrieves complete interview history for post-interview review (no message filtering).

**Endpoint:** `GET /history/{session_id}`

**Authentication:** Required (Bearer Token)

**Response:** Same as Get Session Detail, but includes ALL messages without filtering.

---

### End Session

Manually ends an active interview session.

**Endpoint:** `POST /sessions/{session_id}/end`

**Authentication:** Required (Bearer Token)

**Response:** `204 No Content`

---

## WebSocket API

### Connection

**URL:** `ws://host/api/v1/ws/interview/{session_id}?token={jwt_token}`

**Authentication:** JWT token passed as query parameter

### Connection Flow

```
Client                                Server
   |                                     |
   |--- WebSocket Connect -------------→ |
   |                                     |
   |←-- Connection Accepted -------------|
   |                                     |
   |←-- INTRO Event -------------------- |
   |                                     |
   |←-- QUESTION Event ----------------- |
   |                                     |
   |--- USER_TEXT_ANSWER --------------→ |
   |                                     |
   |←-- FEEDBACK Event ----------------- |
   |                                     |
   |←-- QUESTION Event ----------------- |
   |                                     |
   |    ... (repeat Q&A cycle) ...       |
   |                                     |
   |←-- END_INTERVIEW Event ------------ |
   |                                     |
```

### Client → Server Events

#### USER_TEXT_ANSWER

Send a text answer to the current question.

```json
{
  "type": "USER_TEXT_ANSWER",
  "payload": {
    "message": "My answer is..."
  }
}
```

#### USER_AUDIO_CHUNK

Send an audio chunk for speech-to-text transcription (Deepgram).

```json
{
  "type": "USER_AUDIO_CHUNK",
  "payload": {
    "chunk": "<base64-encoded-audio>",
    "isFirst": true
  }
}
```

| Field     | Type    | Description                                             |
| --------- | ------- | ------------------------------------------------------- |
| `chunk`   | string  | Base64-encoded audio data                               |
| `isFirst` | boolean | Set to `true` for the first chunk to reset audio buffer |

**Supported Audio Formats:** WebM, WAV, MP3

#### USER_AUDIO_END

Signal end of audio stream for transcription.

```json
{
  "type": "USER_AUDIO_END",
  "payload": {}
}
```

After receiving this event, the server will:

1. Send the accumulated audio to Deepgram for transcription
2. Return a `TRANSCRIPT_FINAL` event with the transcribed text
3. Automatically process the transcript as a `USER_TEXT_ANSWER`

#### CONTROL_UPDATE

Update interview controls (e.g., pause, resume).

```json
{
  "type": "CONTROL_UPDATE",
  "payload": {
    "action": "pause"
  }
}
```

#### HANGUP

End the interview session early.

```json
{
  "type": "HANGUP",
  "payload": {}
}
```

### Server → Client Events

#### INTRO

AI interviewer introduction at session start.

```json
{
  "type": "INTRO",
  "payload": {
    "message": "Welcome! I'm your AI interviewer today..."
  }
}
```

| Field     | Type   | Description       |
| --------- | ------ | ----------------- |
| `message` | string | Introduction text |

> **Note:** Audio is streamed separately via `AUDIO_CHUNK` events when `DEEPGRAM_API_KEY` is configured.

#### QUESTION

A new interview question.

```json
{
  "type": "QUESTION",
  "payload": {
    "message": "Can you explain the SOLID principles?",
    "questionNumber": 1
  }
}
```

| Field            | Type    | Description                         |
| ---------------- | ------- | ----------------------------------- |
| `message`        | string  | The interview question text         |
| `questionNumber` | integer | Current question number (1-indexed) |

#### FEEDBACK

AI feedback on the user's answer.

```json
{
  "type": "FEEDBACK",
  "payload": {
    "message": "Great answer! You covered the key points..."
  }
}
```

| Field     | Type   | Description   |
| --------- | ------ | ------------- |
| `message` | string | Feedback text |

#### TRANSCRIPT_FINAL

Final transcription of audio input.

```json
{
  "type": "TRANSCRIPT_FINAL",
  "payload": {
    "text": "Transcribed audio content..."
  }
}
```

#### END_INTERVIEW

Interview session has ended.

```json
{
  "type": "END_INTERVIEW",
  "payload": {
    "message": "Thank you for completing the interview...",
    "sessionId": 123
  }
}
```

| Field       | Type    | Description              |
| ----------- | ------- | ------------------------ |
| `message`   | string  | Closing message text     |
| `sessionId` | integer | The interview session ID |

#### AUDIO_CHUNK

Streaming audio chunk from TTS. These events are sent after text events (INTRO, QUESTION, FEEDBACK, END_INTERVIEW) when `DEEPGRAM_API_KEY` is configured.

```json
{
  "type": "AUDIO_CHUNK",
  "payload": {
    "chunk": "<base64-encoded-audio>",
    "messageType": "question",
    "index": 0
  }
}
```

| Field         | Type    | Description                                    |
| ------------- | ------- | ---------------------------------------------- |
| `chunk`       | string  | Base64-encoded audio chunk (linear16 PCM)      |
| `messageType` | string  | Source message type: intro, question, feedback, end |
| `index`       | integer | Chunk index (0-based)                          |

#### AUDIO_END

Signals that all audio chunks for a message have been sent.

```json
{
  "type": "AUDIO_END",
  "payload": {
    "messageType": "question",
    "totalChunks": 15
  }
}
```

| Field         | Type    | Description                                    |
| ------------- | ------- | ---------------------------------------------- |
| `messageType` | string  | Source message type: intro, question, feedback, end |
| `totalChunks` | integer | Total number of chunks sent                    |

#### ERROR

Error notification.

```json
{
  "type": "ERROR",
  "payload": {
    "message": "An error occurred..."
  }
}
```

---

## Data Models

### InterviewSession

| Field                    | Type     | Description                                    |
| ------------------------ | -------- | ---------------------------------------------- |
| `id`                     | integer  | Primary key                                    |
| `user_id`                | integer  | Owner user ID                                  |
| `status`                 | string   | Session status: `active`, `ended`              |
| `started_at`             | datetime | Session start time                             |
| `ended_at`               | datetime | Session end time (nullable)                    |
| `position`               | string   | Job position                                   |
| `level`                  | string   | Experience level                               |
| `total_questions`        | integer  | Total question count                           |
| `interview_type`         | string   | Interview type                                 |
| `question_count`         | integer  | Questions completed                            |
| `current_question_index` | integer  | Current question number                        |
| `ai_score`               | integer  | AI evaluation score (0-100)                    |
| `ai_feedback`            | string   | AI evaluation feedback                         |
| `evaluation_status`      | string   | `pending`, `processing`, `completed`, `failed` |

### InterviewMessage

| Field          | Type     | Description                                |
| -------------- | -------- | ------------------------------------------ |
| `id`           | integer  | Primary key                                |
| `session_id`   | integer  | Parent session ID                          |
| `sender`       | string   | `ai` or `user`                             |
| `role`         | string   | OpenAI role: `system`, `assistant`, `user` |
| `content`      | string   | Message content                            |
| `message_type` | string   | Message category (see below)               |
| `created_at`   | datetime | Creation timestamp                         |

### Message Types

| Type         | Sender | Description                     |
| ------------ | ------ | ------------------------------- |
| `intro`      | ai     | Initial introduction message    |
| `question`   | ai     | Interview question              |
| `answer`     | user   | User's answer                   |
| `feedback`   | ai     | Feedback on user's answer       |
| `transcript` | user   | Audio transcription             |
| `system`     | ai     | System messages (e.g., closing) |

---

## Interview Flow

### Session Lifecycle

```
┌─────────────────┐
│ Create Session  │  POST /sessions
│ status: active  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ WebSocket       │  Connect to ws://.../{session_id}
│ Connection      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ AI Introduction │  ← INTRO event
│ First Question  │  ← QUESTION event
└────────┬────────┘
         │
    ┌────▼────┐
    │ Q&A     │  USER_TEXT_ANSWER → FEEDBACK → QUESTION
    │ Cycle   │  (repeats for totalQuestions)
    └────┬────┘
         │
         ▼
┌─────────────────┐
│ Session End     │  ← END_INTERVIEW event
│ status: ended   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ AI Evaluation   │  Background task
│ score & feedback│
└─────────────────┘
```

### Question Flow Detail

For each question (except the last):

1. User sends `USER_TEXT_ANSWER`
2. AI generates and sends `FEEDBACK`
3. AI generates and sends next `QUESTION`
4. `current_question_index` increments

For the last question:

1. User sends `USER_TEXT_ANSWER`
2. AI generates closing message
3. Server sends `END_INTERVIEW`
4. Background evaluation task starts

---

## AI Evaluation

### Overview

When an interview ends (either by completing all questions or user hangup), a background task evaluates the interview and generates:

- **Score**: 0-100 rating of performance
- **Feedback**: Comprehensive written evaluation

### Evaluation Process

```python
# Evaluation prompt structure
{
    "role": "system",
    "content": """
    You are an expert interview evaluator...
    Your response MUST be a valid JSON object:
    - "score": integer from 0 to 100
    - "feedback": comprehensive evaluation covering:
      * Overall performance assessment
      * Key strengths demonstrated
      * Areas for improvement
      * Specific recommendations
    """
}
```

### Evaluation Status

| Status       | Description                      |
| ------------ | -------------------------------- |
| `pending`    | Interview not yet evaluated      |
| `processing` | Evaluation in progress           |
| `completed`  | Evaluation finished successfully |
| `failed`     | Evaluation encountered an error  |

### Triggering Evaluation

Evaluation is automatically triggered when:

- User completes all questions (answers final question)
- User ends interview early (HANGUP event)
- Session is manually ended via REST API

---

## Configuration

### Environment Variables

```bash
# OpenRouter Configuration (Required for AI)
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxx  # Required
OPENROUTER_MODEL=openai/gpt-4.1-mini       # Optional, default shown

# Deepgram Configuration (Required for speech features)
DEEPGRAM_API_KEY=your-deepgram-api-key     # Required for STT/TTS
```

### Timeouts

| Operation          | Default Timeout |
| ------------------ | --------------- |
| Regular chat       | 30 seconds      |
| Evaluation         | 60 seconds      |
| WebSocket messages | No timeout      |

---

## Error Handling

### WebSocket Error Codes

| Code | Reason            | Description                        |
| ---- | ----------------- | ---------------------------------- |
| 4401 | Unauthorized      | Invalid or missing JWT token       |
| 4404 | Session not found | Invalid session ID or unauthorized |

### REST API Errors

| Status | Description                             |
| ------ | --------------------------------------- |
| 401    | Unauthorized - Missing or invalid token |
| 404    | Session not found                       |
| 500    | Internal server error                   |

---

## Best Practices

### Client Implementation

1. **Handle Reconnection**: Store the `sessionId` and reconnect to resume if disconnected. The server will resend the current question.

2. **Message Deduplication**: For active sessions, the REST API filters `intro` and `question` messages. Use WebSocket for real-time updates.

3. **Audio Input**: Buffer audio chunks and send with `isFirst: true` for the first chunk. Supported formats: WebM, WAV, MP3.

4. **Audio Output**: When `DEEPGRAM_API_KEY` is configured, server events include an `audio` field with base64-encoded MP3. Play this audio to give the AI interviewer a voice.

5. **Graceful Shutdown**: Always send `HANGUP` event before closing the connection to ensure evaluation runs.

### Performance Tips

1. **Evaluation Delay**: AI evaluation runs asynchronously. Poll the session endpoint or use Socket.IO for real-time updates.

2. **Token Management**: JWT tokens should be refreshed before WebSocket connection if near expiry.

---

## Example Usage

### Creating and Running an Interview

```javascript
// 1. Create session
const response = await fetch("/api/v1/interview/sessions", {
  method: "POST",
  headers: {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    position: "Software Engineer",
    level: "Senior",
    totalQuestions: 5,
    type: "technical",
  }),
});
const { sessionId } = await response.json();

// 2. Connect WebSocket
const ws = new WebSocket(
  `ws://localhost:8000/api/v1/ws/interview/${sessionId}?token=${token}`
);

// Audio streaming state
const audioPlayer = createStreamingAudioPlayer();

ws.onmessage = (event) => {
  const { type, payload } = JSON.parse(event.data);

  switch (type) {
    case "INTRO":
      displayMessage(payload.message, "ai");
      break;
    case "QUESTION":
      displayQuestion(payload.message, payload.questionNumber);
      break;
    case "FEEDBACK":
      displayFeedback(payload.message);
      break;
    case "TRANSCRIPT_FINAL":
      displayTranscript(payload.text);
      break;
    case "END_INTERVIEW":
      handleInterviewEnd(payload);
      break;
    case "AUDIO_CHUNK":
      // Buffer streaming audio chunks
      audioPlayer.addChunk(payload.chunk, payload.messageType);
      break;
    case "AUDIO_END":
      // All chunks received, start playback
      audioPlayer.play(payload.messageType);
      break;
    case "ERROR":
      handleError(payload.message);
      break;
  }
};

// Streaming audio player for TTS chunks
function createStreamingAudioPlayer() {
  const audioBuffers = {};
  
  return {
    addChunk(base64Chunk, messageType) {
      if (!audioBuffers[messageType]) {
        audioBuffers[messageType] = [];
      }
      audioBuffers[messageType].push(base64Chunk);
    },
    
    async play(messageType) {
      const chunks = audioBuffers[messageType];
      if (!chunks || chunks.length === 0) return;
      
      // Combine all chunks into single audio blob
      const binaryChunks = chunks.map(b64 => 
        Uint8Array.from(atob(b64), c => c.charCodeAt(0))
      );
      const totalLength = binaryChunks.reduce((acc, c) => acc + c.length, 0);
      const combined = new Uint8Array(totalLength);
      let offset = 0;
      for (const chunk of binaryChunks) {
        combined.set(chunk, offset);
        offset += chunk.length;
      }
      
      // Create audio context and play
      const audioContext = new AudioContext({ sampleRate: 16000 });
      const audioBuffer = await audioContext.decodeAudioData(combined.buffer);
      const source = audioContext.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(audioContext.destination);
      source.start();
      
      // Clear buffer after playing
      delete audioBuffers[messageType];
    }
  };
}

// 3. Send text answer
function submitAnswer(text) {
  ws.send(
    JSON.stringify({
      type: "USER_TEXT_ANSWER",
      payload: { message: text },
    })
  );
}

// 4. Record and send audio answer (using MediaRecorder API)
let mediaRecorder;
let audioChunks = [];

async function startRecording() {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  mediaRecorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
  audioChunks = [];
  let isFirst = true;

  mediaRecorder.ondataavailable = async (event) => {
    if (event.data.size > 0) {
      const base64 = await blobToBase64(event.data);
      ws.send(
        JSON.stringify({
          type: "USER_AUDIO_CHUNK",
          payload: { chunk: base64, isFirst },
        })
      );
      isFirst = false;
    }
  };

  mediaRecorder.start(1000); // Send chunks every 1 second
}

function stopRecording() {
  mediaRecorder.stop();
  mediaRecorder.stream.getTracks().forEach((track) => track.stop());
  ws.send(JSON.stringify({ type: "USER_AUDIO_END", payload: {} }));
}

function blobToBase64(blob) {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onloadend = () => resolve(reader.result.split(",")[1]);
    reader.readAsDataURL(blob);
  });
}

// 5. End interview
function endInterview() {
  ws.send(
    JSON.stringify({
      type: "HANGUP",
      payload: {},
    })
  );
}
```
