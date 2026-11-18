// SPDX-License-Identifier: CC0-1.0
pragma solidity ^0.8.26;

import {Test, Vm} from "forge-std/Test.sol";
import {MockFrameFollower, MockAdapter} from "../src/Follower.sol";

contract FollowerTest is Test {
    bytes32 constant ROOT = 0xa9c1f4b3e9b45817a1c9dd4ce66ad208f0c5917d38b2a37e380e1954efe5d30e;
    bytes32 constant ROOT_AFTER_REVOKE = 0xcab22dfae4cdaf3d73c65b61582707399c8f1ccc4e592b2818399fd0eb9be998;
    bytes32 constant ROOT_NO_MANAGE = 0x89adf3d471b12fa785074111dca0952104bdbc9bdc38e741c40a893d052f0739;
    bytes32 constant LEAF10 = 0x0abb98a84605f618e2a0b4e9cfcd466acbcbfb327886e779306d441739c82049;
    bytes32 constant NODE_0_7 = 0xdeab47e7915584c519b77ae1e6fb494be44c455065ecb1dc286399aac8ef9394;
    bytes32 constant TOPIC = 0xb06c6c6d281c73dffabcd158f5eb66251a3124ac551dd9efe8897d6b24f76aae;
    address constant KEY1 = 0x7E5F4552091A69125d5DfCb7b8C2659029395Bdf;
    address constant KEY2 = 0x2B5AD5c4795c026514f8317c7a215E218DcCD6cF;
    address constant HOME = address(0xCAFE8403);
    MockAdapter adapter;

    function setUp() public {
        vm.chainId(10);
        adapter = new MockAdapter();
        adapter.put(100, ROOT, 1000000);
        adapter.put(101, ROOT, 1000012);
        adapter.put(102, ROOT, 1003601);
        adapter.put(103, ROOT_AFTER_REVOKE, 1003000);
        adapter.put(104, bytes32(0), 1003000);
        adapter.put(105, ROOT, type(uint256).max);
        adapter.put(106, ROOT_NO_MANAGE, 1003000);
    }

    function fresh() internal returns (MockFrameFollower) {
        return new MockFrameFollower(1, HOME, address(adapter), 3600);
    }

    function node(bytes32 l, bytes32 r) internal pure returns (bytes32) {
        return keccak256(abi.encodePacked(bytes1(0x01), l, r));
    }

    function h1() internal pure returns (bytes32) { return node(0, 0); }
    function h2() internal pure returns (bytes32) { return node(h1(), h1()); }
    function h3() internal pure returns (bytes32) { return node(h2(), h2()); }

    function node8to15() internal pure returns (bytes32) {
        return node(node(h1(), node(LEAF10, 0)), h2());
    }

    function pred(address a) internal pure returns (bytes32) { return bytes32(uint256(uint160(a))); }

    function sib10() internal pure returns (bytes32[4] memory s) {
        s = [bytes32(0), h1(), h2(), NODE_0_7];
    }

    function sib10AfterRevoke() internal pure returns (bytes32[4] memory s) {
        s = [bytes32(0), h1(), h2(), h3()];
    }

    function sib0() internal pure returns (bytes32[4] memory s) {
        s = [bytes32(0), h1(), h2(), node8to15()];
    }

    function accepts(MockFrameFollower f, uint256 id, bytes32 p, bytes32[4] memory s) internal returns (bool) {
        f.clearApproval();
        try f.validate(id, p, s) { return f.approvedScope() == 3; } catch { return false; }
    }

    function test_TreeMatchesSpecValues() public pure {
        assertEq(node(NODE_0_7, node8to15()), ROOT);
        assertEq(node(h3(), node8to15()), ROOT_AFTER_REVOKE);
    }

    function test_SpecVector() public {
        MockFrameFollower f = fresh();
        (bytes32 r0, bytes32 s) = f.authorityRoot();
        assertEq(r0, bytes32(0));
        assertEq(s, 0x2bb847cd2a21945abc5c2efe79af09b5e95a319743bbd1270bc3e13d8acedb94);
        assertEq(f.sync.selector, bytes4(0x5c599843));
        assertEq(f.validate.selector, bytes4(0x806afe1e));
        f.setEntry0(KEY2, true);
        assertFalse(accepts(f, 10, pred(KEY2), sib10()));
        vm.warp(1003600);
        f.sync(100, "");
        (bytes32 r1,) = f.authorityRoot();
        assertEq(r1, ROOT);
        assertTrue(accepts(f, 10, pred(KEY2), sib10()));
        f.setEntry0(KEY2, false);
        assertFalse(accepts(f, 10, pred(KEY2), sib10()));
        f.setEntry0(KEY1, true);
        assertFalse(accepts(f, 10, pred(KEY2), sib10()));
        f.setEntry0(KEY2, true);
        assertFalse(accepts(f, 10, bytes32(0), sib10()));
        vm.expectRevert();
        f.sync(100, "");
        f.sync(101, "");
        assertEq(f.homeBlockNumber(), 101);
        f.sync(102, "");
        assertEq(f.homeBlockNumber(), 102);
        MockFrameFollower g = fresh();
        vm.warp(1003601);
        vm.expectRevert();
        g.sync(100, "");
        vm.warp(1003600);
        vm.chainId(1);
        vm.expectRevert();
        g.sync(100, "");
    }

    function test_ValidateRevertsAfterRevokeSync() public {
        MockFrameFollower f = fresh();
        f.setEntry0(KEY2, true);
        vm.warp(1003600);
        f.sync(100, "");
        f.sync(101, "");
        assertTrue(accepts(f, 10, pred(KEY2), sib10()));
        f.sync(103, "");
        assertFalse(accepts(f, 10, pred(KEY2), sib10()));
        assertTrue(accepts(f, 10, pred(KEY2), sib10AfterRevoke()));
    }

    function test_ZeroRootRejectsEveryCheckData() public {
        MockFrameFollower f = fresh();
        vm.warp(1003600);
        f.sync(104, "");
        assertEq(f.homeBlockNumber(), 104);
        f.setEntry0(KEY2, true);
        assertFalse(accepts(f, 10, pred(KEY2), sib10()));
        MockFrameFollower g = fresh();
        g.sync(100, "");
        g.setEntry0(KEY1, true);
        assertTrue(accepts(g, 0, pred(KEY1), sib0()));
        g.sync(104, "");
        assertFalse(accepts(g, 0, pred(KEY1), sib0()));
        g.setEntry0(KEY2, true);
        assertFalse(accepts(g, 10, pred(KEY2), sib10()));
    }

    function test_ZeroPredicateReverts() public {
        bytes32[4] memory s = sib10();
        bytes32 h = keccak256(abi.encodePacked(bytes1(0x00), uint256(10), bytes32(0)));
        for (uint256 k = 0; k < 4; k++) {
            h = (10 >> k) & 1 == 0 ? node(h, s[k]) : node(s[k], h);
        }
        adapter.put(107, h, 1003000);
        MockFrameFollower f = fresh();
        vm.warp(1003600);
        f.sync(107, "");
        f.setEntry0(address(0), true);
        assertFalse(accepts(f, 10, bytes32(0), s));
    }

    function test_NoManageOnFollower() public {
        MockFrameFollower f = fresh();
        vm.warp(1003600);
        f.sync(106, "");
        bytes32 p = bytes32(uint256(uint160(KEY2)) | (1 << 160));
        f.setEntry0(KEY2, true);
        assertTrue(accepts(f, 10, p, sib10()));
        f.setSenderToSelf(true);
        assertFalse(accepts(f, 10, p, sib10()));
    }

    function test_EventOnlyWhenRootChanges() public {
        MockFrameFollower f = fresh();
        vm.warp(1003600);
        vm.recordLogs();
        f.sync(100, "");
        f.sync(101, "");
        f.sync(103, "");
        Vm.Log[] memory logs = vm.getRecordedLogs();
        assertEq(logs.length, 2);
        assertEq(logs[0].topics[0], TOPIC);
        assertEq(logs[0].topics[1], ROOT);
        assertEq(logs[1].topics[1], ROOT_AFTER_REVOKE);
    }

    function test_ZeroRootWhenHomeAbsent() public {
        MockFrameFollower f = fresh();
        vm.warp(1003600);
        f.sync(100, "");
        f.sync(104, "");
        (bytes32 r,) = f.authorityRoot();
        assertEq(r, bytes32(0));
    }

    function test_ShortReturnReverts() public {
        MockFrameFollower f = fresh();
        vm.warp(1003600);
        adapter.setMode(1);
        vm.expectRevert();
        f.sync(100, "");
    }

    function test_AdapterRevertReverts() public {
        MockFrameFollower f = fresh();
        vm.warp(1003600);
        vm.expectRevert();
        f.sync(999, "");
    }

    function test_HomeValues() public {
        MockFrameFollower f = fresh();
        vm.warp(1003600);
        f.sync(100, "");
        (uint256 c, address a, address ad, uint256 m, uint256 b) = f.home();
        assertEq(c, 1); assertEq(a, HOME); assertEq(ad, address(adapter)); assertEq(m, 3600); assertEq(b, 100);
    }

    function test_FutureTimestampDoesNotRevert() public {
        MockFrameFollower f = fresh();
        vm.warp(1003600);
        f.sync(105, "");
        assertEq(f.homeBlockNumber(), 105);
    }

    function test_RevokeReachesFollowerOnlyWithSync() public {
        MockFrameFollower f = fresh();
        vm.warp(1003600);
        f.sync(100, "");
        vm.warp(1003600 + 365 days);
        (bytes32 r,) = f.authorityRoot();
        assertEq(r, ROOT);
        vm.warp(1003600);
        f.sync(103, "");
        (r,) = f.authorityRoot();
        assertEq(r, ROOT_AFTER_REVOKE);
    }
}
