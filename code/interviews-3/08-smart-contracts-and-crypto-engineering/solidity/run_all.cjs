// Compiles every contract with solc and runs each scenario on an in-memory EVM. No network, no chain, no account.
// Prints one JSON object. Run with NODE_PATH set to the node_modules made from package.json.
const fs = require("fs");
const path = require("path");
const solc = require("solc");
const { createEVM } = require("@ethereumjs/evm");
const { Common, Mainnet, Hardfork } = require("@ethereumjs/common");
const { Account, Address, bytesToHex, hexToBytes, utf8ToBytes } = require("@ethereumjs/util");
const { keccak256 } = require("ethereum-cryptography/keccak.js");
const { secp256k1 } = require("ethereum-cryptography/secp256k1.js");

const ETH = 10n ** 18n;
const here = __dirname;

function compile() {
  const sources = {};
  for (const f of fs.readdirSync(here)) if (f.endsWith(".sol")) sources[f] = { content: fs.readFileSync(path.join(here, f), "utf8") };
  const input = {
    language: "Solidity",
    sources,
    settings: { evmVersion: "cancun", optimizer: { enabled: false }, outputSelection: { "*": { "*": ["abi", "evm.bytecode.object"] } } },
  };
  const out = JSON.parse(solc.compile(JSON.stringify(input)));
  const errors = (out.errors || []).filter((e) => e.severity === "error");
  if (errors.length) throw new Error(errors.map((e) => e.formattedMessage).join("\n"));
  const contracts = {};
  for (const file of Object.values(out.contracts)) for (const [name, c] of Object.entries(file)) contracts[name] = c.evm.bytecode.object;
  return { contracts, warnings: (out.errors || []).length };
}

function word(x) {
  if (typeof x === "string") return x.replace(/^0x/, "").toLowerCase().padStart(64, "0");
  if (x < 0n) x += 2n ** 256n;
  return x.toString(16).padStart(64, "0");
}

function selector(sig) {
  return bytesToHex(keccak256(utf8ToBytes(sig))).slice(2, 10);
}

function addr(n) {
  return new Address(hexToBytes("0x" + n.toString(16).padStart(40, "0")));
}

async function makeWorld(contracts) {
  const common = new Common({ chain: Mainnet, hardfork: Hardfork.Cancun });
  const evm = await createEVM({ common });
  const fund = async (a, wei) => evm.stateManager.putAccount(a, new Account(0n, wei));
  const balance = async (a) => ((await evm.stateManager.getAccount(a)) || { balance: 0n }).balance;
  async function deploy(name, from, args = [], value = 0n) {
    const data = hexToBytes("0x" + contracts[name] + args.map(word).join(""));
    const r = await evm.runCall({ caller: from, origin: from, data, value, gasLimit: 30_000_000n });
    if (r.execResult.exceptionError) throw new Error("deploy " + name + " " + r.execResult.exceptionError.error);
    return r.createdAddress;
  }
  async function call(to, sig, args = [], { from, origin, value = 0n, timestamp } = {}) {
    const data = hexToBytes("0x" + selector(sig) + args.map(word).join(""));
    evm.journal.cleanup();                     // each call is its own transaction: access lists and originals start fresh
    evm.stateManager.originalStorageCache.clear();
    const options = { caller: from, origin: origin || from, to, data, value, gasLimit: 10_000_000n };
    if (timestamp !== undefined) options.block = blockAt(timestamp);
    const r = await evm.runCall(options);
    const failed = !!r.execResult.exceptionError;
    return {
      ok: !failed,
      out: bytesToHex(r.execResult.returnValue),
      gas: Number(r.execResult.executionGasUsed),
      refund: Number(r.execResult.gasRefund || 0n),
    };
  }
  return { evm, fund, balance, deploy, call };
}

function blockAt(timestamp) {
  return {
    common: new Common({ chain: Mainnet, hardfork: Hardfork.Cancun }),
    header: {
      number: 1n, coinbase: addr(0xc0), timestamp, difficulty: 0n, prevRandao: new Uint8Array(32),
      gasLimit: 30_000_000n, baseFeePerGas: 1n, getBlobGasPrice: () => 1n,
    },
  };
}

const u = (r) => BigInt(r.out);

async function main() {
  const { contracts, warnings } = compile();
  const R = { solc: solc.version(), warnings };
  const w = await makeWorld(contracts);
  const alice = addr(0xa11ce), bob = addr(0xb0b), mallory = addr(0xbad);
  for (const a of [alice, bob, mallory]) await w.fund(a, 1000n * ETH);

  const fixed = await w.deploy("Fixed", alice);
  R.fixed = {
    divFirst: u(await w.call(fixed, "divFirst(uint256,uint256,uint256)", [1n, 3n, 3n], { from: alice })).toString(),
    mulFirst: u(await w.call(fixed, "mulFirst(uint256,uint256,uint256)", [1n, 3n, 3n], { from: alice })).toString(),
    wmul: u(await w.call(fixed, "wmul(uint256,uint256)", [15n * 10n ** 17n, 2n * ETH], { from: alice })).toString(),
    wmulTiny: u(await w.call(fixed, "wmul(uint256,uint256)", [1n, 1n], { from: alice })).toString(),
    mulOverflow: (await w.call(fixed, "mulFirst(uint256,uint256,uint256)", [2n ** 255n, 2n, 2n], { from: alice })).ok,
  };

  const loc = await w.deploy("Locations", alice);
  R.locations = {
    viaMemory: u(await w.call(loc, "viaMemory()", [], { from: alice })).toString(),
    viaStorage: u(await w.call(loc, "viaStorage()", [], { from: alice })).toString(),
  };

  const slot = await w.deploy("Slot", alice);
  const set = (x) => w.call(slot, "set(uint256)", [x], { from: alice });
  const s1 = await set(1n), s2 = await set(2n), s3 = await set(2n), s4 = await set(0n);
  R.slot = { zero_to_nonzero: s1.gas, nonzero_to_nonzero: s2.gas, same: s3.gas, to_zero: s4.gas, to_zero_refund: s4.refund };
  const twiceAt = await w.deploy("SlotTwice", alice);          // two writes in ONE transaction: the second finds the slot warm
  const twice = (await w.call(twiceAt, "twice(uint256,uint256)", [1n, 2n], { from: alice })).out.replace(/^0x/, "");
  R.slotTwice = { first: Number(BigInt("0x" + twice.slice(0, 64))), second: Number(BigInt("0x" + twice.slice(64, 128))) };

  const loose = await w.deploy("Loose", alice), tight = await w.deploy("Tight", alice);
  const used = async (a) => {
    let n = 0;
    for (let i = 0n; i < 4n; i++) {
      const v = await w.evm.stateManager.getStorage(a, hexToBytes("0x" + word(i)));
      if (v.length) n += 1;
    }
    return n;
  };
  const tightSlot0 = bytesToHex(await w.evm.stateManager.getStorage(tight, hexToBytes("0x" + word(0n))));
  R.packing = { loose: await used(loose), tight: await used(tight), tightSlot0 };

  const over = await w.deploy("Overflow", alice);
  const chk = await w.call(over, "checkedDec(uint256)", [0n], { from: alice });
  const unc = await w.call(over, "uncheckedDec(uint256)", [0n], { from: alice });
  const nar = await w.call(over, "narrow(uint256)", [300n], { from: alice });
  R.overflow = { checkedOk: chk.ok, checkedOut: chk.out, unchecked: u(unc).toString(), max: (2n ** 256n - 1n).toString(), narrow: u(nar).toString() };

  for (const name of ["Vault", "OrderedVault", "LockedVault"]) {
    const v = await w.deploy(name, alice);
    await w.call(v, "deposit()", [], { from: bob, value: 10n * ETH });
    const a = await w.deploy("Attacker", mallory, [v.toString()]);
    const r = await w.call(a, "attack()", [], { from: mallory, value: ETH });
    const after = { attackOk: r.ok, vault: (await w.balance(v)).toString(), attacker: (await w.balance(a)).toString() };
    const honest = await w.call(v, "withdraw()", [], { from: bob });
    after.bobWithdrawOk = honest.ok;
    after.vaultAfterBob = (await w.balance(v)).toString();
    R[name] = after;
  }

  const rej = await w.deploy("Rejecter", alice), pay = await w.deploy("Payout", alice);
  const unchecked = await w.call(pay, "payUnchecked(address)", [rej.toString()], { from: alice, value: ETH });
  const paid = u(await w.call(pay, "paid(address)", [rej.toString()], { from: alice }));
  const held = await w.balance(pay);
  const rej2 = await w.deploy("Rejecter", alice);
  const checked = await w.call(pay, "payChecked(address)", [rej2.toString()], { from: alice, value: ETH });
  R.pay = { uncheckedOk: unchecked.ok, paid: paid.toString(), rejecter: (await w.balance(rej)).toString(), held: held.toString(), checkedOk: checked.ok };

  const wallet1 = await w.deploy("Wallet", alice, [], 5n * ETH), trap1 = await w.deploy("Trap", mallory);
  const o1 = await w.call(trap1, "claimPrize(address,bool)", [wallet1.toString(), 1n], { from: alice });
  const wallet2 = await w.deploy("Wallet", alice, [], 5n * ETH), trap2 = await w.deploy("Trap", mallory);
  const o2 = await w.call(trap2, "claimPrize(address,bool)", [wallet2.toString(), 0n], { from: alice });
  R.origin = {
    originOk: o1.ok, originTrap: (await w.balance(trap1)).toString(),
    senderOk: o2.ok, senderWallet: (await w.balance(wallet2)).toString(),
  };

  const impl = await w.deploy("Impl", alice);
  const proxy = await w.deploy("Proxy", alice, [impl.toString()]);
  const before = (await w.call(proxy, "impl()", [], { from: alice })).out;
  const setRes = await w.call(proxy, "setX(uint256)", [0xdeadn], { from: alice });
  const afterImpl = (await w.call(proxy, "impl()", [], { from: alice })).out;
  const again = await w.call(proxy, "x()", [], { from: alice });
  const safe = await w.deploy("SafeProxy", alice, [impl.toString()]);
  const safeSet = await w.call(safe, "setX(uint256)", [0xdeadn], { from: alice });
  const safeX = await w.call(safe, "x()", [], { from: alice });
  const safeImpl = (await w.call(safe, "impl()", [], { from: alice })).out;
  R.proxy = {
    implMatches: BigInt(before) === BigInt(impl.toString()), setOk: setRes.ok, implAfter: BigInt(afterImpl).toString(), xAfterOk: again.ok, xAfterOut: again.out,
    safeSetOk: safeSet.ok, safeX: u(safeX).toString(), safeImplMatches: BigInt(safeImpl) === BigInt(impl.toString()),
  };

  const amm = await w.deploy("Amm", alice);
  const cases = JSON.parse(process.argv[2] || "[]");
  R.amm = [];
  for (const [a, x, y] of cases) {
    R.amm.push(u(await w.call(amm, "amountOut(uint256,uint256,uint256)", [BigInt(a), BigInt(x), BigInt(y)], { from: alice })).toString());
  }

  const feed = await w.deploy("Feed", alice), cons = await w.deploy("Consumer", alice);
  const reading = async (sig, args, timestamp) => {
    const r = await w.call(cons, sig, args, { from: alice, timestamp });
    return r.ok ? u(r).toString() : "reverted";
  };
  const T = 1_000_000n;
  await w.call(feed, "push(int256,uint256)", [200_000n, T], { from: alice });
  const fresh = await reading("careful(address,uint256)", [feed.toString(), 3600n], T + 60n);
  const stale = await reading("careful(address,uint256)", [feed.toString(), 3600n], T + 7200n);
  const staleTrusting = await reading("trusting(address)", [feed.toString()], T + 7200n);
  await w.call(feed, "push(int256,uint256)", [-1n, T], { from: alice });
  const negative = await reading("careful(address,uint256)", [feed.toString(), 3600n], T + 60n);
  const negativeTrusting = await reading("trusting(address)", [feed.toString()], T + 60n);
  R.feed = { fresh, stale, staleTrusting, negative, negativeTrusting };

  const pool = await w.deploy("Pool", alice);
  await w.call(pool, "join()", [], { from: bob, value: 100n * ETH });
  const reader = await w.deploy("Reader", mallory, [pool.toString()]);
  const before2 = u(await w.call(pool, "price()", [], { from: alice }));
  const runRes = await w.call(reader, "run()", [], { from: mallory, value: 100n * ETH });
  const seen = u(await w.call(reader, "seen()", [], { from: alice }));
  const afterP = u(await w.call(pool, "price()", [], { from: alice }));
  const sp = await w.deploy("SafePool", alice);
  await w.call(sp, "join()", [], { from: bob, value: 100n * ETH });
  const sr = await w.deploy("SafeReader", mallory, [sp.toString()]);
  const srRun = await w.call(sr, "run()", [], { from: mallory, value: 100n * ETH });
  const srRefused = u(await w.call(sr, "refused()", [], { from: alice }));
  const spAfter = u(await w.call(sp, "price()", [], { from: alice }));
  R.readonly = {
    before: before2.toString(), runOk: runRes.ok, seen: seen.toString(), after: afterP.toString(),
    safeRunOk: srRun.ok, safeRefused: srRefused.toString(), safeAfter: spAfter.toString(),
  };

  const key = new Uint8Array(32).fill(7);
  const signer = new Address(keccak256(secp256k1.getPublicKey(key, false).slice(1)).slice(-20));
  const sign = (digest) => {
    const sig = secp256k1.sign(digest, key);
    return [BigInt(27 + sig.recovery), sig.r, sig.s];
  };
  const packed = (to, amount) => keccak256(hexToBytes("0x" + to.toString().slice(2) + word(amount)));
  const relay = await w.deploy("Relay", alice), relay2 = await w.deploy("Relay", alice);
  await w.call(relay, "fund(address)", [signer.toString()], { from: alice, value: 10n * ETH });
  await w.call(relay2, "fund(address)", [signer.toString()], { from: alice, value: 10n * ETH });
  const [v, r, s] = sign(packed(mallory, ETH));
  const paySig = "pay(address,uint256,uint8,bytes32,bytes32)";
  const payArgs = [mallory.toString(), ETH, v, word(r), word(s)];
  const first = await w.call(relay, paySig, payArgs, { from: bob });
  const replay = await w.call(relay, paySig, payArgs, { from: bob });
  const elsewhere = await w.call(relay2, paySig, payArgs, { from: bob });
  const stolen = u(await w.call(relay, "balance(address)", [mallory.toString()], { from: alice }));
  const safeRelay = await w.deploy("SafeRelay", alice), safeRelay2 = await w.deploy("SafeRelay", alice);
  await w.call(safeRelay, "fund(address)", [signer.toString()], { from: alice, value: 10n * ETH });
  await w.call(safeRelay2, "fund(address)", [signer.toString()], { from: alice, value: 10n * ETH });
  const digest = (await w.call(safeRelay, "digestFor(address,address,uint256)", [signer.toString(), mallory.toString(), ETH], { from: alice })).out;
  const [v2, r2, s2x] = sign(hexToBytes(digest));
  const safeSig = "pay(address,address,uint256,uint8,bytes32,bytes32)";
  const payArgs2 = [signer.toString(), mallory.toString(), ETH, v2, word(r2), word(s2x)];
  const safeFirst = await w.call(safeRelay, safeSig, payArgs2, { from: bob });
  const safeReplay = await w.call(safeRelay, safeSig, payArgs2, { from: bob });
  const safeElsewhere = await w.call(safeRelay2, safeSig, payArgs2, { from: bob });
  const safeGot = u(await w.call(safeRelay, "balance(address)", [mallory.toString()], { from: alice }));
  R.relay = { firstOk: first.ok, replayOk: replay.ok, elsewhereOk: elsewhere.ok, stolen: stolen.toString() };
  R.safeRelay = { firstOk: safeFirst.ok, replayOk: safeReplay.ok, elsewhereOk: safeElsewhere.ok, got: safeGot.toString() };
  console.log(JSON.stringify(R));
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
