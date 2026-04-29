#!/usr/bin/env python3
"""Soft-matte chroma-key cleanup for solid-color background sprite/prop sheets.

Designed for the agent-sprite-forge Cursor adaptation. Use this before
`extract_prop_pack.py` when the raw generated sheet has antialiased fringe or
when the props will be composited over a dark/detailed base map.

For the simple hard-key case, `extract_prop_pack.py` already removes solid
magenta on its own; only run this script when the soft-matte / despill stage
materially improves edge quality.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image


def parse_color(value: str) -> tuple[int, int, int]:
    value = value.strip().lstrip("#")
    if len(value) == 3:
        value = "".join(c * 2 for c in value)
    if len(value) != 6:
        raise ValueError(f"Invalid hex color: {value!r}")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def soft_matte_alpha(
    rgb: np.ndarray,
    key: tuple[int, int, int],
    transparent_threshold: int,
    opaque_threshold: int,
) -> np.ndarray:
    """Compute alpha 0..255 from per-pixel distance to the key color.

    Pixels within `transparent_threshold` of the key are fully transparent.
    Pixels farther than `opaque_threshold` are fully opaque.
    Pixels in between are linearly ramped.
    """

    if opaque_threshold <= transparent_threshold:
        raise ValueError(
            "opaque_threshold must be greater than transparent_threshold"
        )

    diff = rgb.astype(np.int32) - np.array(key, dtype=np.int32)
    dist = np.sqrt(np.sum(diff * diff, axis=-1))
    span = float(opaque_threshold - transparent_threshold)
    alpha = (dist - transparent_threshold) / span
    alpha = np.clip(alpha, 0.0, 1.0)
    return (alpha * 255.0).astype(np.uint8)


def despill_rgb(
    rgb: np.ndarray,
    key: tuple[int, int, int],
    strength: float = 1.0,
) -> np.ndarray:
    """Reduce key-color spill on remaining pixels.

    Implements a simple per-channel approach: for each pixel, suppress the
    component that matches the dominant key channel(s) when it exceeds the
    average of the other two channels. This is intentionally conservative.
    """

    out = rgb.astype(np.float32)
    r, g, b = out[..., 0], out[..., 1], out[..., 2]
    key_r, key_g, key_b = key

    # magenta-like keys (high R + high B, low G) -> suppress R/B above G
    if key_r > 128 and key_b > 128 and key_g < 128:
        avg_other = g
        out[..., 0] = np.minimum(r, np.maximum(avg_other, r - strength * (r - avg_other)))
        out[..., 2] = np.minimum(b, np.maximum(avg_other, b - strength * (b - avg_other)))
    # green-like keys -> suppress G above max(R, B)
    elif key_g > 128 and key_r < 128 and key_b < 128:
        avg_other = np.maximum(r, b)
        out[..., 1] = np.minimum(g, np.maximum(avg_other, g - strength * (g - avg_other)))
    # blue-like keys -> suppress B above max(R, G)
    elif key_b > 128 and key_r < 128 and key_g < 128:
        avg_other = np.maximum(r, g)
        out[..., 2] = np.minimum(b, np.maximum(avg_other, b - strength * (b - avg_other)))
    # red-like keys -> suppress R above max(G, B)
    elif key_r > 128 and key_g < 128 and key_b < 128:
        avg_other = np.maximum(g, b)
        out[..., 0] = np.minimum(r, np.maximum(avg_other, r - strength * (r - avg_other)))

    return np.clip(out, 0, 255).astype(np.uint8)


def edge_contract_alpha(alpha: np.ndarray, depth: int) -> np.ndarray:
    """Erode the alpha channel by `depth` pixels via 4-neighbour min."""

    if depth <= 0:
        return alpha
    out = alpha.copy()
    for _ in range(depth):
        shifted = np.full_like(out, 255)
        shifted[1:, :] = np.minimum(shifted[1:, :], out[:-1, :])
        shifted[:-1, :] = np.minimum(shifted[:-1, :], out[1:, :])
        shifted[:, 1:] = np.minimum(shifted[:, 1:], out[:, :-1])
        shifted[:, :-1] = np.minimum(shifted[:, :-1], out[:, 1:])
        shifted[0, :] = np.minimum(shifted[0, :], out[0, :])
        shifted[-1, :] = np.minimum(shifted[-1, :], out[-1, :])
        shifted[:, 0] = np.minimum(shifted[:, 0], out[:, 0])
        shifted[:, -1] = np.minimum(shifted[:, -1], out[:, -1])
        out = np.minimum(out, shifted)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--key-color", default="#ff00ff",
                        help="Hex color of the background to remove (default: magenta).")
    parser.add_argument("--soft-matte", action="store_true",
                        help="Use a ramp between transparent/opaque thresholds.")
    parser.add_argument("--transparent-threshold", type=int, default=35,
                        help="Pixels within this distance of the key are fully transparent.")
    parser.add_argument("--opaque-threshold", type=int, default=160,
                        help="Pixels farther than this are fully opaque.")
    parser.add_argument("--despill", action="store_true",
                        help="Suppress residual key-color spill on opaque pixels.")
    parser.add_argument("--despill-strength", type=float, default=1.0)
    parser.add_argument("--edge-contract", type=int, default=0,
                        help="Erode the alpha channel by N pixels after matting.")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite the output file if it exists.")
    args = parser.parse_args()

    if args.out.exists() and not args.force:
        raise SystemExit(f"output exists: {args.out} (pass --force to overwrite)")

    img = Image.open(args.input).convert("RGBA")
    arr = np.asarray(img, dtype=np.uint8).copy()
    rgb = arr[..., :3]
    key = parse_color(args.key_color)

    if args.soft_matte:
        alpha = soft_matte_alpha(rgb, key, args.transparent_threshold, args.opaque_threshold)
    else:
        diff = rgb.astype(np.int32) - np.array(key, dtype=np.int32)
        dist = np.sqrt(np.sum(diff * diff, axis=-1))
        alpha = np.where(dist <= args.transparent_threshold, 0, 255).astype(np.uint8)

    if args.despill:
        rgb = despill_rgb(rgb, key, strength=args.despill_strength)

    if args.edge_contract:
        alpha = edge_contract_alpha(alpha, args.edge_contract)

    out_arr = np.dstack([rgb, alpha]).astype(np.uint8)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(out_arr, mode="RGBA").save(args.out)


if __name__ == "__main__":
    main()
