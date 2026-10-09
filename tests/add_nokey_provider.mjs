import { createProviderConnection, getProviderConnections } from "/opt/homebrew/lib/node_modules/omniroute/src/lib/db/providers.ts";
import { deleteProviderConnectionsByProvider } from "/opt/homebrew/lib/node_modules/omniroute/src/lib/db/providers/deletion.ts";
import { countStaleDbNonOkConnections } from "/opt/homebrew/lib/node_modules/omniroute/src/lib/monitoring/observability.ts";
import { topologyProviderIds } from "/opt/homebrew/lib/node_modules/omniroute/src/lib/monitoring/providerHealthMatrix.ts";

const fake = "fake-nokey-b9errrows3";
let created = null;
try {
  created = await createProviderConnection({
    provider: fake,
    authType: "apikey",
    name: fake,
  });
  const active = await getProviderConnections({ isActive: true });
  const inCombo = active.some((row) => row.provider === fake);
  const ddg = active.find((row) => row.provider === "duckduckgo-web");
  const errorCount = countStaleDbNonOkConnections([
    { isActive: created.isActive, testStatus: created.testStatus || "error" },
  ]);
  const topology = topologyProviderIds([
    { provider: created.provider, isActive: created.isActive },
    { provider: "duckduckgo-web", isActive: ddg ? ddg.isActive : 0 },
  ]);
  if (inCombo || created.isActive === true || created.isActive === 1) {
    console.log("FAIL fake no-key provider is in the active combo set");
    process.exit(1);
  }
  console.log("PASS a fake no-key provider is not in the active combo set");
  if (errorCount !== 0 || topology.includes(fake)) {
    console.log("FAIL fake no-key provider still counts", errorCount, topology);
    process.exit(1);
  }
  console.log("PASS a fake no-key provider is not in the error count and not in the topology");
  if (!ddg || (ddg.isActive !== true && ddg.isActive !== 1) || !topology.includes("duckduckgo-web")) {
    console.log("FAIL duckduckgo-web was not left active");
    process.exit(1);
  }
  console.log("PASS duckduckgo-web stays active and in the combo set");
} finally {
  await deleteProviderConnectionsByProvider(fake);
}
