import os
import base64
import streamlit as st
from google import genai


# =========================================================
# PAGE
# =========================================================

st.set_page_config(
    page_title="NEUROLENS",
    page_icon="🧠",
    layout="wide"
)


# =========================================================
# GEMINI
# =========================================================

def get_api_key():
    try:
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]

        if "GOOGLE_API_KEY" in st.secrets:
            return st.secrets["GOOGLE_API_KEY"]

    except Exception:
        pass

    return (
        os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
    )


def ask_ayna(question):

    api_key = get_api_key()

    if not api_key:
        return "Gemini API key nahi mili."

    try:

        client = genai.Client(
            api_key=api_key
        )

        prompt = f"""
You are Ayna, the educational neuroscience guide
inside NEUROLENS.

Explain neuroscience in simple but scientifically
accurate language.

Do not diagnose.
Do not claim that simple cognitive games measure
actual brain activity.

User question:
{question}
"""

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        return response.text

    except Exception as e:

        return f"Ask Ayna error: {e}"


# =========================================================
# BRAIN IMAGE
# =========================================================

BRAIN_FILE = "brain.png"

if not os.path.exists(BRAIN_FILE):

    st.error(
        "❌ brain.png nahi mili. "
        "GitHub mein app.py ke saath brain.png upload karo."
    )

    st.stop()


with open(BRAIN_FILE, "rb") as file:

    brain_bytes = file.read()


brain_base64 = base64.b64encode(
    brain_bytes
).decode("utf-8")


# =========================================================
# BRAIN REGIONS
# =========================================================

REGIONS = {

    "frontal": {
        "name": "Prefrontal Cortex",
        "text": (
            "Planning, decision-making, working memory, "
            "attention and cognitive control."
        )
    },

    "temporal": {
        "name": "Hippocampus",
        "text": (
            "Important for memory formation, "
            "learning and spatial navigation."
        )
    },

    "amygdala": {
        "name": "Amygdala",
        "text": (
            "Helps process emotional significance, "
            "especially threat and fear-related information."
        )
    },

    "striatum": {
        "name": "Striatum",
        "text": (
            "Involved in reward, motivation, "
            "action selection and habit learning."
        )
    },

    "acc": {
        "name": "Anterior Cingulate Cortex",
        "text": (
            "Contributes to conflict monitoring, "
            "error processing, attention and decision-making."
        )
    }
}


# =========================================================
# HTML
# =========================================================

HTML = """

<div class="nl">

    <div class="top">

        <div>
            <div class="title">
                NEURAL JOURNEY
            </div>

            <div class="sub">
                Travel inside the brain
            </div>
        </div>

        <div id="stage">
            WHOLE BRAIN
        </div>

    </div>


    <div class="screen">

        <div id="world">


            <!-- =========================================
                 REAL BRAIN
            ========================================== -->

            <div id="brain">

                <img
                    id="brainImg"
                    src=""
                    draggable="false"
                >


                <!-- BRAIN HOTSPOTS -->

                <button
                    class="spot frontal"
                    data-region="frontal">
                </button>

                <button
                    class="spot temporal"
                    data-region="temporal">
                </button>

                <button
                    class="spot amygdala"
                    data-region="amygdala">
                </button>

                <button
                    class="spot striatum"
                    data-region="striatum">
                </button>

                <button
                    class="spot acc"
                    data-region="acc">
                </button>

            </div>


            <!-- =========================================
                 TRAVEL PATH
            ========================================== -->

            <div id="travelPath"></div>


            <!-- =========================================
                 TISSUE
            ========================================== -->

            <div id="tissue">

                <div class="cell cell1">
                    <div class="nucleus"></div>
                </div>

                <div class="cell cell2">
                    <div class="nucleus"></div>
                </div>

                <div class="cell cell3">
                    <div class="nucleus"></div>
                </div>

            </div>


            <!-- =========================================
                 NEURON
            ========================================== -->

            <div id="neuronWorld">

                <svg
                    viewBox="0 0 900 500"
                    id="neuron">

                    <g class="dendrites">

                        <path d="M420 250 C330 180 250 120 130 70"/>
                        <path d="M420 250 C320 220 220 210 90 180"/>
                        <path d="M420 250 C320 280 210 310 90 360"/>
                        <path d="M420 250 C350 330 300 400 210 450"/>

                    </g>


                    <circle
                        cx="430"
                        cy="250"
                        r="78"
                        class="soma"
                    />


                    <circle
                        cx="430"
                        cy="250"
                        r="28"
                        class="nucleus2"
                    />


                    <path
                        id="axon"
                        d="M505 250 C620 250 730 250 870 250"
                    />


                    <g class="myelin">

                        <rect x="555" y="228"
                              width="55" height="44"
                              rx="20"/>

                        <rect x="630" y="228"
                              width="55" height="44"
                              rx="20"/>

                        <rect x="705" y="228"
                              width="55" height="44"
                              rx="20"/>

                        <rect x="780" y="228"
                              width="55" height="44"
                              rx="20"/>

                    </g>


                    <circle
                        id="signal"
                        cx="510"
                        cy="250"
                        r="11"
                    />

                </svg>

            </div>


            <!-- =========================================
                 SYNAPSE
            ========================================== -->

            <div id="synapseWorld">

                <div class="synapseLabel">
                    SYNAPTIC CONNECTION
                </div>


                <div class="synapse">

                    <div class="preNeuron">

                        <div class="vesicle v1"></div>
                        <div class="vesicle v2"></div>
                        <div class="vesicle v3"></div>
                        <div class="vesicle v4"></div>

                    </div>


                    <div class="gap"></div>


                    <div class="postNeuron">

                        <div class="receptor r1"></div>
                        <div class="receptor r2"></div>
                        <div class="receptor r3"></div>

                    </div>


                    <div class="chemical c1"></div>
                    <div class="chemical c2"></div>
                    <div class="chemical c3"></div>
                    <div class="chemical c4"></div>

                </div>

            </div>


            <!-- =========================================
                 NEUROTRANSMITTER
            ========================================== -->

            <div id="chemicalWorld">

                <div class="molecule">

                    <div class="mol m1">
                        D
                    </div>

                    <div class="mol m2">
                        S
                    </div>

                    <div class="mol m3">
                        G
                    </div>

                    <div class="mol m4">
                        A
                    </div>

                </div>


                <div class="chemicalText">
                    NEUROTRANSMITTER SIGNAL
                </div>

            </div>


        </div>

    </div>


    <!-- =========================================
         CONTROLS
    ========================================== -->

    <div class="controls">

        <button id="back">
            ← BACK
        </button>

        <button id="travel">
            ENTER BRAIN
        </button>

        <button id="voice">
            🔊 VOICE
        </button>

        <button id="ask">
            💬 ASK AYNA
        </button>

    </div>


    <div class="status">

        <span class="statusDot"></span>

        <span id="statusText">
            Select a brain region to begin.
        </span>

    </div>

</div>

"""


# =========================================================
# CSS
# =========================================================

CSS = """

* {
    box-sizing: border-box;
}


.nl {

    width: 100%;

    min-height: 720px;

    overflow: hidden;

    border-radius: 22px;

    color: white;

    background:
        radial-gradient(
            circle at center,
            #182b40,
            #07111d 60%,
            #02060a
        );

    font-family:
        Arial,
        sans-serif;

}


/* HEADER */

.top {

    height: 75px;

    display: flex;

    align-items: center;

    justify-content: space-between;

    padding: 18px 25px;

    border-bottom:
        1px solid rgba(255,255,255,.1);

}


.title {

    font-size: 18px;

    font-weight: bold;

    letter-spacing: 3px;

}


.sub {

    margin-top: 4px;

    font-size: 12px;

    opacity: .55;

}


#stage {

    font-size: 11px;

    letter-spacing: 2px;

    opacity: .7;

}


/* SCREEN */

.screen {

    height: 540px;

    position: relative;

    overflow: hidden;

}


#world {

    position: absolute;

    width: 100%;

    height: 100%;

    transform-origin: 50% 50%;

    transition:
        transform 2.8s
        cubic-bezier(.2,.8,.15,1);

}


/* BRAIN */

#brain {

    position: absolute;

    width: 760px;

    height: 500px;

    left: 50%;

    top: 50%;

    transform:
        translate(-50%,-50%);

}


#brainImg {

    width: 100%;

    height: 100%;

    object-fit: contain;

    user-select: none;

    filter:
        drop-shadow(
            0 30px 50px
            rgba(0,0,0,.5)
        );

}


/* HOTSPOTS */

.spot {

    position: absolute;

    width: 65px;

    height: 65px;

    border-radius: 50%;

    border:
        2px solid
        rgba(90,220,255,.4);

    background:
        radial-gradient(
            circle,
            rgba(90,220,255,.22),
            transparent 70%
        );

    cursor: pointer;

    animation:
        pulse 2s infinite;

}


.spot:hover {

    transform:
        scale(1.25);

    background:
        radial-gradient(
            circle,
            rgba(90,220,255,.45),
            transparent 70%
        );

}


.frontal {

    left: 69%;
    top: 25%;

}


.temporal {

    left: 50%;
    top: 65%;

}


.amygdala {

    left: 56%;
    top: 48%;

}


.striatum {

    left: 62%;
    top: 40%;

}


.acc {

    left: 65%;
    top: 31%;

}


@keyframes pulse {

    0%,100% {

        box-shadow:
            0 0 0 0
            rgba(80,210,255,.15);

    }

    50% {

        box-shadow:
            0 0 0 18px
            rgba(80,210,255,0);

    }

}


/* TRAVEL PATH */

#travelPath {

    position: absolute;

    left: 50%;

    top: 50%;

    width: 5px;

    height: 0;

    opacity: 0;

    transform:
        translate(-50%,-50%);

    background:
        linear-gradient(
            to bottom,
            transparent,
            #72e4ff,
            white,
            #72e4ff,
            transparent
        );

    box-shadow:
        0 0 20px #5edcff,
        0 0 55px rgba(70,210,255,.5);

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
        scale(.05);

    transition:
        2.5s;

}


.cell {

    position: absolute;

    width: 230px;

    height: 230px;

    border-radius: 50%;

    background:
        radial-gradient(
            circle,
            #f1c0dc 0 12%,
            #b46ca7 25%,
            #704172 55%,
            #28182f 100%
        );

    box-shadow:
        0 0 60px
        rgba(220,110,220,.35);

}


.cell1 {

    left: 38%;
    top: 28%;

}


.cell2 {

    left: 8%;
    top: 20%;

    transform: scale(.65);

}


.cell3 {

    right: 8%;
    bottom: 10%;

    transform: scale(.55);

}


.nucleus {

    position: absolute;

    width: 55px;

    height: 55px;

    left: 87px;

    top: 87px;

    border-radius: 50%;

    background:
        radial-gradient(
            circle,
            white,
            #6de0ff 45%,
            #24677f
        );

    box-shadow:
        0 0 25px #6de0ff;

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

    stroke: #8ee8ff;

    stroke-width: 8;

    stroke-linecap: round;

    filter:
        drop-shadow(
            0 0 8px #52d9ff
        );

}


.soma {

    fill: #835c9f;

    stroke: #dcbcff;

    stroke-width: 5;

    filter:
        drop-shadow(
            0 0 20px #a875d8
        );

}


.nucleus2 {

    fill: #63dcff;

    filter:
        drop-shadow(
            0 0 15px #63dcff
        );

}


#axon {

    fill: none;

    stroke: #6bdfff;

    stroke-width: 13;

    stroke-linecap: round;

}


.myelin rect {

    fill: #d8eff4;

    stroke: #8bd8e9;

    stroke-width: 3;

}


#signal {

    fill: white;

    filter:
        drop-shadow(
            0 0 14px white
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


.synapseLabel {

    position: absolute;

    width: 100%;

    top: 18%;

    text-align: center;

    letter-spacing: 3px;

    font-size: 14px;

    opacity: .65;

}


.synapse {

    position: absolute;

    width: 650px;

    height: 300px;

    left: 50%;

    top: 50%;

    transform:
        translate(-50%,-50%);

}


.preNeuron {

    position: absolute;

    left: 20px;

    top: 50px;

    width: 270px;

    height: 190px;

    border-radius:
        55% 20% 20% 55%;

    background:
        radial-gradient(
            circle at 70% 50%,
            #c77ad1,
            #61356f
        );

}


.postNeuron {

    position: absolute;

    right: 20px;

    top: 50px;

    width: 270px;

    height: 190px;

    border-radius:
        20% 55% 55% 20%;

    background:
        radial-gradient(
            circle at 30% 50%,
            #6bcce5,
            #27526d
        );

}


.gap {

    position: absolute;

    left: 305px;

    top: 40px;

    width: 35px;

    height: 210px;

    background:
        linear-gradient(
            90deg,
            transparent,
            rgba(255,255,255,.8),
            transparent
        );

}


.vesicle {

    position: absolute;

    width: 20px;

    height: 20px;

    border-radius: 50%;

    background: #ffeaff;

    box-shadow:
        0 0 12px #ffb8ff;

}


.v1 {
    right: 35px;
    top: 35px;
}

.v2 {
    right: 50px;
    top: 75px;
}

.v3 {
    right: 35px;
    top: 120px;
}

.v4 {
    right: 55px;
    top: 160px;
}


.receptor {

    position: absolute;

    left: 15px;

    width: 30px;

    height: 45px;

    border-radius: 10px;

    background: #b9f4ff;

    box-shadow:
        0 0 12px #61dcff;

}


.r1 {
    top: 40px;
}

.r2 {
    top: 85px;
}

.r3 {
    top: 130px;
}


.chemical {

    position: absolute;

    width: 15px;

    height: 15px;

    border-radius: 50%;

    background: white;

    box-shadow:
        0 0 14px #6ce0ff;

    animation:
        crossGap 2s infinite linear;

}


.c1 {
    left: 250px;
    top: 80px;
}

.c2 {
    left: 255px;
    top: 125px;
    animation-delay: .4s;
}

.c3 {
    left: 250px;
    top: 165px;
    animation-delay: .8s;
}

.c4 {
    left: 265px;
    top: 105px;
    animation-delay: 1.2s;
}


@keyframes crossGap {

    0% {
        transform: translateX(0);
        opacity: 0;
    }

    25% {
        opacity: 1;
    }

    100% {
        transform: translateX(150px);
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


.molecule {

    position: absolute;

    width: 390px;

    height: 390px;

    left: 50%;

    top: 48%;

    transform:
        translate(-50%,-50%);

    border:
        1px solid
        rgba(100,220,255,.25);

    border-radius: 50%;

    animation:
        rotate 12s linear infinite;

}


.mol {

    position: absolute;

    width: 75px;

    height: 75px;

    display: flex;

    align-items: center;

    justify-content: center;

    border-radius: 50%;

    background:
        radial-gradient(
            circle at 30% 25%,
            white,
            #61d9ff 35%,
            #246b8c
        );

    box-shadow:
        0 0 30px #5edcff;

    font-weight: bold;

}


.m1 {
    left: 157px;
    top: -38px;
}

.m2 {
    right: -38px;
    top: 157px;
}

.m3 {
    left: 157px;
    bottom: -38px;
}

.m4 {
    left: -38px;
    top: 157px;
}


@keyframes rotate {

    to {

        transform:
            translate(-50%,-50%)
            rotate(360deg);

    }

}


.chemicalText {

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

    gap: 10px;

    padding: 17px;

}


.controls button {

    padding:
        11px 17px;

    border-radius: 10px;

    border:
        1px solid
        rgba(255,255,255,.15);

    background:
        rgba(255,255,255,.07);

    color: white;

    cursor: pointer;

}


#travel {

    background:
        linear-gradient(
            135deg,
            #299fc4,
            #6b52a7
        );

    border: none;

}


.controls button:hover {

    transform:
        translateY(-2px);

}


/* STATUS */

.status {

    display: flex;

    justify-content: center;

    align-items: center;

    gap: 8px;

    padding-bottom: 18px;

    font-size: 12px;

    opacity: .65;

}


.statusDot {

    width: 7px;

    height: 7px;

    border-radius: 50%;

    background: #64ddff;

    box-shadow:
        0 0 10px #64ddff;

}

"""


# =========================================================
# JAVASCRIPT
# =========================================================

JS = """

export default function(component) {

    const {
        parentElement,
        data,
        setStateValue,
        setTriggerValue
    } = component;


    const root = parentElement;


    const brainImg =
        root.querySelector("#brainImg");

    brainImg.src =
        "data:image/png;base64," + data.brain;


    const world =
        root.querySelector("#world");

    const brain =
        root.querySelector("#brain");

    const path =
        root.querySelector("#travelPath");

    const tissue =
        root.querySelector("#tissue");

    const neuron =
        root.querySelector("#neuronWorld");

    const synapse =
        root.querySelector("#synapseWorld");

    const chemical =
        root.querySelector("#chemicalWorld");


    const stageText =
        root.querySelector("#stage");

    const status =
        root.querySelector("#statusText");


    const travel =
        root.querySelector("#travel");

    const back =
        root.querySelector("#back");

    const voice =
        root.querySelector("#voice");

    const ask =
        root.querySelector("#ask");


    const stages = [

        "WHOLE BRAIN",
        "BRAIN REGION",
        "BRAIN TISSUE",
        "NEURON",
        "AXON",
        "SYNAPSE",
        "NEUROTRANSMITTER"

    ];


    let currentStage = 0;

    let selectedRegion = "";


    function sendState() {

        setStateValue(
            "stage",
            stages[currentStage]
        );

        setStateValue(
            "region",
            selectedRegion
        );

    }


    function showStage(n) {

        currentStage = Math.max(
            0,
            Math.min(
                stages.length - 1,
                n
            )
        );


        stageText.textContent =
            stages[currentStage];


        /* WHOLE BRAIN */

        if(currentStage === 0) {

            world.style.transform =
                "translate(0,0) scale(1)";

            brain.style.opacity = "1";

            path.style.opacity = "0";

            path.style.height = "0";

            tissue.style.opacity = "0";

            tissue.style.transform =
                "scale(.05)";

            neuron.style.opacity = "0";

            synapse.style.opacity = "0";

            chemical.style.opacity = "0";

            travel.textContent =
                "ENTER BRAIN";

            status.textContent =
                "Select a glowing point on the brain.";

        }


        /* REGION */

        if(currentStage === 1) {

            world.style.transform =
                "translate(-10%,-7%) scale(2.2)";

            brain.style.opacity = "1";

            path.style.opacity = "1";

            path.style.height = "55%";

            travel.textContent =
                "GO DEEPER";

            status.textContent =
                "Traveling into the selected brain region...";

        }


        /* TISSUE */

        if(currentStage === 2) {

            world.style.transform =
                "translate(-17%,-10%) scale(5)";

            brain.style.opacity = ".22";

            path.style.opacity = "1";

            path.style.height = "85%";

            tissue.style.opacity = "1";

            tissue.style.transform =
                "scale(1)";

            travel.textContent =
                "ENTER NEURON";

            status.textContent =
                "Moving through the brain tissue...";

        }


        /* NEURON */

        if(currentStage === 3) {

            world.style.transform =
                "translate(0,0) scale(1)";

            brain.style.opacity = "0";

            path.style.opacity = "0";

            tissue.style.opacity = "0";

            neuron.style.opacity = "1";

            neuron.style.transform =
                "scale(1)";

            travel.textContent =
                "FOLLOW AXON";

            status.textContent =
                "You have reached a neuron.";

        }


        /* AXON */

        if(currentStage === 4) {

            neuron.style.opacity = "1";

            neuron.style.transform =
                "scale(1.65) translateX(-14%)";

            travel.textContent =
                "REACH SYNAPSE";

            status.textContent =
                "Following the electrical signal along the axon...";

        }


        /* SYNAPSE */

        if(currentStage === 5) {

            neuron.style.opacity = "0";

            synapse.style.opacity = "1";

            synapse.style.transform =
                "scale(1)";

            travel.textContent =
                "SEE CHEMICAL SIGNAL";

            status.textContent =
                "The signal reaches the synaptic connection.";

        }


        /* NEUROTRANSMITTER */

        if(currentStage === 6) {

            synapse.style.opacity = "0";

            chemical.style.opacity = "1";

            chemical.style.transform =
                "scale(1)";

            travel.textContent =
                "RESTART";

            status.textContent =
                "Neurotransmitters carry chemical signals between neurons.";

        }


        sendState();

    }


    /* ===============================================
       BRAIN REGION CLICK
    =============================================== */

    root
        .querySelectorAll(".spot")
        .forEach((button) => {

            button.onclick = () => {

                selectedRegion =
                    button.dataset.region;

                currentStage = 1;

                showStage(1);

                setTriggerValue(
                    "region_clicked",
                    selectedRegion
                );

            };

        });


    /* ===============================================
       TRAVEL
    =============================================== */

    travel.onclick = () => {

        if(currentStage === 6) {

            showStage(0);

        } else {

            showStage(
                currentStage + 1
            );

        }

    };


    /* ===============================================
       BACK
    =============================================== */

    back.onclick = () => {

        showStage(
            currentStage - 1
        );

    };


    /* ===============================================
       VOICE
    =============================================== */

    voice.onclick = () => {

        let message = "";


        if(currentStage === 0) {

            message =
                "You are viewing the whole brain. Select a region to begin your neural journey.";

        }

        else if(currentStage === 1) {

            message =
                "We are traveling into the selected brain region.";

        }

        else if(currentStage === 2) {

            message =
                "We are moving through brain tissue toward individual neurons.";

        }

        else if(currentStage === 3) {

            message =
                "This is a neuron. Dendrites receive information, the cell body processes it, and the axon carries the signal.";

        }

        else if(currentStage === 4) {

            message =
                "The electrical signal is traveling along the axon toward the synapse.";

        }

        else if(currentStage === 5) {

            message =
                "The signal has reached the synapse, where neurons communicate chemically.";

        }

        else {

            message =
                "Neurotransmitters are chemical messengers that help neurons communicate.";

        }


        if(
            "speechSynthesis"
            in window
        ) {

            window.speechSynthesis.cancel();

            const speech =
                new SpeechSynthesisUtterance(
                    message
                );

            speech.rate = .9;

            speech.pitch = 1;

            window.speechSynthesis.speak(
                speech
            );

        }

    };


    /* ===============================================
       ASK AYNA
    =============================================== */

    ask.onclick = () => {

        setTriggerValue(
            "ask_ayna",
            {
                stage:
                    stages[currentStage],

                region:
                    selectedRegion,

                question:
                    "Explain what is happening at this stage of my neural journey."
            }
        );

    };


    /* ===============================================
       AXON SIGNAL
    =============================================== */

    let signalX = 510;

    function animateSignal() {

        const signal =
            root.querySelector("#signal");

        if(signal) {

            signalX += 2.5;

            if(signalX > 850) {

                signalX = 510;

            }

            signal.setAttribute(
                "cx",
                signalX
            );

        }

        requestAnimationFrame(
            animateSignal
        );

    }

    animateSignal();


    /* START */

    showStage(0);


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
# COMPONENT
# =========================================================

try:

    journey = st.components.v2.component(
        name="neurolens_neural_journey",
        html=HTML,
        css=CSS,
        js=JS,
        isolate_styles=True
    )

except Exception as error:

    st.error(
        "NEUROLENS component load nahi hua."
    )

    st.code(str(error))

    st.stop()


# =========================================================
# MOUNT
# =========================================================

result = journey(

    data={
        "brain": brain_base64
    },

    default={
        "stage": "WHOLE BRAIN",
        "region": ""
    },

    key="neural_journey",

    on_stage_change=lambda: None,
    on_region_change=lambda: None,
    on_region_clicked_change=lambda: None,
    on_ask_ayna_change=lambda: None
)


# =========================================================
# PYTHON STATE
# =========================================================

current_stage = getattr(
    result,
    "stage",
    "WHOLE BRAIN"
)


current_region = getattr(
    result,
    "region",
    ""
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

    st.markdown("---")

    st.subheader(
        "🧠 " +
        REGIONS[current_region]["name"]
    )

    st.write(
        REGIONS[current_region]["text"]
    )


# =========================================================
# ASK AYNA
# =========================================================

if ask_event:

    st.markdown("---")

    st.subheader(
        "💬 Ask Ayna"
    )

    default_question = (
        "Explain what is happening at "
        f"the {current_stage} stage of "
        "my neural journey."
    )


    question = st.text_input(
        "Question",
        value=default_question,
        key="neural_question"
    )


    if st.button(
        "Ask Ayna",
        key="neural_ask_button"
    ):

        with st.spinner(
            "Ayna is thinking..."
        ):

            answer = ask_ayna(
                question
            )

        st.info(answer)


# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.caption(
    "NEUROLENS • Cognitive Neuroscience • Brain • Behavior • AI"
)

st.caption(
    "Created by Ayna Jaffri"
)
