import { topologyProviderIds } from "/opt/homebrew/lib/node_modules/omniroute/src/lib/monitoring/providerHealthMatrix.ts";

const visible = topologyProviderIds([
  { provider: "fake-nokey", isActive: 0 },
  { provider: "ovhcloud", isActive: false },
  { provider: "kilo-gateway", isActive: 0 },
  { provider: "duckduckgo-web", isActive: 1 },
  { provider: "cohere", isActive: true },
]);

const hidden = ["fake-nokey", "ovhcloud", "kilo-gateway"].filter((id) => visible.includes(id));
if (hidden.length) {
  console.log("FAIL no-key rows are still visible", hidden);
  process.exit(1);
}
if (!visible.includes("duckduckgo-web") || !visible.includes("cohere")) {
  console.log("FAIL a keyless or keyed active provider was dropped", visible);
  process.exit(1);
}
console.log(
  "PASS a fake no-key provider stays out of the topology, and duckduckgo-web stays in"
);
console.log("visible", visible.join(","));
