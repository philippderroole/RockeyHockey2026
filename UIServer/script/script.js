const gameTime = 600; // 10 Mins
let gameStopped = true;

const scoreSoundFileNames = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"].map((name) => "resources/sounds/" + name + ".wav");

function playGoalAnimation(gifName, soundName) {
   // if (gifName)
   //     playGIF(gifName);

    if (soundName) {
        goalAudio.src = soundName;
        goalAudio.volume = 0.75;
        goalAudio.play();
    }
}

let requestedAnimation = null;

document.getElementById("idleVideo").addEventListener("seeking", () => {
    let goalVideoElement = null;
    if (requestedAnimation === "right")
        goalVideoElement = rightGoalVideo;
    else if (requestedAnimation === "left")
        goalVideoElement = leftGoalVideo;
    
    if (goalVideoElement) {
        goalVideoElement.style.display = "block";
        goalVideoElement.play();
        
        idleVideo.pause();
        idleVideo.currentTime = 0;
        idleVideo.style.display = "none";
    }
    
    requestedAnimation = null;
});

leftGoalVideo.addEventListener ("ended", (e) => onGoalAnimationEnded(e.srcElement));
rightGoalVideo.addEventListener("ended", (e) => onGoalAnimationEnded(e.srcElement));

function onGoalAnimationEnded(videoElement) {
    videoElement.currentTime = 0;
    idleVideo.style.display = "block";
    idleVideo.play();
    videoElement.style.display = "none";
}

setInterval(() => {
    fetch("state").then((res) => res.json().then((json) => {
        const playerIncrement = json.playerScore - scoreSpieler.value;
        const botIncrement = json.botScore - scoreRoboter.value;
        const playerLead = json.playerScore - json.botScore;

        if (playerIncrement > 0) {
            animation("blue");
            requestedAnimation = "left";

            playGoalAnimation(null, scoreSoundFileNames[json.playerScore]);

            if (playerLead == 2)
                setTimeout(() => playGoalAnimation('losingteeth', 'resources/sounds/godlike.wav'), 1200);
            else if (playerLead == 4)
                setTimeout(() => playGoalAnimation('dog', 'resources/sounds/godlike.wav'), 1200);
            else if (playerLead > 5)
                setTimeout(() => playGoalAnimation('dominance', 'resources/sounds/dominating.wav'), 1200);
        }
        if (botIncrement > 0) {
            animation("red");
            requestedAnimation = "right";
            
            if (playerLead == -2)
                playGoalAnimation('pulp', 'resources/sounds/unstoppable.wav');
            else if (playerLead == -4)
                playGoalAnimation('pengu', 'resources/sounds/unstoppable.wav');
            else if (playerLead < -5)
                playGoalAnimation('godzilla', 'resources/sounds/rampage.wav');
        }

        scoreSpieler.value = json.playerScore;
        scoreRoboter.value = json.botScore;
    }))
}, 500);

async function startGame() {
    document.getElementById("start-button").disabled = true;

    await fetch("resetScores");
    await fetch("start");

    document.getElementById("stop-button").style.display = "block";
    document.getElementById("start-button").style.display = "none";
    document.getElementById("stop-button").disabled = false;

    startAudio.volume = 0.35;
    startAudio.play();
    backgroundAudio.play();
    gameStopped = false;
    startTimer(gameTime);
};

async function stopGame() {
    document.getElementById("stop-button").disabled = true;

    await fetch("stop");

    document.getElementById("start-button").style.display = "block";
    document.getElementById("stop-button").style.display = "none";
    document.getElementById("start-button").disabled = false;

    backgroundAudio.pause();
    backgroundAudio.currentTime = 0;
    gameStopped = true;
};

function startTimer(duration) {
    let timer = duration;
    let minutes, seconds;
    let intervalId;

    intervalId = setInterval(function () {
        minutes = parseInt(timer / 60, 10);
        seconds = parseInt(timer % 60, 10);

        minutes = minutes < 10 ? "0" + minutes : minutes;
        seconds = seconds < 10 ? "0" + seconds : seconds;

        countdown.value = minutes + ":" + seconds;

        if (--timer < 0) {
            timer = duration;
        }

        if (gameStopped) {
            clearInterval(intervalId);
        }
    }, 1000);
};

function playGIF(gifName) {
    const gifElement = document.getElementById('score-gif');
    const gifDisplay = document.getElementById('gifDisplay');

    gifElement.src = 'resources/gifs/' + gifName + '.gif';

    gifDisplay.style.display = 'block';

    setTimeout(() => {
        gifDisplay.style.display = 'none';
        gifElement.src = '';
    }, 3000);
};

function animation(color) {
    fetch("animation/" + color);
};
