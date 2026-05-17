const gameTime = 600; // 10 Mins
let gameStopped = true;
let countdownActive = false;
let countdownValue = 3;
let updateInterval; 
let remainingTime = gameTime;
let timerInterval;
let eventActive= false;
let eventStartTime = null;
let EventDuration = 30000;
let eventTimeout = null;
let remainingEventTime = null;
let requestedAnimation = null;
let isGoldenGoal = false;

const scoreSoundFileNames = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"].map((name) => "resources/sounds/" + name + ".wav");
const idleVideo = document.getElementById("idleVideo");
const leftGoalVideo = document.getElementById("leftGoalVideo");
const rightGoalVideo = document.getElementById("rightGoalVideo");
const loadingVideo = document.getElementById("loadingVideo");
const startButton = document.getElementById("startButton");
const stopButton = document.getElementById("stopButton");
const scoreSpieler = document.getElementById("scoreSpieler");
const scoreRoboter = document.getElementById("scoreRoboter");
const goalAudio = document.getElementById("goalAudio");

if (idleVideo) {
    idleVideo.addEventListener("seeking", () => {
        let goalVideoElement = null;
        if (requestedAnimation === "right") goalVideoElement = rightGoalVideo;
        else if (requestedAnimation === "left") goalVideoElement = leftGoalVideo;
        
        if (goalVideoElement) {
            goalVideoElement.style.display = "block";
            goalVideoElement.play();
            idleVideo.pause();
            idleVideo.currentTime = 0;
            idleVideo.style.display = "none";
        }
        requestedAnimation = null;
    });
}

function onGoalAnimationEnded(videoElement) {
    videoElement.currentTime = 0;
    idleVideo.style.display = "block"; 
    idleVideo.play();
    videoElement.style.display = "none";
    requestedAnimation = null;
}

leftGoalVideo.addEventListener("ended", (e) => onGoalAnimationEnded(e.srcElement)); 
rightGoalVideo.addEventListener("ended", (e) => onGoalAnimationEnded(e.srcElement));

class VisualCountdown {
    constructor(duration = 3) {
        this.duration = duration;
        this.timeLeft = duration;
        this.circumference = 2 * Math.PI * 120;
        
        this.container = document.getElementById('countdownContainer');
        this.svg = document.getElementById('countdownSvg');
        this.numberDisplay = document.getElementById('number');
        this.circle = document.getElementById('circle');
    }
    
    start() {
        return new Promise((resolve) => {
            this.timeLeft = this.duration;
            this.container.style.display = "grid";
            this.svg.style.opacity = "1";
            this.numberDisplay.innerText = this.timeLeft;
            this.numberDisplay.style.color = "#007bff";
            this.numberDisplay.style.fontSize = "56px";

            setTimeout(() => {
                const countdownAudio = document.getElementById("countdownAudio");
                if (countdownAudio) {
                    countdownAudio.volume = 1.0;
                    countdownAudio.play();
                }
            }, 500);
            
            this.circle.style.transition = "none";
            this.circle.style.strokeDashoffset = 0;
            this.circle.getBoundingClientRect(); 

            this.circle.style.transition = "none";
            this.circle.style.strokeDashoffset = 0;

            this.circle.getBoundingClientRect(); 

            const interval = setInterval(() => {
                if (this.timeLeft > 0) {
                    const nextTime = this.timeLeft - 1;
                    const offset = this.circumference - (nextTime / this.duration) * this.circumference;
                    
                    this.circle.style.transition = "stroke-dashoffset 1s linear";
                    this.circle.style.strokeDashoffset = offset;
                }

                setTimeout(() => {
                    if (this.timeLeft > 1) {
                        this.timeLeft--;
                        this.numberDisplay.innerText = this.timeLeft;
                    } else if (this.timeLeft === 1) {
                        this.timeLeft = 0; 
                        
                        this.svg.style.opacity = "0";
                        this.numberDisplay.innerText = "GO!";
                        this.numberDisplay.style.color = "red";
                        this.numberDisplay.style.fontSize = "64px";
                        
                        clearInterval(interval);
                        
                        setTimeout(() => {4
                            this.container.style.display = "none";
                            resolve();
                        }, 1200);
                    }
                }, 900);
            }, 1000);
        });
    }
}


async function startGame() {
    let loadingVideo = document.getElementById("loadingVideo");
    let idleVideo = document.getElementById("idleVideo");
    let startButton = document.getElementById("startButton");
    let scaleElement = document.getElementById("scale");
    
    isGoldenGoal = false; 
    const ggOverlay = document.getElementById("golden-goal-overlay");
    if (ggOverlay) ggOverlay.classList.remove("active");
    const ggLogo = document.getElementById("golden-goal-logo");
    if (ggLogo) ggLogo.classList.remove("active");

    if (scaleElement) {
        scaleElement.style.display = "none";
    }
    if (startButton) {
        startButton.disabled = true;
    }

    const visualCountdown = new VisualCountdown(3);
    await visualCountdown.start();
    

    if (scaleElement) {
        scaleElement.style.display = "block";
    }
    if (loadingVideo) {
        loadingVideo.pause();
        loadingVideo.style.display = "none";
    }
    if (idleVideo) { 
        idleVideo.style.display = "block";
        idleVideo.loop = true;
        idleVideo.play();
    }

    await fetch("resetScores");
    await fetch("start");

    updateInterval = setInterval(fetchUpdate, 500);

    if (eventActive && remainingEventTime !== null && remainingEventTime > 0) {
        console.log("Event wird mit Restzeit forgesetzt: " + (remainingEventTime / 1000) + "s");
        resumeEventTimer(remainingEventTime);
    } else {
        const randomTime = Math.floor(Math.random() * (480-240)) + 240;
        const min = Math.floor(randomTime / 60);
        const sec = randomTime % 60;
        const formattedTime = (min < 10 ? "0" : "") + min + ":" + (sec < 10 ? "0" : "") + sec;
        console.log("Event startet bei: " + formattedTime);
        
        setTimeout(() => {
            triggerEvent();
        }, (gameTime - randomTime) * 1000);
    }
    let stopButton = document.getElementById("stopButton");
    if (stopButton){
        stopButton.style.display = "block";
        stopButton.disabled = false;
    }
   if (startButton) {
    startButton.style.display = "none";
    startButton.disabled = false;
   }
    let startAudio = document.getElementById("startAudio");
    startAudio.volume = 0.35;
    startAudio.play();
    
    let backgroundAudio = document.getElementById("backgroundAudio");
    backgroundAudio.play();
    
    gameStopped = false;
    
    startTimer(remainingTime);
};

function fetchUpdate() {
    fetch('/state')
        .then(response => response.json())
        .then(data => {
            const currentS = parseInt(scoreSpieler.value) || 0; 
            const currentR = parseInt(scoreRoboter.value) || 0; 
            const playerIncrement = data.playerScore - currentS; 
            const botIncrement = data.botScore - currentR; 
            const playerLead = data.playerScore - data.botScore;

            if (isGoldenGoal && (playerIncrement > 0 || botIncrement > 0)) {
                scoreSpieler.value = data.playerScore;
                scoreRoboter.value = data.botScore;
                
                if (playerIncrement > 0) {
                    playGoalAnimation(null, scoreSoundFileNames[data.playerScore]);
                } else {
                    // Optional: Ein Sound für den Roboter
                    playGoalAnimation(null, "resources/sounds/lostmatch.wav"); 
                }
                setTimeout(() => finish(), 1000); 
                return;
            }

            if (playerIncrement > 0) {
                animation("blue");
                requestedAnimation = "left";
                playGoalAnimation(null, scoreSoundFileNames[data.playerScore]); 
                
                if (data.playerScore === 10) setTimeout(() => finish(), 1200);
                else if (playerLead == 2) setTimeout(() => playGoalAnimation('losingteeth', 'resources/sounds/godlike.wav'), 1200);
                else if (playerLead == 4) setTimeout(() => playGoalAnimation('dog', 'resources/sounds/godlike.wav'), 1200);
                else if (playerLead > 5) setTimeout(() => playGoalAnimation('dominance', 'resources/sounds/dominating.wav'), 1200);
            }

            if (botIncrement > 0) {
                animation("red");
                requestedAnimation = "right";
                if (data.botScore === 10) finish();
                else if (playerLead == -2) playGoalAnimation('pulp', 'resources/sounds/unstoppable.wav');
            }

            scoreRoboter.value = data.botScore;
            scoreSpieler.value = data.playerScore; 
        });
}

function playGoalAnimation(gifName, soundName) {
    if (gifName) playGIF(gifName); 
    if (soundName && goalAudio) {
        goalAudio.src = soundName;
        goalAudio.volume = 0.75; 
        goalAudio.play().catch(e => console.warn("Audio Error:", e));
    }
}

function finish() {
    const player = document.getElementById("scoreSpieler");
    const bot = document.getElementById("scoreRoboter");

    const playerScore = Number(player.value) || 0;
    const botScore = Number(bot.value) || 0;
    const playerLead = scoreSpieler.value - scoreRoboter.value;

    document.getElementById("golden-goal-logo").classList.remove("active");
    stopGame();

    const winnerDisplay = document.getElementById("winnerDisplay");
    const winnerName = document.getElementById("winnerName");
    const winnerScore = document.getElementById("winnerScore");
    const winnerTitle = document.getElementById("winnerTitle");

    const imgProf = document.getElementById("winner-img-prof");
    const imgBot = document.getElementById("winner-img-bot");

    imgProf.style.display = "none";
    imgBot.style.display = "none";

    if (playerLead > 0) {
        winnerTitle.innerText = "GEWINNER";
        winnerName.innerText = "PROF GEWINNT";
        imgProf.style.display = "block";
        playGoalAnimation(null, "resources/sounds/winner.wav");
    } else if (playerLead < 0) {
        winnerTitle.innerText = "GEWINNER";
        winnerName.innerText = "RH 2026 GEWINNT";
        imgBot.style.display = "block";
        playGoalAnimation(null, "resources/sounds/Mission_complete.mp3");
    } else {
        winnerTitle.innerText = "SPIELENDE";
        winnerName.innerText = "UNENTSCHIEDEN";
    }
    winnerScore.innerText = botScore + " : " + playerScore;
    winnerDisplay.style.display = "flex";

    const victoryMusic = document.getElementById("victoryMusic");
    const goalAudio = document.getElementById("goalAudio");
    goalAudio.onended = function() {
        victoryMusic.currentTime = 0;
        victoryMusic.volume = 0.7;
        victoryMusic.loop = true;

        victoryMusic.play().catch(function(error) {
        console.log("Sieger-Musik konnte nicht abgespielt werden:", error);
        });
    };

    const restartButton = document.getElementById("restartButton");
    if (restartButton) {
        restartButton.style.display = "none";
    }
    const confettiduration = Infinity;
    const confettiInterval = setInterval(() => {
        confetti({
        particleCount: 250,
        spread: 120,
        origin: { x: 0, y: 0.6 },
        zIndex: 11
        });

        confetti({
            particleCount: 250,
            spread: 120,
            origin: { x: 1, y: 0.6 },
            zIndex: 11
        });
    }, 2000);

    setTimeout(() => {
        if (restartButton) {
            restartButton.style.display = "block";
        }
    }, 8000);
}

async function stopGame() {
    gameStopped = true;
    if (eventActive && eventStartTime !== null) {
        let elapsedTime = Date.now() - eventStartTime;
        remainingEventTime = EventDuration - elapsedTime;

        if (remainingEventTime < 0) remainingEventTime = 0;

        if (eventTimeout) {
            clearTimeout(eventTimeout);
        }
        console.log("Event pausiert. Verbleibende Eventzeit: " + (remainingEventTime / 1000)+ "s");
    }
    fetch("event/stop");
    clearInterval(updateInterval);

    let stopButton = document.getElementById("stopButton");
    
    stopButton.disabled = true;
    
    let idleVideo = document.getElementById("idleVideo");
    idleVideo.pause();
    idleVideo.style.display = "none";
    
    let loadingVideo = document.getElementById("loadingVideo");
    loadingVideo.style.display = "block";
    loadingVideo.loop = true;
    loadingVideo.play();

    await fetch("stop");

    if (timerInterval) {
        clearInterval(timerInterval);
    }
    
    let startButton = document.getElementById("startButton");
    if (startButton && stopButton) {
        startButton.style.display = "block";
        stopButton.style.display = "none";
        startButton.disabled = false;
    }

    let backgroundAudio = document.getElementById("backgroundAudio");
    backgroundAudio.pause();
    backgroundAudio.currentTime = 0;
    
    gameStopped = true;
};

function startTimer(duration) {
    let timer = duration;
    let minutes, seconds;
    let intervalId;
    let eventTriggered= false;
    
    if (gameTime == duration && remainingTime == gameTime) {
        remainingTime = duration;
    }
    let countdown = document.getElementById("countdown");
    if (timerInterval) {
        clearInterval(timerInterval);
    }
    timerInterval = setInterval(function() {
        let minutes = parseInt(remainingTime / 60, 10);
        let seconds = parseInt(remainingTime % 60, 10);

        minutes = minutes < 10 ? "0" + minutes : minutes;
        seconds = seconds < 10 ? "0" + seconds : seconds;

        countdown.value = minutes + ":" + seconds;

        const time_overlay = document.getElementById("time-warning-overlay");
        const halftime_overlay = document.getElementById("halftime-warning-overlay");
        if (remainingTime == 300) {
            if (halftime_overlay) {
                halftime_overlay.classList.add('active');
                const LastMinuteAudio = document.getElementById("LastMinuteAudio");
                const backgroundAudio = document.getElementById("backgroundAudio");
                backgroundAudio.volume = 0.5;
                if (LastMinuteAudio) {
                    LastMinuteAudio.volume = 1.0;
                    LastMinuteAudio.play();
                     LastMinuteAudio.onended = () => {
                        if (backgroundAudio) backgroundAudio.volume = 1.0;
                     }
                }

                setTimeout(() => {
                    time_overlay.classList.remove('active');
                }, 5000);
            }
        }
        if (remainingTime == 60) {
            if (time_overlay) {
                time_overlay.classList.add('active');
                const LastMinuteAudio = document.getElementById("LastMinuteAudio");
                const backgroundAudio = document.getElementById("backgroundAudio");
                backgroundAudio.volume = 0.5;
                if (LastMinuteAudio) {
                    LastMinuteAudio.volume = 1.0;
                    LastMinuteAudio.play();
                     LastMinuteAudio.onended = () => {
                        if (backgroundAudio) backgroundAudio.volume = 1.0;
                     }
                }

                setTimeout(() => {
                    time_overlay.classList.remove('active');
                }, 5000);
            }
        }
        if (remainingTime=== 0) {
            const s = parseInt(scoreSpieler.value) || 0;
            const r = parseInt(scoreRoboter.value) || 0;

            if (s === r) {
                if (!isGoldenGoal) {
                    isGoldenGoal = true;

                    const goldenGoalAudio = document.getElementById("goldengoalAudio")
                    if (goldenGoalAudio) {
                        goldenGoalAudio.volume = 1.0;
                        goldenGoalAudio.play().catch(e => console.warn("GG Sound Error:", e));
                    }

                    const ggLogo = document.getElementById("golden-goal-logo");
                    const ggOverlay = document.getElementById("golden-goal-overlay")

                    if (ggLogo) {
                        ggLogo.classList.add('active'); 
                    }
                    if (ggOverlay) {
                        ggOverlay.classList.add("active");
                    }
                    setTimeout(() => {
                        if (ggOverlay) {
                            ggOverlay.classList.remove("active");
                        }
                    }, 5000);

                    clearInterval(timerInterval);
                } 
            }else {
                    finish();
                    clearInterval(timerInterval);
                }
        } else {
            remainingTime--;
        }

        if (gameStopped) {
            clearInterval(timerInterval);
        }
    }, 1000);
}

function resumeEventTimer(remainingMs) {
    const logo = document.getElementById('event-logo');
    if (logo) {
        logo.classList.add('active');

        eventTimeout = setTimeout(() => {
            logo.classList.remove('active');
            fetch("event/stop")
                .then(response => console.log("Event auf Server beendet"));
            remainingEventTime = null;
            eventActive = false;
        }, remainingMs);
    }
}

function triggerEvent() {
    eventActive = true;
    eventStartTime = Date.now();

    fetch("event/start")
        .then(response => console.log("Event auf Server gestartet"))
        .catch(err => console.error("Fehler beim Starten des Events:", err));

    const overlay = document.getElementById('event-overlay');
    const logo = document.getElementById('event-logo');


    if (overlay && logo) {
        overlay.classList.add('active');
        logo.classList.add('active');
        const backgroundAudio = document.getElementById("backgroundAudio");
        backgroundAudio.volume = 0.5;
        const EventAudio = document.getElementById("doublepointsAudio");
        if (EventAudio) {
            EventAudio.volume = 1.0;
            EventAudio.play();

            eventActive.onended = () => {
                backgroundAudio.volume = 1.0;
            };
        }

        setTimeout(() => {
            overlay.classList.remove('active');
        }, 5000);

        let timeToRun = remainingEventTime !== null ? remainingEventTime : EventDuration;
        eventTimeout = setTimeout(() => {
            logo.classList.remove('active');
            fetch("event/stop")
                .then(response => console.log("Event auf Server beendet"));
            
            remainingEventTime = null;
            eventActive = false;
        }, timeToRun);
    }
}

function onGoalAnimationEnded(videoElement) {
    videoElement.currentTime = 0;
    idleVideo.style.display = "block";
    idleVideo.play();
    videoElement.style.display = "none";
    
    requestedAnimation = null;
}

function playGIF(gifName) {
    const gifElement = document.getElementById('score-gif');
    const gifDisplay = document.getElementById('gifDisplay');
    gifElement.src = 'resources/gifs/' + gifName + '.gif';

    gifDisplay.style.display = 'block';
    setTimeout(() => {
        gifDisplay.style.display = 'none';
        gifElement.src = '';
    }, 3000);
}
function animation(color) {
    fetch("animation/" + color);
}