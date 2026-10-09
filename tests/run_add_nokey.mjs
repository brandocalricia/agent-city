import { registerAliasResolver } from "/opt/homebrew/lib/node_modules/omniroute/bin/aliasResolver.mjs";

const ready = await registerAliasResolver("/opt/homebrew/lib/node_modules/omniroute");
if (!ready) {
  console.log("FAIL alias resolver did not register");
  process.exit(1);
}
await import("./add_nokey_provider.mjs");
