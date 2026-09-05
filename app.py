import os
import base64
import streamlit as st
from PIL import Image
from google import genai

# =========================================================
# PAGE
# =========================================================

st.set_page_config(
    page_title="NEUROLENS",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 NEUROLENS")
st.caption("Explore cognition, behavior & the brain")

# =========================================================
# GEMINI
# =========================================================

def get_gemini_api_key():
    try:
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]

        if "GOOGLE_API_KEY" in st.secrets:
            return st.secrets["GOOGLE_API_KEY"]
    except Exception:
        pass

    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


def ask_ayna(question):
    key = get_gemini_api_key()

    if not key:
        return "Gemini API key nahi mili."

    try:
        client = genai.Client(api_key=key)

        prompt = f"""
You are Ayna, an educational cognitive neuroscience guide
inside the NEUROLENS platform.

Answer the user's question clearly and scientifically.

Do not diagnose medical conditions.
Do not claim that simple games measure actual brain activity.
Use simple language suitable for students and curious learners.

Question:
{question}
"""

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        return response.text

    except Exception as e:
        return f"Ask Ayna temporarily unavailable: {e}"


# =========================================================
# BRAIN IMAGE
# =========================================================

BRAIN_PATH = "brain.png"

if not os.path.exists(BRAIN_PATH):
    st.error("brain.png nahi mili. GitHub repo mein app.py ke saath brain.png upload karo.")
    st.stop()

with open(BRAIN_PATH, "rb") as f:
    brain_bytes = f.read()

brain_base64 = base64.b64encode(brain_bytes).decode("utf-8")

brain_data_uri = f"data:image/png;base64,{brain_base64}"


# =========================================================
# BRAIN INFORMATION
# =========================================================

REGIONS = {

    "frontal": {
        "name": "Prefrontal Cortex",
        "description": """
The prefrontal cortex is strongly involved in planning,
decision-making, working memory, attention and cognitive control.
"""
    },

    "temporal": {
        "name": "Hippocampus",
        "description": """
The hippocampus plays an important role in memory formation,
spatial navigation and contextual learning.
"""
    },

    "amygdala": {
        "name": "Amygdala",
        "description": """
The amygdala helps process emotional significance,
especially threat, fear and emotionally important information.
"""
    },

    "striatum": {
        "name": "Striatum",
        "description": """
The striatum is involved in action selection,
reward processing, motivation and habit learning.
"""
    },

    "acc": {
        "name": "Anterior Cingulate Cortex",
        "description": """
The anterior cingulate cortex contributes to conflict monitoring,
error processing, attention and decision-making.
"""
    }
}


# =========================================================
# STREAMLIT V2 COMPONENT
# =========================================================

HTML = """
<div class="nl-root">

    <div class="nl-header">
        <div>
            <div class="nl-title">NEURAL JOURNEY</div>
            <div class="nl-subtitle">
                Travel inside the brain
            </div>
        </div>

        <div id="stageLabel" class="nl-stage">
            WHOLE BRAIN
        </div>
    </div>


    <div class="viewport">

        <div id="world">

            <!-- ACTUAL BRAIN IMAGE -->
            <div id="brainLayer">

                <img
                    id="brainImage"
                    src=""
                    draggable="false"
                />

                <!-- invisible / glowing navigation points -->
                <button
                    class="hotspot frontal"
                    data-region="frontal"
                    title="Explore frontal region">
                </button>

                <button
                    class="hotspot temporal"
                    data-region="temporal"
                    title="Explore temporal region">
                </button>

                <button
                    class="hotspot amygdala"
                    data-region="amygdala"
                    title="Explore amygdala">
                </button>

                <button
                    class="hotspot striatum"
                    data-region="striatum"
                    title="Explore striatum">
                </button>

                <button
                    class="hotspot acc"
                    data-region="acc"
                    title="Explore ACC">
                </button>

            </div>


            <!-- PATHWAY -->
            <div id="pathway"></div>


            <!-- TISSUE -->
            <div id="tissue">

                <div class="cell">
                    <div class="cell-nucleus"></div>
                </div>

                <div class="cell c2">
                    <div class="cell-nucleus"></div>
                </div>

                <div class="cell c3">
                    <div class="cell-nucleus"></div>
                </div>

            </div>


            <!-- NEURON -->
            <div id="neuronWorld">

                <svg
                    id="neuron"
                    viewBox="0 0 800 500"
                    preserveAspectRatio="xMidYMid meet">

                    <g class="dendrites">

                        <path d="M390 250 C320 200 250 170 180 100"/>
                        <path d="M390 250 C320 250 230 250 120 210"/>
                        <path d="M390 250 C320 300 230 330 120 370"/>
                        <path d="M390 250 C320 190 280 120 250 60"/>
                        <path d="M390 250 C320 320 280 400 240 450"/>

                    </g>

                    <circle
                        class="soma"
                        cx="410"
                        cy="250"
                        r="75"/>

                    <circle
                        class="nucleus"
                        cx="410"
                        cy="250"
                        r="25"/>

                    <path
                        id="axon"
                        d="M485 250 C570 250 650 250 760 250"/>

                    <g class="myelin">

                        <rect x="525" y="232" width="45" height="36" rx="18"/>
                        <rect x="590" y="232" width="45" height="36" rx="18"/>
                        <rect x="655" y="232" width="45" height="36" rx="18"/>
                        <rect x="720" y="232" width="35" height="36" rx="18"/>

                    </g>

                    <circle
                        id="signal"
                        cx="500"
                        cy="250"
                        r="10"/>

                </svg>

            </div>


            <!-- SYNAPSE -->
            <div id="synapseWorld">

                <div class="synapse-title">
                    SYNAPTIC CONNECTION
                </div>

                <div class="synapse">

                    <div class="pre-terminal">
                        <span></span>
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>

                    <div class="synaptic-gap"></div>

                    <div class="post-terminal"></div>

                    <div class="neurotransmitter nt1"></div>
                    <div class="neurotransmitter nt2"></div>
                    <div class="neurotransmitter nt3"></div>
                    <div class="neurotransmitter nt4"></div>

                </div>

            </div>


            <!-- NEUROTRANSMITTER -->
            <div id="chemicalWorld">

                <div class="chemical-orbit">

                    <div class="chemical c1">D</div>
                    <div class="chemical c2">S</div>
                    <div class="chemical c3">G</div>
                    <div class="chemical c4">A</div>

                </div>

                <div class="chemical-name">
                    NEUROTRANSMITTER SIGNAL
                </div>

            </div>

        </div>

    </div>


    <!-- CONTROLS -->

    <div class="controls">

        <button id="backBtn" class="control">
            ← BACK
        </button>

        <button id="travelBtn" class="primary">
            ENTER BRAIN
        </button>

        <button id="voiceBtn" class="control">
            🔊 VOICE
        </button>

        <button id="askBtn" class="control">
            💬 ASK AYNA
        </button>

    </div>


    <div class="journey-status">

        <span class="dot"></span>

        <span id="statusText">
            Select a brain region to begin your journey.
        </span>

    </div>

</div>
"""


CSS = """

* {
    box-sizing: border-box;
}

.nl-root {
    width: 100%;
    min-height: 760px;
    background:
        radial-gradient(
            circle at center,
            #17283b 0%,
            #08111c 55%,
            #03070b 100%
        );

    border-radius: 22px;
    overflow: hidden;

    color: white;

    font-family:
        Inter,
        system-ui,
        sans-serif;
}


/* HEADER */

.nl-header {

    height: 75px;

    display: flex;

    justify-content: space-between;
    align-items: center;

    padding: 18px 25px;

    background:
        linear-gradient(
            180deg,
            rgba(255,255,255,.06),
            rgba(255,255,255,0)
        );

    border-bottom:
        1px solid rgba(255,255,255,.08);
}


.nl-title {

    font-size: 18px;
    font-weight: 700;

    letter-spacing: 2px;
}


.nl-subtitle {

    font-size: 12px;

    opacity: .6;

    margin-top: 3px;
}


.nl-stage {

    font-size: 11px;

    letter-spacing: 1.5px;

    opacity: .75;
}


/* VIEWPORT */

.viewport {

    height: 570px;

    position: relative;

    overflow: hidden;

    perspective: 1300px;

    background:
        radial-gradient(
            ellipse at center,
            rgba(60,110,160,.13),
            transparent 60%
        );
}


/* WORLD */

#world {

    position: absolute;

    width: 100%;
    height: 100%;

    left: 0;
    top: 0;

    transform-origin:
        50% 50%;

    transition:
        transform 2.5s cubic-bezier(.22,.75,.15,1);

}


/* BRAIN */

#brainLayer {

    position: absolute;

    width: 760px;
    height: 520px;

    left: 50%;
    top: 50%;

    transform:
        translate(-50%,-50%);

}


#brainImage {

    position: absolute;

    width: 100%;
    height: 100%;

    object-fit: contain;

    user-select: none;

    filter:
        drop-shadow(
            0 30px 60px rgba(0,0,0,.5)
        );

}


/* HOTSPOTS */

.hotspot {

    position: absolute;

    width: 90px;
    height: 90px;

    border-radius: 50%;

    border:
        1px solid rgba(100,220,255,.25);

    background:
        radial-gradient(
            circle,
            rgba(80,210,255,.14),
            transparent 70%
        );

    cursor: pointer;

    transition:
        .3s;

    animation:
        pulse 2.5s infinite;

}


.hotspot:hover {

    background:
        radial-gradient(
            circle,
            rgba(80,210,255,.4),
            transparent 70%
        );

    transform: scale(1.15);

}


.frontal {

    left: 70%;
    top: 26%;

}


.temporal {

    left: 51%;
    top: 65%;

}


.amygdala {

    left: 56%;
    top: 49%;

}


.striatum {

    left: 62%;
    top: 43%;

}


.acc {

    left: 64%;
    top: 34%;

}


@keyframes pulse {

    0%,100% {
        box-shadow:
            0 0 0 0 rgba(80,210,255,.1);
    }

    50% {
        box-shadow:
            0 0 0 20px rgba(80,210,255,0);
    }

}


/* PATHWAY */

#pathway {

    position: absolute;

    width: 5px;
    height: 0;

    left: 50%;
    top: 50%;

    transform:
        translate(-50%,-50%);

    background:
        linear-gradient(
            to bottom,
            transparent,
            #65ddff,
            #ffffff,
            #65ddff,
            transparent
        );

    box-shadow:
        0 0 20px #65ddff,
        0 0 50px rgba(70,210,255,.5);

    opacity: 0;

    transition:
        height 2s,
        opacity 1s;

}


/* TISSUE */

#tissue {

    position: absolute;

    inset: 0;

    opacity: 0;

    transform:
        scale(.1);

    transition:
        2s;

}


.cell {

    position: absolute;

    width: 250px;
    height: 250px;

    border-radius: 48%;

    left: 42%;
    top: 30%;

    background:
        radial-gradient(
            circle,
            #e9b2d5 0 15%,
            #ba74aa 16% 40%,
            #703f75 41% 60%,
            #34213f 61%
        );

    box-shadow:
        0 0 70px rgba(210,100,210,.35);

}


.c2 {

    left: 10%;
    top: 20%;

    transform: scale(.7);

}


.c3 {

    left: 68%;
    top: 65%;

    transform: scale(.55);

}


.cell-nucleus {

    position: absolute;

    width: 60px;
    height: 60px;

    left: 95px;
    top: 95px;

    border-radius: 50%;

    background:
        radial-gradient(
            circle,
            #fff,
            #8edfff 40%,
            #2e80a5
        );

    box-shadow:
        0 0 30px #65ddff;

}


/* NEURON */

#neuronWorld {

    position: absolute;

    inset: 0;

    opacity: 0;

    transform:
        scale(.1);

    transition:
        2s;

}


#neuron {

    width: 100%;
    height: 100%;

}


.dendrites path {

    fill: none;

    stroke: #9be8ff;

    stroke-width: 7;

    stroke-linecap: round;

    filter:
        drop-shadow(
            0 0 7px #4bd8ff
        );

}


.soma {

    fill:
        radial-gradient(
            circle,
            white,
            #8e6cae
        );

    fill: #8e6cae;

    stroke: #d9b6ff;

    stroke-width: 5;

    filter:
        drop-shadow(
            0 0 20px #a979d6
        );

}


.nucleus {

    fill: #62dcff;

    filter:
        drop-shadow(
            0 0 15px #62dcff
        );

}


#axon {

    fill: none;

    stroke: #75dcff;

    stroke-width: 12;

    stroke-linecap: round;

}


.myelin rect {

    fill: #d4edf3;

    stroke: #8ad6e8;

    stroke-width: 3;

    opacity: .85;

}


#signal {

    fill: white;

    filter:
        drop-shadow(
            0 0 12px white
        );

}


/* SYNAPSE */

#synapseWorld {

    position: absolute;

    inset: 0;

    opacity: 0;

    transform:
        scale(.1);

    transition:
        2s;

}


.synapse-title {

    position: absolute;

    top: 20%;

    width: 100%;

    text-align: center;

    font-size: 16px;

    letter-spacing: 3px;

    opacity: .7;

}


.synapse {

    position: absolute;

    width: 600px;
    height: 280px;

    left: 50%;
    top: 50%;

    transform:
        translate(-50%,-50%);

}


.pre-terminal {

    position: absolute;

    width: 250px;
    height: 180px;

    left: 30px;
    top: 50px;

    border-radius:
        50% 20% 20% 50%;

    background:
        radial-gradient(
            circle at 70% 50%,
            #c67ad1,
            #693b75
        );

}


.post-terminal {

    position: absolute;

    width: 250px;
    height: 180px;

    right: 30px;
    top: 50px;

    border-radius:
        20% 50% 50% 20%;

    background:
        radial-gradient(
            circle at 30% 50%,
            #75cbe2,
            #28516d
        );

}


.synaptic-gap {

    position: absolute;

    left: 285px;
    top: 45px;

    width: 30px;
    height: 190px;

    background:
        linear-gradient(
            90deg,
            transparent,
            rgba(255,255,255,.7),
            transparent
        );

}


.neurotransmitter {

    position: absolute;

    width: 16px;
    height: 16px;

    border-radius: 50%;

    background: #fff;

    box-shadow:
        0 0 15px #65ddff;

    animation:
        neurotransmit 2s infinite linear;

}


.nt1 {
    left: 220px;
    top: 80px;
}


.nt2 {
    left: 220px;
    top: 130px;
    animation-delay: .5s;
}


.nt3 {
    left: 220px;
    top: 170px;
    animation-delay: 1s;
}


.nt4 {
    left: 220px;
    top: 110px;
    animation-delay: 1.5s;
}


@keyframes neurotransmit {

    from {
        transform:
            translateX(0);
        opacity: 0;
    }

    30% {
        opacity: 1;
    }

    to {
        transform:
            translateX(160px);
        opacity: 0;
    }

}


/* CHEMICAL */

#chemicalWorld {

    position: absolute;

    inset: 0;

    opacity: 0;

    transform:
        scale(.1);

    transition:
        2s;

}


.chemical-orbit {

    position: absolute;

    width: 400px;
    height: 400px;

    left: 50%;
    top: 50%;

    transform:
        translate(-50%,-50%);

    border:
        1px solid rgba(120,220,255,.2);

    border-radius: 50%;

    animation:
        rotate 12s linear infinite;

}


.chemical {

    position: absolute;

    width: 80px;
    height: 80px;

    display: flex;

    justify-content: center;
    align-items: center;

    border-radius: 50%;

    background:
        radial-gradient(
            circle at 35% 30%,
            white,
            #63d8ff 30%,
            #226b8d
        );

    color: white;

    font-weight: 800;

    box-shadow:
        0 0 30px #54d8ff;

}


.c1 {
    left: 160px;
    top: -40px;
}


.c2 {
    right: -40px;
    top: 160px;
}


.c3 {
    left: 160px;
    bottom: -40px;
}


.c4 {
    left: -40px;
    top: 160px;
}


@keyframes rotate {

    to {
        transform:
            translate(-50%,-50%)
            rotate(360deg);
    }

}


.chemical-name {

    position: absolute;

    width: 100%;

    bottom: 18%;

    text-align: center;

    font-size: 14px;

    letter-spacing: 3px;

    opacity: .7;

}


/* CONTROLS */

.controls {

    display: flex;

    justify-content: center;

    gap: 12px;

    padding: 18px;

}


.control,
.primary {

    border-radius: 10px;

    padding: 11px 18px;

    border: 1px solid rgba(255,255,255,.15);

    background:
        rgba(255,255,255,.06);

    color: white;

    cursor: pointer;

}


.primary {

    background:
        linear-gradient(
            135deg,
            #2e9fc2,
            #6750a4
        );

    border: none;

}


.control:hover,
.primary:hover {

    transform:
        translateY(-2px);

}


/* STATUS */

.journey-status {

    display: flex;

    justify-content: center;

    align-items: center;

    gap: 8px;

    padding-bottom: 18px;

    font-size: 12px;

    opacity: .65;

}


.dot {

    width: 7px;
    height: 7px;

    border-radius: 50%;

    background: #65ddff;

    box-shadow:
        0 0 10px #65ddff;

}

"""


JS = """

export default function(component) {

    const {
        parentElement,
        data,
        setStateValue,
        setTriggerValue
    } = component;


    const root = parentElement;

    const brain =
        root.querySelector("#brainImage");

    const world =
        root.querySelector("#world");

    const pathway =
        root.querySelector("#pathway");

    const tissue =
        root.querySelector("#tissue");

    const neuronWorld =
        root.querySelector("#neuronWorld");

    const synapseWorld =
        root.querySelector("#synapseWorld");

    const chemicalWorld =
        root.querySelector("#chemicalWorld");

    const stageLabel =
        root.querySelector("#stageLabel");

    const statusText =
        root.querySelector("#statusText");

    const travelBtn =
        root.querySelector("#travelBtn");

    const backBtn =
        root.querySelector("#backBtn");

    const voiceBtn =
        root.querySelector("#voiceBtn");

    const askBtn =
        root.querySelector("#askBtn");


    brain.src = data.brain;


    let stage = 0;

    let selectedRegion = null;


    const stages = [
        "WHOLE BRAIN",
        "REGION",
        "TISSUE",
        "NEURON",
        "AXON",
        "SYNAPSE",
        "NEUROTRANSMITTER"
    ];


    function updateState() {

        setStateValue(
            "stage",
            stages[stage]
        );

        setStateValue(
            "region",
            selectedRegion || ""
        );

    }


    function setStage(newStage) {

        stage =
            Math.max(
                0,
                Math.min(
                    stages.length - 1,
                    newStage
                )
            );


        stageLabel.textContent =
            stages[stage];


        /*
        ===================================================
        WHOLE BRAIN
        ===================================================
        */

        if(stage === 0) {

            world.style.transform =
                "translate(0,0) scale(1)";

            brain.style.opacity = "1";

            pathway.style.opacity = "0";

            tissue.style.opacity = "0";

            neuronWorld.style.opacity = "0";

            synapseWorld.style.opacity = "0";

            chemicalWorld.style.opacity = "0";

            travelBtn.textContent =
                "ENTER BRAIN";

            statusText.textContent =
                "Select a brain region to begin your journey.";

        }


        /*
        ===================================================
        REGION
        ===================================================
        */

        if(stage === 1) {

            world.style.transform =
                "translate(-12%,-8%) scale(2.2)";

            brain.style.opacity = "1";

            pathway.style.opacity = "1";

            pathway.style.height = "55%";

            statusText.textContent =
                "Traveling toward the selected brain region...";

            travelBtn.textContent =
                "GO DEEPER";

        }


        /*
        ===================================================
        TISSUE
        ===================================================
        */

        if(stage === 2) {

            world.style.transform =
                "translate(-18%,-12%) scale(5)";

            brain.style.opacity = ".25";

            pathway.style.opacity = "1";

            pathway.style.height = "85%";

            tissue.style.opacity = "1";

            tissue.style.transform =
                "scale(1)";

            statusText.textContent =
                "Moving through the brain tissue...";

            travelBtn.textContent =
                "ENTER NEURON";

        }


        /*
        ===================================================
        NEURON
        ===================================================
        */

        if(stage === 3) {

            world.style.transform =
                "translate(0,0) scale(1)";

            brain.style.opacity = "0";

            pathway.style.opacity = "0";

            tissue.style.opacity = "0";

            neuronWorld.style.opacity = "1";

            neuronWorld.style.transform =
                "scale(1)";

            statusText.textContent =
                "You have reached a neuron.";

            travelBtn.textContent =
                "FOLLOW AXON";

        }


        /*
        ===================================================
        AXON
        ===================================================
        */

        if(stage === 4) {

            neuronWorld.style.transform =
                "scale(1.7) translateX(-15%)";

            statusText.textContent =
                "Following the electrical signal along the axon...";

            travelBtn.textContent =
                "REACH SYNAPSE";


            const signal =
                root.querySelector("#signal");


            let x = 500;


            function moveSignal() {

                x += 3;

                if(x > 750) {
                    x = 500;
                }

                signal.setAttribute(
                    "cx",
                    x
                );

                if(stage === 4) {
                    requestAnimationFrame(
                        moveSignal
                    );
                }

            }

            moveSignal();

        }


        /*
        ===================================================
        SYNAPSE
        ===================================================
        */

        if(stage === 5) {

            neuronWorld.style.opacity = "0";

            synapseWorld.style.opacity = "1";

            synapseWorld.style.transform =
                "scale(1)";

            statusText.textContent =
                "The signal reaches the synaptic connection.";

            travelBtn.textContent =
                "SEE SIGNAL";

        }


        /*
        ===================================================
        NEUROTRANSMITTER
        ===================================================
        */

        if(stage === 6) {

            synapseWorld.style.opacity = "0";

            chemicalWorld.style.opacity = "1";

            chemicalWorld.style.transform =
                "scale(1.1)";

            statusText.textContent =
                "Neurotransmitters carry chemical signals between neurons.";

            travelBtn.textContent =
                "RESTART JOURNEY";

        }


        updateState();

    }


    /*
    =======================================================
    BRAIN REGION CLICK
    =======================================================
    */

    root
        .querySelectorAll(".hotspot")
        .forEach(button => {

            button.onclick = () => {

                selectedRegion =
                    button.dataset.region;

                stage = 1;

                setStage(stage);

                setTriggerValue(
                    "region_clicked",
                    selectedRegion
                );

            };

        });


    /*
    =======================================================
    TRAVEL
    =======================================================
    */

    travelBtn.onclick = () => {

        if(stage === 6) {

            stage = 0;

        } else {

            stage += 1;

        }

        setStage(stage);

    };


    /*
    =======================================================
    BACK
    =======================================================
    */

    backBtn.onclick = () => {

        stage -= 1;

        setStage(stage);

    };


    /*
    =======================================================
    VOICE
    =======================================================
    */

    voiceBtn.onclick = () => {

        let text = "";

        if(stage === 0) {

            text =
                "You are looking at the whole brain. Select a region to begin your neural journey.";

        }

        else if(stage === 1) {

            text =
                "We are traveling toward the selected brain region.";

        }

        else if(stage === 2) {

            text =
                "We are moving through brain tissue and approaching individual neurons.";

        }

        else if(stage === 3) {

            text =
                "This is a neuron. Dendrites receive information, the cell body integrates it, and the axon carries the signal.";

        }

        else if(stage === 4) {

            text =
                "The electrical signal is traveling along the axon toward the synapse.";

        }

        else if(stage === 5) {

            text =
                "At the synapse, the electrical signal leads to chemical communication between neurons.";

        }

        else {

            text =
                "Neurotransmitters are chemical messengers that help neurons communicate.";

        }


        if(
            "speechSynthesis"
            in window
        ) {

            window.speechSynthesis.cancel();

            const utterance =
                new SpeechSynthesisUtterance(
                    text
                );

            utterance.rate = .92;
            utterance.pitch = 1;

            window.speechSynthesis.speak(
                utterance
            );

        }

    };


    /*
    =======================================================
    ASK AYNA
    =======================================================
    */

    askBtn.onclick = () => {

        setTriggerValue(
            "ask_ayna",
            {
                stage:
                    stages[stage],

                region:
                    selectedRegion || "",

                question:
                    "Explain what is happening at this stage of my neural journey."
            }
        );

    };


    setStage(0);


    return () => {

        if(
            "speechSynthesis"
            in window
        ) {

            window.speechSynthesis.cancel();

        }

    };

}

"""


# =========================================================
# CREATE COMPONENT
# =========================================================

try:

    brain_journey = st.components.v2.component(
        name="neurolens_neural_journey",
        html=HTML,
        css=CSS,
        js=JS,
        isolate_styles=True
    )

except Exception:

    st.error(
        "Tumhare Streamlit version mein Components v2 available nahi hai. "
        "requirements.txt mein latest Streamlit use karo."
    )

    st.stop()


# =========================================================
# MOUNT COMPONENT
# =========================================================

result = brain_journey(
    data={
        "brain": brain_data_uri
    },

    key="neural_journey",

    on_stage_change=lambda: None,
    on_region_change=lambda: None,
    on_region_clicked_change=lambda: None,
    on_ask_ayna_change=lambda: None
)


# =========================================================
# PYTHON RESPONSE FROM COMPONENT
# =========================================================

current_stage = getattr(
    result,
    "stage",
    None
)

current_region = getattr(
    result,
    "region",
    None
)

ask_event = getattr(
    result,
    "ask_ayna",
    None
)


# =========================================================
# REGION INFORMATION
# =========================================================

if current_region in REGIONS:

    region_info = REGIONS[current_region]

    st.markdown("---")

    st.subheader(
        f"🧠 {region_info['name']}"
    )

    st.write(
        region_info["description"]
    )


# =========================================================
# ASK AYNA
# =========================================================

if ask_event:

    st.markdown("---")

    st.subheader("💬 Ask Ayna")

    question = st.text_input(
        "Your neuroscience question:",
        value=(
            f"What is happening at the "
            f"{current_stage or 'current'} stage?"
        ),
        key="ayna_question"
    )

    if st.button(
        "Ask Ayna",
        key="ask_ayna_submit"
    ):

        with st.spinner(
            "Ayna is thinking..."
        ):

            answer =
                ask_ayna(
                    question
                )

        st.info(answer)


# =========================================================
# OLD / SIMPLE BRAIN EXPLORER
# =========================================================

st.markdown("---")

st.subheader("🔬 Brain Explorer")

selected = st.selectbox(
    "Explore a brain region",
    list(REGIONS.keys()),
    format_func=lambda x:
        REGIONS[x]["name"]
)

st.write(
    REGIONS[selected]["description"]
)


# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.caption(
    "NEUROLENS — Cognitive Neuroscience • Brain • Behavior • AI"
)

st.caption(
    "Created by Ayna Jaffri"
)
