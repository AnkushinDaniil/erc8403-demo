object "Account" {
  code {
    function root(p) -> r {
      for { let i := 0 } lt(i, 16) { i := add(i, 1) } {
        let pred := mload(add(p, mul(i, 32)))
        let l := 0
        if pred {
          mstore8(0, 0x00) mstore(1, i) mstore(0x21, pred)
          l := keccak256(0, 65)
        }
        mstore(add(0x400, mul(i, 32)), l)
      }
      for { let n := 16 } gt(n, 1) { n := div(n, 2) } {
        for { let i := 0 } lt(i, n) { i := add(i, 2) } {
          mstore8(0, 0x01)
          mstore(1, mload(add(0x400, mul(i, 32))))
          mstore(0x21, mload(add(0x400, mul(add(i, 1), 32))))
          mstore(add(0x400, mul(div(i, 2), 32)), keccak256(0, 65))
        }
      }
      r := mload(0x400)
    }
    codecopy(0x100, sub(codesize(), 32), 32)
    let first := mload(0x100)
    if shr(160, first) { revert(0, 0) }
    if iszero(first) { revert(0, 0) }
    sstore(0, root(0x100))
    datacopy(0, dataoffset("runtime"), datasize("runtime"))
    return(0, datasize("runtime"))
  }
  object "runtime" {
    code {
      function root(p) -> r {
        for { let i := 0 } lt(i, 16) { i := add(i, 1) } {
          let pred := mload(add(p, mul(i, 32)))
          let l := 0
          if pred {
            mstore8(0, 0x00) mstore(1, i) mstore(0x21, pred)
            l := keccak256(0, 65)
          }
          mstore(add(0x400, mul(i, 32)), l)
        }
        for { let n := 16 } gt(n, 1) { n := div(n, 2) } {
          for { let i := 0 } lt(i, n) { i := add(i, 2) } {
            mstore8(0, 0x01)
            mstore(1, mload(add(0x400, mul(i, 32))))
            mstore(0x21, mload(add(0x400, mul(add(i, 1), 32))))
            mstore(add(0x400, mul(div(i, 2), 32)), keccak256(0, 65))
          }
        }
        r := mload(0x400)
      }
      if iszero(calldatasize()) { stop() }
      switch shr(224, calldataload(0))
      case 0x806afe1e {
        let id := calldataload(4)
        let pred := calldataload(36)
        if iszero(pred) { revert(0, 0) }
        mstore8(0, 0x00) mstore(1, id) mstore(0x21, pred)
        let node := keccak256(0, 65)
        for { let k := 0 } lt(k, 4) { k := add(k, 1) } {
          let sib := calldataload(add(68, mul(k, 32)))
          mstore8(0, 0x01)
          switch and(shr(k, id), 1)
          case 0 { mstore(1, node) mstore(0x21, sib) }
          default { mstore(1, sib) mstore(0x21, node) }
          node := keccak256(0, 65)
        }
        if iszero(eq(node, sload(0))) { revert(0, 0) }
        if verbatim_2i_1o(hex"b4", 0, 2) { revert(0, 0) }
        if iszero(eq(verbatim_2i_1o(hex"b4", 0, 0), and(pred, 0xffffffffffffffffffffffffffffffffffffffff))) { revert(0, 0) }
        if shr(160, pred) {
          let sender := verbatim_1i_1o(hex"b0", 0x02)
          let frames := verbatim_1i_1o(hex"b0", 0x09)
          for { let i := 0 } lt(i, frames) { i := add(i, 1) } {
            if and(eq(verbatim_2i_1o(hex"b3", i, 0x02), 2), eq(verbatim_2i_1o(hex"b3", i, 0x00), sender)) { revert(0, 0) }
          }
        }
        verbatim_3i_0o(hex"aa", 0, 0, verbatim_2i_1o(hex"b3", verbatim_1i_1o(hex"b0", 0x0a), 0x06))
      }
      case 0x1feb3d6a {
        if iszero(eq(caller(), address())) { revert(0, 0) }
        if lt(calldatasize(), 516) { revert(0, 0) }
        calldatacopy(0x100, 4, 512)
        let manager := 0
        for { let i := 0 } lt(i, 16) { i := add(i, 1) } {
          let word := mload(add(0x100, mul(i, 32)))
          if shr(161, word) { revert(0, 0) }
          if word {
            if iszero(and(word, 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0) }
            if iszero(shr(160, word)) { manager := 1 }
          }
        }
        if iszero(manager) { revert(0, 0) }
        sstore(0, root(0x100))
        log1(0x100, 512, 0x83cb463cdb16a1f07dec96ec96c4f7a43dbac052f1975785c20893767dfb825a)
        log2(0, 0, 0xb06c6c6d281c73dffabcd158f5eb66251a3124ac551dd9efe8897d6b24f76aae, sload(0))
        stop()
      }
      case 0xce74c10b {
        mstore(0, sload(0))
        mstore(32, 0xd57d8ea8a9c7e0985d8cc400e0b7162f086f57e9b994099a71b0844e7b682b62)
        return(0, 64)
      }
      default { revert(0, 0) }
    }
  }
}
