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
    
    requestedAnimation = null;
}

function update(playerScore, botScore) {
    const playerIncrement = playerScore - scoreSpieler.value;
        const botIncrement = botScore - scoreRoboter.value;
        const playerLead = playerScore - botScore;

        if (playerIncrement > 0) {
            animation("blue");
            requestedAnimation = "left";

            playGoalAnimation(null, scoreSoundFileNames[playerScore]);
            
            if (playerScore === 10)
                setTimeout(() => finish(), 1200);
            else if (playerLead == 2)
                setTimeout(() => playGoalAnimation('losingteeth', 'resources/sounds/godlike.wav'), 1200);
            else if (playerLead == 4)
                setTimeout(() => playGoalAnimation('dog', 'resources/sounds/godlike.wav'), 1200);
            else if (playerLead > 5)
                setTimeout(() => playGoalAnimation('dominance', 'resources/sounds/dominating.wav'), 1200);
        }
        if (botIncrement > 0) {
            animation("red");
            requestedAnimation = "right";
            
            if (botScore === 10)
                finish();
            else if (playerLead == -2)
                playGoalAnimation('pulp', 'resources/sounds/unstoppable.wav');
            else if (playerLead == -4)
                playGoalAnimation('pengu', 'resources/sounds/unstoppable.wav');
            else if (playerLead < -5)
                playGoalAnimation('godzilla', 'resources/sounds/rampage.wav');
        }

        scoreSpieler.value = playerScore;
        scoreRoboter.value = botScore;
    
}

async function fetchUpdate() {
    const response = await fetch("state");
    const json = await response.json();
    update(json.playerScore, json.botScore);
}

let updateInterval = null;

async function startGame() {
    let loadingVideo = document.getElementById("loadingVideo");
    loadingVideo.pause();
    loadingVideo.style.display = "none";
    
    idleVideo.style.display = "block";
    idleVideo.loop = true;
    idleVideo.play();
    
    startButton.disabled = true;

    await fetch("resetScores");
    await fetch("start");
    
    updateInterval = setInterval(fetchUpdate, 500);

    stopButton.style.display = "block";
    startButton.style.display = "none";
    stopButton.disabled = false;

    startAudio.volume = 0.35;
    startAudio.play();
    backgroundAudio.play();
    gameStopped = false;
    startTimer(gameTime);
};

async function stopGame() {
    stopButton.disabled = true;
    
    
    idleVideo.pause();
    idleVideo.style.display = "none";
    
    loadingVideo.style.display = "block";
    loadingVideo.loop = true;
    loadingVideo.play();
    

    await fetch("stop");

    clearInterval(updateInterval);
    updateInterval = null;
    
    startButton.style.display = "block";
    stopButton.style.display = "none";
    startButton.disabled = false;

    backgroundAudio.pause();
    backgroundAudio.currentTime = 0;
    gameStopped = true;
};

function finish() {
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

    intervalId = setInterval(function () {
        minutes = parseInt(timer / 60, 10);
        seconds = parseInt(timer % 60, 10);

        minutes = minutes < 10 ? "0" + minutes : minutes;
        seconds = seconds < 10 ? "0" + seconds : seconds;

        countdown.value = minutes + ":" + seconds;

        if (timer === 0) {
            finish();
            clearInterval(intervalId);
        } else
            timer--;

        if (gameStopped)
            clearInterval(intervalId);
        
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
