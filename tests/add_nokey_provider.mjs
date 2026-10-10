import {
  createProviderConnection,
  getProviderConnectionById,
  getProviderConnections,
  unkeyedApikeyConnection,
  updateProviderConnection,
} from "/opt/homebrew/lib/node_modules/omniroute/src/lib/db/providers.ts";
import { deleteProviderConnectionsByProvider } from "/opt/homebrew/lib/node_modules/omniroute/src/lib/db/providers/deletion.ts";
import { countStaleDbNonOkConnections } from "/opt/homebrew/lib/node_modules/omniroute/src/lib/monitoring/observability.ts";
import { topologyProviderIds } from "/opt/homebrew/lib/node_modules/omniroute/src/lib/monitoring/providerHealthMatrix.ts";

const fake = "fake-nokey-b9errrows3";
const lost = "fake-lostkey-b9errrows4";
if (typeof unkeyedApikeyConnection !== "function") {
  console.log("FAIL installed OmniRoute is missing unkeyedApikeyConnection");
  process.exit(1);
}
console.log("PASS installed OmniRoute has unkeyedApikeyConnection");
if (countStaleDbNonOkConnections([{ isActive: 0, testStatus: "error" }]) !== 0) {
  console.log("FAIL a numeric inactive row still counts as an error");
  process.exit(1);
}
console.log("PASS a numeric inactive row is not an error");
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

  const keyed = await createProviderConnection({
    provider: lost,
    authType: "apikey",
    name: lost,
    apiKey: "b9errrows4-placeholder",
  });
  if (keyed.isActive !== true && keyed.isActive !== 1) {
    console.log("FAIL a keyed row was created inactive");
    process.exit(1);
  }
  const cleared = await updateProviderConnection(keyed.id, { apiKey: "" });
  const reread = await getProviderConnectionById(keyed.id);
  const stillActive = await getProviderConnections({ isActive: true });
  const lostInCombo = stillActive.some((row) => row.provider === lost);
  const inactive =
    reread && reread.isActive !== true && reread.isActive !== 1 && reread.testStatus === "inactive";
  const lostErrors = countStaleDbNonOkConnections([
    { isActive: reread ? reread.isActive : 1, testStatus: reread ? reread.testStatus : "error" },
  ]);
  const lostTopology = topologyProviderIds([
    { provider: lost, isActive: reread ? reread.isActive : 1 },
  ]);
  if (!inactive || lostInCombo || lostErrors !== 0 || lostTopology.includes(lost) || !cleared) {
    console.log("FAIL lost key stayed routable", inactive, lostInCombo, lostErrors);
    process.exit(1);
  }
  console.log("PASS a lost key leaves the combo set and the error count");
} finally {
  await deleteProviderConnectionsByProvider(fake);
  await deleteProviderConnectionsByProvider(lost);
}
