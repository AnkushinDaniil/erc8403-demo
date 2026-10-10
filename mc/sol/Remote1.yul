object "Remote" {
  code {
    if iszero(eq(caller(), 0xaa)) {
      if iszero(calldatasize()) { stop() }
      calldatacopy(0x80, 0, calldatasize())
      mstore(0x84, 0x00000000000000000000000000000000cafe8403)
      if iszero(staticcall(gas(), 0x000000000000000000000000000000000000f00d, 0x80, calldatasize(), 0, 96)) { revert(0, 0) }
      if iszero(eq(mload(0), 0x9965507d1a55bcc2695c58ba16fb37d819b0a4dc)) { revert(0, 0) }
      let height := mload(32)
      if iszero(gt(height, sload(2))) { revert(0, 0) }
      sstore(2, height)
      sstore(add(0x1000, height), mload(64))
      stop()
    }
    let pred := calldataload(32)
    if iszero(eq(verbatim_2i_1o(hex"b4", 0, 0x00), pred)) { revert(0, 0) }
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
    let named := calldataload(128)
    if gt(named, latest) { revert(0, 0) }
    if iszero(lt(sub(latest, named), 40)) { revert(0, 0) }
    let homeStorageRoot := sload(add(0x1000, named))
    if iszero(homeStorageRoot) { revert(0, 0) }
    let size := sub(calldatasize(), 160)
    calldatacopy(0x80, 160, size)
    mstore(0x84, homeStorageRoot)
    if iszero(staticcall(gas(), 0x000000000000000000000000000000000000f00d, 0x80, size, 0, 32)) { revert(0, 0) }
    if iszero(eq(mload(0), node)) { revert(0, 0) }
    verbatim_3i_0o(hex"aa", 0, 0, 3)
  }
}
