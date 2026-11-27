# modules/puzzle.py
# NEUROLENS — Brain Puzzle
# PC mouse + mobile/tablet touch drag-and-drop puzzle

import streamlit as st
import streamlit.components.v1 as components


PUZZLE_LEVELS = {
    "Beginner": 3,
    "Intermediate": 4,
    "Advanced": 5,
}


def puzzle_screen(image_path="assets/brain.png"):
    st.markdown(
        """
        <style>
        .puzzle-title {
            font-size: 32px;
            font-weight: 800;
            margin-bottom: 4px;
        }

        .puzzle-sub {
            color: #9ca3af;
            margin-bottom: 18px;
        }

        .puzzle-card {
            padding: 18px;
            border-radius: 18px;
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.10);
            margin-bottom: 15px;
        }
        </style>

        <div class="puzzle-title">🧠 Brain Picture Puzzle</div>
        <div class="puzzle-sub">
            Drag each brain piece with your finger or mouse and drop it
            into the correct position.
        </div>
        """,
        unsafe_allow_html=True,
    )

    level = st.selectbox(
        "Puzzle level",
        list(PUZZLE_LEVELS.keys()),
        key="puzzle_level_select",
    )

    size = PUZZLE_LEVELS[level]

    components.html(
        _puzzle_html(image_path, size),
        height=760,
        scrolling=False,
    )

    st.markdown(
        """
        <div class="puzzle-card">
        <b>How to play</b><br>
        • Press and hold a piece.<br>
        • Drag it to its matching position.<br>
        • Release to place it.<br>
        • Correct pieces snap into position.<br>
        • Complete the whole brain to finish the challenge.
        </div>
        """,
        unsafe_allow_html=True,
    )


def _puzzle_html(image_path, size):

    # Escape the image path for JS/HTML usage
    safe_path = image_path.replace("\\", "/").replace("'", "\\'")

    return f"""
<!DOCTYPE html>
<html>
<head>

<meta name="viewport"
      content="width=device-width,
               initial-scale=1.0,
               maximum-scale=1.0,
               user-scalable=no">

<style>

* {{
    box-sizing: border-box;
}}

html, body {{
    margin: 0;
    padding: 0;
    background: transparent;
    font-family: Arial, sans-serif;
    color: white;
    overflow-x: hidden;
}}

.wrapper {{
    width: 100%;
    max-width: 760px;
    margin: auto;
    padding: 8px;
}}

.topbar {{
    display: flex;
    justify-content: space-between;
    gap: 8px;
    flex-wrap: wrap;
    margin-bottom: 12px;
}}

.stat {{
    background: rgba(255,255,255,.07);
    border: 1px solid rgba(255,255,255,.12);
    border-radius: 12px;
    padding: 9px 12px;
    font-size: 13px;
}}

#game {{
    position: relative;
    width: 100%;
    aspect-ratio: 1 / 1;
    max-width: 650px;
    margin: auto;
    border-radius: 18px;
    overflow: hidden;
    background:
        radial-gradient(circle at center,
        rgba(50,100,150,.25),
        rgba(5,10,20,.95));
    border: 2px solid rgba(255,255,255,.15);
    touch-action: none;
}}

#board {{
    position: absolute;
    inset: 0;
}}

.slot {{
    position: absolute;
    border: 1px dashed rgba(255,255,255,.28);
    background: rgba(255,255,255,.025);
    border-radius: 8px;
}}

.piece {{
    position: absolute;
    background-image: url('{safe_path}');
    background-repeat: no-repeat;
    background-size: 100% 100%;
    cursor: grab;
    touch-action: none;
    z-index: 5;
    border-radius: 8px;

    box-shadow:
        0 5px 16px rgba(0,0,0,.35);

    transition:
        left .18s ease,
        top .18s ease,
        transform .18s ease;
}}

.piece.dragging {{
    cursor: grabbing;
    transform: scale(1.04);
    z-index: 100;
    box-shadow:
        0 15px 35px rgba(0,0,0,.55);
}}

.piece.correct {{
    z-index: 2;
    box-shadow:
        0 0 0 2px rgba(100,220,170,.45);
}}

#message {{
    text-align: center;
    min-height: 28px;
    margin-top: 14px;
    font-weight: 700;
    font-size: 17px;
}}

#restart {{
    border: none;
    background: rgba(255,255,255,.10);
    color: white;
    padding: 9px 16px;
    border-radius: 10px;
    cursor: pointer;
}}

#restart:hover {{
    background: rgba(255,255,255,.18);
}}

</style>
</head>

<body>

<div class="wrapper">

    <div class="topbar">

        <div class="stat">
            Level: <b>{size} × {size}</b>
        </div>

        <div class="stat">
            Time: <b id="time">0</b>s
        </div>

        <div class="stat">
            Moves: <b id="moves">0</b>
        </div>

        <div class="stat">
            Correct: <b id="correct">0</b> / {size * size}
        </div>

        <button id="restart">
            ↻ Restart
        </button>

    </div>

    <div id="game">
        <div id="board"></div>
    </div>

    <div id="message">
        🧠 Drag the pieces into the correct positions.
    </div>

</div>


<script>

const SIZE = {size};
const TOTAL = SIZE * SIZE;

const game = document.getElementById("game");
const board = document.getElementById("board");

const timeEl = document.getElementById("time");
const movesEl = document.getElementById("moves");
const correctEl = document.getElementById("correct");
const messageEl = document.getElementById("message");

let pieces = [];
let moves = 0;
let correct = 0;
let seconds = 0;
let started = false;
let completed = false;

let timer = null;


/* ---------------------------------------
   START TIMER
--------------------------------------- */

function startTimer() {{

    if (started) return;

    started = true;

    timer = setInterval(() => {{

        if (!completed) {{
            seconds++;
            timeEl.textContent = seconds;
        }}

    }}, 1000);
}}


/* ---------------------------------------
   CREATE BOARD
--------------------------------------- */

function createBoard() {{

    board.innerHTML = "";
    pieces = [];

    moves = 0;
    correct = 0;
    seconds = 0;
    started = false;
    completed = false;

    if (timer) {{
        clearInterval(timer);
        timer = null;
    }}

    movesEl.textContent = "0";
    correctEl.textContent = "0";
    timeEl.textContent = "0";

    messageEl.textContent =
        "🧠 Drag the pieces into the correct positions.";

    const rect = game.getBoundingClientRect();

    const W = rect.width;
    const H = rect.height;

    const cellW = W / SIZE;
    const cellH = H / SIZE;


    /* -----------------------------------
       TARGET SLOTS
    ----------------------------------- */

    for (let row = 0; row < SIZE; row++) {{

        for (let col = 0; col < SIZE; col++) {{

            const slot = document.createElement("div");

            slot.className = "slot";

            slot.style.width = cellW + "px";
            slot.style.height = cellH + "px";

            slot.style.left = (col * cellW) + "px";
            slot.style.top = (row * cellH) + "px";

            slot.dataset.index =
                row * SIZE + col;

            board.appendChild(slot);
        }}
    }}


    /* -----------------------------------
       CREATE PIECES
    ----------------------------------- */

    const indexes = [];

    for (let i = 0; i < TOTAL; i++) {{
        indexes.push(i);
    }}

    shuffle(indexes);


    indexes.forEach((targetIndex, pieceIndex) => {{

        const piece = document.createElement("div");

        piece.className = "piece";

        piece.style.width = cellW + "px";
        piece.style.height = cellH + "px";


        const targetRow =
            Math.floor(targetIndex / SIZE);

        const targetCol =
            targetIndex % SIZE;


        /*
         * Background position shows the
         * correct section of the original brain.
         */

        piece.style.backgroundSize =
            (SIZE * 100) + "% " +
            (SIZE * 100) + "%";


        const bgX =
            targetCol * (100 / (SIZE - 1));

        const bgY =
            targetRow * (100 / (SIZE - 1));


        if (SIZE === 1) {{
            piece.style.backgroundPosition =
                "center center";
        }} else {{

            piece.style.backgroundPosition =
                bgX + "% " + bgY + "%";
        }}


        /*
         * Random starting area around the
         * board edges.
         */

        const startX =
            Math.random() *
            Math.max(1, W - cellW);

        const startY =
            Math.random() *
            Math.max(1, H - cellH);


        piece.style.left = startX + "px";
        piece.style.top = startY + "px";


        piece.dataset.target = targetIndex;
        piece.dataset.current = "-1";


        board.appendChild(piece);

        pieces.push(piece);

        enableDrag(piece);
    }});
}}


/* ---------------------------------------
   SHUFFLE
--------------------------------------- */

function shuffle(array) {{

    for (
        let i = array.length - 1;
        i > 0;
        i--
    ) {{

        const j =
            Math.floor(Math.random() * (i + 1));

        [
            array[i],
            array[j]
        ] =
        [
            array[j],
            array[i]
        ];
    }}

    return array;
}}


/* ---------------------------------------
   DRAG SYSTEM
--------------------------------------- */

function enableDrag(piece) {{

    let dragging = false;

    let offsetX = 0;
    let offsetY = 0;

    let startX = 0;
    let startY = 0;


    function pointerDown(e) {{

        if (piece.classList.contains("correct")) {{
            return;
        }}

        e.preventDefault();

        startTimer();

        dragging = true;

        piece.classList.add("dragging");

        const rect =
            piece.getBoundingClientRect();

        const gameRect =
            game.getBoundingClientRect();

        const clientX =
            e.clientX !== undefined
                ? e.clientX
                : e.touches[0].clientX;

        const clientY =
            e.clientY !== undefined
                ? e.clientY
                : e.touches[0].clientY;


        offsetX =
            clientX -
            rect.left;

        offsetY =
            clientY -
            rect.top;


        startX =
            clientX -
            gameRect.left -
            offsetX;

        startY =
            clientY -
            gameRect.top -
            offsetY;


        try {{
            piece.setPointerCapture(e.pointerId);
        }} catch(err) {{}}
    }}


    function pointerMove(e) {{

        if (!dragging) return;

        e.preventDefault();

        const gameRect =
            game.getBoundingClientRect();

        let x =
            e.clientX -
            gameRect.left -
            offsetX;

        let y =
            e.clientY -
            gameRect.top -
            offsetY;


        /*
         * Keep piece inside board.
         */

        const maxX =
            game.clientWidth -
            piece.offsetWidth;

        const maxY =
            game.clientHeight -
            piece.offsetHeight;


        x = Math.max(
            -10,
            Math.min(x, maxX + 10)
        );

        y = Math.max(
            -10,
            Math.min(y, maxY + 10)
        );


        piece.style.left = x + "px";
        piece.style.top = y + "px";
    }}


    function pointerUp(e) {{

        if (!dragging) return;

        e.preventDefault();

        dragging = false;

        piece.classList.remove("dragging");

        moves++;

        movesEl.textContent = moves;


        checkPlacement(piece);
    }}


    piece.addEventListener(
        "pointerdown",
        pointerDown
    );

    piece.addEventListener(
        "pointermove",
        pointerMove
    );

    piece.addEventListener(
        "pointerup",
        pointerUp
    );

    piece.addEventListener(
        "pointercancel",
        pointerUp
    );
}}


/* ---------------------------------------
   CHECK DROP
--------------------------------------- */

function checkPlacement(piece) {{

    const targetIndex =
        Number(piece.dataset.target);

    const row =
        Math.floor(targetIndex / SIZE);

    const col =
        targetIndex % SIZE;


    const cellW =
        game.clientWidth / SIZE;

    const cellH =
        game.clientHeight / SIZE;


    const targetX =
        col * cellW;

    const targetY =
        row * cellH;


    const currentX =
        parseFloat(piece.style.left);

    const currentY =
        parseFloat(piece.style.top);


    const distance =
        Math.sqrt(
            Math.pow(currentX - targetX, 2) +
            Math.pow(currentY - targetY, 2)
        );


    /*
     * Snap threshold.
     */

    const threshold =
        Math.min(cellW, cellH) * 0.38;


    if (distance <= threshold) {{

        piece.style.left =
            targetX + "px";

        piece.style.top =
            targetY + "px";

        piece.classList.add("correct");

        piece.dataset.current =
            targetIndex;

        correct++;

        correctEl.textContent =
            correct;


        if (correct === TOTAL) {{
            finishPuzzle();
        }} else {{

            messageEl.textContent =
                "✓ Correct placement!";
        }}

    }} else {{

        messageEl.textContent =
            "Try another position 🧠";
    }}
}}


/* ---------------------------------------
   FINISH
--------------------------------------- */

function finishPuzzle() {{

    completed = true;

    if (timer) {{
        clearInterval(timer);
        timer = null;
    }}


    const score =
        Math.max(
            0,
            Math.round(
                1000
                - seconds * 3
                - moves * 5
            )
        );


    messageEl.innerHTML =
        "🎉 Brain Puzzle Complete! " +
        "Score: <b>" + score + "</b>";


    /*
     * Send result to parent Streamlit page.
     */

    try {{

        window.parent.postMessage(
            {{
                type: "NEUROLENS_PUZZLE_RESULT",
                level: SIZE + "x" + SIZE,
                moves: moves,
                time: seconds,
                correct: correct,
                score: score
            }},
            "*"
        );

    }} catch(err) {{}}
}}


/* ---------------------------------------
   RESTART
--------------------------------------- */

document
    .getElementById("restart")
    .addEventListener(
        "click",
        createBoard
    );


/* ---------------------------------------
   RESPONSIVE REBUILD
--------------------------------------- */

let resizeTimer = null;

window.addEventListener(
    "resize",
    () => {{

        clearTimeout(resizeTimer);

        resizeTimer =
            setTimeout(() => {{
                createBoard();
            }}, 250);
    }}
);


/* ---------------------------------------
   INITIALIZE
--------------------------------------- */

createBoard();

</script>

</body>
</html>
"""


# Optional direct call
def render():
    puzzle_screen()
