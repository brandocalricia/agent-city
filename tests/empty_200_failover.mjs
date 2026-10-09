import { validateResponseQuality } from "/opt/homebrew/lib/node_modules/omniroute/open-sse/services/combo/validateQuality.ts";

const log = { warn() {} };

const fake = {
  choices: [
    {
      message: {
        role: "assistant",
        content: null,
        reasoning_content: "only reasoning",
      },
      finish_reason: "stop",
    },
  ],
  usage: { prompt_tokens: 10, completion_tokens: 0 },
};
const jsonRes = new Response(JSON.stringify(fake), {
  status: 200,
  headers: { "content-type": "application/json" },
});
const jsonResult = await validateResponseQuality(jsonRes, false, log);
if (jsonResult.valid) {
  console.log("FAIL fake reasoning-only 200 was accepted");
  process.exit(1);
}
console.log("PASS fake reasoning-only 200 triggered failover:", jsonResult.reason);

const good = {
  choices: [{ message: { role: "assistant", content: "pong" }, finish_reason: "stop" }],
  usage: { prompt_tokens: 7, completion_tokens: 1 },
};
const goodRes = new Response(JSON.stringify(good), {
  status: 200,
  headers: { "content-type": "application/json" },
});
const goodResult = await validateResponseQuality(goodRes, false, log);
if (!goodResult.valid) {
  console.log("FAIL content HTTP 200 was rejected:", goodResult.reason);
  process.exit(1);
}
console.log("PASS content HTTP 200 stayed valid");

const sse = [
  'data: {"choices":[{"delta":{"reasoning_content":"only reasoning"}}]}',
  "",
  'data: {"choices":[{"delta":{},"finish_reason":"stop"}],"usage":{"completion_tokens":0}}',
  "",
  "data: [DONE]",
  "",
].join("\n");
const streamRes = new Response(sse, {
  status: 200,
  headers: { "content-type": "text/event-stream" },
});
const streamResult = await validateResponseQuality(streamRes, true, log);
if (streamResult.valid) {
  console.log("FAIL streamed reasoning-only 200 was accepted");
  process.exit(1);
}
console.log("PASS streamed reasoning-only 200 triggered failover:", streamResult.reason);
