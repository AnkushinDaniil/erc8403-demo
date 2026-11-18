import os; ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import subprocess, sys
TEMPLATE = '''object "Remote" {
  code {
    if iszero(eq(caller(), 0xaa)) {
      if iszero(calldatasize()) { stop() }
      calldatacopy(0x80, 0, calldatasize())
      mstore(0x84, HOME_ACCOUNT)
      if iszero(staticcall(gas(), HELPER, 0x80, calldatasize(), 0, 96)) { revert(0, 0) }
      if iszero(eq(mload(0), HOME_SIGNER)) { revert(0, 0) }
      let height := mload(32)
      if iszero(gt(height, sload(2))) { revert(0, 0) }
      sstore(2, height)
      sstore(add(0x1000, height), mload(64))
      stop()
    }
    let pred := calldataload(32)
    if iszero(eq(verbatim_2i_1o(hex"b4", 0, 0x00), pred)) { revert(0, 0) }
    if verbatim_2i_1o(hex"b4", 0, 0x02) { revert(0, 0) }
    mstore(0, calldataload(0))
    mstore(32, pred)
    let node := keccak256(0, 64)
    for { let k := 0 } lt(k, 2) { k := add(k, 1) } {
      let sib := calldataload(add(64, mul(k, 32)))
      if sib {
        switch lt(node, sib)
        case 1 { mstore(0, node) mstore(32, sib) }
        default { mstore(0, sib) mstore(32, node) }
        node := keccak256(0, 64)
      }
    }
    let latest := sload(2)
    let named := NAMED
    if gt(named, latest) { revert(0, 0) }
    if iszero(lt(sub(latest, named), WINDOW)) { revert(0, 0) }
    let homeStorageRoot := sload(add(0x1000, named))
    if iszero(homeStorageRoot) { revert(0, 0) }
    let size := sub(calldatasize(), 160)
    calldatacopy(0x80, 160, size)
    mstore(0x84, homeStorageRoot)
    if iszero(staticcall(gas(), HELPER, 0x80, size, 0, 32)) { revert(0, 0) }
    if iszero(eq(mload(0), node)) { revert(0, 0) }
    verbatim_3i_0o(hex"aa", 0, 0, verbatim_2i_1o(hex"b3", verbatim_1i_1o(hex"b0", 0x0a), 0x06))
  }
}
'''
def build(home_account, home_signer, helper, tier, window):
    src = TEMPLATE.replace("HOME_ACCOUNT", "0x" + home_account.hex()).replace("HOME_SIGNER", "0x" + home_signer.hex()).replace("HELPER", "0x" + helper.hex())
    src = src.replace("NAMED", "calldataload(128)" if tier == 1 else "latest").replace("WINDOW", str(window if tier == 1 else 1))
    path = f"{ROOT}/mc/sol/Remote{tier}.yul"
    open(path, "w").write(src)
    out = subprocess.run([os.environ.get("SOLC", "solc"), "--strict-assembly", "--optimize", "--evm-version", "cancun", "--bin", path], capture_output=True, text=True)
    if out.returncode: raise SystemExit(out.stderr)
    lines = [l for l in out.stdout.splitlines() if l.strip()]
    return lines[lines.index("Binary representation:") + 1]
if __name__ == "__main__":
    print(build(bytes(20), bytes(20), bytes(20), 1, 30)); print(build(bytes(20), bytes(20), bytes(20), 2, 30))
