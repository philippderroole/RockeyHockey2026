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

const scoreSoundFileNames = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"].map((name) => "resources/sounds/" + name + ".wav");

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

            const backgroundAudio = document.getElementById("backgroundAudio");
            if (backgroundAudio) {
                backgroundAudio.pause()
            }
            setTimeout(() => {
                const backgroundAudio = document.getElementById("backgroundAudio");
                backgroundAudio.volume = 0.5;

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

                            if (backgroundAudio) {
                                backgroundAudio.play();
                            }
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
        const randomTime = Math.floor(Math.random() * (480-240 + 1)) + 240;
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

function finish() {
    const scoreSpieler = document.getElementById("scoreSpieler");
    const scoreRoboter = document.getElementById("scoreRoboter");
    const playerLead = scoreSpieler.value - scoreRoboter.value;
    
    stopGame();
    if (playerLead > 0)
    	playGoalAnimation(null, "resources/sounds/winner.wav");
    if (playerLead < 0)
    	playGoalAnimation(null, "resources/sounds/lostmatch.wav");
}

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

        if (remainingTime=== 0) {
            finish();
            clearInterval(timerInterval);
        } else {
            remainingTime--;
        }

        if (gameStopped) {
            clearInterval(timerInterval);
        }
    }, 1000);
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

function fetchUpdate() {
    fetch('/state')
        .then(response => response.json())
        .then(data => {
            document.getElementById("scoreRoboter").value = data.botScore;
            document.getElementById("scoreSpieler").value = data.playerScore;
        })
}
