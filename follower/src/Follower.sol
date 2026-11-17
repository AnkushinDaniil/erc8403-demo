// SPDX-License-Identifier: CC0-1.0
pragma solidity ^0.8.26;

interface IERC8403HomeAdapter {
    function read(uint256 chainId, address account, bytes32 slot, uint256 blockNumber, bytes calldata proof)
        external view returns (bytes32 value, uint256 timestamp);
}

abstract contract Follower {
    event AuthorityStateChanged(bytes32 indexed root);

    bytes32 constant SLOTS16_SYNC = keccak256("ERC8403_SLOTS16_SYNC");
    uint256 constant NO_MANAGE = 1 << 160;

    uint256 immutable homeChainId;
    address immutable homeAccount;
    address immutable adapter;
    uint256 immutable maxAge;

    bytes32 public currentRoot;
    uint256 public homeBlockNumber;

    constructor(uint256 chainId_, address account_, address adapter_, uint256 maxAge_) {
        homeChainId = chainId_;
        homeAccount = account_;
        adapter = adapter_;
        maxAge = maxAge_;
    }

    function authorityRoot() external view returns (bytes32, bytes32) {
        return (currentRoot, SLOTS16_SYNC);
    }

    function home() external view returns (uint256, address, address, uint256, uint256) {
        return (homeChainId, homeAccount, adapter, maxAge, homeBlockNumber);
    }

    function sync(uint256 blockNumber, bytes calldata proof) external {
        require(block.chainid != homeChainId);
        require(blockNumber > homeBlockNumber);
        (bool ok, bytes memory ret) = adapter.staticcall(
            abi.encodeCall(IERC8403HomeAdapter.read, (homeChainId, homeAccount, bytes32(0), blockNumber, proof))
        );
        require(ok && ret.length >= 64);
        (bytes32 value, uint256 timestamp) = abi.decode(ret, (bytes32, uint256));
        if (timestamp < block.timestamp) require(block.timestamp - timestamp <= maxAge);
        homeBlockNumber = blockNumber;
        if (value != currentRoot) {
            currentRoot = value;
            emit AuthorityStateChanged(value);
        }
    }

    function validate(uint256 id, bytes32 predicate, bytes32[4] calldata siblings) external {
        require(predicate != bytes32(0));
        bytes32 h = keccak256(abi.encodePacked(bytes1(0x00), id, predicate));
        for (uint256 k = 0; k < 4; k++) {
            h = (id >> k) & 1 == 0
                ? keccak256(abi.encodePacked(bytes1(0x01), h, siblings[k]))
                : keccak256(abi.encodePacked(bytes1(0x01), siblings[k], h));
        }
        require(h == currentRoot);
        (address signer, bool msgEmpty) = _entry0();
        require(msgEmpty);
        require(signer == address(uint160(uint256(predicate))));
        if (uint256(predicate) & NO_MANAGE != 0) require(!_senderFrameToSelf());
        _approve(_frameScope());
    }

    function _entry0() internal view virtual returns (address signer, bool msgEmpty);
    function _senderFrameToSelf() internal view virtual returns (bool);
    function _frameScope() internal view virtual returns (uint256);
    function _approve(uint256 scope) internal virtual;
}

contract MockAdapter is IERC8403HomeAdapter {
    struct Entry { bytes32 value; uint256 timestamp; bool set; }
    mapping(uint256 => Entry) public entries;
    uint256 public mode;

    function put(uint256 blockNumber, bytes32 value, uint256 timestamp) external {
        entries[blockNumber] = Entry(value, timestamp, true);
    }

    function setMode(uint256 m) external { mode = m; }

    function read(uint256, address, bytes32, uint256 blockNumber, bytes calldata)
        external view returns (bytes32, uint256)
    {
        Entry memory e = entries[blockNumber];
        require(e.set);
        if (mode == 1) {
            assembly { mstore(0, 1) return(0, 32) }
        }
        return (e.value, e.timestamp);
    }
}

contract MockFrameFollower is Follower {
    address public signer0;
    bool public msgEmpty0 = true;
    bool public senderToSelf;
    uint256 public approvedScope;

    constructor(uint256 c, address a, address ad, uint256 m) Follower(c, a, ad, m) {}

    function setEntry0(address s, bool e) external { signer0 = s; msgEmpty0 = e; }
    function setSenderToSelf(bool b) external { senderToSelf = b; }
    function clearApproval() external { approvedScope = 0; }

    function _entry0() internal view override returns (address, bool) { return (signer0, msgEmpty0); }
    function _senderFrameToSelf() internal view override returns (bool) { return senderToSelf; }
    function _frameScope() internal pure override returns (uint256) { return 3; }
    function _approve(uint256 s) internal override { approvedScope = s; }
}
