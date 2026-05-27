# AI Router Architecture

## Goals

The AI router should provide fast, reliable, provider-neutral streaming with automatic failover. Users should not need to understand provider outages, quota exhaustion, rate limits, or transient model errors.

## Provider abstraction

```csharp
public interface IAiProvider
{
    string Id { get; }
    AiProviderCapabilities Capabilities { get; }
    IAsyncEnumerable<AiResponseChunk> StreamAsync(AiRequest request, CancellationToken cancellationToken);
}
```

Each provider owns:

- Request translation.
- Auth headers.
- Streaming parser.
- Error classification.
- Provider-specific model catalog.

## Routing modes

### Auto

Default. Select based on prompt type, text size, user preference, recent provider health, and cost.

### Fast

Prefer low-latency models and providers with healthy recent response times.

### Best Quality

Prefer strongest reasoning/writing/coding model available.

### Cheapest

Prefer low-cost models and OpenRouter/local options.

### Privacy

Prefer local models when available. If no local model exists, require explicit user opt-in before cloud calls.

## Smart routing examples

| Request type | Preferred provider policy |
| --- | --- |
| Code explanation | Strong coding model first, then best general model. |
| Long document summary | Long-context provider first. |
| Writing/rewrite | Writing-optimized provider first. |
| Translate | Fast low-cost provider first unless user chooses quality. |
| Privacy/sensitive mode | Local provider only or explicit confirmation. |

## Failover algorithm

```text
build candidate provider list
for provider in candidates:
  try:
    stream response
    if first usable token arrives:
      mark provider healthy
      continue until completion
      return success
  catch provider error:
    classify error
    if recoverable:
      mark provider degraded
      try next provider
    else:
      stop and show actionable error
if all providers fail:
  show compact failure summary with retry options
```

Recoverable errors:

- HTTP 408, 409, 429, 500, 502, 503, 504.
- Quota exceeded.
- Rate limit.
- Timeout.
- Transient stream disconnect before first token.
- Provider outage messages.

Non-recoverable errors:

- Invalid API key.
- Missing API key.
- Unsupported model.
- Content policy block.
- Malformed request caused by app bug.
- User disabled all fallback providers.

## Streaming failover behavior

Failover is safest before any visible tokens arrive. If a provider fails after streaming has begun:

1. Stop current stream.
2. Show inline retry/failover affordance.
3. Either:
   - Continue with next provider and clearly restart answer, or
   - Ask user to regenerate using fallback provider.

Do not splice partial answers from different models without labeling the transition.

## Provider order example

```text
Auto:
  1. OpenAI
  2. Gemini
  3. Anthropic
  4. OpenRouter
  5. Local

Privacy:
  1. Local
  2. Explicit-confirm cloud provider

Cheapest:
  1. Local
  2. OpenRouter low-cost model
  3. Gemini flash/fast tier
  4. OpenAI mini tier
```

## Request model

An `AiRequest` should contain:

- Action ID.
- System instruction.
- Selected text.
- User follow-up prompt.
- Conversation history.
- Preferred language.
- Routing mode.
- Model override.
- Sensitive-mode flag.
- Streaming preference.
- Timeout budget.

## API key storage

Store credentials with:

- Windows Credential Manager, or
- DPAPI-protected encrypted local settings.

Never store API keys in SQLite as plaintext. Never log headers, complete URLs with keys, or provider payloads containing secrets.

## Health model

Track provider health locally:

- Last success time.
- Last failure time.
- Failure count by reason.
- Recent latency p50/p95.
- Quota/rate-limit cool-down expiration.

Use this only to avoid bad providers temporarily. Do not permanently disable a provider without user action.

## Production provider classes

```text
AI/
  AiRouterService.cs
  AiProviderRegistry.cs
  ProviderErrorClassifier.cs
  ProviderHealthStore.cs
  OpenAiProvider.cs
  GeminiProvider.cs
  AnthropicProvider.cs
  OpenRouterProvider.cs
  LocalModelProvider.cs
```

## User experience

When fallback happens, keep it subtle:

```text
Using Gemini because OpenAI is currently rate limited.
```

Expose details in a diagnostics panel, not in the main answer body.
