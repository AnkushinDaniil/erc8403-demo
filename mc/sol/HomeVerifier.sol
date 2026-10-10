// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

contract HomeVerifier {
    function importCheck(address homeAccount, bytes calldata header, bytes[] calldata proof)
        external
        pure
        returns (address signer, uint256 number, bytes32 storageRoot)
    {
        (uint256 start, uint256 payload) = _item(header, 0);
        uint256 end = start + payload;
        uint256 cursor = start;
        bytes32 stateRoot;
        uint256 extraItem;
        uint256 extraData;
        uint256 extraLength;
        for (uint256 i = 0; i < 13; i++) {
            (uint256 data, uint256 length) = _item(header, cursor);
            if (i == 3) stateRoot = bytes32(header[data:data + 32]);
            if (i == 8) number = _toUint(header[data:data + length]);
            if (i == 12) {
                extraItem = cursor;
                extraData = data;
                extraLength = length;
            }
            cursor = data + length;
        }
        uint256 vanity = extraLength - 65;
        bytes memory extraHead = _head(vanity, 0x80);
        uint256 sealedPayload = payload - 65 - (extraData - extraItem) + extraHead.length;
        bytes32 sealHash = keccak256(
            bytes.concat(
                _head(sealedPayload, 0xc0),
                header[start:extraItem],
                extraHead,
                header[extraData:extraData + vanity],
                header[extraData + extraLength:end]
            )
        );
        bytes calldata signature = header[extraData + vanity:extraData + extraLength];
        signer = ecrecover(sealHash, uint8(signature[64]) + 27, bytes32(signature[0:32]), bytes32(signature[32:64]));
        bytes calldata account = _walk(stateRoot, keccak256(abi.encodePacked(homeAccount)), proof);
        (uint256 fields,) = _item(account, 0);
        (uint256 nonceData, uint256 nonceLength) = _item(account, fields);
        (uint256 balanceData, uint256 balanceLength) = _item(account, nonceData + nonceLength);
        (uint256 rootData,) = _item(account, balanceData + balanceLength);
        storageRoot = bytes32(account[rootData:rootData + 32]);
    }

    function slotZero(bytes32 storageRoot, bytes[] calldata proof) external pure returns (bytes32) {
        bytes calldata encoded = _walk(storageRoot, keccak256(abi.encode(uint256(0))), proof);
        (uint256 data, uint256 length) = _item(encoded, 0);
        return bytes32(_toUint(encoded[data:data + length]));
    }

    function _walk(bytes32 root, bytes32 key, bytes[] calldata proof) private pure returns (bytes calldata) {
        bytes32 expected = root;
        uint256 depth = 0;
        for (uint256 k = 0; k < proof.length; k++) {
            bytes calldata node = proof[k];
            require(keccak256(node) == expected);
            (uint256 start, uint256 payload) = _item(node, 0);
            uint256 count = 0;
            uint256 cursor = start;
            while (cursor < start + payload) {
                (uint256 data, uint256 length) = _item(node, cursor);
                cursor = data + length;
                count++;
            }
            if (count == 17) {
                uint256 branch = _nibble(key, depth);
                depth++;
                cursor = start;
                for (uint256 j = 0; j < branch; j++) {
                    (uint256 data, uint256 length) = _item(node, cursor);
                    cursor = data + length;
                }
                (uint256 child, uint256 childLength) = _item(node, cursor);
                require(childLength == 32);
                expected = bytes32(node[child:child + 32]);
            } else {
                require(count == 2);
                (uint256 path, uint256 pathLength) = _item(node, start);
                (uint256 value, uint256 valueLength) = _item(node, path + pathLength);
                uint8 flag = uint8(node[path]) >> 4;
                uint256 skip = flag & 1 == 1 ? 1 : 2;
                uint256 nibbles = pathLength * 2 - skip;
                for (uint256 t = 0; t < nibbles; t++) {
                    uint256 at = t + skip;
                    uint8 pair = uint8(node[path + at / 2]);
                    uint256 nibble = at % 2 == 0 ? pair >> 4 : pair & 0x0f;
                    require(nibble == _nibble(key, depth + t));
                }
                depth += nibbles;
                if (flag >= 2) {
                    require(depth == 64 && k == proof.length - 1);
                    return node[value:value + valueLength];
                }
                require(valueLength == 32);
                expected = bytes32(node[value:value + 32]);
            }
        }
        revert();
    }

    function _nibble(bytes32 key, uint256 index) private pure returns (uint256) {
        return (uint256(key) >> (252 - 4 * index)) & 0x0f;
    }

    function _toUint(bytes calldata raw) private pure returns (uint256 result) {
        require(raw.length <= 32);
        for (uint256 i = 0; i < raw.length; i++) {
            result = (result << 8) | uint8(raw[i]);
        }
    }

    function _item(bytes calldata encoded, uint256 at) private pure returns (uint256 data, uint256 length) {
        uint256 prefix = uint8(encoded[at]);
        if (prefix < 0x80) return (at, 1);
        if (prefix < 0xb8) return (at + 1, prefix - 0x80);
        if (prefix < 0xc0) return (at + 1 + prefix - 0xb7, _toUint(encoded[at + 1:at + 1 + prefix - 0xb7]));
        if (prefix < 0xf8) return (at + 1, prefix - 0xc0);
        return (at + 1 + prefix - 0xf7, _toUint(encoded[at + 1:at + 1 + prefix - 0xf7]));
    }

    function _head(uint256 length, uint8 base) private pure returns (bytes memory) {
        if (length < 56) return abi.encodePacked(uint8(base + length));
        uint256 size = 0;
        for (uint256 rest = length; rest > 0; rest >>= 8) {
            size++;
        }
        bytes memory out = new bytes(size + 1);
        out[0] = bytes1(uint8(base + 55 + size));
        for (uint256 i = 0; i < size; i++) {
            out[size - i] = bytes1(uint8(length >> (8 * i)));
        }
        return out;
    }
}
