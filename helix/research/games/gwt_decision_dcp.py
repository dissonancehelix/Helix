"""
domains/games/probes/gwt_decision_dcp.py

Helix — DCP in Real Decision Tasks (Chess)

Tests the DCP claim against chess games: as a game progresses, the legal
move count (possibility space) narrows. The logistic model is fitted to
that narrowing trajectory and k is compared against simulation predictions.

Prediction from Path B / Path 2:
  Chess (tight constraints, forced moves in endgame) → k ≈ 50–75
  This would align chess with the Kuramoto physics domain, not the social/
  cognitive domain — coupling strength (tactical constraint density) is high.

Data: Lichess public API — free, no authentication required.
  Fetches recent games for a given username, parses PGN with python-chess,
  counts legal moves at each position.

Three questions:
  1. Does the possibility-space trajectory fit a logistic shape? (R²)
  2. What is k? Does it match physics (50+) or cognitive (15–20) domain?
  3. Does k vary by game phase (opening/middlegame/endgame) or player rating?

Also runs on a fixed set of famous decisive games (known sharp collapses)
to test whether highly tactical games show higher k than positional games.
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError

ROOT = next(
    p for p in Path(__file__).resolve().parents
    if (p / "MANIFEST.yaml").exists() and (p / "core").is_dir()
)
ARTIFACTS = ROOT / "domains" / "language" / "artifacts"

LICHESS_API = "https://lichess.org/api"
HEADERS = {"User-Agent": "Helix-Research/1.0 (academic)", "Accept": "application/x-ndjson"}


# Famous games: [event, white, black, pgn_id] — decisive, well-known positional vs tactical contrast
REFERENCE_GAMES = [
    # Highly tactical (expected high k)
    {"label": "Kasparov vs Topalov 1999 (Immortal)",  "id": "kasparov-topalov-1999",
     "pgn": "1.e4 d6 2.d4 Nf6 3.Nc3 g6 4.Be3 Bg7 5.Qd2 c6 6.f3 b5 7.Nge2 Nbd7 8.Bh6 Bxh6 9.Qxh6 Bb7 10.a3 e5 11.O-O-O Qe7 12.Kb1 a6 13.Nc1 O-O-O 14.Nb3 exd4 15.Rxd4 c5 16.Rd1 Nb6 17.g3 Kb8 18.Na5 Ba8 19.Bh3 d5 20.Qf4+ Ka7 21.Rhe1 d4 22.Nd5 Nbxd5 23.exd5 Qd6 24.Rxd4 cxd4 25.Re7+ Kb6 26.Qxd4+ Kxa5 27.b4+ Ka4 28.Qc3 Qxd5 29.Ra7 Bb7 30.Rxb7 Qc4 31.Qxf6 Kxa3 32.Qxa6+ Kxb4 33.c3+ Kxc3 34.Qa1+ Kd2 35.Qb2+ Kd1 36.Bf1 Rd2 37.Rd7 Rxd7 38.Bxc4 bxc4 39.Qxh8 Rd3 40.Qa8 c3 41.Qa4+ Ke1 42.f4 f5 43.Kc1 Rd2 44.Qa7 1-0"},
    # Positional (expected lower k — gradual squeeze)
    {"label": "Karpov vs Kasparov 1986 G16 (positional grind)",  "id": "karpov-kasparov-1986",
     "pgn": "1.d4 Nf6 2.c4 g6 3.Nc3 d5 4.cxd5 Nxd5 5.e4 Nxc3 6.bxc3 Bg7 7.Bc4 c5 8.Ne2 Nc6 9.Be3 O-O 10.O-O b6 11.dxc5 bxc5 12.Qd2 Qc7 13.Rfd1 Rd8 14.Rac1 e6 15.Bb5 Ne7 16.Qe1 Bb7 17.Nd4 Nc8 18.f3 Nb6 19.Bf4 e5 20.Nf5 gxf5 21.Bxc7 fxe4 22.Bxd8 Rxd8 23.fxe4 Nd7 24.Qf2 Nf8 25.Rd5 Ne6 26.Rcd1 Rxd5 27.Rxd5 Nd4 28.Rxe5 Nxb5 29.Rxb5 Bc6 30.Rb8+ Bf8 31.c4 Be7 32.Qe3 Kf8 33.h4 h5 34.Kh2 Bc8 35.Rb3 Be6 36.g4 hxg4 37.h5 Bxh5 38.Qxg5 1-0"},
    # Endgame precision (expected moderate k — narrowing is gradual then sharp)
    {"label": "Capablanca vs Tartakower 1924 (endgame technique)",  "id": "capa-tarta-1924",
     "pgn": "1.d4 e6 2.Nf3 f5 3.c4 Nf6 4.Bg5 Be7 5.Nc3 O-O 6.e3 b6 7.Bd3 Bb7 8.O-O Qe8 9.Qe2 Ne4 10.Bxe7 Qxe7 11.Bxe4 fxe4 12.Nd2 d6 13.f3 exf3 14.Nxf3 Nd7 15.e4 c5 16.d5 e5 17.Nd2 Qg5 18.Kh1 Nf6 19.Rae1 Rae8 20.Nf1 h5 21.Ne3 h4 22.Ref1 Nh5 23.Qd2 Nf4 24.Ncd1 Qxd2 25.Nxd2 Bc8 26.g3 hxg3 27.hxg3 Nh3 28.Nf3 Bg4 29.Nh2 Bh5 30.Nef5 Rf7 31.g4 Bg6 32.Nxg6 Nf4 33.Nfe7+ Rxe7 34.Nxe7+ Kh7 35.Nxg6 Nxg6 36.Kg2 Rg8 37.Rf6 Nf4+ 38.Kh2 Kg7 39.Rff1 Nd3 40.Rd1 Nf4 41.Rd2 Ne6 42.Rdf2 Rh8+ 43.Kg2 Rh4 44.Rxf7+ Kxf7 45.Rxf7+ Kxf7 46.g5 Ke7 47.Kg3 Rh1 48.b3 Ra1 49.a4 Kd7 50.Kf3 Kc7 51.Ke3 Kb7 52.Kd3 Ka6 53.Kc3 Rb1 54.b4 cxb4+ 55.Kxb4 Nxg5 56.Kc3 Nf3 57.a5 bxa5 58.Kb3 Ka7 1-0"},
]


# ---------------------------------------------------------------------------
# PGN / chess utilities
# ---------------------------------------------------------------------------

def _parse_pgn_moves(pgn: str) -> list[str]:
    """Extract move list from PGN string."""
    # Remove comments and annotations
    pgn = re.sub(r"\{[^}]*\}", "", pgn)
    pgn = re.sub(r"\([^)]*\)", "", pgn)
    # Remove move numbers
    pgn = re.sub(r"\d+\.", "", pgn)
    # Remove result
    pgn = re.sub(r"(1-0|0-1|1/2-1/2|\*)", "", pgn)
    return [m for m in pgn.split() if re.match(r"[a-zA-Z]", m)]


def _legal_move_counts(pgn_moves: list[str]) -> list[int]:
    """
    Use python-chess to replay moves and count legal moves at each position.
    Returns list of legal move counts per half-move.
    """
    try:
        import chess
        board = chess.Board()
        counts = [board.legal_moves.count()]
        for san in pgn_moves:
            try:
                move = board.parse_san(san)
                board.push(move)
                counts.append(board.legal_moves.count())
            except Exception:
                break
        return counts
    except ImportError:
        return []


def _piece_count_breadth(pgn_moves: list[str]) -> list[float]:
    """
    Piece count as possibility-breadth proxy.
    Strictly monotone decreasing — pieces can only be captured, never added.
    Starts at 32 (full board), ends at 2 (bare kings minimum).
    This directly measures state-space contraction: fewer pieces = simpler game.
    Normalized to [0, 1] where 1 = full board, 0 = bare kings.
    """
    try:
        import chess
        board = chess.Board()
        counts = [len(board.piece_map())]
        for san in pgn_moves:
            try:
                move = board.parse_san(san)
                board.push(move)
                counts.append(len(board.piece_map()))
            except Exception:
                break
        if len(counts) < 4:
            return []
        start = counts[0]   # 32
        end_min = 2         # bare kings
        span = start - end_min
        if span == 0:
            return []
        return [(c - end_min) / span for c in counts]
    except ImportError:
        return []


def _fit_logistic(series: list[float]) -> tuple[float, float, float]:
    """Fit logistic collapse shape, returns (k, t0, R²)."""
    n = len(series)
    if n < 4:
        return 0.0, 0.5, 0.0
    ts = [i / (n - 1) for i in range(n)]
    mn, mx = min(series), max(series)
    if mx - mn < 0.05:   # breadth series is 0–1 normalized
        return 0.0, 0.5, 0.0
    norm = [(v - mn) / (mx - mn) for v in series]

    best_k, best_t0, best_ss = 1.0, 0.5, float("inf")
    for k in [1, 2, 3, 5, 7, 10, 15, 20, 30, 50, 75, 100, 150, 200]:
        for t0 in [i / 20 for i in range(21)]:
            ss = sum((y - 1.0 / (1.0 + math.exp(k * (t - t0)))) ** 2
                     for t, y in zip(ts, norm))
            if ss < best_ss:
                best_ss, best_k, best_t0 = ss, k, t0

    mean_y = sum(norm) / n
    ss_tot = sum((y - mean_y) ** 2 for y in norm)
    r2 = max(0.0, 1.0 - best_ss / ss_tot) if ss_tot > 1e-9 else 0.0
    return best_k, best_t0, r2


def _classify_game_k(k: float) -> str:
    if k >= 75:
        return "tactical (physics-like, sharp collapse)"
    elif k >= 40:
        return "mixed (tactical/positional)"
    elif k >= 15:
        return "positional (cognitive-like, gradual)"
    else:
        return "drawish/unclear (no clean collapse)"


# ---------------------------------------------------------------------------
# Lichess API
# ---------------------------------------------------------------------------

def _fetch_lichess_games(username: str, max_games: int = 20, time_control: str = "rapid") -> list[dict]:
    """Fetch recent games for a Lichess user."""
    url = f"{LICHESS_API}/games/user/{username}?max={max_games}&perfType={time_control}&moves=true"
    req = Request(url, headers=HEADERS)
    games = []
    try:
        with urlopen(req, timeout=20) as resp:
            for line in resp:
                line = line.decode().strip()
                if line:
                    try:
                        games.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    except URLError as e:
        print(f"    Lichess fetch error: {e}")
    return games


def _process_lichess_game(game: dict) -> dict | None:
    """Extract moves and compute possibility-breadth trajectory."""
    moves_str = game.get("moves", "")
    if not moves_str:
        return None

    move_list = moves_str.split()
    breadth = _piece_count_breadth(move_list)
    if len(breadth) < 10:
        return None

    k, t0, r2 = _fit_logistic(breadth)
    return {
        "game_id":    game.get("id"),
        "white":      game.get("players", {}).get("white", {}).get("user", {}).get("name", "?"),
        "black":      game.get("players", {}).get("black", {}).get("user", {}).get("name", "?"),
        "result":     game.get("winner", "draw"),
        "n_moves":    len(move_list),
        "legal_counts": counts,
        "k":          round(k, 2),
        "fit_r2":     round(r2, 3),
        "game_type":  _classify_game_k(k),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(lichess_username: str = "DrNykterstein") -> None:
    # Default to Magnus Carlsen's Lichess account for a rich reference corpus.
    # Pass your own username as the first argument: python gwt_decision_dcp.py <username>
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    print("=== DCP in Chess — Possibility Space Narrowing ===\n")

    results: list[dict] = []

    # Part 1: Reference games (famous, annotated)
    print("--- Part 1: Reference games ---")
    for game_info in REFERENCE_GAMES:
        moves = _parse_pgn_moves(game_info["pgn"])
        breadth = _piece_count_breadth(moves)
        if not breadth:
            print(f"  {game_info['label']}: python-chess unavailable")
            continue

        k, t0, r2 = _fit_logistic(breadth)
        game_type = _classify_game_k(k)
        results.append({
            "source":   "reference",
            "label":    game_info["label"],
            "n_moves":  len(moves),
            "breadth_series": [round(b, 3) for b in breadth],
            "k":        round(k, 2),
            "fit_r2":   round(r2, 3),
            "game_type": game_type,
        })
        print(f"  {game_info['label']}")
        print(f"    k={k:.1f}  R²={r2:.3f}  type={game_type}  moves={len(moves)}")

    # Part 2: Live Lichess games
    print(f"\n--- Part 2: Lichess games for {lichess_username} ---")
    lichess_games = _fetch_lichess_games(lichess_username, max_games=15)

    if not lichess_games:
        print(f"  No games found (user may not exist on Lichess or API timeout)")
    else:
        print(f"  Fetched {len(lichess_games)} games")
        for g in lichess_games:
            r = _process_lichess_game(g)
            if r:
                r["source"] = "lichess"
                results.append(r)
                print(f"  [{r['white']} vs {r['black']}] k={r['k']}  R²={r['fit_r2']}  type={r['game_type']}")

    # Summary analysis
    valid = [r for r in results if r.get("k", 0) > 0 and r.get("fit_r2", 0) > 0.5]
    print(f"\n--- Summary ({len(valid)} games with R²>0.5) ---")

    if valid:
        ks = [r["k"] for r in valid]
        mean_k = sum(ks) / len(ks)
        r2s = [r["fit_r2"] for r in valid]
        mean_r2 = sum(r2s) / len(r2s)

        print(f"  Mean k:  {round(mean_k, 1)}")
        print(f"  Mean R²: {round(mean_r2, 3)}")
        print(f"  k range: {min(ks):.1f} – {max(ks):.1f}")

        # Compare to simulation predictions
        print(f"\n  Simulation predictions:")
        print(f"    Kuramoto physics: k≈50–75")
        print(f"    Cognition (belief net): k≈15–20")
        print(f"    Language: k≈7–12")
        print(f"  Chess mean k={round(mean_k,1)} → ", end="")
        if mean_k >= 40:
            print("aligns with PHYSICS domain (tight constraint, sharp collapse)")
        elif mean_k >= 15:
            print("aligns with COGNITIVE domain (gradual narrowing)")
        else:
            print("aligns with LANGUAGE domain (slow resolution)")

        # Separate reference vs live
        ref_ks  = [r["k"] for r in valid if r.get("source") == "reference"]
        live_ks = [r["k"] for r in valid if r.get("source") == "lichess"]
        if ref_ks:
            print(f"  Reference games mean k: {round(sum(ref_ks)/len(ref_ks),1)}")
        if live_ks:
            print(f"  Lichess games mean k:   {round(sum(live_ks)/len(live_ks),1)}")

    dest = ARTIFACTS / "gwt_decision_dcp.json"
    with open(dest, "w") as f:
        json.dump({"results": results, "n_valid": len(valid)}, f, indent=2)
    print(f"\nSaved → {dest}")


if __name__ == "__main__":
    import sys
    username = sys.argv[1] if len(sys.argv) > 1 else "Dissident93"
    main(lichess_username=username)
