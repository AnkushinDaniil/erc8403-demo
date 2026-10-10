object "Account" {
  code {
    datacopy(0, dataoffset("runtime"), datasize("runtime"))
    return(0, datasize("runtime"))
  }
  object "runtime" {
    code {
      if eq(caller(), address()) {
        sstore(0, calldataload(0))
        let n := calldataload(32)
        sstore(1, n)
        for { let i := 0 } lt(i, n) { i := add(i, 1) } {
          sstore(add(0x100, mul(i, 2)), calldataload(add(64, mul(i, 64))))
          sstore(add(0x101, mul(i, 2)), calldataload(add(96, mul(i, 64))))
        }
        stop()
      }
      let fidx := verbatim_1i_1o(hex"b0", 0x0a)
      let aid  := verbatim_2i_1o(hex"b1", 0, fidx)
      let pred := verbatim_2i_1o(hex"b1", 32, fidx)
      let signer := verbatim_2i_1o(hex"b4", 0, 0x00)
      if iszero(eq(signer, pred)) { revert(0, 0) }
      mstore(0, aid)
      mstore(32, pred)
      let node := keccak256(0, 64)
      for { let k := 0 } lt(k, 2) { k := add(k, 1) } {
        let sib := verbatim_2i_1o(hex"b1", add(64, mul(k, 32)), fidx)
        if sib {
          switch lt(node, sib)
          case 1 { mstore(0, node) mstore(32, sib) }
          default { mstore(0, sib) mstore(32, node) }
          node := keccak256(0, 64)
        }
      }
      if iszero(eq(node, sload(0))) { revert(0, 0) }
      verbatim_3i_0o(hex"aa", 0, 0, 3)
      stop()
    }
  }
}
